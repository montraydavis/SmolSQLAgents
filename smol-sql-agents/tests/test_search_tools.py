"""Tests for the enhanced search tools using OpenAI embeddings."""

import pytest
from unittest.mock import Mock, patch
from src.vector.search import (
    search_table_documentation,
    search_relationship_documentation,
    semantic_search_all_documentation
)

@pytest.fixture
def mock_agent():
    """Create a mock PersistentDocumentationAgent."""
    with patch('src.vector.search.PersistentDocumentationAgent') as mock:
        agent_instance = Mock()
        mock.return_value = agent_instance
        yield agent_instance

@pytest.fixture
def mock_search_results():
    """Create mock search results."""
    table_result = {
        "metadata": {
            "table_name": "users",
            "business_purpose": "Stores user information",
            "schema": {
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "username", "type": "varchar"}
                ]
            }
        },
        "similarity": 0.95
    }
    
    relationship_result = {
        "metadata": {
            "relationship_id": "users_orders_fk",
            "relationship_type": "one-to-many",
            "documentation": "Each user can have multiple orders",
            "tables": ["users", "orders"]
        },
        "similarity": 0.85
    }
    
    return {"table": table_result, "relationship": relationship_result}

def test_search_table_documentation(mock_agent, mock_search_results):
    """Test searching table documentation."""
    # Setup
    mock_agent.indexer_agent.search_documentation.return_value = [mock_search_results["table"]]
    
    # Execute
    results = search_table_documentation("user tables", limit=5)
    
    # Verify
    assert len(results) == 1
    assert results[0]["table_name"] == "users"
    assert results[0]["similarity_score"] == 0.95
    assert "schema" in results[0]
    
    mock_agent.indexer_agent.search_documentation.assert_called_once_with(
        "user tables", doc_type="tables", limit=5
    )

def test_search_relationship_documentation(mock_agent, mock_search_results):
    """Test searching relationship documentation."""
    # Setup
    mock_agent.indexer_agent.search_documentation.return_value = [mock_search_results["relationship"]]
    
    # Execute
    results = search_relationship_documentation("user relationships", limit=5)
    
    # Verify
    assert len(results) == 1
    assert results[0]["relationship_id"] == "users_orders_fk"
    assert results[0]["similarity_score"] == 0.85
    assert results[0]["tables_involved"] == ["users", "orders"]
    
    mock_agent.indexer_agent.search_documentation.assert_called_once_with(
        "user relationships", doc_type="relationships", limit=5
    )

def test_semantic_search_all_documentation(mock_agent, mock_search_results):
    """Test searching all documentation types."""
    # Setup
    def mock_search_side_effect(query, doc_type, limit):
        if doc_type == "tables":
            return [mock_search_results["table"]]
        else:
            return [mock_search_results["relationship"]]
    
    mock_agent.indexer_agent.search_documentation.side_effect = mock_search_side_effect
    
    # Execute
    results = semantic_search_all_documentation("user data", limit=10)
    
    # Verify
    assert "tables" in results
    assert "relationships" in results
    assert results["total_results"] > 0
    
    # Verify tables results
    assert len(results["tables"]) > 0
    assert results["tables"][0]["table_name"] == "users"
    
    # Verify relationship results
    assert len(results["relationships"]) > 0
    assert results["relationships"][0]["relationship_id"] == "users_orders_fk"

def test_semantic_search_empty_results(mock_agent):
    """Test searching with no results."""
    # Setup
    mock_agent.indexer_agent.search_documentation.return_value = []
    
    # Execute
    results = semantic_search_all_documentation("nonexistent data", limit=10)
    
    # Verify
    assert results["total_results"] == 0
    assert len(results["tables"]) == 0
    assert len(results["relationships"]) == 0

def test_search_with_invalid_limit(mock_agent, mock_search_results):
    """Test searching with invalid limit values."""
    # Setup
    def mock_search_side_effect(query, doc_type, limit):
        if doc_type == "tables":
            return [mock_search_results["table"]]
        else:
            return [mock_search_results["relationship"]]
    
    mock_agent.indexer_agent.search_documentation.side_effect = mock_search_side_effect
    
    # Execute with zero limit
    results = semantic_search_all_documentation("test", limit=0)
    assert results["total_results"] == 0
    
    # Execute with negative limit
    results = semantic_search_all_documentation("test", limit=-1)
    assert results["total_results"] == 0
