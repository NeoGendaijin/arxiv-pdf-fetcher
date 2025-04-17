# Research Paper Search and Download Tool

This project uses the OpenAI API with web search capabilities to gather information about research papers on any topic, and provides functionality to download the papers from arXiv or other sources.

## Project Structure

```
.
├── data/
│   ├── json/           # JSON files with paper information
│   └── pdf/            # Downloaded PDF papers
├── search_papers.py    # Main script to search for papers on any topic
├── display_papers.py   # Script to display papers in a readable format
├── download_papers.py  # Script to download papers as PDFs
├── run_all.py          # All-in-one script to search, display, and download papers
└── README.md
```

## Requirements

- Python 3.8+
- Poetry (for dependency management)
- OpenAI API key (required)

## Setup

1. Clone this repository
2. Install dependencies using Poetry:
   ```
   poetry install
   ```
3. Set your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-api-key'
   ```
4. Create the necessary data directories (these are gitignored):
   ```
   mkdir -p data/json data/pdf
   ```

> **Note:** The `data/` directory is excluded from version control via `.gitignore` to avoid storing paper PDFs and search results in the repository. This prevents potential copyright issues and keeps the repository size manageable.

## Usage

### Quick Start: Run All Steps at Once

The easiest way to use this tool is with the `run_all.py` script, which performs all steps (search, display, and download) in sequence:

```
poetry run python run_all.py "your search query"
```

For example:
```
poetry run python run_all.py "quantum computing"
poetry run python run_all.py "climate change"
```

The script will:
1. Search for papers on your topic
2. Display the results in a readable format
3. Ask if you want to download the papers
4. If you choose yes, download the papers to the `data/pdf/` directory

Additional options:
```
poetry run python run_all.py "quantum computing" --download  # Automatically download without asking
poetry run python run_all.py "quantum computing" --no-download  # Skip downloading
poetry run python run_all.py "quantum computing" --model gpt-3.5-turbo  # Use a different model
poetry run python run_all.py "quantum computing" --threshold 0.5  # Lower similarity threshold for downloads
poetry run python run_all.py "quantum computing" --no-manual  # Disable manual search mode
```

### Individual Steps

If you prefer to run each step separately, you can use the individual scripts:

#### 1. Search for Papers

```
poetry run python search_papers.py "your search query"
```

For example:
```
poetry run python search_papers.py "quantum computing"
poetry run python search_papers.py "climate change"
poetry run python search_papers.py "machine learning"
```

You can also specify a custom output file and model:
```
poetry run python search_papers.py "quantum computing" --output custom_output.json --model gpt-4o
```

The script will:
1. Use the OpenAI API to search for research papers on your topic
2. Parse the JSON response and save it to `data/json/<query>_papers.json`
3. Display the formatted JSON in the terminal
4. Suggest next steps for displaying and downloading the papers

#### 2. Display Papers

Display the search results in a readable format:

```
poetry run python display_papers.py data/json/<query>_papers.json
```

For example:
```
poetry run python display_papers.py data/json/quantum_computing_papers.json
```

This will read the JSON file and display the papers in a formatted list with color highlighting in the terminal. The output is also saved to a text file.

#### 3. Download Papers

Download the papers as PDF files:

```
poetry run python download_papers.py --json data/json/<query>_papers.json
```

This script will:
1. Read the paper information from the JSON file
2. Try to download each paper using one of these methods:
   - Direct download if the URL points to a PDF
   - Extract arXiv ID from the URL and download from arXiv
   - Search arXiv by title with fuzzy matching (handles special characters like β₂)
   - Interactive manual search for papers not found automatically
3. Save the PDFs to the `data/pdf/` directory
4. Create a `download_results.json` file with download status information

#### Advanced Download Options

The download script supports several command-line options:

```
poetry run python download_papers.py --help
```

Key options include:
- `--json PATH`: Specify a custom JSON file path
- `--output DIR`: Specify a custom output directory for PDFs
- `--threshold VALUE`: Set the similarity threshold for fuzzy matching (0.0-1.0)
- `--no-manual`: Disable interactive manual search
- `--retry-failed`: Retry only papers that failed to download previously

Example for retrying failed downloads with a lower similarity threshold:
```
poetry run python download_papers.py --retry-failed --threshold 0.5
```

#### Manual Search Mode

For papers that can't be found automatically, the script enters manual search mode (if enabled), allowing you to:
1. Provide an arXiv ID directly
2. Enter custom search terms
3. Select from search results
4. Skip the paper

## Output Format

The JSON output has the following structure:

```json
{
  "papers": [
    {
      "paper_name": "Example Paper Title 1",
      "paper_url": "https://example.com/paper1"
    },
    {
      "paper_name": "Example Paper Title 2",
      "paper_url": "https://example.com/paper2"
    }
  ],
  "metadata": {
    "query": "your search query",
    "timestamp": "2025-04-17 16:45:00",
    "model": "gpt-4o"
  }
}
```

After downloading, the `download_results.json` file will include additional information:

```json
{
  "papers": [
    {
      "paper_name": "Example Paper Title 1",
      "paper_url": "https://example.com/paper1",
      "arxiv_id": "2310.12345",
      "pdf_path": "data/pdf/Example_Paper_Title_1.pdf",
      "downloaded": true
    },
    {
      "paper_name": "Example Paper Title 2",
      "paper_url": "https://example.com/paper2",
      "downloaded": false,
      "error": "No results found on arXiv"
    }
  ]
}
```

## Files

- `search_papers.py`: Main script that uses the OpenAI API to search for papers on any topic
- `display_papers.py`: Helper script to display the papers in a readable format
- `download_papers.py`: Script to download the papers as PDF files
- `run_all.py`: All-in-one script to search, display, and download papers in one go
- `data/json/<query>_papers.json`: Output file containing the search results
- `data/json/download_results.json`: File containing download status information
- `data/pdf/`: Directory containing downloaded PDF papers
- `README.md`: This documentation file
