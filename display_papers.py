import json
import sys
import os
import argparse

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def display_papers(json_file, output_file=None):
    """Display papers from JSON file in a readable format"""
    try:
        # Read the JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the expected structure exists
        if 'papers' not in data:
            message = f"Error: JSON file does not contain 'papers' key"
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(message)
            print(f"{Colors.RED}{message}{Colors.ENDC}")
            return
        
        papers = data['papers']
        if not papers:
            message = f"No papers found in the JSON file"
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(message)
            print(f"{Colors.YELLOW}{message}{Colors.ENDC}")
            return
        
        # Get the search query from metadata if available, otherwise use a default title
        title = "RESEARCH PAPERS"
        if 'metadata' in data and 'query' in data['metadata']:
            query = data['metadata']['query']
            title = f"RESEARCH PAPERS ON {query.upper()}"
        
        # Prepare output
        output = []
        output.append("=" * 80)
        output.append(f"{title:^80}")
        output.append("=" * 80)
        output.append("")
        
        for i, paper in enumerate(papers, 1):
            output.append(f"{i}. {paper['paper_name']}")
            output.append(f"   URL: {paper['paper_url']}")
            output.append("")
        
        output.append(f"Total papers: {len(papers)}")
        
        # Write to output file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))
        
        # Print to console with colors
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title:^80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")
        
        for i, paper in enumerate(papers, 1):
            print(f"{Colors.BOLD}{Colors.GREEN}{i}. {paper['paper_name']}{Colors.ENDC}")
            print(f"{Colors.BLUE}   URL: {Colors.UNDERLINE}{paper['paper_url']}{Colors.ENDC}")
            print()
        
        print(f"{Colors.BOLD}Total papers: {len(papers)}{Colors.ENDC}")
        
    except FileNotFoundError:
        message = f"Error: File '{json_file}' not found\nRun 'poetry run python search_papers.py \"your search query\"' first to generate the JSON file."
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(message)
        print(f"{Colors.RED}{message}{Colors.ENDC}")
    except json.JSONDecodeError:
        message = f"Error: '{json_file}' is not a valid JSON file"
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(message)
        print(f"{Colors.RED}{message}{Colors.ENDC}")
    except Exception as e:
        message = f"Error: {str(e)}"
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(message)
        print(f"{Colors.RED}{message}{Colors.ENDC}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Display papers from JSON file in a readable format')
    parser.add_argument('json_file', type=str, nargs='?', default="data/json/papers.json",
                        help='Path to JSON file with paper information')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output text file path (default: data/json/papers_output.txt)')
    
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs("data/json", exist_ok=True)
    os.makedirs("data/pdf", exist_ok=True)
    
    # Set default output file if not specified
    output_file = args.output
    if not output_file:
        # Generate output filename based on input filename
        base_name = os.path.basename(args.json_file)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = f"data/json/{name_without_ext}_output.txt"
    
    # Check if the file exists
    if not os.path.exists(args.json_file):
        message = f"Error: File '{args.json_file}' not found\nRun 'poetry run python search_papers.py \"your search query\"' first to generate the JSON file."
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(message)
        print(f"{Colors.RED}{message}{Colors.ENDC}")
        return
    
    display_papers(args.json_file, output_file)
    print(f"\nOutput also saved to {output_file}")

if __name__ == "__main__":
    main()
