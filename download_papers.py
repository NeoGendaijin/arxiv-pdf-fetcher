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
    
    # Calculate basic similarity
    basic_similarity = SequenceMatcher(None, norm_title1, norm_title2).ratio()
    
    # Check if one title is contained within the other (allowing for prefixes/suffixes)
    contained = norm_title1 in norm_title2 or norm_title2 in norm_title1
    
    # Check if they share significant words (more than 70% of words)
    words1 = set(norm_title1.split())
    words2 = set(norm_title2.split())
    
    # Calculate word overlap
    if words1 and words2:  # Avoid division by zero
        common_words = words1.intersection(words2)
        word_overlap = len(common_words) / min(len(words1), len(words2))
    else:
        word_overlap = 0
    
    # Calculate a weighted similarity score
    weighted_similarity = 0.5 * basic_similarity + 0.3 * float(contained) + 0.2 * word_overlap
    
    return weighted_similarity

def verify_paper_match(requested_title, candidate_title):
    """Verify if a candidate paper title is a good match for the requested title"""
    # Calculate similarity
    similarity = title_similarity(requested_title, candidate_title)
    
    # Normalize titles for additional checks
    norm_requested = normalize_title(requested_title)
    norm_candidate = normalize_title(candidate_title)
    
    # Split into words
    req_words = set(norm_requested.split())
    cand_words = set(norm_candidate.split())
    
    # Get important words (longer than 4 characters)
    important_req_words = {w for w in req_words if len(w) > 4}
    important_cand_words = {w for w in cand_words if len(w) > 4}
    
    # Check if important words are present
    if important_req_words:
        important_word_overlap = len(important_req_words.intersection(important_cand_words)) / len(important_req_words)
    else:
        important_word_overlap = 0
    
    # Check for completely unrelated titles (blacklist certain patterns)
    blacklist_patterns = [
        "existence of weak solutions",
        "continuity equation",
        "darcy law",
        "electronic health records",
        "multimodal electronic"
    ]
    
    for pattern in blacklist_patterns:
        if pattern in norm_candidate.lower() and pattern not in norm_requested.lower():
            return False, 0.0, "Blacklisted pattern detected"
    
    # Check if the candidate title is much longer than the requested title
    len_ratio = len(norm_candidate) / len(norm_requested) if norm_requested else 0
    if len_ratio > 2.0:
        return False, similarity, "Candidate title too long"
    
    # Check if the similarity is high enough
    if similarity >= 0.7:
        return True, similarity, "High similarity"
    
    # Check if important words overlap significantly
    if important_word_overlap >= 0.8:
        return True, similarity, "High important word overlap"
    
    # Check if one title is contained within the other
    if norm_requested in norm_candidate or norm_candidate in norm_requested:
        return True, similarity, "Title containment"
    
    # Default: not a good match
    return False, similarity, "Low similarity"

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

def search_arxiv_by_title(title, similarity_threshold=0.6, is_neurips=False):
    """Search arXiv for a paper by title with fuzzy matching"""
    # Clean the title for search
    normalized_title = normalize_title(title)
    
    # Extract key terms from the title
    words = normalized_title.split()
    
    # For NeurIPS papers, use a more aggressive search strategy
    if is_neurips:
        # Lower the similarity threshold for NeurIPS papers
        similarity_threshold = max(0.4, similarity_threshold - 0.2)
        
        # Try to extract the main concept from the title (often before "for" or "with")
        main_concept = title
        for separator in [" for ", " with ", " using ", " via ", " in ", " on "]:
            if separator in title:
                main_concept = title.split(separator)[0]
                break
        
        normalized_main_concept = normalize_title(main_concept)
    
    # Try different search strategies
    search_strategies = [
        # Strategy 1: Use exact title with quotes
        lambda: arxiv.Search(
            query=f'ti:"{title}"',
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        ),
        # Strategy 2: Use first 8 words with title filter
        lambda: arxiv.Search(
            query=f'ti:"{" ".join(words[:8])}"',
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance
        ),
        # Strategy 3: Use first 5 words with title filter
        lambda: arxiv.Search(
            query=f'ti:"{" ".join(words[:5])}"',
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance
        ),
        # Strategy 4: Use the most distinctive words from the title
        lambda: arxiv.Search(
            query=f'"{" ".join(sorted(words, key=len, reverse=True)[:3])}"',
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance
        )
    ]
    
    # Add NeurIPS-specific strategies
    if is_neurips:
        # Strategy 5: Use main concept only
        if 'normalized_main_concept' in locals():
            search_strategies.append(
                lambda: arxiv.Search(
                    query=f'"{normalized_main_concept}"',
                    max_results=20,
                    sort_by=arxiv.SortCriterion.Relevance
                )
            )
        
        # Strategy 6: Use key terms without requiring exact phrase match
        key_terms = " ".join([word for word in words if len(word) > 4])
        search_strategies.append(
            lambda: arxiv.Search(
                query=key_terms,
                max_results=20,
                sort_by=arxiv.SortCriterion.Relevance
            )
        )
        
        # Strategy 7: Use the title without quotes to allow partial matches
        search_strategies.append(
            lambda: arxiv.Search(
                query=normalized_title,
                max_results=20,
                sort_by=arxiv.SortCriterion.Relevance
            )
        )
    
    all_results = []
    verified_results = []
    
    # Try each search strategy
    for i, strategy_fn in enumerate(search_strategies):
        try:
            print(f"Trying search strategy {i+1}...")
            search = strategy_fn()
            results = list(search.results())
            
            if results:
                print(f"Found {len(results)} potential matches using strategy {i+1}")
                
                # Verify each result
                for result in results:
                    is_match, similarity, reason = verify_paper_match(title, result.title)
                    print(f"Comparing: '{title}' vs '{result.title}' - Similarity: {similarity:.2f} - {reason}")
                    
                    if is_match:
                        verified_results.append((result, similarity, reason))
                    
                    # Add to all results regardless of verification
                    all_results.append(result)
                
                # If we found verified results, we can stop searching
                if verified_results:
                    print(f"Found {len(verified_results)} verified matches")
                    break
            
        except Exception as e:
            print(f"Search strategy {i+1} failed: {str(e)}")
    
    # If we have verified results, return the best one
    if verified_results:
        # Sort by similarity score
        verified_results.sort(key=lambda x: x[1], reverse=True)
        best_result, best_similarity, reason = verified_results[0]
        print(f"Best verified match: {best_result.title} (similarity: {best_similarity:.2f}, reason: {reason})")
        return [best_result]
    
    # If no verified results but we have some results, try to find the best match
    if all_results:
        # Find the best match based on similarity
        best_match = None
        best_similarity = 0
        
        for result in all_results:
            similarity = title_similarity(title, result.title)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = result
        
        # Only return if it's above the threshold
        if best_match and best_similarity >= similarity_threshold:
            print(f"Best unverified match: {best_match.title} (similarity: {best_similarity:.2f})")
            
            # Double-check with verification function
            is_match, _, reason = verify_paper_match(title, best_match.title)
            if is_match:
                print(f"Match verified: {reason}")
                return [best_match]
            else:
                print(f"Match rejected: {reason}")
    
    print("No suitable matches found")
    return []

