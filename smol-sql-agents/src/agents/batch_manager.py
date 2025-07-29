"""Batch processing manager for efficient OpenAI embeddings generation."""

import os
import logging
from typing import List, Dict, Optional
from .indexer import SQLIndexerAgent
from ..database.persistence import DocumentationStore

logger = logging.getLogger(__name__)

class BatchIndexingManager:
    """Manages efficient batch processing for OpenAI embeddings."""
    
    def __init__(self, indexer_agent: SQLIndexerAgent):
        """Initialize the batch indexing manager.
        
        Args:
            indexer_agent: The SQLIndexerAgent instance to use for indexing
        """
        self.indexer = indexer_agent
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
        self.max_retries = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
        
    def batch_process_pending_tables(self, doc_store: DocumentationStore) -> Dict[str, bool]:
        """Process multiple tables in batches to optimize OpenAI API usage.
        
        Args:
            doc_store: Documentation store to get pending tables from
            
        Returns:
            Dict[str, bool]: Mapping of table names to processing success status
        """
        pending_tables = doc_store.get_pending_tables()
        if not pending_tables:
            logger.info("No pending tables to process")
            return {}
            
        logger.info(f"Processing {len(pending_tables)} tables in batches of {self.batch_size}")
        
        # Group tables into batches
        table_batches = self._group_into_batches(pending_tables, self.batch_size)
        
        results = {}
        for i, batch in enumerate(table_batches):
            logger.info(f"Processing batch {i+1}/{len(table_batches)} ({len(batch)} tables)")
            
            # Prepare table data for batch processing
            tables_data = []
            for table_name in batch:
                try:
                    # Get table schema and documentation
                    table_info = doc_store.get_table_info(table_name)
                    if table_info:
                        tables_data.append({
                            "name": table_name,
                            "schema": table_info.get("schema_data", {}),
                            "business_purpose": table_info.get("business_purpose", ""),
                            "documentation": table_info.get("documentation", "")
                        })
                except Exception as e:
                    logger.error(f"Failed to prepare table data for {table_name}: {e}")
                    results[table_name] = False
                    continue
            
            # Process batch
            if tables_data:
                batch_results = self.indexer.batch_index_tables(tables_data)
                results.update(batch_results)
                
                # Log batch progress
                successful = sum(1 for success in batch_results.values() if success)
                logger.info(f"Batch {i+1} completed: {successful}/{len(batch_results)} successful")
        
        return results
    
    def batch_process_pending_relationships(self, doc_store: DocumentationStore) -> Dict[str, bool]:
        """Process multiple relationships in batches to optimize OpenAI API usage.
        
        Args:
            doc_store: Documentation store to get pending relationships from
            
        Returns:
            Dict[str, bool]: Mapping of relationship IDs to processing success status
        """
        pending_relationships = doc_store.get_pending_relationships()
        if not pending_relationships:
            logger.info("No pending relationships to process")
            return {}
            
        logger.info(f"Processing {len(pending_relationships)} relationships in batches of {self.batch_size}")
        
        # Group relationships into batches
        rel_batches = self._group_into_batches(pending_relationships, self.batch_size)
        
        results = {}
        for i, batch in enumerate(rel_batches):
            logger.info(f"Processing batch {i+1}/{len(rel_batches)} ({len(batch)} relationships)")
            
            # Prepare relationship data for batch processing
            relationships_data = []
            for relationship in batch:
                try:
                    rel_id = relationship.get("id", "unknown")
                    # Get relationship documentation
                    rel_info = doc_store.get_relationship_info(rel_id)
                    if rel_info:
                        relationships_data.append({
                            "id": rel_id,
                            "name": rel_id,
                            "type": rel_info.get("relationship_type", ""),
                            "documentation": rel_info.get("documentation", ""),
                            "tables": [relationship.get("constrained_table"), relationship.get("referred_table")]
                        })
                except Exception as e:
                    logger.error(f"Failed to prepare relationship data for {rel_id}: {e}")
                    results[rel_id] = False
                    continue
            
            # Process batch
            if relationships_data:
                batch_results = self.indexer.batch_index_relationships(relationships_data)
                results.update(batch_results)
                
                # Log batch progress
                successful = sum(1 for success in batch_results.values() if success)
                logger.info(f"Batch {i+1} completed: {successful}/{len(batch_results)} successful")
        
        return results
    
    def estimate_embedding_costs(self, texts: List[str]) -> Dict[str, float]:
        """Estimate OpenAI API costs for embedding generation request.
        
        Args:
            texts: List of texts to estimate costs for
            
        Returns:
            Dict[str, float]: Cost estimation details
        """
        try:
            # Rough estimation based on OpenAI pricing
            # text-embedding-3-small: $0.00002 per 1K tokens
            # Average tokens per text (rough estimate)
            total_tokens = sum(len(text.split()) * 1.3 for text in texts)  # Rough token estimation
            cost_per_1k_tokens = 0.00002
            
            estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens
            
            return {
                "total_texts": len(texts),
                "estimated_tokens": int(total_tokens),
                "estimated_cost_usd": round(estimated_cost, 6),
                "cost_per_text": round(estimated_cost / len(texts), 6) if texts else 0
            }
        except Exception as e:
            logger.error(f"Failed to estimate embedding costs: {e}")
            return {
                "total_texts": len(texts),
                "estimated_tokens": 0,
                "estimated_cost_usd": 0,
                "cost_per_text": 0,
                "error": str(e)
            }
    
    def _group_into_batches(self, items: List, batch_size: int) -> List[List]:
        """Group items into optimal batch sizes.
        
        Args:
            items: List of items to group
            batch_size: Maximum size of each batch
            
        Returns:
            List[List]: List of batches
        """
        if not items:
            return []
        
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def get_processing_stats(self, doc_store: DocumentationStore) -> Dict[str, any]:
        """Get statistics about pending processing tasks.
        
        Args:
            doc_store: Documentation store to analyze
            
        Returns:
            Dict[str, any]: Processing statistics
        """
        pending_tables = doc_store.get_pending_tables()
        pending_relationships = doc_store.get_pending_relationships()
        
        # Estimate costs for pending items
        table_texts = [f"Table: {table}" for table in pending_tables]
        rel_texts = [f"Relationship: {rel.get('id', 'unknown')}" for rel in pending_relationships]
        
        table_cost_estimate = self.estimate_embedding_costs(table_texts)
        rel_cost_estimate = self.estimate_embedding_costs(rel_texts)
        
        return {
            "pending_tables": len(pending_tables),
            "pending_relationships": len(pending_relationships),
            "total_pending": len(pending_tables) + len(pending_relationships),
            "estimated_table_cost": table_cost_estimate["estimated_cost_usd"],
            "estimated_relationship_cost": rel_cost_estimate["estimated_cost_usd"],
            "total_estimated_cost": table_cost_estimate["estimated_cost_usd"] + rel_cost_estimate["estimated_cost_usd"],
            "batch_size": self.batch_size,
            "estimated_batches": (len(pending_tables) + len(pending_relationships)) // self.batch_size + 1
        } 