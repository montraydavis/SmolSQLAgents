"""Tests for indexing already processed documents."""

import pytest
from unittest.mock import Mock, patch
from src.agents.core import PersistentDocumentationAgent

def test_index_processed_documents_with_vector_indexing():
    """Test indexing processed documents when vector indexing is available."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Mock the documentation store methods
        mock_doc_store.return_value.get_all_tables.return_value = ["table1", "table2"]
        mock_doc_store.return_value.get_all_relationships.return_value = [
            {"id": "rel1", "constrained_table": "table1", "referred_table": "table2"}
        ]
        mock_doc_store.return_value.get_table_info.return_value = {
            "table_name": "table1",
            "business_purpose": "Test table",
            "schema_data": {"columns": []},
            "documentation": "Test documentation"
        }
        mock_doc_store.return_value.get_relationship_info.return_value = {
            "id": "rel1",
            "relationship_type": "one-to-many",
            "documentation": "Test relationship"
        }
        
        # Mock the indexer agent
        mock_indexer = Mock()
        mock_indexer.index_table_documentation.return_value = True
        mock_indexer.index_relationship_documentation.return_value = True
        
        # Create agent with mocked indexer
        agent = PersistentDocumentationAgent()
        agent.indexer_agent = mock_indexer
        agent.vector_indexing_available = True
        
        # Call the method
        agent.index_processed_documents()
        
        # Verify that the indexer was called for both tables and relationships
        assert mock_indexer.index_table_documentation.call_count == 2
        assert mock_indexer.index_relationship_documentation.call_count == 1

def test_index_processed_documents_without_vector_indexing():
    """Test indexing processed documents when vector indexing is not available."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Create agent without vector indexing
        agent = PersistentDocumentationAgent()
        agent.indexer_agent = None
        agent.vector_indexing_available = False
        
        # Call the method - should not raise an exception
        agent.index_processed_documents()
        
        # Verify that no indexing was attempted
        # (The method should just log a warning and return)

def test_index_processed_documents_with_indexing_failures():
    """Test indexing processed documents when some indexing operations fail."""
    with patch('src.agents.core.SQLVectorStore') as mock_vector_store, \
         patch('src.agents.core.DatabaseInspector') as mock_db_inspector, \
         patch('src.agents.core.OpenAIModel') as mock_llm_model, \
         patch('src.agents.core.DocumentationStore') as mock_doc_store, \
         patch('src.agents.core.CodeAgent') as mock_code_agent, \
         patch('src.agents.core.os.getenv', return_value='dummy-api-key'):
        
        # Mock the documentation store methods
        mock_doc_store.return_value.get_all_tables.return_value = ["table1", "table2"]
        mock_doc_store.return_value.get_all_relationships.return_value = [
            {"id": "rel1", "constrained_table": "table1", "referred_table": "table2"}
        ]
        mock_doc_store.return_value.get_table_info.return_value = {
            "table_name": "table1",
            "business_purpose": "Test table",
            "schema_data": {"columns": []},
            "documentation": "Test documentation"
        }
        mock_doc_store.return_value.get_relationship_info.return_value = {
            "id": "rel1",
            "relationship_type": "one-to-many",
            "documentation": "Test relationship"
        }
        
        # Mock the indexer agent with some failures
        mock_indexer = Mock()
        mock_indexer.index_table_documentation.side_effect = [True, False]  # Second table fails
        mock_indexer.index_relationship_documentation.return_value = True
        
        # Create agent with mocked indexer
        agent = PersistentDocumentationAgent()
        agent.indexer_agent = mock_indexer
        agent.vector_indexing_available = True
        
        # Call the method - should handle failures gracefully
        agent.index_processed_documents()
        
        # Verify that the indexer was called for both tables and relationships
        assert mock_indexer.index_table_documentation.call_count == 2
        assert mock_indexer.index_relationship_documentation.call_count == 1 