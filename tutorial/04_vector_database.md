# Chapter 4: Vector Database Integration with ChromaDB

In this chapter, we'll implement ChromaDB to store and search vector embeddings of our database documentation, enabling semantic search capabilities.

## Understanding Vector Embeddings

Vector embeddings are numerical representations of text that capture semantic meaning. Similar content will have similar vector representations, allowing us to perform semantic searches.

## Setting Up ChromaDB

First, let's create a vector store manager:

```python
# src/vector/chroma_manager.py
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os

class ChromaManager:
    def __init__(self, collection_name: str = "database_docs"):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=".chroma_db"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Optimize for cosine similarity
        )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store."""
        if not documents:
            return
            
        ids = [str(hash(doc["content"])) for doc in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return [
            {
                "content": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]
    
    def persist(self) -> None:
        """Persist the vector store to disk."""
        self.client.persist()
```

## Generating Embeddings

Let's create a service to generate embeddings using OpenAI:

```python
# src/vector/embedding_service.py
import openai
from typing import List, Dict, Any
import os

class EmbeddingService:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        response = openai.Embedding.create(
            input=texts,
            model=self.model
        )
        return [item["embedding"] for item in response["data"]]
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.get_embeddings([text])[0]
```

## Document Chunking

For large documents, we need to split them into smaller chunks:

```python
# src/utils/chunking.py
from typing import List, Dict, Any
import re

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append({
            "content": chunk,
            "metadata": {
                "chunk_index": len(chunks),
                "total_chunks": -1  # Will be updated later
            }
        })
    
    # Update total chunks count
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = len(chunks)
    
    return chunks

def chunk_document(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Chunk a document into smaller pieces with metadata."""
    content = document.get("content", "")
    metadata = document.get("metadata", {})
    
    chunks = chunk_text(content)
    
    # Add document metadata to each chunk
    for chunk in chunks:
        chunk["metadata"].update(metadata)
    
    return chunks
```

## Integrating with Database Documentation

Now, let's create a service to handle our documentation vectors:

```python
# src/services/document_service.py
from typing import List, Dict, Any
from src.vector.chroma_manager import ChromaManager
from src.vector.embedding_service import EmbeddingService
from src.utils.chunking import chunk_document

class DocumentService:
    def __init__(self):
        self.vector_store = ChromaManager()
        self.embedding_service = EmbeddingService()
    
    def index_document(self, document: Dict[str, Any]) -> None:
        """Index a single document."""
        chunks = chunk_document(document)
        self.vector_store.add_documents(chunks)
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Index multiple documents."""
        for doc in documents:
            self.index_document(doc)
        self.vector_store.persist()
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for documents similar to the query."""
        return self.vector_store.search(query, n_results)
    
    def get_relevant_documentation(self, question: str, context: str = "") -> str:
        """Get relevant documentation for a question with optional context."""
        # Enhance query with context if provided
        if context:
            enhanced_query = f"{question} (Context: {context})"
        else:
            enhanced_query = question
        
        results = self.search_documents(enhanced_query)
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"--- Result {i} ---\n"
                f"Content: {result['content']}\n"
                f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                f"Relevance: {1 - result['distance']:.2f}"
            )
        
        return "\n\n".join(formatted_results) if formatted_results \
               else "No relevant documentation found."
```

## Testing the Implementation

Create a test script to verify everything works:

```python
# examples/test_vector_search.py
from src.services.document_service import DocumentService

def main():
    # Initialize document service
    doc_service = DocumentService()
    
    # Sample documentation
    documents = [
        {
            "content": "The users table stores all registered user information including email and hashed passwords.",
            "metadata": {"source": "database_schema", "table": "users"}
        },
        {
            "content": "The orders table contains all purchase orders with references to users and payment status.",
            "metadata": {"source": "database_schema", "table": "orders"}
        },
        {
            "content": "API endpoint: POST /api/orders - Creates a new order with the provided items.",
            "metadata": {"source": "api_docs", "endpoint": "create_order"}
        }
    ]
    
    # Index documents
    print("Indexing documents...")
    doc_service.index_documents(documents)
    
    # Test search
    queries = [
        "How do I create a new order?",
        "Where is user data stored?",
        "Show me order-related tables"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        results = doc_service.search_documents(query)
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Content: {result['content']}")
            print(f"Source: {result['metadata']}")
            print(f"Relevance: {1 - result['distance']:.2f}")

if __name__ == "__main__":
    main()
```

## Next Steps

In the next chapter, we'll build AI agents that leverage this vector store to answer natural language questions about the database schema.
