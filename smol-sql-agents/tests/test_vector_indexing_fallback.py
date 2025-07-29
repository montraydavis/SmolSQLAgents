"""Tests for vector indexing fallback behavior."""

import pytest
from unittest.mock import Mock, patch
from src.agents.core import PersistentDocumentationAgent

def test_agent_initialization_with_vector_store_failure():
    """Test that agent initializes gracefully when vector store fails."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Make the vector store initialization fail
        mock_vector_store.side_effect = RuntimeError("vectordb compatibility issue")
        
        # Agent should still initialize successfully
        agent = PersistentDocumentationAgent()
        
        # Check that vector indexing is marked as unavailable
        assert agent.vector_indexing_available is False
        assert agent.indexer_agent is None
        
        # Check that other components are still available
        assert agent.llm_model is not None
        assert agent.db_inspector is not None
        assert agent.store is not None

def test_table_processing_without_vector_indexing():
    """Test table processing when vector indexing is not available."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Make the vector store initialization fail
        mock_vector_store.side_effect = RuntimeError("vectordb compatibility issue")
        
        agent = PersistentDocumentationAgent()
        
        # Mock the agent's run method to return valid JSON
        mock_response = {
            "business_purpose": "Test table for user data",
            "schema_data": {
                "table_name": "test_table",
                "columns": [{"name": "id", "type": "integer"}]
            }
        }
        agent.agent.run.return_value = '{"business_purpose": "Test table for user data", "schema_data": {"table_name": "test_table", "columns": [{"name": "id", "type": "integer"}]}}'
        
        # Mock the store methods
        agent.store.save_table_documentation = Mock()
        agent.store.get_table_schema = Mock(return_value={"name": "test_table", "columns": []})
        
        # Process table - should work without vector indexing
        agent.process_table_documentation("test_table")
        
        # Verify that documentation was saved
        agent.store.save_table_documentation.assert_called_once()
        
        # Verify that vector indexing was not attempted
        assert agent.vector_indexing_available is False

def test_relationship_processing_without_vector_indexing():
    """Test relationship processing when vector indexing is not available."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Make the vector store initialization fail
        mock_vector_store.side_effect = RuntimeError("vectordb compatibility issue")
        
        agent = PersistentDocumentationAgent()
        
        # Mock the agent's run method to return valid JSON
        agent.agent.run.return_value = '{"relationship_type": "one-to-many", "documentation": "Test relationship"}'
        
        # Mock the store methods
        agent.store.save_relationship_documentation = Mock()
        
        # Test relationship data
        relationship = {
            "id": "test_rel",
            "constrained_table": "table1",
            "constrained_columns": ["id"],
            "referred_table": "table2",
            "referred_columns": ["id"]
        }
        
        # Process relationship - should work without vector indexing
        agent.process_relationship_documentation(relationship)
        
        # Verify that documentation was saved
        agent.store.save_relationship_documentation.assert_called_once()
        
        # Verify that vector indexing was not attempted
        assert agent.vector_indexing_available is False 