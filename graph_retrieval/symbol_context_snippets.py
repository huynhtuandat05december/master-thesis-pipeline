from typing import List, Dict, Optional, Set, Union, Any, Tuple

# Import LSP commands from our rewritten module
from graph_retrieval.lsp_command import (
    get_definition_locations,
    # get_implementation_locations,
    # get_type_definition_locations,
    get_parsed_hovers,
    get_document_symbol,
    get_text_from_location,
    get_lines_from_location,
)
from graph_retrieval.identifiers import get_last_n_graph_context_identifiers_from_string
from graph_retrieval.hover import is_unhelpful_symbol_snippet
from schema.common import Position, Location
from schema.lsp import LSPSymbolContextSnippet
from schema.tree_sitter import SymbolRequest

# These would normally be imported from other modules
# For this implementation we'll use placeholders
NESTED_IDENTIFIERS_TO_RESOLVE = 5
CAPTURE_NAME_OBJECT_CREATE = "object_create"

# Common keywords and import paths (simplified)
common_keywords = {"self", "this", "super", "None", "True", "False"}
common_import_paths = [
    "stdlib", 
    "site-packages", 
    "dist-packages",
    "python3",
    "venv",
    "lib"
]



def is_common_import(uri: str) -> bool:
    """Check if a URI points to a common import path."""
    for import_path in common_import_paths:
        if import_path in uri:
            return True
    return False


def is_javascript(language_id: str) -> bool:
    """Check if language ID is JavaScript or TypeScript."""
    return language_id in ["javascript", "typescript", "javascriptreact", "typescriptreact"]


async def get_text_by_symbols(definition_location: Location, symbol_name: str, capture_name: str, language_id: str = None) -> str:
    """Get text for symbols in a document."""
    document_symbols = await get_document_symbol(definition_location.uri, language=language_id)
    
    symbol = None
    if capture_name == CAPTURE_NAME_OBJECT_CREATE:
        for s in document_symbols:
            if s.name == symbol_name or symbol_name in s.name:
                symbol = s
                break
    else:
        for s in document_symbols:
            # Check if symbol is at the same location
            if hasattr(s, 'location') and s.location.range.start.line == definition_location.range.start.line:
                symbol = s
                break
            elif s.name == symbol_name or symbol_name in s.name:
                symbol = s
                break
    
    if not symbol:
        return ''
    
    definition_string = (await get_text_from_location(symbol.location)).strip()
    return definition_string


def is_defined(item: Optional[Any]) -> bool:
    """Check if an item is defined (not None)."""
    return item is not None


