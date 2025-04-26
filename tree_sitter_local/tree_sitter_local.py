from tree_sitter import Language, Parser
from typing import List, Tuple, Optional
from dataclasses import dataclass
import os
# from tree_sitter_languages import get_language
import tree_sitter_python as tspython
from tree_sitter_languages import get_language
from programing_language import ProgrammingLanguage

@dataclass
class FunctionCall:
    name: str
    start_line: int
    end_line: int
    start_char: int
    end_char: int
    content: str

class TreeSitterAnalyzer:
    def __init__(self, language_string: str):
        # Initialize parser with Python grammar
        self.language_string = language_string
        self.language = get_language(language=self.language_string)
        self.parser = Parser()
        self.parser.set_language(self.language)
        self.FUNCTION_CALL_QUERY = self.language.query("""(call (identifier) @identifier)""")
        self.initialize_language()

    def initialize_language(self):
        if self.language_string == "python":
            self.FUNCTION_CALL_QUERY = self.language.query("""(call (identifier) @identifier)""")
        if self.language_string == "java":
            self.FUNCTION_CALL_QUERY = self.language.query("""            
            (method_invocation name:(identifier) @identifier)
            (object_creation_expression (type_identifier) @identifier_object_creation)
            (formal_parameter (type_identifier) @identifier)
            (local_variable_declaration (type_identifier) @identifier)
            (field_access field:(identifier) @identifier)""")
        if self.language_string == "cpp":
            self.FUNCTION_CALL_QUERY = self.language.query("""(call function: (identifier) @identifier)""")
        if self.language_string == "c_sharp":
            self.FUNCTION_CALL_QUERY = self.language.query(""" (call function: (identifier) @identifier)""")
    
    def safe_parse(self, raw_code, old_tree=None):
        try:
            if old_tree:
                self.parser.parse(bytes(raw_code, "utf8"), old_tree)
            return self.parser.parse(bytes(raw_code, "utf8"))
        except Exception as e:
            return None

    def analyze_file(self, file_path: str) -> List[FunctionCall]:
        """Analyze a Python file for function calls"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        return self.analyze_source(source_code)

    def analyze_source(self, source_code: str, start_pos: Tuple[int, int] = None, end_pos: Tuple[int, int] = None) -> List[FunctionCall]:
        """Analyze Python source code for function calls within specified range
        
        Args:
            source_code (str): The source code to analyze
            start_pos (Tuple[int, int]): Start position as (line, character), optional
            end_pos (Tuple[int, int]): End position as (line, character), optional
        """
        tree = self.parser.parse(bytes(source_code, "utf8"))
        calls = []

        # Get all lines for content extraction
        lines = source_code.split('\n')

        # Convert positions to byte offsets if provided
        start_byte = None if start_pos is None else self._pos_to_byte(source_code, start_pos[0], start_pos[1])
        end_byte = None if end_pos is None else self._pos_to_byte(source_code, end_pos[0], end_pos[1])

        # Get all nodes from the query
        nodes = self.get_nodes_from_query(self.FUNCTION_CALL_QUERY, tree.root_node)
        
        for node in nodes:
            # Manually filter nodes based on position if range is specified
            if start_byte is not None or end_byte is not None:
                node_start_byte = node.start_byte
                node_end_byte = node.end_byte
                
                # Skip nodes that are outside our range
                if (start_byte is not None and node_end_byte < start_byte) or \
                   (end_byte is not None and node_start_byte > end_byte):
                    continue
            
            start_point = node.start_point
            end_point = node.end_point
            
            # Extract the actual content
            if start_point[0] == end_point[0]:  # Same line
                content = lines[start_point[0]][start_point[1]:end_point[1]]
            else:
                # Multi-line call
                content = []
                for i in range(start_point[0], end_point[0] + 1):
                    if i == start_point[0]:
                        content.append(lines[i][start_point[1]:])
                    elif i == end_point[0]:
                        content.append(lines[i][:end_point[1]])
                    else:
                        content.append(lines[i])
                content = '\n'.join(content)

            calls.append(FunctionCall(
                name=node.text.decode('utf8'),
                start_line=start_point[0],
                end_line=end_point[0],
                start_char=start_point[1],
                end_char=end_point[1],
                content=content
            ))

        return calls

    def _pos_to_byte(self, source: str, line: int, character: int) -> int:
        """Convert line and character position to byte offset"""
        lines = source.split('\n')
        byte_offset = 0
        
        # Add bytes for complete lines
        for i in range(line):
            byte_offset += len(lines[i].encode('utf-8')) + 1  # +1 for newline

        # Add bytes for characters in current line
        if character > 0:
            byte_offset += len(lines[line][:character].encode('utf-8'))
            
        return byte_offset

    def get_nodes_from_query(self, query, root_node, start_byte=None, end_byte=None):
        """Extract only the Node objects from query captures
        
        Args:
            query: The compiled tree-sitter query
            root_node: The root node to search in
            start_byte: Not used, kept for API compatibility
            end_byte: Not used, kept for API compatibility
            
        Returns:
            List of Node objects matching the query
        """
        # The captures method returns a structure with nodes
        captures = query.captures(root_node)
        
        # Print for debugging
        
        # Check if it's a tuple/list structure
        if isinstance(captures, list):
            # If it's a list of tuples (node, name), extract just the nodes
            if captures and isinstance(captures[0], tuple):
                return [capture[0] for capture in captures]
            
            # If it's a list within a list, flatten it
            if captures and isinstance(captures[0], list):
                return captures[0]
                
            # If it's already a flat list of nodes
            return captures
            
        # Handle dictionary-like structure if that's what's returned
        if hasattr(captures, 'values'):
            values_list = list(captures.values())
            # If values() returns a list of lists, flatten it
            if values_list and isinstance(values_list[0], list):
                return values_list[0]
            return values_list
            
        # Fallback: return an empty list if we can't determine the structure
        return []

    def get_function_at_position(self, source_code: str, line: int, character: int) -> Optional[FunctionCall]:
        """Get function call at a specific position"""
        calls = self.analyze_source(source_code)
        for call in calls:
            if (call.start_line <= line <= call.end_line and
                (call.start_line != line or call.start_char <= character) and
                (call.end_line != line or character <= call.end_char)):
                return call
        return None

if __name__ == "__main__":
    # Example usage
    analyzer = TreeSitterAnalyzer(language_string='python')
    
    # Example source code
    source = """
def example():
    print("Hello")
    my_function(arg1, 
                arg2)
    another_call()
    """
    
    # Analyze source code
    calls = analyzer.analyze_source(source)
    
    # Print results
    print("Found function calls:")
    for call in calls:
        print(f"\nFunction: {call.name}")
        print(f"Location: Line {call.start_line + 1}, Char {call.start_char} to Line {call.end_line + 1}, Char {call.end_char}")
        print(f"Content: {call.content}")

    # Test position lookup
    position_call = analyzer.get_function_at_position(source, 3, 5)  # Should find my_function
    if position_call:
        print(f"\nFound function at position: {position_call.name}")