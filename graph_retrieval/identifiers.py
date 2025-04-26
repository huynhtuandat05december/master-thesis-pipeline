from typing import List, Optional

from tree_sitter_local.tree_sitter_local import TreeSitterAnalyzer
from schema.common import Position, Document
from schema.tree_sitter import SymbolRequest


def get_last_n_graph_context_identifiers_from_document(document: Document, position: Position, n: int) -> List[SymbolRequest]:
    # Define start and end positions for analysis
    start_pos = (max(position.line - 100, 0), 0)
    end_pos = (position.line, position.character + 1)

    current_analyzer = TreeSitterAnalyzer(language_string=document.language_id) 

    function_calls = current_analyzer.analyze_source(
        source_code=document.text,
        start_pos=start_pos,
        end_pos=end_pos
    )

    # Convert the function calls to symbol requests
    symbol_requests = [
        SymbolRequest(
            uri=document.uri,
            language_id=document.language_id,
            node_type="call",  # Function calls are of type "call"
            symbol_name=call.name,
            position=Position(
                line=call.start_line,
                character=call.start_char,
            ),
            capture_name="identifier",  # This was the capture name in the TreeSitter query
        )
        for call in function_calls
    ]

    # Sort the symbol requests to match TypeScript logic
    def custom_sort(a, b):
        # Check if positions are equal
        if a.position.line == b.position.line and a.position.character == b.position.character:
            # If equal, sort by symbol_name length (longer first)
            return -1 if len(a.symbol_name) > len(b.symbol_name) else 1
        # Otherwise sort by position (earlier positions come last)
        if a.position.line < b.position.line or (a.position.line == b.position.line and a.position.character < b.position.character):
            return 1  # a is before b, so it should come after
        return -1     # a is after b, so it should come before
    
    # Use Python's functools.cmp_to_key to convert the comparison function for sort()
    from functools import cmp_to_key
    symbol_requests.sort(key=cmp_to_key(custom_sort))
    
    # Deduplicate and return the top n results
    return symbol_requests[:n]



def get_last_n_graph_context_identifiers_from_string(n: int, uri: str, language_id: str, source: str, prioritize: str = None) -> List[SymbolRequest]:
    # Define start and end positions for analysis
    # For string analysis, we start from the beginning
    start_pos = (0, 0)
    
    # Calculate the end position based on the number of lines in the source
    lines = source.splitlines()
    end_pos = (len(lines) - 1, len(lines[-1]) if lines else 0)

    # Use the TreeSitterAnalyzer.analyze_source method
    # Make sure we're using the right language analyzer
    if language_id != analyzer.language_string:
        # If a different language is needed, create a new analyzer instance
        current_analyzer = TreeSitterAnalyzer(language_string=language_id)
    else:
        current_analyzer = analyzer

    function_calls = current_analyzer.analyze_source(
        source_code=source,
        start_pos=start_pos,
        end_pos=end_pos
    )

    # Convert the function calls to symbol requests
    symbol_requests = [
        SymbolRequest(
            uri=uri,
            language_id=language_id,
            node_type="call",  # Function calls are of type "call"
            symbol_name=call.name,
            position=Position(
                line=call.start_line,
                character=call.start_char,
            ),
            capture_name="identifier",  # This was the capture name in the TreeSitter query
        )
        for call in function_calls
    ]

    # Sort the symbol requests to match TypeScript logic
    def custom_sort(a, b):
        # Check if positions are equal
        if a.position.line == b.position.line and a.position.character == b.position.character:
            # If equal, sort by symbol_name length (longer first)
            return -1 if len(a.symbol_name) > len(b.symbol_name) else 1
        # Otherwise sort by position (earlier positions come last)
        if a.position.line < b.position.line or (a.position.line == b.position.line and a.position.character < b.position.character):
            return 1  # a is before b, so it should come after
        return -1     # a is after b, so it should come before
    
    # Use Python's functools.cmp_to_key to convert the comparison function for sort()
    from functools import cmp_to_key
    symbol_requests.sort(key=cmp_to_key(custom_sort))
    
    # Deduplicate and return the top n results
    return symbol_requests[:n]

