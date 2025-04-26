import re
from typing import List, Optional, Dict, Any
from schema.lsp import ParsedHover

def extract_hover_content(hover_content: Any) -> List[ParsedHover]:
    """Extract content from hover response.
    
    This function handles the response format from lsp.request_hover.
    It processes the hover content and returns a list of ParsedHover objects.
    """
    # Handle None or empty hover content
    if not hover_content:
        return [ParsedHover()]
    
    # If it's a list of hovers, process each one
    if isinstance(hover_content, list):
        hovers = hover_content
    else:
        # If it's a single hover, wrap it in a list
        hovers = [hover_content]
    
    parsed_hovers = []
    
    for hover in hovers:
        # Extract contents, which could be a string, dict, or list
        contents = hover.get('contents', [])
        
        # Normalize contents to a list
        if isinstance(contents, str):
            contents = [contents]
        elif isinstance(contents, dict):
            contents = [contents]
        elif not isinstance(contents, list):
            contents = []
        
        # Process each content item
        for content_item in contents:
            # Extract the value from dict items
            if isinstance(content_item, dict):
                content_text = content_item.get('value', '')
                kind = content_item.get('kind')
            else:
                content_text = str(content_item)
                kind = None
            
            # Clean up the content
            cleaned_content = extract_markdown_code_block(content_text).strip()
            if not cleaned_content:
                cleaned_content = content_text.strip()
            
            if cleaned_content:
                # Process hover lines (remove import statements at the end)
                hover_lines = cleaned_content.split('\n')
                if len(hover_lines) > 1 and hover_lines[-1].startswith('import'):
                    cleaned_content = '\n'.join(hover_lines[:-1])
                
                # Parse the hover string to extract kind and text
                parsed = parse_hover_string(cleaned_content)
                parsed_hovers.append(
                    ParsedHover(
                        text=parsed["text"] or cleaned_content,
                        kind=parsed["kind"] or kind
                    )
                )
    
    # Return default if no hovers were parsed
    if not parsed_hovers:
        return [ParsedHover()]
    
    return parsed_hovers

def parse_hover_string(hover_string: str) -> Dict[str, Optional[str]]:
    HOVER_STRING_REGEX = re.compile(r'^\(([^)]+)\)\s([\s\S]+)$|^([\s\S]+)$', re.MULTILINE)
    match = HOVER_STRING_REGEX.match(hover_string)
    
    if match:
        return {
            "kind": match.group(1),
            "text": match.group(2) or match.group(3),
        }
    
    print(f"Unexpected hover string format: {hover_string}")
    return {"kind": None, "text": hover_string}

def extract_markdown_code_block(text: str) -> str:
    lines = text.split('\n')
    code_blocks = []
    is_code_block = False
    
    for line in lines:
        is_code_block_delimiter = line.strip().startswith('```')
        
        if is_code_block_delimiter:
            is_code_block = not is_code_block
        elif is_code_block:
            code_blocks.append(line)
    
    return '\n'.join(code_blocks)

def is_unhelpful_symbol_snippet(symbol_name: str, symbol_snippet: Optional[str] = None) -> bool:
    if not symbol_snippet:
        return True
    
    trimmed = symbol_snippet.strip()
    return (
        symbol_snippet == ''
        or symbol_snippet == symbol_name
        or (symbol_name not in symbol_snippet and 'constructor' not in symbol_snippet)
        or trimmed in {f"interface {symbol_name}", f"enum {symbol_name}", f"class {symbol_name}", f"type {symbol_name}"}
    )
