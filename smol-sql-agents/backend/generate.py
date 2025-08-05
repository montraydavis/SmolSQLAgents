import os
import logging
import sys
import asyncio
import concurrent.futures
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import time
from contextlib import contextmanager

# Add parent directory to Python path to find src module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# FIXED: Consistent relative imports from sql_agents package
from src.database.inspector import DatabaseInspector
from src.agents.core import PersistentDocumentationAgent
from src.agents.entity_recognition import EntityRecognitionAgent
from src.agents.business import BusinessContextAgent
from src.agents.nl2sql import NL2SQLAgent
from src.agents.integration import SQLAgentPipeline
from src.agents.tools.factory import DatabaseToolsFactory
from src.agents.concepts.loader import ConceptLoader
from src.agents.concepts.matcher import ConceptMatcher
from src.output.formatters import DocumentationFormatter
from src.agents.batch_manager import BatchIndexingManager




def setup_logging():
    """Configure logging for the application."""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'agent.log')
    
    # Create logs directory
    logs_dir = Path('__bin__/logs')
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / log_file),
            logging.StreamHandler()
        ]
    )

def generate_documentation(resume: bool = False, batch_indexing: bool = True):
    """Enhanced main function with OpenAI-powered vector indexing and batch processing."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Autonomous SQL Knowledgebase Agent")
    
    try:
        agent = PersistentDocumentationAgent()
        
        if not resume:
            logger.info("Starting fresh documentation generation")
            # Initial data collection
            inspector = DatabaseInspector()
            tables = inspector.get_all_table_names()
            relationships = inspector.get_all_foreign_key_relationships()
            
            # Initialize session
            session_id = agent.store.start_generation_session(
                os.getenv('DATABASE_URL'), tables, relationships
            )
            logger.info(f"Started session {session_id}")
        else:
            logger.info("Resuming previous documentation generation")
        
        if batch_indexing and agent.vector_indexing_available and agent.indexer_agent:
            # Use batch processing for efficiency
            logger.info("Using batch processing for vector indexing")
            batch_manager = BatchIndexingManager(agent.indexer_agent)
            
            # Get processing statistics
            stats = batch_manager.get_processing_stats(agent.store)
            logger.info(f"Processing stats: {stats}")
            
            # Process tables in batches
            logger.info("Processing tables with batch indexing...")
            table_results = batch_manager.batch_process_pending_tables(agent.store)
            successful_tables = sum(1 for success in table_results.values() if success)
            logger.info(f"Table processing completed: {successful_tables}/{len(table_results)} successful")
            
            # Process relationships in batches
            logger.info("Processing relationships with batch indexing...")
            rel_results = batch_manager.batch_process_pending_relationships(agent.store)
            successful_rels = sum(1 for success in rel_results.values() if success)
            logger.info(f"Relationship processing completed: {successful_rels}/{len(rel_results)} successful")
        elif batch_indexing and not agent.vector_indexing_available:
            logger.warning("Batch indexing requested but vector indexing is not available")
            logger.info("Falling back to individual processing mode")
            batch_indexing = False
            
        else:
            # Process individually (existing logic)
            logger.info("Using individual processing mode")
            
            # Process pending tables
            pending_tables = agent.store.get_pending_tables()
            logger.info(f"Found {len(pending_tables)} pending tables")
            
            processed_tables = set()  # Track tables processed in this session
            for table in pending_tables:
                if table in processed_tables:
                    logger.warning(f"Skipping already processed table in this session: {table}")
                    continue
                    
                if agent.store.is_table_processed(table):
                    logger.warning(f"Skipping previously processed table: {table}")
                    continue
                
                try:
                    agent.process_table_documentation(table)
                    processed_tables.add(table)
                    
                    # Log progress
                    progress = agent.store.get_generation_progress()
                    logger.info(f"Progress - Tables: {progress['tables']}")
                except Exception as e:
                    logger.error(f"Failed to process table {table}: {e}")
                    if not resume:
                        raise
            
            # Process pending relationships
            pending_relationships = agent.store.get_pending_relationships()
            logger.info(f"Found {len(pending_relationships)} pending relationships")
            
            processed_relationships = set()  # Track relationships processed in this session
            for relationship in pending_relationships:
                rel_id = relationship['id']
                if rel_id in processed_relationships:
                    logger.warning(f"Skipping already processed relationship in this session: {rel_id}")
                    continue
                    
                if agent.store.is_relationship_processed(relationship):
                    logger.warning(f"Skipping previously processed relationship: {relationship['constrained_table']} -> {relationship['referred_table']}")
                    continue
                
                try:
                    agent.process_relationship_documentation(relationship)
                    processed_relationships.add(rel_id)
                    
                    # Log progress
                    progress = agent.store.get_generation_progress()
                    logger.info(f"Progress - Relationships: {progress['relationships']}")
                except Exception as e:
                    logger.error(f"Failed to process relationship {rel_id}: {e}")
                    if not resume:
                        raise
        
        # Generate final documentation
        formatter = DocumentationFormatter()
        
        # Generate multiple formats
        formats = ['markdown', 'html']
        for fmt in formats:
            output_path = f"__bin__/output/database_docs.{fmt}"
            documentation = formatter.generate_documentation(fmt)
            
            Path('__bin__/output').mkdir(exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            logger.info(f"Documentation generated: {output_path}")
        
        logger.info("Documentation generation completed successfully")
        
        # Index already processed documents if vector indexing is available
        if agent.vector_indexing_available and agent.indexer_agent:
            logger.info("Indexing already processed documents...")
            agent.index_processed_documents()
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise

generate_documentation(resume=True)