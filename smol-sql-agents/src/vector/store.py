"""Vector database wrapper for SQL documentation using ChromaDB."""

from typing import Dict, List, Optional, Protocol, Any
import os
import json
import logging
import chromadb
from pathlib import Path
from .embeddings import OpenAIEmbeddingsClient

logger = logging.getLogger(__name__)

class VectorIndex(Protocol):
    """Protocol for vector index implementations."""
    
    def add(self, id: str, vector: List[float], metadata: Optional[Dict] = None) -> None:
        """Add vector to index."""
        ...
        
    def search(self, vector: List[float], k: int = 5) -> List[Dict]:
        """Search for similar vectors."""
        ...
        
    def save(self) -> None:
        """Save the index."""
        ...

class ChromaDBIndex:
    """ChromaDB-based vector index implementation."""
    
    def __init__(self, collection_name: str, persist_directory: str = None):
        """Initialize ChromaDB index.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or "__bin__/data/vector_indexes"
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing ChromaDB collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Vector index for {collection_name}"}
            )
            logger.info(f"Created new ChromaDB collection: {collection_name}")
        
    def add(self, id: str, vector: List[float], metadata: Optional[Dict] = None) -> None:
        """Add vector to ChromaDB collection."""
        try:
            # Prepare metadata for ChromaDB (convert lists to strings)
            chroma_metadata = self._prepare_metadata_for_chroma(metadata or {})
            
            # Add the document ID to metadata for retrieval
            chroma_metadata["id"] = id
            
            # Add to collection
            self.collection.add(
                embeddings=[vector],
                documents=[self._create_document_text(metadata)],
                metadatas=[chroma_metadata],
                ids=[id]
            )
            
            logger.debug(f"Added vector to ChromaDB collection: {id}")
            
        except Exception as e:
            logger.error(f"Failed to add vector to ChromaDB: {e}")
            raise
        
    def search(self, vector: List[float], k: int = 5) -> List[Dict]:
        """Search for similar vectors using ChromaDB."""
        try:
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=k,
                include=["metadatas", "distances"]
            )
            
            # Process results
            search_results = []
            
            if results["metadatas"] and results["metadatas"][0]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    # Get distance from ChromaDB
                    distance = results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0
                    
                    # ChromaDB uses cosine distance (0 = identical, 2 = completely opposite)
                    # Convert to similarity score (1 = identical, 0 = completely opposite)
                    similarity = 1.0 - (distance / 2.0)
                    
                    # Ensure similarity is between 0 and 1
                    similarity = max(0.0, min(1.0, similarity))
                    
                    logger.debug(f"ChromaDB distance: {distance}, calculated similarity: {similarity}")
                    
                    search_results.append({
                        "id": metadata.get("id", f"result_{i}"),
                        "metadata": metadata,
                        "score": similarity
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search ChromaDB collection: {e}")
            return []
        
    def save(self) -> None:
        """Save index - ChromaDB handles persistence automatically."""
        # ChromaDB automatically persists data
        pass
    
    def _create_document_text(self, metadata: Optional[Dict]) -> str:
        """Create document text for ChromaDB storage."""
        if not metadata:
            return ""
        
        # Create a text representation of the metadata
        parts = []
        
        if metadata.get("type") == "table":
            parts.extend([
                f"Table: {metadata.get('name', '')}",
                f"Description: {metadata.get('description', '')}",
                f"Columns: {', '.join(metadata.get('columns', []))}",
                f"Business Purpose: {metadata.get('business_purpose', '')}"
            ])
        else:
            parts.extend([
                f"Relationship: {metadata.get('name', '')}",
                f"Type: {metadata.get('relationship_type', '')}",
                f"Description: {metadata.get('description', '')}",
                f"Tables: {', '.join(metadata.get('tables', []))}"
            ])
        
        return " | ".join(filter(None, parts))

    def _prepare_metadata_for_chroma(self, metadata: Dict) -> Dict:
        """Prepare metadata for ChromaDB by converting lists to strings."""
        chroma_metadata = {}
        
        for key, value in metadata.items():
            if isinstance(value, list):
                # Convert lists to comma-separated strings
                chroma_metadata[key] = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                # Convert dictionaries to JSON strings
                chroma_metadata[key] = json.dumps(value)
            else:
                # Keep primitive types as-is
                chroma_metadata[key] = value
                
        return chroma_metadata

class SQLVectorStore:
    """Manages vector indexes using OpenAI embeddings with ChromaDB persistence."""
    
    def __init__(self, base_path: str = "__bin__/data/vector_indexes", vector_index_factory: Any = None):
        """Initialize vector store with base path for indexes.
        
        Args:
            base_path (str): Base directory for storing vector indexes
            vector_index_factory: Factory function to create vector indexes
        """
        self.base_path = base_path
        self.embeddings_client = OpenAIEmbeddingsClient()
        self.vector_index_factory = vector_index_factory or self._default_index_factory
        self.table_index = None     # vector index instance for tables
        self.relationship_index = None  # vector index instance for relationships
        self._ensure_directories()
        
    def _default_index_factory(self, path: str) -> VectorIndex:
        """Create default vector index implementation using ChromaDB."""
        # Extract collection name from path
        collection_name = os.path.basename(path).replace('.db', '')
        return ChromaDBIndex(collection_name=collection_name, persist_directory=self.base_path)
        
    def create_table_index(self, index_name: str = "tables"):
        """Create vector index for table documentation.
        
        Args:
            index_name: Name of the index
            
        Returns:
            None
        """
        index_path = os.path.join(self.base_path, "tables", f"{index_name}.db")
        self.table_index = self.vector_index_factory(index_path)
        
    def create_relationship_index(self, index_name: str = "relationships"):
        """Create vector index for relationship documentation.
        
        Args:
            index_name: Name of the index
            
        Returns:
            None
        """
        index_path = os.path.join(self.base_path, "relationships", f"{index_name}.db")
        self.relationship_index = self.vector_index_factory(index_path)
        
    def add_table_document(self, table_name: str, content: Dict):
        """Add table documentation with OpenAI-generated embedding.
        
        Args:
            table_name: Name of the table
            content: Dictionary containing table documentation
            
        Returns:
            None
            
        Raises:
            ValueError: If table index hasn't been created
        """
        if not self.table_index:
            raise ValueError("Table index not initialized. Call create_table_index first.")
            
        doc_text = self._prepare_document_text(content, "table")
        embedding = self.embeddings_client.generate_embedding(doc_text)
        metadata = self._create_document_metadata(content, "table")
        metadata["id"] = table_name  # Add ID for search results
        
        self.table_index.add(
            id=table_name,
            vector=embedding,
            metadata=metadata
        )
        self.table_index.save()
        
    def add_relationship_document(self, relationship_id: str, content: Dict):
        """Add relationship documentation with OpenAI-generated embedding.
        
        Args:
            relationship_id: Unique identifier for the relationship
            content: Dictionary containing relationship documentation
            
        Returns:
            None
            
        Raises:
            ValueError: If relationship index hasn't been created
        """
        if not self.relationship_index:
            raise ValueError("Relationship index not initialized. Call create_relationship_index first.")
            
        doc_text = self._prepare_document_text(content, "relationship")
        embedding = self.embeddings_client.generate_embedding(doc_text)
        metadata = self._create_document_metadata(content, "relationship")
        metadata["id"] = relationship_id  # Add ID for search results
        
        self.relationship_index.add(
            id=relationship_id,
            vector=embedding,
            metadata=metadata
        )
        self.relationship_index.save()
        
    def search_tables(self, query: str, limit: int = 5) -> List[Dict]:
        """Search table documentation using OpenAI query embedding.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching table documents with scores
        """
        if not self.table_index:
            raise ValueError("Table index not initialized. Call create_table_index first.")
            
        query_embedding = self.embeddings_client.generate_embedding(query)
        results = self.table_index.search(
            vector=query_embedding,
            k=limit
        )
        
        # Process results based on the VectorIndex protocol
        return [
            {
                "id": result["id"],
                "content": result["metadata"],  # metadata is already the dictionary
                "score": result.get("score", 1.0)  # default score if not provided
            }
            for result in results
        ]
        
    def search_relationships(self, query: str, limit: int = 5) -> List[Dict]:
        """Search relationship documentation using OpenAI query embedding.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching relationship documents with scores
        """
        if not self.relationship_index:
            raise ValueError("Relationship index not initialized. Call create_relationship_index first.")
            
        query_embedding = self.embeddings_client.generate_embedding(query)
        results = self.relationship_index.search(
            vector=query_embedding,
            k=limit
        )
        
        # Process results based on the VectorIndex protocol
        return [
            {
                "id": result["id"],
                "content": result["metadata"],  # metadata is already the dictionary
                "score": result.get("score", 1.0)  # default score if not provided
            }
            for result in results
        ]
        
    def _prepare_document_text(self, content: Dict, doc_type: str) -> str:
        """Prepare document content for embedding generation.
        
        Args:
            content: Document content dictionary
            doc_type: Type of document ('table' or 'relationship')
            
        Returns:
            str: Prepared text for embedding
        """
        if doc_type == "table":
            # Combine relevant table information
            parts = [
                f"Table: {content.get('name', '')}",
                f"Description: {content.get('description', '')}",
                f"Columns: {', '.join(content.get('columns', []))}"
            ]
        else:
            # Combine relevant relationship information
            parts = [
                f"Relationship: {content.get('name', '')}",
                f"Type: {content.get('type', '')}",
                f"Description: {content.get('description', '')}",
                f"Related Tables: {', '.join(content.get('tables', []))}"
            ]
            
        return " | ".join(filter(None, parts))
        
    def _create_document_metadata(self, content: Dict, doc_type: str) -> Dict:
        """Create metadata to store alongside vectors.
        
        Args:
            content: Document content dictionary
            doc_type: Type of document ('table' or 'relationship')
            
        Returns:
            Dict: Metadata dictionary
        """
        metadata = {
            "type": doc_type,
            "name": content.get("name", ""),
            "description": content.get("description", "")
        }
        
        if doc_type == "table":
            columns = content.get("columns", [])
            metadata.update({
                "columns": columns,
                "column_count": len(columns),
                "business_purpose": content.get("business_purpose", ""),
                "schema_data": content.get("schema_data", {})
            })
        else:
            tables = content.get("tables", [])
            metadata.update({
                "relationship_type": content.get("type", ""),
                "tables": tables,
                "table_count": len(tables),
                "constrained_table": content.get("constrained_table", ""),
                "referred_table": content.get("referred_table", ""),
                "documentation": content.get("documentation", "")
            })
            
        return metadata
        
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(os.path.join(self.base_path, "tables")).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(self.base_path, "relationships")).mkdir(parents=True, exist_ok=True)
