from typing import List, Optional, Any
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
import os
from schema.common import Position, Location, Range
from schema.lsp import DocumentSymbol, ParsedHover
from graph_retrieval.hover import extract_hover_content

# Initialize logger and workspace
logger = MultilspyLogger()
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Create LSP handler function
def get_lsp_server(language: str = "python") -> SyncLanguageServer:
    """
    Get a language server instance for the specified programming language.
    
    Args:
        language: The programming language to initialize the LSP for (default: "python")
        
    Returns:
        SyncLanguageServer: An initialized language server
    """
    config = MultilspyConfig.from_dict({"code_language": language})
    return SyncLanguageServer.create(config, logger, workspace_root)

# Default LSP instance
lsp = get_lsp_server("python")

def _uri_to_file_path(uri: str) -> str:
    """Convert URI to file path."""
    # Simple conversion for file:// URIs
    if uri.startswith("file://"):
        return uri[7:]
    return uri

def _position_to_line_col(position: Position) -> tuple:
    """Convert Position to line, column tuple."""
    return position.line, position.character

async def get_definition_locations(uri: str, position: Position, language: str = None) -> List[Location]:
    file_path = _uri_to_file_path(uri)
    line, col = _position_to_line_col(position)

    try:
        # Use language-specific LSP if provided
        current_lsp = get_lsp_server(language) if language else lsp
    
        with current_lsp.start_server():
            definitions = current_lsp.request_definition(file_path, line, col)
        
        # Convert results to Location objects
        locations = []
        for def_loc in definitions or []:
            # Handle the actual multilspy response format
            loc = Location(
                uri=_uri_to_file_path(def_loc.get('uri', uri)),
                range=Range(
                    start=Position(line=def_loc.get('range', {}).get('start', {}).get('line', 0), 
                                character=def_loc.get('range', {}).get('start', {}).get('character', 0)),
                    end=Position(line=def_loc.get('range', {}).get('end', {}).get('line', 0), 
                                character=def_loc.get('range', {}).get('end', {}).get('character', 0))
                )
            )
            locations.append(loc)
        
        return locations
    except Exception as e:
        print(f"Error getting definition locations: {e}")
        return []


async def get_implementation_locations(uri: str, position: Position, language: str = None) -> List[Location]:
    file_path = _uri_to_file_path(uri)
    line, col = _position_to_line_col(position)
    
    # Use language-specific LSP if provided
    current_lsp = get_lsp_server(language) if language else lsp
    
    with current_lsp.start_server():
        implementations = current_lsp.request_implementations(file_path, line, col)
    
    # Convert results to Location objects
    locations = []
    for impl_loc in implementations or []:
        loc = Location(
            uri=_uri_to_file_path(impl_loc.get('uri', uri)),
            range=Range(
                start=Position(line=impl_loc.get('range', {}).get('start', {}).get('line', 0), 
                               character=impl_loc.get('range', {}).get('start', {}).get('character', 0)),
                end=Position(line=impl_loc.get('range', {}).get('end', {}).get('line', 0), 
                             character=impl_loc.get('range', {}).get('end', {}).get('character', 0))
            )
        )
        locations.append(loc)
    
    return locations

async def get_type_definition_locations(uri: str, position: Position, language: str = None) -> List[Location]:
    file_path = _uri_to_file_path(uri)
    line, col = _position_to_line_col(position)
    
    # Use language-specific LSP if provided
    current_lsp = get_lsp_server(language) if language else lsp
    
    with current_lsp.start_server():
        type_definitions = current_lsp.request_type_definition(file_path, line, col)
    
    # Convert results to Location objects
    locations = []
    for type_def_loc in type_definitions or []:
        loc = Location(
            uri=_uri_to_file_path(type_def_loc.get('uri', uri)),
            range=Range(
                start=Position(line=type_def_loc.get('range', {}).get('start', {}).get('line', 0), 
                               character=type_def_loc.get('range', {}).get('start', {}).get('character', 0)),
                end=Position(line=type_def_loc.get('range', {}).get('end', {}).get('line', 0), 
                             character=type_def_loc.get('range', {}).get('end', {}).get('character', 0))
            )
        )
        locations.append(loc)
    
    return locations

async def get_document_symbol(uri: str, language: str = None):
    file_path = _uri_to_file_path(uri)
    
    # Use language-specific LSP if provided
    current_lsp = get_lsp_server(language) if language else lsp
    
    with current_lsp.start_server():
        symbols = current_lsp.request_document_symbols(file_path)
    
    # Convert to a more usable format that includes location
    document_symbols = []
    for symbol in symbols[0] or []:
        # Handle the actual multilspy document symbol format
        if 'range' in symbol and 'name' in symbol:
            # Create a DocumentSymbol object
            symbol_obj = DocumentSymbol(
                name=symbol.get('name', ''),
                kind=symbol.get('kind', 0),
                location=Location(
                    uri=_uri_to_file_path(uri),
                    range=Range(
                        start=Position(
                            line=symbol.get('range', {}).get('start', {}).get('line', 0),
                            character=symbol.get('range', {}).get('start', {}).get('character', 0)
                        ),
                        end=Position(
                            line=symbol.get('range', {}).get('end', {}).get('line', 0),
                            character=symbol.get('range', {}).get('end', {}).get('character', 0)
                        )
                    )
                )
            )
            document_symbols.append(symbol_obj)
    
    return document_symbols

async def get_text_from_location(location: Location) -> str:
    """Fetch text from a given location."""
    file_path = _uri_to_file_path(location.uri)
    
    # Read the file and extract the relevant text
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
        start_line = location.range.start.line
        start_char = location.range.start.character
        end_line = location.range.end.line
        end_char = location.range.end.character
        
        if start_line == end_line:
            return lines[start_line][start_char:end_char]
        else:
            text = lines[start_line][start_char:]
            for line_num in range(start_line + 1, end_line):
                text += lines[line_num]
            text += lines[end_line][:end_char]
            return text
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

async def get_lines_from_location(location: Location, line_count: int) -> str:
    """Fetch a specified number of lines from a given location."""
    file_path = _uri_to_file_path(location.uri)
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
        start_line = location.range.start.line
        end_line = min(start_line + line_count, len(lines))
        
        return ''.join(lines[start_line:end_line])
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


async def get_parsed_hovers(uri: str, position: Position, symbol_name: Optional[str] = None, language: str = None) -> List[ParsedHover]:
    """Get parsed hover information for a position."""
    file_path = _uri_to_file_path(uri)
    line, col = _position_to_line_col(position)
    
    # Use language-specific LSP if provided
    current_lsp = get_lsp_server(language) if language else lsp
    
    with current_lsp.start_server():
        hover_response = current_lsp.request_hover(file_path, line, col)
    # Process and return the hover response
    return extract_hover_content(hover_response)
