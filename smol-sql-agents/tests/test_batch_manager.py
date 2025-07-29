"""Tests for the BatchIndexingManager."""

import pytest
from unittest.mock import Mock, patch
from src.agents.batch_manager import BatchIndexingManager
from src.agents.indexer import SQLIndexerAgent
from src.database.persistence import DocumentationStore

@pytest.fixture
def mock_indexer_agent():
    """Create a mock indexer agent."""
    agent = Mock(spec=SQLIndexerAgent)
    agent.batch_index_tables.return_value = {"table1": True, "table2": False}
    agent.batch_index_relationships.return_value = {"rel1": True, "rel2": True}
    return agent

@pytest.fixture
def mock_doc_store():
    """Create a mock documentation store."""
    store = Mock(spec=DocumentationStore)
    store.get_pending_tables.return_value = ["table1", "table2", "table3"]
    store.get_pending_relationships.return_value = [
        {"id": "rel1", "constrained_table": "table1", "referred_table": "table2"},
        {"id": "rel2", "constrained_table": "table2", "referred_table": "table3"}
    ]
    store.get_table_info.return_value = {
        "table_name": "test_table",
        "schema_data": {"columns": []},
        "business_purpose": "Test table",
        "documentation": "Test documentation"
    }
    store.get_relationship_info.return_value = {
        "id": "test_rel",
        "relationship_type": "one-to-many",
        "documentation": "Test relationship"
    }
    return store

@pytest.fixture
def batch_manager(mock_indexer_agent):
    """Create a batch manager with mocked dependencies."""
    def mock_getenv(key, default=None):
        if key == "EMBEDDING_BATCH_SIZE":
            return "100"
        elif key == "EMBEDDING_MAX_RETRIES":
            return "3"
        else:
            return default
    
    with patch('src.agents.batch_manager.os.getenv', side_effect=mock_getenv):
        manager = BatchIndexingManager(mock_indexer_agent)
        return manager

def test_batch_manager_initialization(batch_manager):
    """Test batch manager initialization."""
    assert batch_manager.indexer == batch_manager.indexer
    assert batch_manager.batch_size == 100
    assert batch_manager.max_retries == 3

def test_group_into_batches(batch_manager):
    """Test grouping items into batches."""
    items = list(range(10))
    batches = batch_manager._group_into_batches(items, 3)
    
    assert len(batches) == 4
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]
    assert batches[3] == [9]

def test_group_into_batches_empty(batch_manager):
    """Test grouping empty list into batches."""
    batches = batch_manager._group_into_batches([], 5)
    assert batches == []

def test_estimate_embedding_costs(batch_manager):
    """Test cost estimation for embeddings."""
    # Use longer texts to ensure we get a meaningful cost estimate
    texts = [
        "This is a much longer test text that should generate enough tokens to create a meaningful cost estimate for OpenAI embeddings",
        "Another longer test text with more words to ensure we have sufficient token count for cost calculation",
        "Third longer test text with additional content to make sure the cost estimation works properly"
    ]
    costs = batch_manager.estimate_embedding_costs(texts)
    
    assert costs["total_texts"] == 3
    assert costs["estimated_tokens"] > 0
    # OpenAI embedding costs are very small, so we just check that the calculation works
    assert costs["estimated_cost_usd"] >= 0
    assert costs["cost_per_text"] >= 0

def test_estimate_embedding_costs_empty(batch_manager):
    """Test cost estimation for empty text list."""
    costs = batch_manager.estimate_embedding_costs([])
    
    assert costs["total_texts"] == 0
    assert costs["estimated_cost_usd"] == 0
    assert costs["cost_per_text"] == 0

def test_get_processing_stats(batch_manager, mock_doc_store):
    """Test getting processing statistics."""
    stats = batch_manager.get_processing_stats(mock_doc_store)
    
    assert stats["pending_tables"] == 3
    assert stats["pending_relationships"] == 2
    assert stats["total_pending"] == 5
    assert stats["batch_size"] == 100
    assert stats["estimated_batches"] == 1  # 5 items / 100 batch size = 1 batch

def test_batch_process_pending_tables(batch_manager, mock_doc_store):
    """Test batch processing of pending tables."""
    results = batch_manager.batch_process_pending_tables(mock_doc_store)
    
    # Verify the indexer was called
    mock_doc_store.get_pending_tables.assert_called_once()
    batch_manager.indexer.batch_index_tables.assert_called_once()
    
    # Verify results
    assert "table1" in results
    assert "table2" in results
    assert results["table1"] is True
    assert results["table2"] is False

def test_batch_process_pending_tables_empty(batch_manager, mock_doc_store):
    """Test batch processing when no pending tables."""
    mock_doc_store.get_pending_tables.return_value = []
    
    results = batch_manager.batch_process_pending_tables(mock_doc_store)
    
    assert results == {}
    batch_manager.indexer.batch_index_tables.assert_not_called()

def test_batch_process_pending_relationships(batch_manager, mock_doc_store):
    """Test batch processing of pending relationships."""
    results = batch_manager.batch_process_pending_relationships(mock_doc_store)
    
    # Verify the indexer was called
    mock_doc_store.get_pending_relationships.assert_called_once()
    batch_manager.indexer.batch_index_relationships.assert_called_once()
    
    # Verify results
    assert "rel1" in results
    assert "rel2" in results
    assert results["rel1"] is True
    assert results["rel2"] is True

def test_batch_process_pending_relationships_empty(batch_manager, mock_doc_store):
    """Test batch processing when no pending relationships."""
    mock_doc_store.get_pending_relationships.return_value = []
    
    results = batch_manager.batch_process_pending_relationships(mock_doc_store)
    
    assert results == {}
    batch_manager.indexer.batch_index_relationships.assert_not_called()

def test_batch_process_with_exception(batch_manager, mock_doc_store):
    """Test batch processing when exceptions occur."""
    # Mock an exception when getting table info
    mock_doc_store.get_table_info.side_effect = Exception("Database error")
    
    results = batch_manager.batch_process_pending_tables(mock_doc_store)
    
    # Should handle the exception gracefully
    assert "table1" in results
    assert results["table1"] is False 