async def get_snippet_for_location_getter_with_hover_and_get_symbols(
    location_getter,
    symbol_snippet_request: SymbolRequest,
    recursion_limit: int,
) -> Optional[List[Dict[str, Any]]]:
    """Get snippet for a location using hover and symbol information."""
    uri = symbol_snippet_request.uri
    position = symbol_snippet_request.position
    node_type = symbol_snippet_request.node_type
    symbol_name = symbol_snippet_request.symbol_name
    language_id = symbol_snippet_request.language_id
    capture_name = symbol_snippet_request.capture_name
    
    definition_locations = await location_getter(uri, position, language=language_id)
    # Sort for the narrowest definition range
    sorted_definition_locations = sorted(
        [loc for loc in definition_locations if not is_common_import(loc.uri)],
        key=lambda a: (a.range.start.line - a.range.end.line)
    )
    
    if not sorted_definition_locations:
        return None
    
    definition_location = sorted_definition_locations[0]
    definition_uri = definition_location.uri
    definition_range = definition_location.range
    
    # Create basic symbol context snippet
    symbol_context_snippet = {
        "identifier": "LSPRetriever",
        "uri": definition_uri,
        "start_line": definition_range.start.line,
        "end_line": definition_range.end.line,
        "symbol": symbol_name,
        "location": definition_location,
        "content": None,
    }
    
    # Get hover information
    parsed_hover = (await get_parsed_hovers(uri, position, symbol_name, language=language_id))[0]
    definition_string = parsed_hover.text
    hover_kind = parsed_hover.kind
    is_hover = True
    
    # Try different approaches to get meaningful definition text
    if is_unhelpful_symbol_snippet(symbol_name, definition_string):
        hover_kind = None
        is_hover = False
        
        if node_type == "type_identifier":
            definition_string = await get_text_from_location(definition_location)
        
        if is_unhelpful_symbol_snippet(symbol_name, definition_string):
            parsed_hover = (await get_parsed_hovers(
                definition_location.uri,
                definition_range.start,
                language=language_id
            ))[0]
            
            definition_string = parsed_hover.text
            hover_kind = parsed_hover.kind
            is_hover = True

    if is_unhelpful_symbol_snippet(symbol_name, definition_string):
        hover_kind = None
        is_hover = False
        definition_string = await get_text_from_location(definition_location)
    

    if not definition_string or is_unhelpful_symbol_snippet(symbol_name, definition_string) or len(definition_string.splitlines()) > 100:
        return [symbol_context_snippet]
    
    # Get nested symbols
    nested_symbols_source = await get_lines_from_location(definition_location, 10)
    
    if is_javascript(language_id):
        # Modify source for proper parsing
        if hover_kind == "method":
            nested_symbols_source = "function " + nested_symbols_source
        
        if nested_symbols_source.strip().startswith("constructor"):
            nested_symbols_source = f"{{{nested_symbols_source}}}"
    
    # Get nested symbols from the source
    initial_nested_symbol_requests = get_last_n_graph_context_identifiers_from_string(
        n=NESTED_IDENTIFIERS_TO_RESOLVE,
        uri=definition_location.uri,
        language_id=language_id,
        source=nested_symbols_source,
        prioritize="head"
    )

    # Filter nested symbol requests
    nested_symbol_requests = []
    for request in initial_nested_symbol_requests:
        if (
            len(request.symbol_name) > 0 and
            symbol_name != request.symbol_name and
            request.symbol_name not in common_keywords 
            # and ("class" in nested_symbols_source or (definition_string and request.symbol_name in definition_string))
        ):
            # Adjust position
            if is_hover:
                request.position = Position(
                    line=request.position.line + definition_range.start.line,
                    character=request.position.character
                )
            else:
                request.position = Position(
                    line=request.position.line + definition_range.start.line,
                    character=request.position.character + definition_range.start.character
                )
            
            nested_symbol_requests.append(request)
    
    # Get final definition string
    if "class" in nested_symbols_source or capture_name == CAPTURE_NAME_OBJECT_CREATE:
        final_definition_string = definition_string + "\n" + await get_text_by_symbols(definition_location, symbol_name, capture_name, language_id)
    else:
        final_definition_string = definition_string
    
    symbol_context_snippet["content"] = final_definition_string
    
    if not nested_symbol_requests:
        return [symbol_context_snippet]
    
    nested_result = await get_symbol_context_snippets_recursive(
        symbols_snippet_requests=nested_symbol_requests,
        recursion_limit=recursion_limit - 1,
    )
    return [symbol_context_snippet] + nested_result


async def get_symbol_context_snippets_recursive(
    symbols_snippet_requests: List[SymbolRequest],
    recursion_limit: int,
) -> List[Dict[str, Any]]:
    """Recursively get symbol context snippets."""
    if recursion_limit == 0:
        return []
    
    
    for symbol_snippet_request in symbols_snippet_requests:
        location_getters = [
            get_definition_locations,
            # get_type_definition_locations,
            # get_implementation_locations,
        ]
        
        for location_getter in location_getters:
            symbol_context_snippets = await get_snippet_for_location_getter_with_hover_and_get_symbols(
                location_getter,
                symbol_snippet_request,
                recursion_limit,
            )
            
            # If we found a content, we can stop trying other location getters
            if symbol_context_snippets is not None:
                break
        
        if symbol_context_snippets is None:
            return []

        return symbol_context_snippets
    
    return []


async def get_symbol_context_snippets(
    symbols_snippet_requests: List[SymbolRequest],
    recursion_limit: int
) -> List[LSPSymbolContextSnippet]:
    """Get symbol context snippets from requests."""
    result = await get_symbol_context_snippets_recursive(
        symbols_snippet_requests=symbols_snippet_requests,
        recursion_limit=recursion_limit
    )
    context_snippets = []
    for snippet in result:
        context_snippets.append(LSPSymbolContextSnippet(
            identifier=snippet["identifier"],
            content=snippet["content"],
            symbol=snippet["symbol"],
            uri=snippet["uri"],
            start_line=snippet["start_line"],
            end_line=snippet["end_line"],
        ))
    
    return context_snippets


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(get_symbol_context_snippets([SymbolRequest(symbol_name='another_call', position=Position(line=3, character=4), uri='file://test/test.py', node_type='call', language_id='python', capture_name='identifier')], 2))
    print('result',result)