# Vector Store

The Vector Store is a ChromaDB-based component that manages OpenAI embeddings for SQL documentation. It provides persistent vector storage, semantic search capabilities, and efficient similarity matching for both table and relationship documentation.

## 🎯 What It Does

The Vector Store handles vector embeddings and semantic search for SQL documentation:

- **Vector Storage**: Persistent storage of OpenAI embeddings using ChromaDB
- **Semantic Search**: Fast similarity search using cosine distance metrics
- **Document Management**: Add, update, and remove documentation with metadata
- **Dual Indexes**: Separate indexes for table and relationship documentation
- **Local Persistence**: ChromaDB-based local storage without external dependencies
- **Metadata Enrichment**: Rich metadata storage alongside vector embeddings

## 🔄 Vector Flow

```markdown
Documentation Content → Text Preparation → OpenAI Embeddings → ChromaDB Storage → Similarity Search
```

1. **Document Preparation**: Converts documentation to searchable text format
2. **Embedding Generation**: Creates 3072-dimensional OpenAI embeddings
3. **Metadata Preparation**: Structures metadata for ChromaDB compatibility  
4. **Vector Storage**: Persists embeddings and metadata in ChromaDB collections
5. **Search Processing**: Converts queries to embeddings for similarity search
6. **Result Ranking**: Returns ranked results with similarity scores

## 🚀 Usage Examples

### Programmatic Usage

```python
from src.vector.store import SQLVectorStore

# Initialize the vector store
vector_store = SQLVectorStore()

# Create indexes for tables and relationships
vector_store.create_table_index()
vector_store.create_relationship_index()

# Add table documentation
table_data = {
    "name": "users",
    "business_purpose": "Stores user account information and authentication data",
    "schema": {
        "columns": ["id", "username", "email", "created_at"]
    },
    "type": "table"
}

vector_store.add_table_document("users", table_data)

# Add relationship documentation
relationship_data = {
    "name": "users_orders_rel",
    "type": "one-to-many", 
    "documentation": "Each user can have multiple orders",
    "tables": ["users", "orders"]
}

vector_store.add_relationship_document("users_orders_fk", relationship_data)

# Search for relevant tables
table_results = vector_store.search_tables("user authentication", limit=5)
for result in table_results:
    print(f"Table: {result['content']['name']} (score: {result['score']:.3f})")
    print(f"Purpose: {result['content']['business_purpose']}")

# Search for relevant relationships  
rel_results = vector_store.search_relationships("user orders", limit=3)
for result in rel_results:
    print(f"Relationship: {result['content']['name']} (score: {result['score']:.3f})")
    print(f"Documentation: {result['content']['documentation']}")
```

### Advanced Search Operations

```python
# Combined search across both indexes
def comprehensive_search(vector_store, query, limit=10):
    """Search across both tables and relationships."""
    
    # Search tables and relationships separately
    table_results = vector_store.search_tables(query, limit=limit//2)
    rel_results = vector_store.search_relationships(query, limit=limit//2)
    
    # Combine and sort by score
    all_results = []
    
    for result in table_results:
        all_results.append({
            "type": "table",
            "name": result["content"]["name"],
            "score": result["score"],
            "content": result["content"]
        })
    
    for result in rel_results:
        all_results.append({
            "type": "relationship", 
            "name": result["content"]["name"],
            "score": result["score"],
            "content": result["content"]
        })
    
    # Sort by relevance score
    all_results.sort(key=lambda x: x["score"], reverse=True)
    
    return all_results[:limit]

# Use comprehensive search
results = comprehensive_search(vector_store, "customer data management")
for result in results:
    print(f"{result['type']}: {result['name']} (score: {result['score']:.3f})")
```

### Batch Operations

```python
# Add multiple documents efficiently
tables_to_add = [
    {
        "name": "customers",
        "business_purpose": "Customer information and contact details",
        "schema": {"columns": ["id", "name", "email", "phone"]},
        "type": "table"
    },
    {
        "name": "orders", 
        "business_purpose": "Customer order tracking and history",
        "schema": {"columns": ["id", "customer_id", "total", "order_date"]},
        "type": "table"
    }
]

# Add each table to the index
for table_data in tables_to_add:
    vector_store.add_table_document(table_data["name"], table_data)
    print(f"Added table: {table_data['name']}")

# Verify storage
for table_data in tables_to_add:
    results = vector_store.search_tables(table_data["name"], limit=1)
    if results and results[0]["score"] > 0.9:
        print(f"✓ {table_data['name']} successfully stored and searchable")
```

