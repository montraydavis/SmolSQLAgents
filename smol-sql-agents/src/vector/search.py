"""Enhanced search tools using OpenAI embeddings for semantic similarity."""

from typing import List, Dict
from ..agents.core import PersistentDocumentationAgent
from ..agents.indexer import SQLIndexerAgent
from .store import SQLVectorStore

def search_table_documentation(query: str, limit: int = 5) -> List[Dict]:
    """Search table documentation using OpenAI embeddings similarity.
    
    Args:
        query: Natural language search query
        limit: Maximum number of results to return
        
    Returns:
        list[dict]: Relevant table documentation matches with similarity scores
    """
    agent = PersistentDocumentationAgent()
    results = agent.indexer_agent.search_documentation(query, doc_type="tables", limit=limit)
    
    # Format results for consistent output
    formatted_results = []
    for result in results:
        formatted_results.append({
            "table_name": result["metadata"]["table_name"],
            "business_purpose": result["metadata"]["business_purpose"],
            "similarity_score": result["similarity"],
            "schema": result["metadata"].get("schema", {}),
        })
    
    return formatted_results

def search_relationship_documentation(query: str, limit: int = 5) -> List[Dict]:
    """Search relationship documentation using OpenAI embeddings similarity.
    
    Args:
        query: Natural language search query
        limit: Maximum number of results to return
        
    Returns:
        list[dict]: Relevant relationship documentation matches with similarity scores
    """
    agent = PersistentDocumentationAgent()
    results = agent.indexer_agent.search_documentation(query, doc_type="relationships", limit=limit)
    
    # Format results for consistent output
    formatted_results = []
    for result in results:
        formatted_results.append({
            "relationship_id": result["metadata"]["relationship_id"],
            "relationship_type": result["metadata"]["relationship_type"],
            "documentation": result["metadata"]["documentation"],
            "tables_involved": result["metadata"]["tables"],
            "similarity_score": result["similarity"]
        })
    
    return formatted_results

def semantic_search_all_documentation(query: str, limit: int = 10) -> Dict:
    """Search across all documentation using OpenAI embeddings.
    
    Args:
        query: Natural language search query
        limit: Maximum total results to return
        
    Returns:
        dict: Combined results from tables and relationships with similarity scores
    """
    # Handle invalid limits
    if limit <= 0:
        return {
            "tables": [],
            "relationships": [],
            "total_results": 0
        }
    
    # Calculate per-category limits ensuring total doesn't exceed overall limit
    per_category_limit = limit // 2
    remaining_limit = limit % 2
    
    # Search both categories
    table_results = search_table_documentation(query, per_category_limit + remaining_limit)
    relationship_results = search_relationship_documentation(query, per_category_limit)
    
    # Combine and sort all results by similarity score
    all_results = []
    for result in table_results:
        all_results.append({
            "type": "table",
            "name": result["table_name"],
            "similarity": result["similarity_score"],
            "content": result
        })
    
    for result in relationship_results:
        all_results.append({
            "type": "relationship",
            "name": result["relationship_id"],
            "similarity": result["similarity_score"],
            "content": result
        })
    
    # Sort combined results by similarity score
    all_results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Take top results up to limit
    all_results = all_results[:limit]
    
    # Format final response
    return {
        "tables": [r["content"] for r in all_results if r["type"] == "table"],
        "relationships": [r["content"] for r in all_results if r["type"] == "relationship"],
        "total_results": len(all_results)
    }
