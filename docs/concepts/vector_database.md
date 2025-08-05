# Vector Database

This document explains the vector database capabilities in smol-sql-agents, including embedding generation, storage, and similarity search.

## Overview

The vector database enables semantic search and similarity comparisons by storing and querying vector embeddings of text data.

## Key Components

### 1. Embeddings Client

Handles text-to-vector conversion using various embedding models.

**Features:**

- Multiple model support (OpenAI, Hugging Face, etc.)
- Batch processing
- Caching layer
- Normalization and preprocessing

### 2. Vector Store

Manages storage and retrieval of vector embeddings.

**Supported Backends:**

- In-memory (for development)
- Pinecone
- Weaviate
- FAISS
- Chroma

### 3. Search Tools

Provides similarity search and nearest neighbor lookups.

**Search Types:**

- Exact search
- Approximate Nearest Neighbor (ANN)
- Hybrid search (combining vector and metadata)

## Usage Examples

### Initialization

```python
from smol_sql_agents.vector import VectorStore, EmbeddingsClient

# Initialize embeddings client
embeddings = EmbeddingsClient(model="text-embedding-ada-002")

# Initialize vector store
vector_store = VectorStore(
    store_type="pinecone",
    index_name="my-index",
    dimension=1536  # Depends on the embedding model
)
```

### Generating and Storing Embeddings

```python
# Generate embeddings
texts = ["First document", "Second document"]
embeddings_list = await embeddings.embed_documents(texts)

# Store in vector store
ids = ["doc1", "doc2"]
metadata = [{"source": "example"}, {"source": "example"}]
await vector_store.add_vectors(ids, embeddings_list, metadata)
```

### Similarity Search

```python
# Find similar documents
query = "Find similar documents"
query_embedding = await embeddings.embed_query(query)
results = await vector_store.similarity_search(
    query_embedding=query_embedding,
    k=5  # Number of results
)
```

## Integration with SQL

### Vector-Enhanced Queries

```python
from smol_sql_agents import NL2SQLAgent

agent = NL2SQLAgent()
result = agent.execute(
    query="Find products similar to 'wireless headphones' in the electronics category",
    schema=database_schema,
    vector_search=True
)
```

## Performance Considerations

### Indexing

- **Batch Processing**: Process documents in batches for better performance
- **Parallel Processing**: Use async/await for concurrent operations
- **Incremental Updates**: Update indexes incrementally when possible

### Query Optimization

- **Filtering**: Apply metadata filters before vector search
- **Pagination**: Implement result pagination for large result sets
- **Caching**: Cache frequent queries and their results

## Best Practices

1. **Dimensionality**: Choose appropriate embedding dimensions for your use case
2. **Normalization**: Normalize vectors for consistent similarity scores
3. **Metadata**: Include rich metadata for better filtering
4. **Monitoring**: Track query performance and index size

## Troubleshooting

### Common Issues

1. **Dimension Mismatch**
   - Verify embedding model dimensions match vector store configuration
   - Check for model version changes

2. **Performance Problems**
   - Optimize batch sizes
   - Consider using approximate nearest neighbor search for large datasets

3. **Memory Usage**
   - Monitor vector store memory consumption
   - Use disk-based storage for large datasets

## Related Documentation

- [Architecture Overview](./architecture.md)
- [API Reference](../api/vector/README.md)
- [Performance Tuning Guide](../troubleshooting/performance_tuning.md)