## 📊 Response Structure

### Search Results Response

```json
[
  {
    "id": "users",
    "content": {
      "name": "users",
      "business_purpose": "Stores user account information and authentication data",
      "schema_data": {
        "columns": ["id", "username", "email", "created_at"]
      },
      "type": "table",
      "columns": ["id", "username", "email", "created_at"],
      "column_count": 4
    },
    "score": 0.923
  },
  {
    "id": "user_profiles", 
    "content": {
      "name": "user_profiles",
      "business_purpose": "Extended user profile information and preferences",
      "schema_data": {
        "columns": ["user_id", "first_name", "last_name", "bio"]
      },
      "type": "table",
      "columns": ["user_id", "first_name", "last_name", "bio"],
      "column_count": 4
    },
    "score": 0.856
  }
]
```

### Document Metadata Structure

```json
{
  "type": "table",
  "name": "users",
  "description": "Stores user account information",
  "columns": ["id", "username", "email", "created_at"],
  "column_count": 4,
  "business_purpose": "User authentication and profile management",
  "schema_data": {
    "table_name": "users",
    "columns": [
      {"name": "id", "type": "INTEGER", "primary_key": true},
      {"name": "username", "type": "VARCHAR(50)", "nullable": false}
    ]
  }
}
```

## ⚙️ Configuration

### Environment Variables

```env
# Required for OpenAI embeddings
OPENAI_API_KEY="your-api-key-here"

# Optional: Customize embedding model  
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Optional: ChromaDB storage location
CHROMA_PERSIST_DIRECTORY="__bin__/data/vector_indexes"

# Optional: Batch processing settings
EMBEDDING_BATCH_SIZE="100"
EMBEDDING_MAX_RETRIES="3"
```

### Initialization Parameters

```python
SQLVectorStore(
    base_path="__bin__/data/vector_indexes",  # Optional: Custom storage path
    vector_index_factory=None                # Optional: Custom index factory
)

# Method parameters
add_table_document(
    table_name,                # Required: Unique table identifier
    content                    # Required: Dictionary with table documentation
)

add_relationship_document(
    relationship_id,           # Required: Unique relationship identifier  
    content                   # Required: Dictionary with relationship documentation
)

search_tables(
    query,                    # Required: Natural language search query
    limit=5                   # Optional: Maximum results to return
)

search_relationships(
    query,                    # Required: Natural language search query
    limit=5                   # Optional: Maximum results to return
)
```

### Storage Structure

```markdown
__bin__/data/vector_indexes/
├── chroma.sqlite3           # ChromaDB database file
├── tables/                  # Table embeddings collection
└── relationships/           # Relationship embeddings collection
```

## 🎯 Use Cases

### 1. Semantic Documentation Search

Find relevant documentation using natural language queries:

```python
# Search for authentication-related tables
auth_results = vector_store.search_tables("user authentication login", limit=5)

print("Authentication-related tables:")
for result in auth_results:
    table_name = result["content"]["name"]
    purpose = result["content"]["business_purpose"]
    score = result["score"]
    
    print(f"  {table_name} (relevance: {score:.3f})")
    print(f"    Purpose: {purpose}")

# Search for specific relationship types
rel_results = vector_store.search_relationships("foreign key constraints", limit=5)

print("\nRelationship information:")
for result in rel_results:
    rel_name = result["content"]["name"]
    documentation = result["content"]["documentation"]
    score = result["score"]
    
    print(f"  {rel_name} (relevance: {score:.3f})")
    print(f"    Description: {documentation}")
```

### 2. Content Discovery

Discover related documentation based on context:

```python
def find_related_content(vector_store, table_name, limit=5):
    """Find content related to a specific table."""
    
    # Get the table's documentation first
    table_results = vector_store.search_tables(table_name, limit=1)
    if not table_results:
        return {"tables": [], "relationships": []}
    
    table_info = table_results[0]["content"]
    business_purpose = table_info.get("business_purpose", "")
    
    # Search for related tables using the business purpose
    related_tables = vector_store.search_tables(business_purpose, limit=limit)
    # Exclude the original table
    related_tables = [t for t in related_tables if t["content"]["name"] != table_name]
    
    # Search for related relationships
    search_terms = f"{table_name} {business_purpose}"
    related_relationships = vector_store.search_relationships(search_terms, limit=limit)
    
    return {
        "tables": related_tables[:limit],
        "relationships": related_relationships[:limit]
    }

# Find content related to users table
related = find_related_content(vector_store, "users")
print(f"Found {len(related['tables'])} related tables")
print(f"Found {len(related['relationships'])} related relationships")
```

