from dataclasses import dataclass
from schema.common import Location, Position
from typing import Optional

@dataclass
class ParsedHover:
    """Parsed hover information."""
    text: str = ""
    kind: Optional[str] = None

# A simple DocumentSymbol class for our needs
@dataclass
class DocumentSymbol:
    name: str
    kind: int
    location: Location
@dataclass
class LSPSymbolContextSnippet:
    """Symbol context snippet for autocomplete."""
    identifier: str
    content: str
    symbol: str
    uri: str
    start_line: int
    end_line: int
    
    def __hash__(self):
        return hash((self.identifier, self.uri, self.start_line, self.end_line, self.symbol))
    
    def __eq__(self, other):
        if not isinstance(other, LSPSymbolContextSnippet):
            return False
        return (self.identifier == other.identifier and
                self.uri == other.uri and
                self.start_line == other.start_line and
                self.end_line == other.end_line and
                self.symbol == other.symbol)
    def to_dict(self):
        return {
            'identifier': self.identifier,
            'uri': self.uri,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'symbol': self.symbol
        }