import os
import sys
import argparse
import subprocess
import json
import time

def run_command(command):
    """Run a command and return its output"""
    print(f"\n=== Running: {' '.join(command)} ===\n")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Print output in real-time
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    
    process.stdout.close()
    return_code = process.wait()
    
    if return_code != 0:
        print(f"\nCommand failed with return code {return_code}")
    
    return return_code

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Search, display, and download research papers in one go')
    parser.add_argument('query', type=str, nargs='?', default=None,
                        help='Search query for papers (e.g., "quantum computing", "climate change")')
    parser.add_argument('--model', '-m', type=str, default="gpt-4o",
                        help='OpenAI model to use (default: gpt-4o)')
    parser.add_argument('--download', '-d', action='store_true',
                        help='Automatically download papers without asking')
    parser.add_argument('--no-download', '-n', action='store_true',
                        help='Skip downloading papers')
    parser.add_argument('--threshold', '-t', type=float, default=0.6,
                        help='Similarity threshold for fuzzy matching when downloading (0.0-1.0)')
    parser.add_argument('--no-manual', action='store_true',
                        help='Disable interactive manual search when downloading')
    
    args = parser.parse_args()
    
    # If no query provided, prompt the user
    query = args.query
    if not query:
        query = input("Enter search query for papers: ")
        if not query.strip():
            print("Error: Search query cannot be empty")
            sys.exit(1)
    
    # Create a safe filename from the query
    safe_query = query.lower().replace(' ', '_')
    safe_query = ''.join(c for c in safe_query if c.isalnum() or c == '_')
    
    # Define file paths
    json_file = f"data/json/{safe_query}_papers.json"
    
    # Step 1: Search for papers
    print("\n" + "="*80)
    print(f"STEP 1: SEARCHING FOR PAPERS ON '{query.upper()}'")
    print("="*80)
    
    search_cmd = ["python", "search_papers.py", query, "--output", json_file, "--model", args.model]
    if run_command(search_cmd) != 0:
        print("Error: Search failed. Exiting.")
        sys.exit(1)
    
    # Wait a moment to ensure file is written
    time.sleep(1)
    
    # Step 2: Display papers
    print("\n" + "="*80)
    print(f"STEP 2: DISPLAYING PAPERS ON '{query.upper()}'")
    print("="*80)
    
    display_cmd = ["python", "display_papers.py", json_file]
    if run_command(display_cmd) != 0:
        print("Error: Display failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Download papers (if requested)
    if args.no_download:
        print("\nSkipping download as requested.")
        return
    
    download_papers = args.download
    if not download_papers and not args.no_download:
        # Count papers in the JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                paper_count = len(data.get('papers', []))
                
            if paper_count > 0:
                response = input(f"\nDo you want to download {paper_count} papers? (y/n): ").strip().lower()
                download_papers = response.startswith('y')
            else:
                print("\nNo papers found to download.")
                return
        except Exception as e:
            print(f"\nError reading JSON file: {str(e)}")
            return
    
    if download_papers:
        print("\n" + "="*80)
        print(f"STEP 3: DOWNLOADING PAPERS ON '{query.upper()}'")
        print("="*80)
        
        download_cmd = ["python", "download_papers.py", "--json", json_file, "--threshold", str(args.threshold)]
        if args.no_manual:
            download_cmd.append("--no-manual")
        
        run_command(download_cmd)
    
    print("\n" + "="*80)
    print("PROCESS COMPLETE")
    print("="*80)
    print(f"\nSearch results saved to: {json_file}")
    print(f"Downloaded PDFs saved to: data/pdf/")

if __name__ == "__main__":
    main()
