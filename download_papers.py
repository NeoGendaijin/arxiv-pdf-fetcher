import os
import json
import sys
import re
import time
import arxiv
import requests
import unicodedata
from urllib.parse import urlparse, unquote
from difflib import SequenceMatcher

def clean_filename(filename):
    """Clean a filename to make it safe for all operating systems"""
    # Replace invalid characters with underscore
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Limit length to avoid issues with long filenames
    if len(cleaned) > 100:
        cleaned = cleaned[:97] + "..."
    return cleaned

def normalize_title(title):
    """Normalize a title for better matching"""
    # Convert to lowercase
    normalized = title.lower()
    # Remove special characters and symbols
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    # Replace Greek letters and other special characters
    normalized = normalized.replace('β', 'beta')
    normalized = normalized.replace('α', 'alpha')
    normalized = normalized.replace('γ', 'gamma')
    normalized = normalized.replace('δ', 'delta')
    normalized = normalized.replace('ε', 'epsilon')
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    # Remove common words that don't add much meaning
    stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'with', 'for', 'of', 'to', 'by']
    normalized = ' '.join(word for word in normalized.split() if word not in stop_words)
    return normalized

def title_similarity(title1, title2):
    """Calculate similarity between two titles"""
    # Normalize titles
    norm_title1 = normalize_title(title1)
    norm_title2 = normalize_title(title2)
    # Calculate similarity
    return SequenceMatcher(None, norm_title1, norm_title2).ratio()

def extract_arxiv_id(url):
    """Extract arXiv ID from a URL"""
    # Handle direct arXiv URLs
    if "arxiv.org" in url:
        # Extract ID from URL like https://arxiv.org/abs/2310.17042
        match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', url)
        if match:
            return match.group(1)
        
        # Extract ID from URL with /arxiv: prefix
        match = re.search(r'/arxiv:(\d+\.\d+)', url)
        if match:
            return match.group(1)
    
    return None