### 3. Documentation Quality Assessment

Analyze documentation coverage and quality:

```python
def analyze_documentation_coverage(vector_store):
    """Analyze the quality and coverage of stored documentation."""
    
    # Test search quality with common terms
    test_queries = [
        "user management",
        "order processing", 
        "product catalog",
        "authentication",
        "foreign key relationships"
    ]
    
    coverage_report = {
        "total_queries": len(test_queries),
        "queries_with_results": 0,
        "average_top_score": 0.0,
        "query_results": {}
    }
    
    total_top_scores = 0
    
    for query in test_queries:
        # Search both tables and relationships
        table_results = vector_store.search_tables(query, limit=3)
        rel_results = vector_store.search_relationships(query, limit=3)
        
        has_results = len(table_results) > 0 or len(rel_results) > 0
        if has_results:
            coverage_report["queries_with_results"] += 1
        
        # Get top score
        top_score = 0.0
        if table_results:
            top_score = max(top_score, table_results[0]["score"])
        if rel_results:
            top_score = max(top_score, rel_results[0]["score"])
            
        total_top_scores += top_score
        
        coverage_report["query_results"][query] = {
            "has_results": has_results,
            "top_score": top_score,
            "table_results": len(table_results),
            "relationship_results": len(rel_results)
        }
    
    coverage_report["average_top_score"] = total_top_scores / len(test_queries)
    
    return coverage_report

# Analyze documentation quality
report = analyze_documentation_coverage(vector_store)
print(f"Documentation Coverage Report:")
print(f"  Queries with results: {report['queries_with_results']}/{report['total_queries']}")
print(f"  Average top score: {report['average_top_score']:.3f}")
```

### 4. Custom Vector Index Implementation

Create custom vector indexes for specialized use cases:

```python
class CustomVectorIndex:
    """Custom vector index implementation for specialized requirements."""
    
    def __init__(self, collection_name):
        self.collection_name = collection_name
        self.documents = {}  # In-memory storage for demo
        
    def add(self, id, vector, metadata=None):
        """Add document to custom index."""
        self.documents[id] = {
            "vector": vector,
            "metadata": metadata or {}
        }
        
    def search(self, vector, k=5):
        """Custom search implementation."""
        import numpy as np
        
        results = []
        for doc_id, doc_data in self.documents.items():
            # Calculate cosine similarity
            similarity = np.dot(vector, doc_data["vector"]) / (
                np.linalg.norm(vector) * np.linalg.norm(doc_data["vector"])
            )
            
            results.append({
                "id": doc_id,
                "metadata": doc_data["metadata"],
                "score": similarity
            })
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def save(self):
        """Save index state."""
        pass

# Use custom index factory
def custom_index_factory(path):
    collection_name = os.path.basename(path).replace('.db', '')
    return CustomVectorIndex(collection_name)

# Create vector store with custom index
custom_vector_store = SQLVectorStore(
    base_path="__bin__/data/custom_indexes",
    vector_index_factory=custom_index_factory
)
```

## 🔍 Integration with Other Components

The Vector Store provides the foundation for semantic search capabilities:

- **Indexer Agent**: Uses vector store for document storage and retrieval
- **Entity Recognition Agent**: Leverages vector search for entity discovery
- **Search Tools**: Provides semantic search functionality for documentation
- **Embeddings Client**: Generates vectors for storage and search operations

## 🎖️ Advanced Features

### ChromaDB Integration

- **Persistent Storage**: Local ChromaDB storage with SQLite backend
- **Collection Management**: Separate collections for tables and relationships  
- **Metadata Support**: Rich metadata storage alongside embeddings
- **Query Optimization**: Efficient similarity search with distance metrics

### Vector Operations

- **Embedding Generation**: OpenAI text-embedding-3-small (3072 dimensions)
- **Similarity Calculation**: Cosine distance with similarity score conversion
- **Result Ranking**: Automatic sorting by relevance scores
- **Batch Processing**: Efficient bulk operations for large datasets

### Document Management

- **Text Preparation**: Intelligent text preprocessing for embeddings
- **Metadata Enrichment**: Automatic metadata generation and formatting
- **Update Operations**: Support for updating existing documents
- **Removal Operations**: Clean removal of documents from indexes

