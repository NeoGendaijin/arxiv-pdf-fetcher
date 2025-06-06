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
    parser.add_argument('query', type=str, nargs='*', default=None,
                        help='Search query for papers (e.g., quantum computing, climate change)')
    parser.add_argument('--model', '-m', type=str, default="gpt-4o",
                        help='OpenAI model to use (default: gpt-4o)')
    parser.add_argument('--no-download', '-n', action='store_true',
                        help='Skip downloading papers')
    parser.add_argument('--threshold', '-t', type=float, default=0.5,
                        help='Similarity threshold for fuzzy matching when downloading (0.0-1.0)')
    parser.add_argument('--no-manual', action='store_true',
                        help='Disable interactive manual search when downloading')
    
    args = parser.parse_args()
    
    # If no query provided, prompt the user
    if not args.query:
        query_input = input("Enter search query for papers: ")
        if not query_input.strip():
            print("Error: Search query cannot be empty")
            sys.exit(1)
        query = query_input
    else:
        # Join the list of query words into a single string
        query = " ".join(args.query)
    
    # Create a safe filename from the query
    safe_query = query.lower().replace(' ', '_')
    safe_query = ''.join(c for c in safe_query if c.isalnum() or c == '_')
    
    # Define file paths
    json_file = f"data/json/{safe_query}_papers.json"
    
    # Step 1: Search for papers
    print("\n" + "="*80)
    print(f"STEP 1: SEARCHING FOR PAPERS ON '{query.upper()}'")
    print("="*80)
    
    # Pass the query as a single argument
    search_cmd = ["python", "search_papers.py", query, "--output", json_file, "--model", args.model]
    if run_command(search_cmd) != 0:
        print("Error: Search failed. Exiting.")
        sys.exit(1)
    
    # Wait a moment to ensure file is written
    time.sleep(1)
    
    # Step 2: Download papers (unless explicitly disabled)
    if args.no_download:
        print("\nSkipping download as requested.")
    else:
        # Count papers in the JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                paper_count = len(data.get('papers', []))
                
            if paper_count > 0:
                print(f"\nAutomatically downloading {paper_count} papers...")
                
                # Download papers
                print("\n" + "="*80)
                print(f"STEP 2: DOWNLOADING PAPERS ON '{query.upper()}'")
                print("="*80)
                
                download_cmd = ["python", "download_papers.py", "--json", json_file, "--threshold", str(args.threshold)]
                if args.no_manual:
                    download_cmd.append("--no-manual")
                
                run_command(download_cmd)
            else:
                print("\nNo papers found to download.")
        except Exception as e:
            print(f"\nError reading JSON file: {str(e)}")
    
    # Step 3: Display papers (with download status if available)
    print("\n" + "="*80)
    print(f"STEP 3: DISPLAYING PAPERS ON '{query.upper()}'")
    print("="*80)
    
    display_cmd = ["python", "display_papers.py", json_file]
    if run_command(display_cmd) != 0:
        print("Error: Display failed. Exiting.")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("PROCESS COMPLETE")
    print("="*80)
    print(f"\nSearch results saved to: {json_file}")
    print(f"Downloaded PDFs saved to: data/pdf/")

if __name__ == "__main__":
    main()