def download_papers_from_json(json_file, output_dir, enable_manual_search=True, similarity_threshold=0.5):
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
        
        # Check if it's a NeurIPS paper
        is_neurips = any(domain in paper_url.lower() for domain in 
                         ['neurips', 'nips.cc', 'proceedings.neurips', 'proceedings.nips'])
        
        if is_neurips:
            print(f"Detected NeurIPS paper, using specialized search strategy")
        
        # Always search arXiv by title first
        print(f"Searching arXiv for: {paper_name}")
        try:
            # Try with improved search
            results = search_arxiv_by_title(paper_name, similarity_threshold, is_neurips)
            
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
                
                # For NeurIPS papers, try to download directly from the URL
                if is_neurips:
                    print(f"Attempting to download directly from NeurIPS URL: {paper_url}")
                    
                    # Try to extract PDF URL from the paper URL
                    pdf_url = paper_url
                    
                    # If URL points to abstract page, try to convert to PDF URL
                    if "Abstract" in paper_url:
                        pdf_url = paper_url.replace("Abstract", "Paper")
                    
                    # If URL doesn't end with .pdf, try adding .pdf
                    if not pdf_url.lower().endswith('.pdf'):
                        # For NeurIPS proceedings, try to find the PDF link pattern
                        if "proceedings.neurips.cc" in pdf_url or "papers.nips.cc" in pdf_url:
                            # Try to extract the paper hash
                            hash_match = re.search(r'hash/([a-f0-9]+)', pdf_url)
                            if hash_match:
                                paper_hash = hash_match.group(1)
                                pdf_url = f"https://proceedings.neurips.cc/paper_files/paper/2023/file/{paper_hash}-Paper.pdf"
                    
                    # Try to download the PDF
                    try:
                        filename = f"{clean_filename(paper_name)}.pdf"
                        output_path = os.path.join(output_dir, filename)
                        
                        print(f"Attempting to download from: {pdf_url}")
                        if download_pdf(pdf_url, output_path):
                            paper_info = {
                                "paper_name": paper_name,
                                "paper_url": paper_url,
                                "pdf_url": pdf_url,
                                "pdf_path": output_path,
                                "downloaded": True,
                                "direct_download": True
                            }
                            downloaded_papers.append(paper_info)
                            print(f"Downloaded directly to: {output_path}")
                            continue
                        else:
                            print(f"Failed to download directly from NeurIPS URL")
                    except Exception as e:
                        print(f"Error downloading from NeurIPS URL: {str(e)}")
                
                # If all attempts failed, mark as not downloaded
                downloaded_papers.append({**paper, "downloaded": False, "error": "No results found on arXiv and direct download failed"})
            
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
    parser.add_argument('--manual', action='store_true', default=False,
                        help='Enable manual search for papers not found automatically')
    parser.add_argument('--no-manual', action='store_false', dest='manual',
                        help='Disable manual search (default)')
    parser.add_argument('--threshold', type=float, default=0.5,
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
