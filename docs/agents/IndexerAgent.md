# Indexer Agent

The Indexer Agent is an intelligent vector indexing component that manages OpenAI embeddings for SQL documentation. It provides semantic search capabilities and natural language processing for database tables and relationships using ChromaDB as the vector store.

## 🎯 What It Does

The Indexer Agent handles vector indexing and semantic search operations for SQL documentation:

- **Vector Indexing**: Creates and manages OpenAI embeddings for table and relationship documentation
- **Semantic Search**: Enables natural language queries to find relevant database entities
- **Batch Processing**: Efficiently indexes multiple documents using batch operations
- **Index Management**: Provides status monitoring and maintenance operations
- **Natural Language Interface**: Processes indexing instructions in plain English
- **ChromaDB Integration**: Uses ChromaDB for persistent vector storage with similarity search

## 🔄 Indexing Flow

```markdown
Documentation Data → Indexer Agent → OpenAI Embeddings → ChromaDB Storage → Semantic Search Results
```

1. **Input**: Table or relationship documentation with business purpose and schema
2. **Embedding Generation**: Uses OpenAI's text-embedding-3-small model (3072 dimensions)
3. **Vector Storage**: Stores embeddings in ChromaDB collections with metadata
4. **Similarity Search**: Enables cosine similarity search for natural language queries
5. **Results**: Returns ranked search results with relevance scores

## 🚀 Usage Examples

### Command Line Interface

```bash
# Search for tables related to user management
python main.py --search "user authentication" --type table

# Search for relationships involving customer data
python main.py --search "customer relationships" --type relationship

# Get indexing status and statistics
python main.py --index-status

# Batch index all processed documents
python main.py --batch-index
```

### Programmatic Usage

```python
from src.agents.indexer import SQLIndexerAgent
from src.vector.store import SQLVectorStore

# Initialize the indexer agent
vector_store = SQLVectorStore()
indexer_agent = SQLIndexerAgent(vector_store)

# Index table documentation
table_data = {
    "name": "users",
    "business_purpose": "Stores user account information and authentication data",
    "schema": {"columns": [...]},
    "type": "table"
}
success = indexer_agent.index_table_documentation(table_data)

# Search for relevant documentation
results = indexer_agent.search_documentation("user authentication", "table")

# Process natural language instructions
result = indexer_agent.process_indexing_instruction(
    "Index the customer table with business purpose for customer management"
)

# Batch index multiple tables
tables_data = [table1_data, table2_data, table3_data]
batch_results = indexer_agent.batch_index_tables(tables_data)
```

## 📊 Response Structure

### Search Results Response

```json
{
  "success": true,
  "query": "user authentication",
  "doc_type": "table",
  "tables": [
    {
      "content": {
        "name": "users",
        "business_purpose": "Stores user account information and authentication data",
        "schema": {...}
      },
      "score": 0.92,
      "id": "users_table"
    }
  ],
  "relationships": [],
  "total_results": 1
}
```

### Indexing Status Response

```json
{
  "success": true,
  "table_index_count": 15,
  "relationship_index_count": 8,
  "total_indexed_documents": 23,
  "vector_dimensions": 3072
}
```

### Natural Language Instruction Response

```json
{
  "success": true,
  "operation": "index_table_documentation",
  "message": "Successfully indexed table: customers",
  "table_name": "customers",
  "vector_dimensions": 3072,
  "details": "Table documentation indexed with OpenAI embeddings"
}
```

## 🧠 Embedding and Search Algorithm

The agent uses OpenAI's text-embedding-3-small model with the following characteristics:

```markdown
Model: text-embedding-3-small
Dimensions: 3072
Distance Metric: Cosine Distance
Similarity Calculation: 1.0 - (distance / 2.0)
```

### Search Process

1. **Query Embedding**: Convert user query to 3072-dimensional vector
2. **Similarity Search**: Find most similar vectors in ChromaDB collections
3. **Score Conversion**: Convert cosine distance to similarity score (0-1)
4. **Ranking**: Sort results by similarity score (highest first)
5. **Filtering**: Apply relevance thresholds and result limits

### Indexing Process

1. **Document Preparation**: Validate and structure documentation data
2. **Text Embedding**: Generate embeddings for business purpose and schema
3. **Metadata Storage**: Store table/relationship metadata with embeddings
4. **Collection Management**: Organize embeddings in separate table/relationship collections
5. **Persistence**: Save to ChromaDB for persistent storage

## ⚙️ Configuration

### Environment Variables

