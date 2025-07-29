# Entity Recognition Agent

The Entity Recognition Agent is an intelligent component that determines the most applicable database entities (tables) for a given user query. It leverages semantic search capabilities from the Indexer Agent to provide contextual entity recommendations.

## 🎯 What It Does

The Entity Recognition Agent analyzes user queries and determines which database tables are most relevant based on:

- **Semantic Similarity**: Uses OpenAI embeddings to find tables with similar meaning to the user's query
- **Business Purpose Matching**: Analyzes how well table purposes align with user intent
- **Table Name Relevance**: Evaluates direct mentions or conceptual matches in table names
- **Relevance Scoring**: Provides weighted relevance scores combining multiple factors
- **Entity Recommendations**: Identifies the most applicable entities for the user's query

## 🔄 Query Flow

```markdown
User Query → Entity Recognition Agent → Indexer Agent → Search Results → Entity Analysis → Entity Rankings
```

1. **User Input**: Natural language query (e.g., "customer information")
2. **Semantic Search**: Uses Indexer Agent to search table documentation
3. **Relevance Analysis**: Calculates multi-factor relevance scores
4. **Entity Filtering**: Identifies highly relevant entities (score > 0.5)
5. **Rankings**: Returns ranked list of applicable entities with relevance scores

## 🚀 Usage Examples

### Command Line Interface

```bash
# Comprehensive entity recognition with recommendations
python main.py --recognize-entities "customer data" "I want to analyze user behavior"

# Quick entity lookup with custom threshold
python main.py --quick-lookup "order information" 0.8

# Search for user-related entities
python main.py --recognize-entities "user authentication"
```

### Programmatic Usage

```python
from src.agents.entity_recognition import EntityRecognitionAgent
from src.agents.core import PersistentDocumentationAgent

# Initialize agents
doc_agent = PersistentDocumentationAgent()
entity_agent = EntityRecognitionAgent(doc_agent.indexer_agent)

# Comprehensive entity recognition
results = entity_agent.recognize_entities(
    user_query="customer information",
    user_intent="I want to analyze customer demographics",
    max_entities=5
)

# Quick table lookup
relevant_tables = entity_agent.quick_entity_lookup(
    "user data", 
    threshold=0.7
)

# Get detailed entity information
entity_details = entity_agent.get_entity_details(relevant_tables)
```

## 📊 Response Structure

### Comprehensive Entity Recognition Response

```json
{
  "success": true,
  "applicable_entities": [
    {
      "table_name": "users",
      "business_purpose": "Stores user account information",
      "relevance_score": 0.92,
      "relevance_factors": {
        "semantic_similarity": 0.95,
        "business_purpose_match": 0.85,
        "table_name_relevance": 1.0
      },
      "recommendation": "Highly relevant - strongly recommended for your query"
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "table_name": "users",
      "relevance_score": 0.92,
      "business_purpose": "Stores user account information",
      "recommendation": "Highly relevant - strongly recommended for your query"
    }
  ],
  "analysis": "Found 1 applicable entities for intent: 'customer information'. Top match is 'users' with average relevance score of 0.92.",
  "confidence": 0.92,
  "total_entities_analyzed": 3
}
```

### Quick Lookup Response

```python
["users", "user_profiles", "customer_data"]  # List of relevant table names
```

## 🧠 Relevance Scoring Algorithm

The agent uses a weighted scoring system to determine entity relevance:

```markdown
Overall Relevance = (Semantic Similarity × 0.5) + 
                   (Business Purpose Match × 0.3) + 
                   (Table Name Relevance × 0.2)
```

### Scoring Components

1. **Semantic Similarity (50% weight)**: OpenAI embedding cosine similarity
2. **Business Purpose Match (30% weight)**: Keyword overlap analysis
3. **Table Name Relevance (20% weight)**: Direct and partial name matching

### Relevance Thresholds

- **≥ 0.8**: Highly relevant - strongly recommended
- **≥ 0.6**: Relevant - good match
- **≥ 0.4**: Moderately relevant - may contain useful information
- **≥ 0.2**: Low relevance - tangentially related
- **< 0.2**: Not relevant - unlikely to be useful

## ⚙️ Configuration

### Environment Variables

```env
# Required for entity recognition
OPENAI_API_KEY="your-api-key-here"

# Optional: Customize embedding model
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Optional: Batch processing settings
EMBEDDING_BATCH_SIZE="100"
EMBEDDING_MAX_RETRIES="3"
```

### Initialization Parameters

```python
EntityRecognitionAgent(
    indexer_agent,              # Required: SQLIndexerAgent instance
)

# Method parameters
recognize_entities(
    user_query,                 # Required: Natural language query
    user_intent=None,           # Optional: Specific user intent
    max_entities=5              # Optional: Maximum entities to return
)

quick_entity_lookup(
    user_query,                 # Required: Natural language query
    threshold=0.7               # Optional: Minimum relevance threshold
)
```

## 🎯 Use Cases

### 1. Entity Discovery

Identify which tables contain data relevant to your query:

```bash
python main.py --recognize-entities "sales performance" "I need quarterly revenue data"
```

### 2. Database Exploration

Discover relevant tables when exploring an unfamiliar database:

```bash
python main.py --quick-lookup "inventory management" 0.6
```

### 3. Schema Navigation

Find tables related to specific business domains:

```bash
python main.py --recognize-entities "customer support" "I want to analyze ticket resolution times"
```

### 4. Data Source Identification

Identify the most relevant data sources before further analysis:

```bash
python main.py --recognize-entities "user engagement" "I need to create a dashboard"
```

## 🔍 Integration with Other Agents

The Entity Recognition Agent works seamlessly with other components:

- **Indexer Agent**: Provides semantic search capabilities
- **Documentation Agent**: Uses documented table information
- **Batch Manager**: Supports efficient processing of large databases
- **Vector Store**: Leverages OpenAI embeddings for similarity search

## 🎖️ Advanced Features

### Natural Language Processing

- Handles complex user intents and queries
- Understands synonyms and related concepts
- Supports multi-word entity matching

### Smart Entity Scoring

- Multi-factor relevance analysis
- Context-aware entity recommendations
- Business-purpose alignment assessment

### Confidence Assessment

- Overall analysis confidence scoring
- Individual entity confidence metrics
- Threshold-based filtering for high-quality results

### Error Handling

- Graceful degradation when vector indexing unavailable
- Comprehensive error reporting with actionable feedback
- Fallback mechanisms for edge cases

## 📈 Performance Characteristics

- **Response Time**: Sub-second for quick lookups, 2-5 seconds for comprehensive analysis
- **Accuracy**: High relevance scoring accuracy with multi-factor analysis
- **Scalability**: Handles databases with hundreds of tables efficiently
- **Memory Usage**: Minimal memory footprint with efficient vector operations

## 🚦 Prerequisites

1. **Vector Indexing**: Requires functional vector indexing (ChromaDB + OpenAI embeddings)
2. **Documented Tables**: Tables must be processed by the Documentation Agent
3. **API Access**: Valid OpenAI API key for embeddings generation
4. **Dependencies**: All required packages from requirements.txt

---

The Entity Recognition Agent enhances the SQL Documentation suite by providing intelligent entity discovery and relevance scoring, making database exploration more intuitive and efficient for users who need to identify the most applicable tables for their data needs.
