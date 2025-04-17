import os
import json
import sys
import re
from openai import OpenAI

def extract_papers_from_response(text):
    """Extract paper names and URLs directly from the response text"""
    papers = []
    
    # First try to extract from JSON code block
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
        
        # Extract paper names and URLs using a more precise regex
        # This pattern looks for "paper_name": "title" and "paper_url": "url" pairs
        paper_pattern = r'"paper_name":\s*"([^"]+)".*?"paper_url":\s*"([^"]+)"'
        paper_matches = re.finditer(paper_pattern, json_text, re.DOTALL)
        
        for match in paper_matches:
            name = match.group(1)
            url = match.group(2)
            papers.append({
                "paper_name": name,
                "paper_url": url
            })
    
    # If no papers were found, try a more general approach
    if not papers:
        # Look for patterns like "paper_name": "Title" and "paper_url": "URL" in the entire text
        paper_pattern = r'"paper_name":\s*"([^"]+)".*?"paper_url":\s*"([^"]+)"'
        paper_matches = re.finditer(paper_pattern, text, re.DOTALL)
        
        for match in paper_matches:
            name = match.group(1)
            url = match.group(2)
            papers.append({
                "paper_name": name,
                "paper_url": url
            })
    
    # If still no papers, try an even more general approach
    if not papers:
        # Try to find all URLs and associate them with preceding text that might be titles
        url_matches = re.finditer(r'(https?://[^\s"]+)', text)
        for match in url_matches:
            url = match.group(1)
            # Look for a potential title before this URL
            start_pos = max(0, match.start() - 200)  # Look at up to 200 chars before URL
            context = text[start_pos:match.start()]
            # Try to find the last quotation-enclosed text before the URL
            title_match = re.search(r'"([^"]+)"[^"]*$', context)
            if title_match:
                papers.append({
                    "paper_name": title_match.group(1),
                    "paper_url": url
                })
    
    return papers

def main():
    # Check if API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set your OpenAI API key using:")
        print("  export OPENAI_API_KEY='your-api-key'")
        print("You can find your API key at https://platform.openai.com/account/api-keys")
        sys.exit(1)
    
    # Create directories if they don't exist
    os.makedirs("data/json", exist_ok=True)
    os.makedirs("data/pdf", exist_ok=True)
    
    output_file = "data/json/adam_optimizer_papers.json"
    
    try:
        # Initialize the OpenAI client
        client = OpenAI()
        
        # Make the API request
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input="Please provide a comprehensive report on recent advancements in optimization techniques, with a particular focus on improvements to the Adam optimizer. The report should reference up-to-date research from leading conferences such as NeurIPS and ICLR. Output should be json. Content should be paper_url, paper_name."
        )
        
        # Print the raw response text
        print("Raw API Response:")
        print(response.output_text)
        
        # Try to parse the JSON directly
        try:
            json_data = json.loads(response.output_text)
            valid_json = True
            print("Successfully parsed JSON directly from response.")
        except json.JSONDecodeError:
            valid_json = False
            
        # If direct parsing fails, try to extract papers from the response
        if not valid_json:
            print("\nAttempting to extract papers from response...")
            papers = extract_papers_from_response(response.output_text)
            
            if papers:
                print(f"Successfully extracted {len(papers)} papers from response!")
                json_data = {"papers": papers}
                valid_json = True
            else:
                print("Could not extract papers from response.")
                valid_json = False
        
        # If we have valid JSON, write it to file
        if valid_json:
            # If we extracted papers directly, create a clean JSON structure
            if not valid_json and papers:
                # Create a clean JSON structure with the extracted papers
                clean_json = {"papers": []}
                for paper in papers:
                    clean_json["papers"].append({
                        "paper_name": paper["paper_name"],
                        "paper_url": paper["paper_url"]
                    })
                json_data = clean_json
            else:
                # Ensure we have the expected format
                if isinstance(json_data, list):
                    # Wrap the array in a papers object
                    json_data = {"papers": json_data}
                elif isinstance(json_data, dict) and "papers" not in json_data:
                    # If it's a dict but doesn't have a papers key, wrap it
                    json_data = {"papers": [json_data]}
            
            # Create a clean JSON structure from scratch
            clean_json = {"papers": []}
            if "papers" in json_data and isinstance(json_data["papers"], list):
                for paper in json_data["papers"]:
                    if "paper_name" in paper and "paper_url" in paper:
                        clean_json["papers"].append({
                            "paper_name": paper["paper_name"],
                            "paper_url": paper["paper_url"]
                        })
            
            # Write the clean JSON to file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(clean_json, f, indent=2, ensure_ascii=False)
            print(f"\nJSON response saved to {output_file}")
            
            # Print formatted JSON
            print("\nFormatted JSON:")
            print(json.dumps(clean_json, indent=2, ensure_ascii=False))
        else:
            print("\nError: Could not parse or extract papers from the API response.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
