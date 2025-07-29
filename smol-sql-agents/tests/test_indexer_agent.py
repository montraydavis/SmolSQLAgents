"""Tests for the SQL Indexer Agent and related components."""

import sys
import os
import pytest
from unittest.mock import Mock, patch

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.indexer import SQLIndexerAgent
from src.vector.store import SQLVectorStore
from src.vector.embeddings import OpenAIEmbeddingsClient

@pytest.fixture
def mock_embedding():
    """Mock embedding vector."""
    return [0.1] * 3072  # OpenAI embeddings are 3072-dimensional

@pytest.fixture
def mock_embeddings_client():
    """Create a mock OpenAI embeddings client."""
    client = Mock(spec=OpenAIEmbeddingsClient)
    client.generate_embedding.return_value = [0.1] * 3072
    client.generate_embeddings_batch.return_value = [[0.1] * 3072]
    return client

@pytest.fixture
def mock_vector_index():
    """Create a mock vector index."""
    index = Mock()
    index.docs = []
    
    def mock_add(id, vector, metadata):
        index.docs.append({"id": id, "metadata": metadata})
    index.add = Mock(side_effect=mock_add)
    
    def mock_delete(ids):
        if not any(doc["id"] in ids for doc in index.docs):
            raise ValueError("Document not found")
        index.docs = [doc for doc in index.docs if doc["id"] not in ids]
        return True
    index.delete = Mock(side_effect=mock_delete)
    
    def mock_save():
        return True
    index.save = Mock(side_effect=mock_save)
    
    def mock_search(vector, k=5):
        if not index.docs:
            return []
        return [
            {
                "id": doc["id"],
                "metadata": doc["metadata"],
                "score": 0.95
            }
            for doc in index.docs[:k]
        ]
    index.search = Mock(side_effect=mock_search)
    return index

@pytest.fixture
def mock_vector_index_factory(mock_vector_index):
    """Create a mock vector index factory."""
    def factory(path):
        return mock_vector_index
    return factory

@pytest.fixture
def mock_vector_store(mock_embeddings_client, mock_vector_index_factory, tmp_path):
    """Create a mock vector store with test indexes."""
    store = SQLVectorStore(
        base_path=str(tmp_path),
        vector_index_factory=mock_vector_index_factory
    )
    store.embeddings_client = mock_embeddings_client
    store.create_table_index()
    store.create_relationship_index()
    return store

@pytest.fixture
def indexer_agent(mock_vector_store):
    """Create an indexer agent with mocked dependencies."""
    return SQLIndexerAgent(mock_vector_store)

def test_vector_store_init_failure(mock_embeddings_client):
    """Test handling of vector store initialization failure."""
    failing_store = Mock(spec=SQLVectorStore)
    failing_store.embeddings_client = mock_embeddings_client
    failing_store.create_table_index.side_effect = Exception("Failed to create index")
    
    with pytest.raises(Exception) as exc_info:
        SQLIndexerAgent(failing_store)
    assert "Failed to create index" in str(exc_info.value)

def test_index_table_documentation(indexer_agent):
    """Test indexing a single table document."""
    table_data = {
        "name": "users",
        "columns": ["id", "username", "email"],
        "description": "User account information"
    }
    
    result = indexer_agent.index_table_documentation(table_data)
    assert result == True

def test_index_table_documentation_invalid_data(indexer_agent):
    """Test indexing with invalid table data."""
    invalid_table_data = {
        "description": "Missing required fields"
    }
    
    result = indexer_agent.index_table_documentation(invalid_table_data)
    assert result == False

def test_index_relationship_documentation(indexer_agent):
    """Test indexing a single relationship document."""
    relationship_data = {
        "name": "user_orders",
        "type": "one_to_many",
        "tables": ["users", "orders"],
        "description": "User's order history"
    }
    
    result = indexer_agent.index_relationship_documentation(relationship_data)
    assert result == True

