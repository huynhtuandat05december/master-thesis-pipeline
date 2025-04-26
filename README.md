# JaccardWarp

A contextual code retrieval and suggestion system for intelligent programming assistance. JaccardWarp combines multiple retrieval strategies to provide relevant code context for autocompletion and code understanding tasks.

## Overview

JaccardWarp is designed to improve code completion by retrieving and ranking relevant code snippets from a repository. It uses various retrieval strategies:

1. **Jaccard Similarity Retrieval**: Finds similar code blocks based on textual similarity
2. **Graph-based Retrieval**: Uses LSP (Language Server Protocol) to find related code through code relationships
3. **Context Mixing**: Combines retrieval results using reciprocal rank fusion

## Features

- Semantic code search using Jaccard similarity
- Graph-based code retrieval through LSP
- Intelligent context mixing of results
- Support for multiple programming languages
- Post-processing for improved suggestion quality

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jaccard_warp.git
   cd jaccard_warp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up required Python environments and Tree-sitter bindings.

## Project Structure

- `context_mixer.py`: Main component that combines multiple context retrieval strategies
- `text_retrieval/`: Contains Jaccard similarity-based text retrieval components
- `graph_retrieval/`: LSP and graph-based code retrieval
- `ranking/`: Algorithms for ranking and fusing retrieved results
- `schema/`: Data models and type definitions
- `post_processing/`: Post-processors for refining retrieved results
- `test/`: Test cases and examples

## Usage

The core usage involves providing a document and position to get relevant context:

```python
from context_mixer import ContextMixer
from schema.common import Document, Position

# Initialize the mixer
context_mixer = ContextMixer()

# Create a document object
document = Document(
    uri="/path/to/your/file.py",
    language_id="python",
    text="your code here",
    prefix="code before cursor",
    suffix="code after cursor"
)

# Define cursor position
position = Position(line=10, character=15)

# Get context
result = await context_mixer.get_context(document, position, repo="your_repo_name")

# Use the retrieved context
for snippet in result["context"]:
    print(f"File: {snippet.uri}, Line: {snippet.start_line}-{snippet.end_line}")
    print(snippet.content)
```

## Command-line Tools

### Prompt Builder

The prompt builder tool generates prompts with context for code completion models. To run:

```bash
python prompt_builder.py --base_dir /path/to/source/code/ --input /path/to/input.jsonl --output /path/to/output.jsonl
```

Arguments:
- `--base_dir`: Base directory containing source code files
- `--input`: Input JSONL file path with metadata
- `--output`: Output JSONL file path where prompts will be saved

### Post Processing

The post processing tool refines model completions with context. To run:

```bash
python post_processing.py --base_dir /path/to/source/code/ --input /path/to/input.jsonl --output /path/to/output.jsonl
```

Arguments:
- `--base_dir`: Base directory containing source code files
- `--input`: Input JSONL file with model completions and metadata
- `--output`: Output JSONL file path for processed completions