### Performance Optimization

- **Local Storage**: No external dependencies for vector operations
- **Memory Efficiency**: Optimized memory usage for large document sets
- **Query Caching**: Efficient caching of frequently accessed embeddings
- **Concurrent Access**: Thread-safe operations for multi-user scenarios

## 📈 Performance Characteristics

- **Storage**: Handles 10,000+ documents efficiently with ChromaDB
- **Search Speed**: Sub-second response times for typical queries
- **Memory Usage**: Minimal memory footprint with lazy loading
- **Scalability**: Linear scaling with document count
- **Accuracy**: High-quality semantic search with OpenAI embeddings
- **Persistence**: Durable storage with automatic recovery

## 🚦 Prerequisites

1. **OpenAI API Access**: Valid API key for embedding generation
2. **ChromaDB**: ChromaDB package for vector storage (installed via requirements.txt)
3. **File System Access**: Write permissions for vector index storage
4. **Disk Space**: Storage space for embeddings (typically 1-10MB per 1000 documents)
5. **Dependencies**: All required packages from requirements.txt

## 🔧 Error Handling

### Common Error Scenarios

1. **ChromaDB Initialization**: Collection creation or connection failures
2. **OpenAI API Issues**: Rate limiting, authentication, or network problems
3. **Storage Issues**: Disk space, permissions, or file system problems
4. **Invalid Documents**: Malformed document data or missing required fields
5. **Search Failures**: Query processing or result retrieval errors

### Error Recovery

```python
try:
    # Initialize vector store
    vector_store = SQLVectorStore()
    vector_store.create_table_index()
    vector_store.create_relationship_index()
    
    print("Vector store initialized successfully")
    
except Exception as e:
    print(f"Vector store initialization failed: {e}")
    
    if "chromadb" in str(e).lower():
        print("ChromaDB initialization issue:")
        print("  - Check if ChromaDB is properly installed")
        print("  - Verify write permissions to storage directory")
        print("  - Ensure sufficient disk space")
    elif "openai" in str(e).lower():
        print("OpenAI API issue:")
        print("  - Check OPENAI_API_KEY environment variable")
        print("  - Verify API key has embeddings access")
        print("  - Check network connectivity")
    else:
        print("General initialization error:")
        print("  - Check file system permissions")
        print("  - Verify all dependencies are installed")

# Test basic operations
try:
    # Test document addition
    test_doc = {
        "name": "test_table",
        "business_purpose": "Test table for verification",
        "schema": {"columns": ["id"]},
        "type": "table"
    }
    
    vector_store.add_table_document("test_table", test_doc)
    
    # Test search
    results = vector_store.search_tables("test", limit=1)
    
    if results and results[0]["content"]["name"] == "test_table":
        print("✓ Vector store working correctly")
    else:
        print("⚠ Vector store may have issues")
        
except Exception as e:
    print(f"Vector store operation failed: {e}")
```

### Recovery Strategies

```python
def repair_vector_store(base_path):
    """Attempt to repair corrupted vector store."""
    try:
        import shutil
        
        # Backup existing data
        backup_path = f"{base_path}_backup"
        if os.path.exists(base_path):
            shutil.copytree(base_path, backup_path)
            print(f"Backed up existing data to {backup_path}")
        
        # Reinitialize vector store
        if os.path.exists(base_path):
            shutil.rmtree(base_path)
            
        vector_store = SQLVectorStore(base_path=base_path)
        vector_store.create_table_index()
        vector_store.create_relationship_index()
        
        print("Vector store reinitialized successfully")
        return vector_store
        
    except Exception as e:
        print(f"Vector store repair failed: {e}")
        return None

def check_vector_store_health(vector_store):
    """Check vector store health and performance."""
    health_report = {
        "status": "unknown",
        "issues": [],
        "recommendations": []
    }
    
    try:
        # Test basic operations
        test_doc = {"name": "health_check", "type": "table", "business_purpose": "test"}
        vector_store.add_table_document("health_check", test_doc)
        
        results = vector_store.search_tables("health_check", limit=1)
        
        if results and len(results) > 0:
            health_report["status"] = "healthy"
        else:
            health_report["status"] = "degraded"
            health_report["issues"].append("Search not returning expected results")
            
    except Exception as e:
        health_report["status"] = "unhealthy"
        health_report["issues"].append(f"Basic operations failing: {e}")
        health_report["recommendations"].append("Consider reinitializing vector store")
    
    return health_report
```
