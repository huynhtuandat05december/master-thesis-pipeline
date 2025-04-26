from dataclasses import dataclass
from schema.common import Position
@dataclass
class SymbolRequest:
    symbol_name: str
    position: Position
    uri: str
    node_type: str
    language_id: str
    capture_name: str