def test_search_documentation_all(indexer_agent, mock_embedding):
    """Test searching across all documentation types."""
    # First add some test data
    table_data = {
        "name": "products",
        "columns": ["id", "name", "price"],
        "description": "Product catalog"
    }
    relationship_data = {
        "name": "product_categories",
        "type": "many_to_many",
        "tables": ["products", "categories"],
        "description": "Product categorization"
    }
    
    indexer_agent.index_table_documentation(table_data)
    indexer_agent.index_relationship_documentation(relationship_data)
    
    results = indexer_agent.search_documentation("product")
    assert "tables" in results
    assert "relationships" in results
    assert "total_results" in results
    assert results["total_results"] > 0

def test_batch_index_tables(indexer_agent):
    """Test batch indexing of multiple tables."""
    tables_data = [
        {
            "name": "customers",
            "columns": ["id", "name", "email"],
            "description": "Customer information"
        },
        {
            "name": "orders",
            "columns": ["id", "customer_id", "total"],
            "description": "Order details"
        }
    ]
    
    results = indexer_agent.batch_index_tables(tables_data)
    assert len(results) == 2
    assert all(results.values())

def test_update_table_index(indexer_agent):
    """Test updating an existing table document."""
    original_data = {
        "name": "products",
        "columns": ["id", "name"],
        "description": "Basic product info"
    }
    updated_data = {
        "name": "products",
        "columns": ["id", "name", "price"],
        "description": "Enhanced product info"
    }
    
    # First add the original
    indexer_agent.index_table_documentation(original_data)
    
    # Then update it
    result = indexer_agent.update_table_index("products", updated_data)
    assert result == True

def test_remove_from_index(indexer_agent):
    """Test removing a document from the index."""
    table_data = {
        "name": "temp_table",
        "columns": ["id"],
        "description": "Temporary table"
    }
    
    # First add the table
    indexer_agent.index_table_documentation(table_data)
    
    # Then remove it
    result = indexer_agent.remove_from_index("temp_table", "table")
    assert result == True

def test_search_with_empty_indexes(indexer_agent):
    """Test search behavior with empty indexes."""
    results = indexer_agent.search_documentation("test query")
    assert results["total_results"] == 0
    assert len(results["tables"]) == 0
    assert len(results["relationships"]) == 0

def test_search_specific_type(indexer_agent):
    """Test searching only tables or only relationships."""
    table_data = {
        "name": "inventory",
        "columns": ["id", "quantity"],
        "description": "Stock levels"
    }
    
    indexer_agent.index_table_documentation(table_data)
    
    # Search only tables
    table_results = indexer_agent.search_documentation("inventory", doc_type="table")
    assert "relationships" in table_results
    assert len(table_results["relationships"]) == 0
    assert len(table_results["tables"]) > 0

def test_batch_index_relationships(indexer_agent):
    """Test batch indexing of multiple relationships."""
    relationships_data = [
        {
            "name": "user_addresses",
            "type": "one_to_many",
            "tables": ["users", "addresses"],
            "description": "User's addresses"
        },
        {
            "name": "order_items",
            "type": "one_to_many",
            "tables": ["orders", "items"],
            "description": "Items in an order"
        }
    ]
    
    results = indexer_agent.batch_index_relationships(relationships_data)
    assert len(results) == 2
    assert all(results.values())

def test_invalid_search_type(indexer_agent):
    """Test search with invalid doc_type."""
    results = indexer_agent.search_documentation("test", doc_type="invalid_type")
    assert results["total_results"] == 0
    assert "error" in results

def test_update_nonexistent_table(indexer_agent):
    """Test updating a table that doesn't exist."""
    updated_data = {
        "name": "nonexistent",
        "columns": ["id"],
        "description": "This table doesn't exist"
    }
    result = indexer_agent.update_table_index("nonexistent", updated_data)
    assert result == False

def test_remove_nonexistent_document(indexer_agent):
    """Test removing a document that doesn't exist."""
    result = indexer_agent.remove_from_index("nonexistent", "table")
    assert result == False

def test_special_characters_handling(indexer_agent):
    """Test handling of special characters in names."""
    table_data = {
        "name": "user$data#2023",
        "columns": ["id", "data"],
        "description": "Table with special characters in name"
    }
    result = indexer_agent.index_table_documentation(table_data)
    assert result == True
    
    # Try searching for it
    search_results = indexer_agent.search_documentation("user$data")
    assert search_results["total_results"] > 0

if __name__ == "__main__":
    pytest.main([__file__])
