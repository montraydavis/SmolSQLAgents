# Core Agent

The Core Agent is the central orchestrator of the SQL Documentation suite that manages autonomous documentation generation, persistence, and vector indexing. It combines LLM-powered analysis with database schema discovery to create comprehensive documentation for tables and relationships.

## 🎯 What It Does

The Core Agent serves as the primary interface for SQL documentation operations:

- **Autonomous Documentation**: Generates business purpose and schema documentation using GPT-4
- **Database Discovery**: Inspects database schemas to identify tables and relationships
- **Persistence Management**: Maintains documentation state across sessions with resume capability
- **Vector Indexing**: Integrates with Indexer Agent for semantic search capabilities
- **Error Handling**: Provides robust error handling and retry mechanisms
- **State Management**: Tracks processing progress and enables session resumption

## 🔄 Documentation Flow

```markdown
Database Schema → Core Agent → LLM Analysis → Documentation Store → Vector Indexing → Searchable Knowledge Base
```

1. **Schema Discovery**: Inspects database to identify tables and relationships
2. **LLM Processing**: Uses GPT-4 to analyze schema and infer business purpose
3. **Documentation Generation**: Creates structured documentation with business context
4. **Persistence**: Saves documentation to SQLite database for state management
5. **Vector Indexing**: Indexes documentation for semantic search capabilities
6. **Resume Capability**: Tracks progress and enables interrupted session resumption

## 🚀 Usage Examples

### Command Line Interface

```bash
# Generate documentation for all tables and relationships
python main.py

# Resume interrupted documentation generation
python main.py --resume

# Process specific table
python main.py --table users

# Process specific relationship
python main.py --relationship "users_orders_fk"

# Generate documentation with batch indexing
python main.py --batch-index
```

### Programmatic Usage

```python
from src.agents.core import PersistentDocumentationAgent

# Initialize the core agent
agent = PersistentDocumentationAgent()

# Process a single table
agent.process_table_documentation("users")

# Process a relationship
relationship = {
    "id": 1,
    "constrained_table": "orders",
    "referred_table": "users",
    "constrained_columns": "user_id",
    "referred_columns": "id"
}
agent.process_relationship_documentation(relationship)

# Index all processed documents
agent.index_processed_documents()

# Check vector indexing availability
if agent.vector_indexing_available:
    print("Vector indexing is available for semantic search")
```

## 📊 Response Structure

### Table Documentation Response

```json
{
  "business_purpose": "Stores user account information and authentication data",
  "schema_data": {
    "table_name": "users",
    "columns": [
      {
        "name": "id",
        "type": "INTEGER",
        "nullable": false,
        "primary_key": true,
        "default": null
      },
      {
        "name": "email",
        "type": "VARCHAR(255)",
        "nullable": false,
        "primary_key": false,
        "default": null
      }
    ]
  }
}
```

### Relationship Documentation Response

```json
{
  "relationship_type": "one-to-many",
  "documentation": "Each user can have multiple orders, establishing a customer-order relationship"
}
```

### Processing Status Response

```python
{
  "vector_indexing_available": True,
  "indexer_agent": "Available",
  "database_store": "Available",
  "llm_model": "Available",
  "processed_tables": 15,
  "processed_relationships": 8
}
```

## 🧠 LLM Processing Algorithm

The agent uses GPT-4 for intelligent documentation generation:

```markdown
Model: gpt-4o-mini
Context Window: 128K tokens
Processing: Schema analysis + Business purpose inference
Output: Structured JSON documentation
```

### Table Processing Steps

1. **Schema Retrieval**: Extract table schema using database inspector
2. **LLM Analysis**: Send schema to GPT-4 for business purpose inference
3. **JSON Generation**: Generate structured documentation in JSON format
4. **Validation**: Validate required fields and data structure
5. **Persistence**: Save to documentation store
6. **Vector Indexing**: Index for semantic search (if available)

### Relationship Processing Steps

1. **Relationship Data**: Extract foreign key relationship information
2. **LLM Analysis**: Analyze relationship type and business context
3. **Documentation Generation**: Create relationship documentation
4. **Validation**: Ensure proper relationship type classification
5. **Persistence**: Save relationship documentation
6. **Vector Indexing**: Index for semantic search (if available)

## ⚙️ Configuration

### Environment Variables

```env
# Required for LLM processing
OPENAI_API_KEY="your-api-key-here"

# Required for database connection
DATABASE_URL="sqlite:///__bin__/data/documentation.db"

# Optional: Logging configuration
LOG_LEVEL="INFO"
LOG_FILE="agent.log"

# Optional: Vector indexing settings
EMBEDDING_BATCH_SIZE="100"
EMBEDDING_MAX_RETRIES="3"
```

### Initialization Parameters

