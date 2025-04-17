# Research Paper Search and Download Tool

This project uses the OpenAI API with web search capabilities to gather information about research papers on any topic, and provides functionality to download the papers from arXiv or other sources.

## Features

- **Universal Search**: Search for research papers on any topic using OpenAI's web search capabilities
- **Intelligent Paper Matching**: Advanced algorithm to accurately match papers with their arXiv versions
- **Automatic Downloads**: Fully autonomous workflow from search to download without manual intervention
- **NeurIPS Paper Support**: Special handling for NeurIPS conference papers with improved matching
- **Comprehensive Display**: View paper titles, URLs, arXiv links, and download status in one place
- **All-in-One Script**: Run the entire process with a single command

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

The easiest way to use this tool is with the `run_all.py` script, which performs all steps (search, download, and display) in sequence:

```
poetry run python run_all.py "your search query"
```

For example:
```
poetry run python run_all.py "quantum computing"
poetry run python run_all.py "diffusion model neurips"
```

The script will:
1. Search for papers on your topic using OpenAI's web search
2. Automatically download the papers from arXiv or directly from conference websites
3. Display the results with titles, URLs, arXiv links, and download status

Additional options:
```
poetry run python run_all.py "quantum computing" --no-download  # Skip downloading
poetry run python run_all.py "quantum computing" --model gpt-3.5-turbo  # Use a different model
poetry run python run_all.py "quantum computing" --threshold 0.6  # Adjust similarity threshold
poetry run python run_all.py "quantum computing" --manual  # Enable manual search mode
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
poetry run python search_papers.py "diffusion models"
```

You can also specify a custom output file and model:
```
poetry run python search_papers.py "quantum computing" --output custom_output.json --model gpt-4o
```

#### 2. Download Papers

Download the papers as PDF files:

```
poetry run python download_papers.py --json data/json/<query>_papers.json
```

The download script uses an advanced paper matching algorithm that:
- Performs intelligent title matching with multiple search strategies
- Verifies matches using a sophisticated similarity calculation
- Filters out incorrect matches using pattern detection
- Handles papers with prefixes/suffixes (e.g., "DiscDiff: Latent Diffusion Model...")
- Has special handling for NeurIPS conference papers

Advanced download options:
```
poetry run python download_papers.py --json data/json/quantum_computing_papers.json --threshold 0.7  # Stricter matching
poetry run python download_papers.py --json data/json/quantum_computing_papers.json --manual  # Enable manual search
poetry run python download_papers.py --retry-failed  # Retry only papers that failed previously
```

#### 3. Display Papers

Display the search results with download status:

```
poetry run python display_papers.py data/json/<query>_papers.json
```

This will show:
- Paper titles
- Original URLs
- arXiv URLs (when available)
- Download status (success/failure with details)

## Technical Details

### Paper Matching Algorithm

The tool uses a sophisticated algorithm to match papers with their arXiv versions:

1. **Multiple Search Strategies**:
   - Exact title search
   - First N words search
   - Most distinctive words search
   - Special strategies for NeurIPS papers

2. **Advanced Similarity Calculation**:
   - Basic string similarity (Levenshtein distance)
   - Title containment check
   - Important word overlap analysis
   - Weighted scoring system

3. **Verification Process**:
   - Blacklist for known problematic patterns
   - Length ratio check
   - Important word overlap threshold
   - Title containment verification

This ensures that papers like "Latent Diffusion Model for DNA Sequence Generation" are correctly matched with "DiscDiff: Latent Diffusion Model for DNA Sequence Generation" while avoiding completely unrelated papers.

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
      "arxiv_url": "http://arxiv.org/abs/2310.12345v1",
      "pdf_path": "data/pdf/Example_Paper_Title_1.pdf",
      "downloaded": true
    },
    {
      "paper_name": "Example Paper Title 2",
      "paper_url": "https://example.com/paper2",
      "downloaded": false,
      "error": "No results found on arXiv and direct download failed"
    }
  ]
}
```

## Files

- `search_papers.py`: Main script that uses the OpenAI API to search for papers on any topic
- `display_papers.py`: Helper script to display the papers in a readable format with download status
- `download_papers.py`: Script to download the papers as PDFs with advanced matching algorithm
- `run_all.py`: All-in-one script to search, download, and display papers in one go
- `data/json/<query>_papers.json`: Output file containing the search results
- `data/json/download_results.json`: File containing download status information
- `data/pdf/`: Directory containing downloaded PDF papers
- `README.md`: This documentation file
