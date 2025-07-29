"""Tests for the PersistentDocumentationAgent with vector indexing."""

import json
import pytest
from unittest.mock import Mock, patch, ANY

from src.agents.core import PersistentDocumentationAgent
from src.database.inspector import DatabaseInspector
from src.database.persistence import DocumentationStore
from src.agents.indexer import SQLIndexerAgent
from src.vector.store import SQLVectorStore

@pytest.fixture
def mock_llm_model():
    """Create a mock LLM model."""
    model = Mock()
    return model

@pytest.fixture
def mock_db_inspector():
    """Create a mock database inspector."""
    inspector = Mock(spec=DatabaseInspector)
    inspector.get_all_table_names.return_value = ["users", "orders"]
    inspector.get_table_schema.return_value = {
        "name": "users",
        "columns": [
            {"name": "id", "type": "integer", "primary_key": True},
            {"name": "username", "type": "varchar"},
            {"name": "email", "type": "varchar"}
        ]
    }
    inspector.get_all_foreign_key_relationships.return_value = [
        {
            "id": "users_orders_fk",
            "constrained_table": "orders",
            "constrained_columns": ["user_id"],
            "referred_table": "users",
            "referred_columns": ["id"]
        }
    ]
    return inspector

@pytest.fixture
def mock_doc_store():
    """Create a mock documentation store."""
    store = Mock(spec=DocumentationStore)
    return store

@pytest.fixture
def mock_indexer_agent():
    """Create a mock indexer agent."""
    agent = Mock(spec=SQLIndexerAgent)
    agent.index_table_documentation.return_value = True
    agent.index_relationship_documentation.return_value = True
    return agent

@pytest.fixture
def mock_code_agent():
    """Create a mock code agent."""
    agent = Mock()
    return agent

@pytest.fixture
def doc_agent(mock_llm_model, mock_db_inspector, mock_doc_store, mock_code_agent):
    """Create a documentation agent with mocked dependencies."""
    def mock_getenv(key, default=None):
        if key == "OPENAI_API_KEY":
            return "dummy-api-key"
        elif key == "OPENAI_EMBEDDING_MODEL":
            return "text-embedding-3-small"
        elif key == "EMBEDDING_BATCH_SIZE":
            return "100"
        else:
            return default
    
    # Mock the vector store and indexer agent
    mock_vector_store = Mock(spec=SQLVectorStore)
    mock_indexer_agent = Mock(spec=SQLIndexerAgent)
    
    with patch('src.agents.core.OpenAIModel', return_value=mock_llm_model), \
         patch('src.agents.core.DatabaseInspector', return_value=mock_db_inspector), \
         patch('src.agents.core.DocumentationStore', return_value=mock_doc_store), \
         patch('src.agents.core.CodeAgent', return_value=mock_code_agent), \
         patch('src.agents.core.SQLVectorStore', return_value=mock_vector_store), \
         patch('src.agents.core.SQLIndexerAgent', return_value=mock_indexer_agent), \
         patch('src.agents.core.os.getenv', side_effect=mock_getenv), \
         patch('src.vector.embeddings.os.getenv', side_effect=mock_getenv), \
         patch('src.vector.store.os.getenv', side_effect=mock_getenv):
        agent = PersistentDocumentationAgent()
        return agent

@pytest.fixture
def doc_agent_with_indexing(mock_llm_model, mock_db_inspector, mock_doc_store, mock_code_agent, mock_indexer_agent):
    """Create a documentation agent with vector indexing capabilities."""
    def mock_getenv(key, default=None):
        if key == "OPENAI_API_KEY":
            return "dummy-api-key"
        elif key == "OPENAI_EMBEDDING_MODEL":
            return "text-embedding-3-small"
        elif key == "EMBEDDING_BATCH_SIZE":
            return "100"
        else:
            return default
    
    with patch('agent.agent_core.OpenAIModel', return_value=mock_llm_model), \
         patch('agent.agent_core.DatabaseInspector', return_value=mock_db_inspector), \
         patch('agent.agent_core.DocumentationStore', return_value=mock_doc_store), \
         patch('agent.agent_core.CodeAgent', return_value=mock_code_agent), \
         patch('agent.agent_core.SQLIndexerAgent', return_value=mock_indexer_agent), \
         patch('agent.agent_core.SQLVectorStore'), \
         patch('agent.agent_core.os.getenv', side_effect=mock_getenv), \
         patch('agent.embeddings_client.os.getenv', side_effect=mock_getenv), \
         patch('agent.vector_store.os.getenv', side_effect=mock_getenv):
        agent = PersistentDocumentationAgent()
        return agent

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = Mock(spec=SQLVectorStore)
    return store