```python
PersistentDocumentationAgent(
    # No parameters required - uses environment variables
)

# Method parameters
process_table_documentation(
    table_name                 # Required: Name of table to process
)

process_relationship_documentation(
    relationship               # Required: Dict with relationship data
)

index_processed_documents(
    # No parameters - indexes all processed documents
)
```

## 🎯 Use Cases

### 1. Autonomous Documentation Generation

Generate comprehensive documentation for entire databases:

```python
# Process all tables in database
tables = agent.db_inspector.get_all_table_names()
for table in tables:
    agent.process_table_documentation(table)

# Process all relationships
relationships = agent.db_inspector.get_all_foreign_key_relationships()
for rel in relationships:
    agent.process_relationship_documentation(rel)
```

### 2. Incremental Processing

Process specific tables or relationships:

```python
# Process specific table
agent.process_table_documentation("customers")

# Process specific relationship
relationship = {
    "id": 1,
    "constrained_table": "orders",
    "referred_table": "customers",
    "constrained_columns": "customer_id",
    "referred_columns": "id"
}
agent.process_relationship_documentation(relationship)
```

### 3. Resume Capability

Continue interrupted processing sessions:

```python
# Check what's been processed
pending_tables = agent.store.get_pending_tables()
pending_relationships = agent.store.get_pending_relationships()

# Resume processing
for table in pending_tables:
    agent.process_table_documentation(table)
```

### 4. Vector Indexing Integration

Index processed documents for semantic search:

```python
# Index all processed documents
agent.index_processed_documents()

# Check indexing status
if agent.vector_indexing_available:
    print("Vector indexing is working")
    # Use indexer agent for search
    results = agent.indexer_agent.search_documentation("user data")
```

## 🔍 Integration with Other Agents

The Core Agent orchestrates all other components:

- **Database Inspector**: Discovers schema information
- **Documentation Store**: Manages persistence and state
- **Indexer Agent**: Provides vector indexing capabilities
- **LLM Model**: Powers intelligent documentation generation
- **Vector Store**: Enables semantic search functionality

## 🎖️ Advanced Features

### Intelligent Schema Analysis

- Automatic business purpose inference from table names and columns
- Relationship type classification (one-to-one, one-to-many, many-to-many)
- Context-aware documentation generation
- Multi-language schema support

### State Management

- Persistent session tracking across restarts
- Progress monitoring and reporting
- Resume capability for large databases
- Error recovery and retry mechanisms

### Error Handling

- Graceful degradation when vector indexing unavailable
- Comprehensive error logging and reporting
- Retry logic for transient failures
- Fallback mechanisms for edge cases

### Performance Optimization

- Efficient batch processing capabilities
- Memory-conscious processing for large schemas
- Parallel processing where possible
- Caching of frequently accessed data

## 📈 Performance Characteristics

- **Documentation Generation**: 2-5 seconds per table/relationship
- **Schema Discovery**: Sub-second for typical databases
- **Vector Indexing**: ~100ms per document when available
- **Memory Usage**: Minimal footprint with efficient data structures
- **Scalability**: Handles databases with thousands of tables
- **Resume Capability**: Instant session restoration

## 🚦 Prerequisites

1. **OpenAI API Access**: Valid API key for GPT-4 processing
2. **Database Connection**: Accessible database with schema information
3. **Dependencies**: All required packages from requirements.txt
4. **Storage**: SQLite database for persistence
5. **Vector Store**: ChromaDB for semantic search (optional)

## 🔧 Error Handling

### Common Error Scenarios

1. **LLM Processing Errors**: JSON parsing failures, invalid responses
2. **Database Connection Issues**: Connection timeouts, schema access problems
3. **Vector Indexing Failures**: API rate limits, ChromaDB issues
4. **Validation Errors**: Missing required fields, invalid data structures

### Error Response Format

```json
{
  "success": false,
  "error": "Invalid JSON response from LLM",
  "table_name": "users",
  "raw_response": "Generated response text",
  "suggestion": "Check LLM response format and retry"
}
```

### Retry Mechanisms

1. **LLM Processing**: Automatic retry for transient API errors
2. **Vector Indexing**: Exponential backoff for rate limits
3. **Database Operations**: Connection retry with timeout handling
4. **Validation Errors**: Detailed error messages with correction suggestions

## 🔄 Session Management

### Progress Tracking

```python
# Get processing progress
progress = agent.store.get_generation_progress()
print(f"Tables: {progress['tables']}")
print(f"Relationships: {progress['relationships']}")

# Check specific item status
is_processed = agent.store.is_table_processed("users")
is_processed = agent.store.is_relationship_processed(relationship)
```

### Resume Capability

```python
# Start new session
session_id = agent.store.start_generation_session(
    database_url, tables, relationships
)

# Resume existing session
agent = PersistentDocumentationAgent()  # Automatically resumes
```

---

The Core Agent is the heart of the SQL Documentation suite, providing intelligent, autonomous documentation generation with robust state management and seamless integration with vector indexing for semantic search capabilities.
