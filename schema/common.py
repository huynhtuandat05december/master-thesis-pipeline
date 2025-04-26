from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Position:
    line: int
    character: int
    def translate(self, line, character):
        self.line = self.line + line
        self.character = self.character + character

        return self

@dataclass
class Range:
    start: Position
    end: Position

@dataclass
class Location:
    uri: str
    range: Range

@dataclass
class Document:
    uri: str
    language_id: Optional[str]
    text: str
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    offset: Optional[int] = None
    position: Optional[Position] = None

@dataclass
class AutocompleteSymbolContextSnippet:
    content: str
    uri: str
    start_line: int
    end_line: int
