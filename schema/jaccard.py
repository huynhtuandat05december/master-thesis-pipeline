from dataclasses import dataclass, field
from typing import List

@dataclass(eq=True)
class JaccardMatch:
    """Represents a match using Jaccard similarity."""
    score: float
    content: str
    start_line: int
    end_line: int
    
    def __hash__(self):
        """Make this class hashable."""
        return hash((self.score, self.start_line, self.end_line, self.content))
    
    def to_dict(self):
        """Convert the object to a dictionary for JSON serialization."""
        return {
            'score': self.score,
            'content': self.content,
            'start_line': self.start_line,
            'end_line': self.end_line
        }

@dataclass(eq=True)
class JaccardMatchWithFilename(JaccardMatch):
    """Represents a JaccardMatch with file information."""
    uri: str
    
    def __hash__(self):
        """Make this class hashable so it can be used in sets."""
        # Include parent class attributes in hash
        return hash((super().__hash__(), self.uri))
    
    def to_dict(self):
        """Convert the object to a dictionary for JSON serialization."""
        result = super().to_dict()
        result['uri'] = self.uri
        return result