def search_arxiv_by_title(title, similarity_threshold=0.7):
    """Search arXiv for a paper by title with fuzzy matching"""
    # Clean the title for search
    normalized_title = normalize_title(title)
    search_title = ' '.join(normalized_title.split()[:8])  # Use first 8 words for search
    
    # Search arXiv
    search = arxiv.Search(
        query=f'ti:"{search_title}"',
        max_results=10,  # Increase to get more potential matches
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = list(search.results())
    
    # If no results, try a more general search
    if not results:
        # Try with fewer words
        search_title = ' '.join(normalized_title.split()[:5])  # Use first 5 words
        search = arxiv.Search(
            query=f'ti:"{search_title}"',
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = list(search.results())
    
    # Find the best match based on title similarity
    best_match = None
    best_similarity = 0
    
    for result in results:
        similarity = title_similarity(title, result.title)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = result
    
    # Return the best match if it's above the threshold
    if best_match and best_similarity >= similarity_threshold:
        print(f"Best match: {best_match.title} (similarity: {best_similarity:.2f})")
        return [best_match]
    elif results:
        print(f"No good matches found. Best candidate: {results[0].title} (similarity: {title_similarity(title, results[0].title):.2f})")
    
    return results

def download_pdf(url, output_path):
    """Download a PDF file from a URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def manual_search_arxiv(paper_name):
    """Allow manual search for a paper on arXiv"""
    print("\nManual search mode for paper:")
    print(f"  {paper_name}")
    print("\nEnter one of the following:")
    print("1. arXiv ID (e.g., 2310.17042)")
    print("2. Search terms (e.g., adopt adam optimizer)")
    print("3. Skip this paper")
    
    choice = input("\nYour choice: ").strip()
    
    if choice.startswith("1"):
        # User provided arXiv ID
        arxiv_id = input("Enter arXiv ID: ").strip()
        search = arxiv.Search(id_list=[arxiv_id])
        return list(search.results())
    elif choice.startswith("2"):
        # User provided search terms
        search_terms = input("Enter search terms: ").strip()
        search = arxiv.Search(
            query=search_terms,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = list(search.results())
        
        if not results:
            print("No results found for your search terms.")
            return []
        
        # Display results
        print("\nSearch results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
        
        # Let user select a result
        selection = input("\nSelect a paper (number) or 0 to skip: ").strip()
        try:
            selection = int(selection)
            if 1 <= selection <= len(results):
                return [results[selection-1]]
        except ValueError:
            pass
        
        return []
    else:
        # Skip this paper
        return []

def download_papers_from_json(json_file, output_dir, enable_manual_search=True, similarity_threshold=0.6):
    """Download papers from JSON file"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'papers' not in data:
        print(f"Error: JSON file does not contain 'papers' key")
        return
    
    papers = data['papers']
    if not papers:
        print(f"No papers found in the JSON file")
        return
    
    # Track downloaded papers and update JSON
    downloaded_papers = []
    
    for i, paper in enumerate(papers, 1):
        paper_name = paper['paper_name']
        paper_url = paper['paper_url']
        
        print(f"\nProcessing paper {i}/{len(papers)}: {paper_name}")
        
        # Check if it's a direct PDF link
        is_pdf = paper_url.lower().endswith('.pdf')
        
        # Try to extract arXiv ID from URL
        arxiv_id = extract_arxiv_id(paper_url)
        
        if arxiv_id:
            print(f"Found arXiv ID: {arxiv_id}")
            try:
                # Get paper details from arXiv
                search = arxiv.Search(id_list=[arxiv_id])
                results = list(search.results())
                
                if results:
                    result = results[0]
                    filename = f"{clean_filename(result.title)}.pdf"
                    output_path = os.path.join(output_dir, filename)
                    
                    print(f"Downloading: {result.title}")
                    result.download_pdf(filename=output_path)
                    
                    # Update paper info
                    paper_info = {
                        "paper_name": paper_name,
                        "paper_url": paper_url,
                        "arxiv_id": arxiv_id,
                        "pdf_path": output_path,
                        "downloaded": True
                    }
                    downloaded_papers.append(paper_info)
                    print(f"Downloaded to: {output_path}")
                    
                    # Sleep to avoid hitting rate limits
                    time.sleep(1)
                else:
                    print(f"No results found for arXiv ID: {arxiv_id}")
                    downloaded_papers.append({**paper, "downloaded": False, "error": "No results found for arXiv ID"})
            except Exception as e:
                print(f"Error downloading paper with arXiv ID {arxiv_id}: {str(e)}")
                downloaded_papers.append({**paper, "downloaded": False, "error": str(e)})
        
        elif is_pdf:
            # Direct PDF download
            try:
                # Extract filename from URL or use paper name
                parsed_url = urlparse(paper_url)
                url_filename = os.path.basename(unquote(parsed_url.path))
                
                if url_filename.lower().endswith('.pdf'):
                    filename = url_filename
                else:
                    filename = f"{clean_filename(paper_name)}.pdf"
                
                output_path = os.path.join(output_dir, filename)
                
                print(f"Downloading PDF directly: {paper_url}")
                if download_pdf(paper_url, output_path):
                    paper_info = {
                        "paper_name": paper_name,
                        "paper_url": paper_url,
                        "pdf_path": output_path,
                        "downloaded": True
                    }
                    downloaded_papers.append(paper_info)
                    print(f"Downloaded to: {output_path}")
                else:
                    downloaded_papers.append({**paper, "downloaded": False, "error": "Failed to download PDF"})
                
                # Sleep to avoid hitting rate limits
                time.sleep(1)
            except Exception as e:
                print(f"Error downloading PDF {paper_url}: {str(e)}")
                downloaded_papers.append({**paper, "downloaded": False, "error": str(e)})
        
        else:
            # Try to search arXiv by title with improved matching
            print(f"Searching arXiv for: {paper_name}")
            try:
                # Try with fuzzy matching
                results = search_arxiv_by_title(paper_name, similarity_threshold)
                
                if results:
                    # Use the first result
                    result = results[0]
                    filename = f"{clean_filename(result.title)}.pdf"
                    output_path = os.path.join(output_dir, filename)
                    
                    print(f"Found on arXiv: {result.title}")
                    print(f"Downloading...")
                    result.download_pdf(filename=output_path)
                    
                    # Update paper info
                    paper_info = {
                        "paper_name": paper_name,
                        "paper_url": paper_url,
                        "arxiv_id": result.get_short_id(),
                        "arxiv_url": result.entry_id,
                        "pdf_path": output_path,
                        "downloaded": True
                    }
                    downloaded_papers.append(paper_info)
                    print(f"Downloaded to: {output_path}")
                elif enable_manual_search:
                    # Try manual search if automatic search failed
                    print(f"No results found on arXiv for: {paper_name}")
                    print("Entering manual search mode...")
                    
                    manual_results = manual_search_arxiv(paper_name)
                    
                    if manual_results:
                        result = manual_results[0]
                        filename = f"{clean_filename(result.title)}.pdf"
                        output_path = os.path.join(output_dir, filename)
                        
                        print(f"Downloading manually selected paper: {result.title}")
                        result.download_pdf(filename=output_path)
                        
                        # Update paper info
                        paper_info = {
                            "paper_name": paper_name,
                            "paper_url": paper_url,
                            "arxiv_id": result.get_short_id(),
                            "arxiv_url": result.entry_id,
                            "pdf_path": output_path,
                            "downloaded": True,
                            "manual_search": True
                        }
                        downloaded_papers.append(paper_info)
                        print(f"Downloaded to: {output_path}")
                    else:
                        print(f"Manual search skipped or no results found.")
                        downloaded_papers.append({**paper, "downloaded": False, "error": "No results found on arXiv (manual search)"})
                else:
                    print(f"No results found on arXiv for: {paper_name}")
                    downloaded_papers.append({**paper, "downloaded": False, "error": "No results found on arXiv"})
                
                # Sleep to avoid hitting rate limits
                time.sleep(3)
            except Exception as e:
                print(f"Error searching arXiv for {paper_name}: {str(e)}")
                downloaded_papers.append({**paper, "downloaded": False, "error": str(e)})
    
    # Save download results
    download_results = {
        "papers": downloaded_papers
    }
    
    results_file = os.path.join(os.path.dirname(json_file), "download_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(download_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDownload results saved to: {results_file}")
    
    # Print summary
    successful = sum(1 for paper in downloaded_papers if paper.get("downloaded", False))
    print(f"\nDownload Summary:")
    print(f"Total papers: {len(papers)}")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {len(papers) - successful}")

def main():
    # Create directories if they don't exist
    os.makedirs("data/json", exist_ok=True)
    os.makedirs("data/pdf", exist_ok=True)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Download papers from arXiv based on JSON file')
    parser.add_argument('--json', type=str, default="data/json/papers.json",
                        help='Path to JSON file with paper information')
    parser.add_argument('--output', type=str, default="data/pdf",
                        help='Directory to save downloaded PDFs')
    parser.add_argument('--manual', action='store_true', default=True,
                        help='Enable manual search for papers not found automatically')
    parser.add_argument('--no-manual', action='store_false', dest='manual',
                        help='Disable manual search')
    parser.add_argument('--threshold', type=float, default=0.6,
                        help='Similarity threshold for fuzzy matching (0.0-1.0)')
    parser.add_argument('--retry-failed', action='store_true',
                        help='Retry papers that failed to download previously')
    
    args = parser.parse_args()
    
    # Check if the file exists
    if not os.path.exists(args.json):
        print(f"Error: File '{args.json}' not found")
        print(f"Run 'poetry run python search_papers.py \"your search query\"' first to generate the JSON file.")
        return
    
    # If retry-failed is specified, load the download_results.json file
    if args.retry_failed:
        results_file = os.path.join(os.path.dirname(args.json), "download_results.json")
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Create a new JSON file with only the failed papers
            failed_papers = [p for p in results.get('papers', []) if not p.get('downloaded', False)]
            
            if failed_papers:
                retry_file = os.path.join(os.path.dirname(args.json), "retry_papers.json")
                with open(retry_file, 'w', encoding='utf-8') as f:
                    json.dump({"papers": failed_papers}, f, indent=2, ensure_ascii=False)
                
                print(f"Found {len(failed_papers)} papers that failed to download previously.")
                print(f"Created retry file: {retry_file}")
                
                # Use the retry file instead
                args.json = retry_file
            else:
                print("No failed papers found to retry.")
                return
        else:
            print(f"Error: Results file '{results_file}' not found")
            return
    
    # Download papers
    download_papers_from_json(args.json, args.output, 
                             enable_manual_search=args.manual,
                             similarity_threshold=args.threshold)

if __name__ == "__main__":
    main()