@pytest.fixture
def doc_agent_with_vector(doc_agent, mock_indexer_agent, mock_vector_store):
    """Create a documentation agent with vector indexing capabilities."""
    doc_agent.indexing_agent = mock_indexer_agent
    doc_agent.vector_store = mock_vector_store
    return doc_agent

# ============================================================================
# Basic Agent Functionality Tests
# ============================================================================

def test_agent_initialization_success(doc_agent, mock_db_inspector, mock_doc_store):
    """Test successful agent initialization."""
    assert doc_agent.db_inspector == mock_db_inspector
    assert doc_agent.store == mock_doc_store

def test_agent_initialization_missing_api_key():
    """Test agent initialization with missing API key."""
    with patch('agent.agent_core.os.getenv', return_value=None), \
         pytest.raises(ValueError) as exc_info:
        PersistentDocumentationAgent()
    assert "OPENAI_API_KEY environment variable is not set" in str(exc_info.value)

# ============================================================================
# Table Documentation Tests
# ============================================================================

def test_process_table_documentation_success(doc_agent, mock_code_agent):
    """Test successful processing of table documentation."""
    # Mock LLM response
    mock_response = {
        "business_purpose": "Stores user account information",
        "schema_data": {
            "table_name": "users",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "username", "type": "varchar"}
            ]
        }
    }
    mock_code_agent.run.return_value = json.dumps(mock_response)
    
    # Process table
    doc_agent.process_table_documentation("users")
    
    # Verify interactions
    mock_code_agent.run.assert_called_once()
    doc_agent.store.save_table_documentation.assert_called_once_with(
        "users",
        mock_response["schema_data"],
        mock_response["business_purpose"],
        ANY  # We don't need to verify the exact markdown format
    )

def test_process_table_documentation_invalid_json(doc_agent, mock_code_agent):
    """Test handling of invalid JSON response for table documentation."""
    mock_code_agent.run.return_value = "Invalid JSON"
    
    with pytest.raises(json.JSONDecodeError):
        doc_agent.process_table_documentation("users")

def test_process_table_documentation_missing_fields(doc_agent, mock_code_agent):
    """Test handling of missing fields in table documentation response."""
    mock_response = {
        "business_purpose": "Stores user account information"
        # Missing schema_data
    }
    mock_code_agent.run.return_value = json.dumps(mock_response)
    
    with pytest.raises(ValueError) as exc_info:
        doc_agent.process_table_documentation("users")
    assert "Missing required fields" in str(exc_info.value)

# ============================================================================
# Relationship Documentation Tests
# ============================================================================

def test_process_relationship_documentation_success(doc_agent, mock_code_agent):
    """Test successful processing of relationship documentation."""
    relationship = {
        "id": "users_orders_fk",
        "constrained_table": "orders",
        "constrained_columns": ["user_id"],
        "referred_table": "users",
        "referred_columns": ["id"]
    }
    
    mock_response = {
        "relationship_type": "one-to-many",
        "documentation": "Each user can have multiple orders"
    }
    mock_code_agent.run.return_value = json.dumps(mock_response)
    
    doc_agent.process_relationship_documentation(relationship)
    
    mock_code_agent.run.assert_called_once()
    doc_agent.store.save_relationship_documentation.assert_called_once_with(
        "users_orders_fk",
        mock_response["relationship_type"],
        mock_response["documentation"]
    )

def test_process_relationship_documentation_invalid_json(doc_agent, mock_code_agent):
    """Test handling of invalid JSON response for relationship documentation."""
    relationship = {
        "id": "users_orders_fk",
        "constrained_table": "orders",
        "constrained_columns": ["user_id"],
        "referred_table": "users",
        "referred_columns": ["id"]
    }
    mock_code_agent.run.return_value = "Invalid JSON"
    
    with pytest.raises(json.JSONDecodeError):
        doc_agent.process_relationship_documentation(relationship)

def test_process_relationship_documentation_missing_fields(doc_agent, mock_code_agent):
    """Test handling of missing fields in relationship documentation response."""
    relationship = {
        "id": "users_orders_fk",
        "constrained_table": "orders",
        "constrained_columns": ["user_id"],
        "referred_table": "users",
        "referred_columns": ["id"]
    }
    mock_response = {
        "relationship_type": "one-to-many"
        # Missing documentation
    }
    mock_code_agent.run.return_value = json.dumps(mock_response)
    
    with pytest.raises(ValueError) as exc_info:
        doc_agent.process_relationship_documentation(relationship)
    assert "Missing required fields" in str(exc_info.value)