```env
# Required for OpenAI embeddings
OPENAI_API_KEY="your-api-key-here"

# Optional: Customize embedding model
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Optional: Batch processing settings
EMBEDDING_BATCH_SIZE="100"
EMBEDDING_MAX_RETRIES="3"

# Optional: ChromaDB settings
CHROMA_PERSIST_DIRECTORY="__bin__/data/vector_indexes"
```

### Initialization Parameters

```python
SQLIndexerAgent(
    vector_store,              # Required: SQLVectorStore instance
)

# Method parameters
index_table_documentation(
    table_data                 # Required: Dict with name, business_purpose, schema, type
)

search_documentation(
    query,                     # Required: Natural language search query
    doc_type="all"            # Optional: 'all', 'table', or 'relationship'
)

process_indexing_instruction(
    instruction                # Required: Natural language instruction
)
```

## 🎯 Use Cases

### 1. Semantic Search

Find relevant tables using natural language:

```python
# Search for user-related tables
results = indexer_agent.search_documentation("user management", "table")

# Search for customer relationships
results = indexer_agent.search_documentation("customer data", "relationship")
```

### 2. Batch Indexing

Efficiently index multiple documents:

```python
# Index all processed tables
tables_data = [table1, table2, table3, ...]
batch_results = indexer_agent.batch_index_tables(tables_data)

# Index all relationships
relationships_data = [rel1, rel2, rel3, ...]
batch_results = indexer_agent.batch_index_relationships(relationships_data)
```

### 3. Natural Language Instructions

Process indexing operations using plain English:

```python
# Index a table with natural language
result = indexer_agent.process_indexing_instruction(
    "Index the orders table with business purpose for order management"
)

# Search using natural language
result = indexer_agent.process_indexing_instruction(
    "Search for tables related to customer information"
)
```

### 4. Index Management

Monitor and maintain vector indexes:

```python
# Get indexing status
status = indexer_agent.get_indexing_status()

# Update existing index
success = indexer_agent.update_table_index("users", updated_data)

# Remove from index
success = indexer_agent.remove_from_index("old_table", "table")
```

## 🔍 Integration with Other Agents

The Indexer Agent works seamlessly with other components:

- **Core Agent**: Receives documentation data for indexing
- **Entity Recognition Agent**: Provides search capabilities for entity discovery
- **Batch Manager**: Supports efficient batch processing operations
- **Vector Store**: Manages ChromaDB collections and embeddings
- **Embeddings Client**: Handles OpenAI API interactions

## 🎖️ Advanced Features

### Intelligent Document Processing

- Validates documentation structure before indexing
- Handles both table and relationship documentation formats
- Supports metadata enrichment and organization

### Semantic Search Capabilities

- Natural language query understanding
- Multi-factor relevance scoring
- Configurable search result filtering
- Support for different document types

### Batch Processing Optimization

- Efficient bulk indexing operations
- Error handling and retry mechanisms
- Progress tracking and status reporting
- Memory-efficient processing for large datasets

### Index Management

- Real-time status monitoring
- Index health and performance metrics
- Update and removal operations
- Collection organization and maintenance

## 📈 Performance Characteristics

- **Embedding Generation**: ~100ms per document with OpenAI API
- **Search Response Time**: Sub-second for typical queries
- **Index Storage**: Efficient ChromaDB persistence with metadata
- **Batch Processing**: 10-50 documents per second depending on API limits
- **Memory Usage**: Minimal memory footprint with streaming operations
- **Scalability**: Handles databases with thousands of tables efficiently

## 🚦 Prerequisites

1. **OpenAI API Access**: Valid API key for embeddings generation
2. **ChromaDB**: Local or remote ChromaDB instance for vector storage
3. **Documentation Data**: Tables and relationships must be documented by Core Agent
4. **Dependencies**: All required packages from requirements.txt
5. **Vector Store**: Properly configured SQLVectorStore with ChromaDB

## 🔧 Error Handling

### Common Error Scenarios

1. **API Rate Limits**: Automatic retry with exponential backoff
2. **Invalid Documentation**: Validation errors with detailed feedback
3. **ChromaDB Issues**: Graceful degradation with error reporting
4. **Network Problems**: Connection timeout handling and retry logic

### Error Response Format

```json
{
  "success": false,
  "error": "OpenAI API rate limit exceeded",
  "details": "Rate limit of 3000 requests per minute exceeded",
  "retry_after": 60,
  "suggestion": "Wait 60 seconds before retrying"
}
```

---

The Indexer Agent provides the foundation for semantic search capabilities in the SQL Documentation suite, enabling intelligent discovery and retrieval of database documentation through natural language queries and vector similarity search. 
