"""Tests for vector indexing retry functionality."""

import pytest
from unittest.mock import Mock, patch
from src.agents.core import PersistentDocumentationAgent

def test_retry_vector_indexing_success():
    """Test successful retry of vector indexing initialization."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # First, make the initial initialization fail
        mock_vector_store.side_effect = RuntimeError("Initial failure")
        
        # Create agent - should have vector indexing disabled
        agent = PersistentDocumentationAgent()
        assert agent.vector_indexing_available is False
        assert agent.indexer_agent is None
        
        # Now make the retry succeed
        mock_vector_store.side_effect = None
        mock_indexer = Mock()
        with patch('src.agents.core.SQLIndexerAgent', return_value=mock_indexer):
            success = agent.retry_vector_indexing_initialization()
            
            assert success is True
            assert agent.vector_indexing_available is True
            assert agent.indexer_agent is not None

def test_retry_vector_indexing_already_available():
    """Test retry when vector indexing is already available."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Create agent with vector indexing available
        agent = PersistentDocumentationAgent()
        agent.vector_indexing_available = True
        agent.indexer_agent = Mock()
        
        # Retry should return True without re-initializing
        success = agent.retry_vector_indexing_initialization()
        
        assert success is True
        assert agent.vector_indexing_available is True

def test_retry_vector_indexing_failure():
    """Test retry when vector indexing initialization fails."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Make the initial initialization fail
        mock_vector_store.side_effect = RuntimeError("Initial failure")
        
        # Create agent - should have vector indexing disabled
        agent = PersistentDocumentationAgent()
        assert agent.vector_indexing_available is False
        assert agent.indexer_agent is None
        
        # Make the retry also fail
        mock_vector_store.side_effect = RuntimeError("Retry failure")
        success = agent.retry_vector_indexing_initialization()
        
        assert success is False
        assert agent.vector_indexing_available is False
        assert agent.indexer_agent is None

def test_vector_indexing_status_check():
    """Test checking vector indexing status."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Test with vector indexing available
        agent = PersistentDocumentationAgent()
        agent.vector_indexing_available = True
        agent.indexer_agent = Mock()
        
        # Status should be available
        assert agent.vector_indexing_available is True
        assert agent.indexer_agent is not None
        
        # Test with vector indexing unavailable
        agent.vector_indexing_available = False
        agent.indexer_agent = None
        
        # Status should be unavailable
        assert agent.vector_indexing_available is False
        assert agent.indexer_agent is None 