def test_process_relationship_documentation_agent_error(doc_agent, mock_code_agent):
    """Test handling of agent errors during relationship documentation."""
    relationship = {
        "id": "users_orders_fk",
        "constrained_table": "orders",
        "constrained_columns": ["user_id"],
        "referred_table": "users",
        "referred_columns": ["id"]
    }
    mock_code_agent.run.side_effect = Exception("Agent error")
    
    with pytest.raises(Exception) as exc_info:
        doc_agent.process_relationship_documentation(relationship)
    assert "Agent error" in str(exc_info.value)

# ============================================================================
# Vector Indexing Tests
# ============================================================================

def test_process_table_documentation_with_indexing(doc_agent_with_indexing, mock_code_agent, mock_indexer_agent):
    """Test table documentation processing with vector indexing."""
    # Mock LLM response
    table_response = {
        "business_purpose": "Stores user account information",
        "schema_data": {
            "table_name": "users",
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "username", "type": "varchar"}
            ]
        }
    }
    mock_code_agent.run.return_value = json.dumps(table_response)
    
    # Process table
    doc_agent_with_indexing.process_table_documentation("users")
    
    # Verify regular documentation was saved
    doc_agent_with_indexing.store.save_table_documentation.assert_called_once_with(
        "users",
        table_response["schema_data"],
        table_response["business_purpose"],
        ANY
    )
    
    # Verify vector indexing was performed
    mock_indexer_agent.index_table_documentation.assert_called_once()
    table_data = mock_indexer_agent.index_table_documentation.call_args[0][0]
    assert table_data["name"] == "users"
    assert table_data["business_purpose"] == table_response["business_purpose"]
    assert table_data["schema"] == table_response["schema_data"]

def test_process_relationship_documentation_with_indexing(doc_agent_with_indexing, mock_code_agent, mock_indexer_agent):
    """Test relationship documentation processing with vector indexing."""
    relationship = {
        "id": "users_orders_fk",
        "constrained_table": "orders",
        "constrained_columns": ["user_id"],
        "referred_table": "users",
        "referred_columns": ["id"]
    }
    
    # Mock LLM response
    rel_response = {
        "relationship_type": "one-to-many",
        "documentation": "Each user can have multiple orders"
    }
    mock_code_agent.run.return_value = json.dumps(rel_response)
    
    # Process relationship
    doc_agent_with_indexing.process_relationship_documentation(relationship)
    
    # Verify regular documentation was saved
    doc_agent_with_indexing.store.save_relationship_documentation.assert_called_once_with(
        "users_orders_fk",
        rel_response["relationship_type"],
        rel_response["documentation"]
    )
    
    # Verify vector indexing was performed
    mock_indexer_agent.index_relationship_documentation.assert_called_once()
    rel_data = mock_indexer_agent.index_relationship_documentation.call_args[0][0]
    assert rel_data["name"] == "users_orders_fk"
    assert rel_data["type"] == rel_response["relationship_type"]
    assert rel_data["documentation"] == rel_response["documentation"]
    assert rel_data["tables"] == ["orders", "users"]

def test_indexing_error_handling(doc_agent_with_indexing, mock_code_agent, mock_indexer_agent):
    """Test handling of indexing errors."""
    # Mock LLM response
    table_response = {
        "business_purpose": "Stores user account information",
        "schema_data": {
            "table_name": "users",
            "columns": [{"name": "id", "type": "integer"}]
        }
    }
    mock_code_agent.run.return_value = json.dumps(table_response)
    
    # Simulate indexing failure
    mock_indexer_agent.index_table_documentation.return_value = False
    
    # Process should complete but log the error
    with pytest.raises(ValueError) as exc_info:
        doc_agent_with_indexing.process_table_documentation("users")
    assert "Failed to index table documentation" in str(exc_info.value)
    
    # Regular documentation should still be saved
    doc_agent_with_indexing.store.save_table_documentation.assert_called_once()

# ============================================================================
# Vector Store Tests
# ============================================================================

# Note: These tests were removed because they test functionality that doesn't exist
# in the current implementation. The agent_core.py doesn't have index_documentation()
# or search_documentation() methods, and the DocumentationStore doesn't have
# get_all_table_documentation() method.
