"""Tests for the Entity Recognition Agent."""

import pytest
from unittest.mock import Mock, patch
from src.agents.entity_recognition import EntityRecognitionAgent
from src.agents.indexer import SQLIndexerAgent

@pytest.fixture
def mock_indexer_agent():
    """Create a mock indexer agent."""
    agent = Mock(spec=SQLIndexerAgent)
    
    # Mock search results for different scenarios
    def mock_search_documentation(query, doc_type):
        if "user" in query.lower():
            return {
                "tables": [
                    {
                        "id": "users",
                        "content": {
                            "name": "users",
                            "business_purpose": "Stores user account information and profile data",
                            "schema_data": {"columns": ["id", "username", "email", "created_at"]},
                            "type": "table"
                        },
                        "score": 0.92
                    },
                    {
                        "id": "user_profiles",
                        "content": {
                            "name": "user_profiles",
                            "business_purpose": "Extended user profile information",
                            "schema_data": {"columns": ["user_id", "first_name", "last_name", "phone"]},
                            "type": "table"
                        },
                        "score": 0.85
                    }
                ],
                "relationships": [],
                "total_results": 2
            }
        elif "order" in query.lower():
            return {
                "tables": [
                    {
                        "id": "orders",
                        "content": {
                            "name": "orders",
                            "business_purpose": "Customer order information and transaction data",
                            "schema_data": {"columns": ["id", "user_id", "total_amount", "order_date"]},
                            "type": "table"
                        },
                        "score": 0.88
                    }
                ],
                "relationships": [],
                "total_results": 1
            }
        else:
            return {
                "tables": [],
                "relationships": [],
                "total_results": 0
            }
    
    agent.search_documentation.side_effect = mock_search_documentation
    return agent

@pytest.fixture
def entity_agent(mock_indexer_agent):
    """Create an entity recognition agent with mocked dependencies."""
    def mock_getenv(key, default=None):
        if key == "OPENAI_API_KEY":
            return "dummy-api-key"
        else:
            return default
    
    with patch('src.agents.entity_recognition.OpenAIModel') as mock_model, \
         patch('src.agents.entity_recognition.CodeAgent') as mock_code_agent, \
         patch('src.agents.entity_recognition.os.getenv', side_effect=mock_getenv):
        agent = EntityRecognitionAgent(mock_indexer_agent)
        return agent

def test_entity_agent_initialization(mock_indexer_agent):
    """Test successful initialization of entity recognition agent."""
    def mock_getenv(key, default=None):
        if key == "OPENAI_API_KEY":
            return "dummy-api-key"
        else:
            return default
    
    with patch('src.agents.entity_recognition.OpenAIModel') as mock_model, \
         patch('src.agents.entity_recognition.CodeAgent') as mock_code_agent, \
         patch('src.agents.entity_recognition.os.getenv', side_effect=mock_getenv):
        agent = EntityRecognitionAgent(mock_indexer_agent)
        assert agent.indexer_agent == mock_indexer_agent
        assert agent.llm_model is not None
        assert agent.agent is not None

def test_entity_agent_initialization_missing_api_key(mock_indexer_agent):
    """Test agent initialization with missing API key."""
    with patch('src.agents.entity_recognition.os.getenv', return_value=None), \
         pytest.raises(ValueError) as exc_info:
        EntityRecognitionAgent(mock_indexer_agent)
    assert "OPENAI_API_KEY environment variable is not set" in str(exc_info.value)

def test_quick_entity_lookup_success(entity_agent, mock_indexer_agent):
    """Test successful quick entity lookup."""
    result = entity_agent.quick_entity_lookup("user data", threshold=0.8)
    
    # Should return tables that meet the threshold
    assert isinstance(result, list)
    assert "users" in result  # Score 0.92 > 0.8
    assert "user_profiles" in result  # Score 0.85 > 0.8
    
    mock_indexer_agent.search_documentation.assert_called_once_with(
        query="user data",
        doc_type="table"
    )

def test_quick_entity_lookup_high_threshold(entity_agent, mock_indexer_agent):
    """Test quick entity lookup with high threshold."""
    result = entity_agent.quick_entity_lookup("user data", threshold=0.95)
    
    # Only very high scoring results should be returned
    assert isinstance(result, list)
    # No tables should meet 0.95 threshold based on mock data (highest is 0.92)
    assert len(result) == 0 or "users" not in result

def test_quick_entity_lookup_no_results(entity_agent, mock_indexer_agent):
    """Test quick entity lookup when no entities are found."""
    result = entity_agent.quick_entity_lookup("nonexistent data", threshold=0.7)
    
    assert isinstance(result, list)
    assert len(result) == 0

def test_quick_entity_lookup_with_exception(entity_agent, mock_indexer_agent):
    """Test quick entity lookup when an exception occurs."""
    mock_indexer_agent.search_documentation.side_effect = Exception("Search failed")
    
    result = entity_agent.quick_entity_lookup("user data")
    
    assert isinstance(result, list)
    assert len(result) == 0

def test_get_entity_details_success(entity_agent, mock_indexer_agent):
    """Test successful retrieval of entity details."""
    # Mock specific table search
    def mock_specific_search(query, doc_type):
        if query.lower() == "users":
            return {
                "tables": [
                    {
                        "id": "users",
                        "content": {
                            "name": "users",
                            "business_purpose": "Stores user account information",
                            "schema_data": {"columns": ["id", "username", "email"]},
                            "type": "table"
                        },
                        "score": 1.0  # Exact match
                    }
                ]
            }
        return {"tables": []}
    
    mock_indexer_agent.search_documentation.side_effect = mock_specific_search
    
    result = entity_agent.get_entity_details(["users"])
    
    assert isinstance(result, dict)
    assert "users" in result
    assert result["users"]["name"] == "users"
    assert result["users"]["business_purpose"] == "Stores user account information"

