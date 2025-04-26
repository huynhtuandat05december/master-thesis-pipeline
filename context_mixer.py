import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, TypedDict

from schema.common import Position, Document
from ranking.reciprocal_rank_fusion import fuse_results
from text_retrieval.jaccard_retriever import JaccardSimilarityRetriever
from graph_retrieval.lsp import LsptRetriever

BASE_DIR = '/Users/datht22/Desktop/codevista/jaccard_warp/ReccEval/Source_Code/'

class ContextMixer:
    """
    The context mixer is responsible for combining multiple context retrieval strategies into a
    single proposed context list.
    
    This is done by ranking the order of documents using reciprocal rank fusion and then combining
    the snippets from each retriever into a single list.
    """
    
    def __init__(self):
        self.retrievers = [JaccardSimilarityRetriever(base_dir=BASE_DIR), LsptRetriever()]
        self.maxChars = 10000  # Default value
    
    async def get_context(self, document: Document, position: Position, repo: Optional[str] = None):
        
        retrievers = self.retrievers
        
        # Gather results from all retrievers asynchronously
        results_with_data_logging = await self._gather_retriever_results(retrievers, document, position, repo)
        
        # Extract original retriever results
        results = self._extract_original_retriever_results(results_with_data_logging, retrievers)
        
        # Original retrievers were 'none'
        if len(results) == 0:
            return {
                "context": [],
            }
    
        # Get prefix and suffix from document for character counting
        prefix = document.prefix if hasattr(document, 'prefix') else ""
        suffix = document.suffix if hasattr(document, 'suffix') else ""
        max_chars = self.maxChars
        
        # Convert snippets to sets before passing to fuse_results
        # This ensures we're passing the correct type to the function
        retrieved_sets = []
        for result in results:
            # Convert list to set for the fuse_results function
            snippet_set = set()
            for snippet in result["snippets"]:
                snippet_set.add(snippet)
            retrieved_sets.append(snippet_set)
        
        # Fuse results using reciprocal rank fusion
        fused_results = fuse_results(
            retrieved_sets=retrieved_sets,
            ranking_identities=lambda result: self._get_line_ids(result)
        )

        
        # Calculate total characters
        total_chars = len(prefix) + len(suffix)
        
        # Create mixed context
        mixed_context = []
        
        for snippet in fused_results:
            if total_chars + len(snippet.content) > max_chars:
                continue
            
            mixed_context.append(snippet)
            total_chars += len(snippet.content)

        return {
            "context": mixed_context,
        }
    
    def _get_line_ids(self, result):
        """
        Generate identifiers for each line in the result.
        This matches the behavior of the TypeScript implementation.
        
        Args:
            result: A result object with uri, startLine, and endLine fields
            
        Returns:
            A list of string identifiers in the format "uri:line_number"
        """
        # If start_line and end_line are not defined, just use the URI
        if not hasattr(result, 'start_line') or not hasattr(result, 'end_line'):
            return [result.uri]
        
        # Generate an identifier for each line in the range
        line_ids = []
        for i in range(result.start_line, result.end_line + 1):
            line_ids.append(f"{result.uri}:{i}")
        
        return line_ids
    
    async def _gather_retriever_results(self, retrievers, document: Document, position: Optional[Position] = None, repo: Optional[str] = None):
        """Gather results from all retrievers asynchronously."""
        tasks = []
        
        for retriever in retrievers:
            tasks.append(self._get_retriever_result(retriever, document, position, repo))
        
        return await asyncio.gather(*tasks)
    
    async def _get_retriever_result(self, retriever, document: Document, position: Optional[Position] = None, repo: Optional[str] = None):
        """Get result from a single retriever with timing."""
        
        all_snippets = await retriever.retrieve(document, position, repo)
        
        # For now, no filtering
        filtered_snippets = all_snippets
        
        return {
            "identifier": retriever.identifier,
            "snippets": filtered_snippets,
        }
    
    def _extract_original_retriever_results(
        self, results_with_data_logging, 
        original_retrievers
    ) :
        """Extract results from original retrievers."""
        original_identifiers = {retriever.identifier for retriever in original_retrievers}
        return [result for result in results_with_data_logging if result["identifier"] in original_identifiers]
    
if __name__ == "__main__":
    context_mixer = ContextMixer()
    document =Document(uri="/Users/datht22/Desktop/codevista/jaccard_warp/test/test.py", language_id="python", text="""
from .import_test import another_call
def example():
    print("Hello")
    another_call()
    """.strip())
    position = Position(line=3, character=17)
    repo = "test"
    result = asyncio.run(context_mixer.get_context(document, position, repo))
    print(result)