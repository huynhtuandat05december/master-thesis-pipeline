from typing import List, Optional
from text_retrieval.best_jaccard_match import best_jaccard_matches
from schema.jaccard import JaccardMatchWithFilename
from schema.common import Document, Position
from .tool import iterate_repository, last_n_lines


class JaccardSimilarityRetriever:
    def __init__(self, snippet_window_size = 50, max_matches_per_file = 20, max_chunk_result = 20, slide = 1, thresh_hold = 0, base_dir = '/Users/datht22/Desktop/codevista/jaccard_warp'):
        self.identifier = "JaccardSimilarityRetriever"
        self.snippet_window_size = snippet_window_size
        self.max_matches_per_file = max_matches_per_file
        self.max_chunk_result = max_chunk_result
        self.slide = slide
        self.thresh_hold = thresh_hold
        self.base_dir = base_dir
    
    async def retrieve(self, document: Document, position: Optional[Position] = None, repo: Optional[str] = None) -> List[JaccardMatchWithFilename]:
        """Retrieve context using Jaccard similarity."""
        # Set identifier for the retriever
        self.identifier = "JaccardSimilarityRetriever"
        
        # Use do_retrieval method if it exists
        if hasattr(document, 'prefix'):
            # Get target text using last_n_lines similar to jaccardRetriever.ts
            target_text = last_n_lines(document.prefix, self.snippet_window_size)
        else:
            # Fallback to full text if prefix is not available
            target_text = last_n_lines(document.text, self.snippet_window_size)
        
        files = iterate_repository(self.base_dir, repo, document.uri)
        
        matches = []
        for file_contents in files:
            file_matches = best_jaccard_matches(
                target_text,
                file_contents.text,
                self.snippet_window_size,
                self.max_matches_per_file,
                self.slide
            )

            related_matches = [match for match in file_matches if match.score > 0]

            for match in related_matches:
                if match.score < self.thresh_hold:
                    continue
                matches.append(JaccardMatchWithFilename(start_line=match.start_line, end_line=match.end_line, uri=file_contents.uri, score=match.score, content=match.content))

        matches.sort(key=lambda x: -x.score)
        return matches


if __name__ == "__main__":
    import asyncio
    # Test document with prefix for jaccard matching
    test_document = Document(
        uri="/Users/datht22/Desktop/codevista/jaccard_warp/test/test.py",
        text="""from .import_test import another_call
def example():
    print("Hello")
    another_call()
    """.strip(),
    language_id="python"
    )
    

    # Path to repository for testing
    repo_path = "/Users/datht22/Desktop/codevista/test_context_autocompletion"
    
    retriever = JaccardSimilarityRetriever()

    result = asyncio.run(retriever.retrieve(
        document=test_document,
        repo='test'
    ))

    print(result)