def test_get_entity_details_no_match(entity_agent, mock_indexer_agent):
    """Test get entity details when no matching entities found."""
    mock_indexer_agent.search_documentation.return_value = {"tables": []}
    
    result = entity_agent.get_entity_details(["nonexistent_table"])
    
    assert isinstance(result, dict)
    assert len(result) == 0

def test_get_entity_details_with_exception(entity_agent, mock_indexer_agent):
    """Test get entity details when an exception occurs."""
    mock_indexer_agent.search_documentation.side_effect = Exception("Search failed")
    
    result = entity_agent.get_entity_details(["users"])
    
    assert isinstance(result, dict)
    assert len(result) == 0

def test_recognize_entities_empty_query(entity_agent):
    """Test entity recognition with empty query."""
    result = entity_agent.recognize_entities("")
    
    assert result["success"] is False
    assert "Query cannot be empty" in result["error"]
    assert result["applicable_entities"] == []
    assert result["recommendations"] == []

def test_recognize_entities_whitespace_query(entity_agent):
    """Test entity recognition with whitespace-only query."""
    result = entity_agent.recognize_entities("   ")
    
    assert result["success"] is False
    assert "Query cannot be empty" in result["error"]

def test_recognize_entities_success(entity_agent):
    """Test successful entity recognition."""
    # Mock the agent's run method to return a successful response
    mock_response = {
        "success": True,
        "applicable_entities": [
            {
                "table_name": "users",
                "business_purpose": "Stores user account information",
                "relevance_score": 0.92,
                "recommendation": "Highly relevant - strongly recommended for your query"
            }
        ],
        "recommendations": [
            {
                "priority": 1,
                "table_name": "users",
                "suggested_actions": ["Query users to retrieve relevant data"]
            }
        ],
        "confidence": 0.92
    }
    
    entity_agent.agent.run.return_value = mock_response
    
    result = entity_agent.recognize_entities("user information")
    
    assert result["success"] is True
    assert len(result["applicable_entities"]) > 0
    assert result["applicable_entities"][0]["table_name"] == "users"
    assert result["confidence"] == 0.92

def test_recognize_entities_json_response(entity_agent):
    """Test entity recognition with JSON string response."""
    import json
    
    mock_response = {
        "success": True,
        "applicable_entities": [
            {
                "table_name": "orders",
                "relevance_score": 0.88
            }
        ],
        "recommendations": []
    }
    
    entity_agent.agent.run.return_value = json.dumps(mock_response)
    
    result = entity_agent.recognize_entities("order data")
    
    assert result["success"] is True
    assert len(result["applicable_entities"]) > 0

def test_recognize_entities_invalid_json(entity_agent):
    """Test entity recognition with invalid JSON response."""
    entity_agent.agent.run.return_value = "Invalid JSON response"
    
    result = entity_agent.recognize_entities("user data")
    
    assert result["success"] is False
    assert "Invalid JSON response from agent" in result["error"]
    assert result["applicable_entities"] == []

def test_recognize_entities_unexpected_response(entity_agent):
    """Test entity recognition with unexpected response type."""
    entity_agent.agent.run.return_value = 12345  # Unexpected integer
    
    result = entity_agent.recognize_entities("user data")
    
    assert result["success"] is False
    assert "Unexpected response type from agent" in result["error"]

def test_recognize_entities_with_exception(entity_agent):
    """Test entity recognition when an exception occurs."""
    entity_agent.agent.run.side_effect = Exception("Agent execution failed")
    
    result = entity_agent.recognize_entities("user data")
    
    assert result["success"] is False
    assert "Agent execution failed" in result["error"]
    assert result["applicable_entities"] == []

def test_recognize_entities_with_intent(entity_agent):
    """Test entity recognition with specific user intent."""
    mock_response = {
        "success": True,
        "applicable_entities": [
            {
                "table_name": "users",
                "relevance_score": 0.95
            }
        ],
        "recommendations": []
    }
    
    entity_agent.agent.run.return_value = mock_response
    
    result = entity_agent.recognize_entities(
        user_query="show me data",
        user_intent="I want to analyze user demographics"
    )
    
    assert result["success"] is True
    entity_agent.agent.run.assert_called_once()
    
    # Verify that the prompt included both query and intent
    call_args = entity_agent.agent.run.call_args[0][0]
    assert "show me data" in call_args
    assert "I want to analyze user demographics" in call_args

def test_private_methods(entity_agent):
    """Test private helper methods."""
    # Test _calculate_purpose_match
    match_score = entity_agent._calculate_purpose_match(
        "Stores user account information",
        "user account data"
    )
    assert match_score > 0.0
    assert match_score <= 1.0
    
    # Test _calculate_name_relevance
    name_relevance = entity_agent._calculate_name_relevance("users", "user data")
    assert name_relevance > 0.0
    
    # Test _get_relevance_recommendation
    high_rec = entity_agent._get_relevance_recommendation(0.9)
    assert "Highly relevant" in high_rec
    
    low_rec = entity_agent._get_relevance_recommendation(0.1)
    assert "Not relevant" in low_rec
    
    # Test _generate_analysis_summary
    entities = [{"table_name": "users", "relevance_score": 0.9}]
    summary = entity_agent._generate_analysis_summary(entities, "user data")
    assert "Found 1 applicable entities" in summary
    
    empty_summary = entity_agent._generate_analysis_summary([], "nonexistent")
    assert "No highly relevant entities found" in empty_summary

if __name__ == "__main__":
    pytest.main([__file__])