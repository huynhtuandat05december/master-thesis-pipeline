from collections import defaultdict
from typing import List, Set, TypeVar, Callable

T = TypeVar("T")
RRF_K = 60

def fuse_results(
    retrieved_sets: List[Set[T]], ranking_identities: Callable[[T], List[str]]
) -> Set[T]:
    """
    Implements a basic variant of reciprocal rank fusion to combine context items from various
    retrievers into one result set.

    Args:
        retrieved_sets: Lists of result sets from different retrievers
        ranking_identities: Function that returns identifiers for each result

    Returns:
        A fused set of results
    """
    # For every retrieved result set, create a map of results by document
    results_by_document = {}
    
    for retriever_index, results in enumerate(retrieved_sets):
        for result in results:
            for doc_id in ranking_identities(result):
                if doc_id not in results_by_document:
                    results_by_document[doc_id] = {}
                
                if retriever_index not in results_by_document[doc_id]:
                    results_by_document[doc_id][retriever_index] = []
                
                results_by_document[doc_id][retriever_index].append(result)

    # Rank the order of documents using reciprocal rank fusion
    fused_document_scores = {}
    
    for retriever_index, results in enumerate(retrieved_sets):
        for rank, result in enumerate(results):
            for doc_id in ranking_identities(result):
                # Only consider the best ranked result per document for each retriever
                if results_by_document[doc_id][retriever_index][0] != result:
                    continue
                
                reciprocal_rank = 1 / (RRF_K + rank)
                
                if doc_id not in fused_document_scores:
                    fused_document_scores[doc_id] = 0
                
                fused_document_scores[doc_id] += reciprocal_rank

    # Sort documents by score in descending order
    top_documents = sorted(fused_document_scores.keys(), 
                          key=lambda doc_id: fused_document_scores[doc_id], 
                          reverse=True)
    
    fused_results = set()

    # Combine results from each document and retriever into a result set
    for doc_id in top_documents:
        result_by_document = results_by_document.get(doc_id)
        if not result_by_document:
            continue
        
        # Find the maximum number of matches across all retrievers for this document
        max_matches = max(len(snippets) for snippets in result_by_document.values())

        # Add results to the fused set, prioritizing by retriever order
        for i in range(max_matches):
            for _, snippets in result_by_document.items():
                if i >= len(snippets):
                    continue
                
                snippet = snippets[i]
                fused_results.add(snippet)

    return fused_results
