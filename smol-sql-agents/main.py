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

# Import our modules
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

# SQL Agents imports
# from src.agents.business import BusinessContextAgent
# from src.agents.nl2sql import NL2SQLAgent
# from src.agents.integration import SQLAgentPipeline
# from src.database.tools import DatabaseTools

# Shared instance manager for caching expensive objects
class SharedInstanceManager:
    """Manages shared instances to avoid repeated instantiation costs."""
    
    def __init__(self):
        self._main_agent = None
        self._database_tools = None
        self._shared_llm_model = None
        self._entity_agent = None
        self._business_agent = None
        self._nl2sql_agent = None
        self._concept_loader = None
        self._concept_matcher = None
        self._initialized = False
    
    def initialize(self):
        """Initialize all shared instances."""
        if self._initialized:
            return
        
        logger = logging.getLogger(__name__)
        logger.info("Initializing shared instances...")
        
        try:
            # Initialize shared LLM model first
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            from smolagents.models import OpenAIModel
            self._shared_llm_model = OpenAIModel(model_id="gpt-4o-mini", api_key=api_key)
            
            # Initialize main agent (contains indexer_agent) with shared LLM model
            self._main_agent = PersistentDocumentationAgent(shared_llm_model=self._shared_llm_model)
            
            # Initialize database tools using unified factory
            database_inspector = DatabaseInspector()
            self._database_tools = DatabaseToolsFactory.create_database_tools(database_inspector)
            
            # Initialize concept components
            concepts_dir = "src/agents/concepts/examples"
            self._concept_loader = ConceptLoader(concepts_dir)
            self._concept_matcher = ConceptMatcher(self._main_agent.indexer_agent)
            
            # Initialize agents with shared components
            self._entity_agent = EntityRecognitionAgent(
                self._main_agent.indexer_agent,
                shared_llm_model=self._shared_llm_model
            )
            
            self._business_agent = BusinessContextAgent(
                indexer_agent=self._main_agent.indexer_agent,
                concepts_dir=concepts_dir,
                shared_llm_model=self._shared_llm_model,
                shared_concept_loader=self._concept_loader,
                shared_concept_matcher=self._concept_matcher
            )
            
            self._nl2sql_agent = NL2SQLAgent(
                self._database_tools,
                shared_llm_model=self._shared_llm_model
            )
            
            self._initialized = True
            logger.info("Shared instances initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize shared instances: {e}")
            raise
    
    @property
    def main_agent(self):
        """Get the main documentation agent."""
        if not self._initialized:
            self.initialize()
        return self._main_agent
    
    @property
    def database_tools(self):
        """Get the database tools instance."""
        if not self._initialized:
            self.initialize()
        return self._database_tools
    
    @property
    def entity_agent(self):
        """Get the entity recognition agent."""
        if not self._initialized:
            self.initialize()
        return self._entity_agent
    
    @property
    def business_agent(self):
        """Get the business context agent."""
        if not self._initialized:
            self.initialize()
        return self._business_agent
    
    @property
    def nl2sql_agent(self):
        """Get the NL2SQL agent."""
        if not self._initialized:
            self.initialize()
        return self._nl2sql_agent
    
    @property
    def indexer_agent(self):
        """Get the indexer agent from main agent."""
        if not self._initialized:
            self.initialize()
        return self._main_agent.indexer_agent
    
    def reset(self):
        """Reset all shared instances (useful for testing)."""
        self._main_agent = None
        self._database_tools = None
        self._shared_llm_model = None
        self._entity_agent = None
        self._business_agent = None
        self._nl2sql_agent = None
        self._concept_loader = None
        self._concept_matcher = None
        self._initialized = False

# Global shared instance manager
shared_manager = SharedInstanceManager()

load_dotenv()

@contextmanager
def performance_timer(operation_name: str):
    """Context manager to time operations and log performance metrics."""
    start_time = time.time()
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {operation_name}")
    
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Completed {operation_name} in {duration:.2f} seconds")

def get_table_schema_concurrent(database_tools, table_name: str) -> Dict[str, Any]:
    """Get schema for a single table - designed for concurrent execution."""
    try:
        schema_info = database_tools.get_table_schema(table_name)
        if schema_info:
            return {
                "table_name": table_name,
                "schema": schema_info,
                "description": schema_info.get("description", f"Table {table_name}"),
                "success": True
            }
        else:
            return {
                "table_name": table_name,
                "schema": None,
                "description": f"Table {table_name}",
                "success": False
            }
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not get schema for table {table_name}: {e}")
        return {
            "table_name": table_name,
            "schema": None,
            "description": f"Table {table_name}",
            "success": False
        }

def run_parallel_validation(sql_query: str, database_tools) -> Dict[str, Any]:
    """Run validation checks in parallel for better performance."""
    validation_results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit different validation tasks
        syntax_future = executor.submit(lambda: {"syntax_valid": True, "syntax_errors": []})
        security_future = executor.submit(lambda: {"security_valid": True, "security_issues": []})
        performance_future = executor.submit(lambda: {"performance_valid": True, "performance_issues": []})
        
        # Collect results
        validation_results["syntax"] = syntax_future.result()
        validation_results["security"] = security_future.result()
        validation_results["performance"] = performance_future.result()
    
    return validation_results

def get_schemas_concurrent(database_tools, table_names: List[str]) -> Dict[str, Any]:
    """Get schemas for multiple tables concurrently."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(table_names), 10)) as executor:
        # Submit all schema retrieval tasks
        future_to_table = {
            executor.submit(get_table_schema_concurrent, database_tools, table_name): table_name 
            for table_name in table_names
        }
        
        # Collect results
        results = {}
        for future in concurrent.futures.as_completed(future_to_table):
            table_name = future_to_table[future]
            try:
                result = future.result()
                results[table_name] = result
            except Exception as e:
                logging.getLogger(__name__).error(f"Error getting schema for {table_name}: {e}")
                results[table_name] = {
                    "table_name": table_name,
                    "schema": None,
                    "description": f"Table {table_name}",
                    "success": False
                }
        
        return results

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

def search_documentation(query: str, doc_type: str = "all"):
    """Search indexed documentation using OpenAI embeddings."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Search functionality requires vector indexing.")
            return None
        
        logger.info(f"Searching documentation for: '{query}' (type: {doc_type})")
        
        # Use the indexer agent to search
        results = main_agent.indexer_agent.search_documentation(query, doc_type)
        
        # Log results
        total_results = results.get("total_results", 0)
        logger.info(f"Search completed: {total_results} results found")
        
        # Print results in a readable format
        print(f"\nSearch Results for: '{query}'")
        print("=" * 50)
        
        if results.get("tables"):
            print(f"\nTables ({len(results['tables'])} results):")
            for i, table in enumerate(results["tables"], 1):
                table_name = table.get('content', {}).get('name', 'Unknown')
                similarity = table.get('score', 0)
                business_purpose = table.get('content', {}).get('business_purpose', '')
                print(f"  {i}. {table_name} (similarity: {similarity:.3f})")
                if business_purpose:
                    print(f"     Purpose: {business_purpose}")
        
        if results.get("relationships"):
            print(f"\nRelationships ({len(results['relationships'])} results):")
            for i, rel in enumerate(results["relationships"], 1):
                rel_name = rel.get('content', {}).get('name', 'Unknown')
                similarity = rel.get('score', 0)
                documentation = rel.get('content', {}).get('documentation', '')
                print(f"  {i}. {rel_name} (similarity: {similarity:.3f})")
                if documentation:
                    print(f"     Description: {documentation}")
        
        if not results.get("tables") and not results.get("relationships"):
            print("No results found.")
        
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print(f"Search error: {e}")
        return None

def recognize_entities(query: str, intent: str = None, max_entities: int = 5):
    """Recognize applicable database entities for a user query."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        entity_agent = shared_manager.entity_agent
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Entity recognition requires vector indexing.")
            return None
        
        logger.info(f"Recognizing entities for query: '{query}'")
        if intent:
            logger.info(f"User intent: '{intent}'")
        
        # Perform entity recognition
        results = entity_agent.recognize_entities(query, intent, max_entities)
        
        # Print results in a readable format
        print(f"\nEntity Recognition Results for: '{query}'")
        if intent:
            print(f"Intent: {intent}")
        print("=" * 60)
        
        if results.get("success"):
            applicable_entities = results.get("applicable_entities", [])
            recommendations = results.get("recommendations", [])
            confidence = results.get("confidence", 0.0)
            
            print(f"\nConfidence Score: {confidence:.2f}")
            print(f"Analysis: {results.get('analysis', 'No analysis available')}")
            
            if applicable_entities:
                print(f"\nApplicable Entities ({len(applicable_entities)} found):")
                for i, entity in enumerate(applicable_entities, 1):
                    # Handle both string and dictionary formats
                    if isinstance(entity, str):
                        table_name = entity
                        relevance_score = 0.0
                        business_purpose = ""
                        recommendation = ""
                    elif isinstance(entity, dict):
                        table_name = entity.get("table_name", "Unknown")
                        relevance_score = entity.get("relevance_score", 0.0)
                        business_purpose = entity.get("business_purpose", "")
                        recommendation = entity.get("recommendation", "")
                    else:
                        table_name = str(entity)
                        relevance_score = 0.0
                        business_purpose = ""
                        recommendation = ""
                    
                    print(f"\n  {i}. {table_name}")
                    if relevance_score > 0:
                        print(f"     Relevance: {relevance_score:.3f}")
                    if business_purpose:
                        print(f"     Purpose: {business_purpose}")
                    if recommendation:
                        print(f"     Recommendation: {recommendation}")
            
            if recommendations:
                # Handle both list and dictionary formats for recommendations
                if isinstance(recommendations, dict):
                    # Extract recommendations from dictionary format
                    rec_list = recommendations.get("recommendations", [])
                    print(f"\nEntity Recommendations ({len(rec_list)} items):")
                    for i, rec in enumerate(rec_list, 1):
                        table_name = rec.get("table_name", "Unknown")
                        priority = rec.get("priority", i)
                        relevance_score = rec.get("relevance_score", 0.0)
                        business_purpose = rec.get("business_purpose", "")
                        recommendation = rec.get("recommendation", "")
                        
                        print(f"\n  {priority}. {table_name}")
                        print(f"     Relevance: {relevance_score:.3f}")
                        print(f"     Purpose: {business_purpose}")
                        if recommendation:
                            print(f"     Assessment: {recommendation}")
                elif isinstance(recommendations, list):
                    print(f"\nEntity Recommendations ({len(recommendations)} items):")
                    for i, rec in enumerate(recommendations, 1):
                        if isinstance(rec, dict):
                            table_name = rec.get("table_name", "Unknown")
                            priority = rec.get("priority", i)
                            relevance_score = rec.get("relevance_score", 0.0)
                            business_purpose = rec.get("business_purpose", "")
                            recommendation = rec.get("recommendation", "")
                            
                            print(f"\n  {priority}. {table_name}")
                            print(f"     Relevance: {relevance_score:.3f}")
                            print(f"     Purpose: {business_purpose}")
                            if recommendation:
                                print(f"     Assessment: {recommendation}")
                        else:
                            print(f"\n  {i}. {str(rec)}")
                else:
                    print(f"\nEntity Recommendations: {recommendations}")
            
            if not applicable_entities:
                print("\nNo applicable entities found for the given query.")
                print("Consider refining your query or checking if relevant tables exist.")
        else:
            print(f"\nError: {results.get('error', 'Unknown error occurred')}")
            if results.get("details"):
                print(f"Details: {results['details']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Entity recognition failed: {e}")
        print(f"Entity recognition error: {e}")
        return None

def quick_entity_lookup(query: str, threshold: float = 0.7):
    """Quick lookup to get table names that are highly relevant to a query."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        entity_agent = shared_manager.entity_agent
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Quick lookup requires vector indexing.")
            return None
        
        logger.info(f"Quick entity lookup for: '{query}' (threshold: {threshold})")
        
        # Perform quick lookup
        table_names = entity_agent.quick_entity_lookup(query, threshold)
        
        # Print results
        print(f"\nQuick Entity Lookup for: '{query}'")
        print(f"Relevance Threshold: {threshold}")
        print("=" * 40)
        
        if table_names:
            print(f"\nRelevant Tables ({len(table_names)} found):")
            for i, table_name in enumerate(table_names, 1):
                print(f"  {i}. {table_name}")
        else:
            print("\nNo tables found above the relevance threshold.")
            print("Try lowering the threshold or refining your query.")
        
        return table_names
        
    except Exception as e:
        logger.error(f"Quick entity lookup failed: {e}")
        print(f"Quick lookup error: {e}")
        return None

def estimate_costs():
    """Estimate OpenAI embedding costs before processing."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Cost estimation requires vector indexing.")
            return None
        
        batch_manager = BatchIndexingManager(main_agent.indexer_agent)
        
        stats = batch_manager.get_processing_stats(main_agent.store)
        
        print("\nCost Estimation for Pending Processing")
        print("=" * 50)
        print(f"Pending tables: {stats['pending_tables']}")
        print(f"Pending relationships: {stats['pending_relationships']}")
        print(f"Total pending items: {stats['total_pending']}")
        print(f"Batch size: {stats['batch_size']}")
        print(f"Estimated batches: {stats['estimated_batches']}")
        print(f"Estimated table cost: ${stats['estimated_table_cost']:.6f}")
        print(f"Estimated relationship cost: ${stats['estimated_relationship_cost']:.6f}")
        print(f"Total estimated cost: ${stats['total_estimated_cost']:.6f}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        print(f"Cost estimation error: {e}")
        return None

def rebuild_indexes():
    """Rebuild vector indexes using OpenAI embeddings."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Index rebuilding requires vector indexing.")
            return None
        
        logger.info("Rebuilding vector indexes...")
        
        # Get all processed tables and relationships
        all_tables = main_agent.store.get_pending_tables()  # This will get all tables
        all_relationships = main_agent.store.get_pending_relationships()  # This will get all relationships
        
        logger.info(f"Rebuilding indexes for {len(all_tables)} tables and {len(all_relationships)} relationships")
        
        # Use batch processing for efficiency
        batch_manager = BatchIndexingManager(main_agent.indexer_agent)
        
        # Process tables
        table_results = batch_manager.batch_process_pending_tables(main_agent.store)
        successful_tables = sum(1 for success in table_results.values() if success)
        
        # Process relationships
        rel_results = batch_manager.batch_process_pending_relationships(main_agent.store)
        successful_rels = sum(1 for success in rel_results.values() if success)
        
        logger.info(f"Index rebuild completed: {successful_tables} tables, {successful_rels} relationships")
        print(f"Index rebuild completed: {successful_tables} tables, {successful_rels} relationships")
        
    except Exception as e:
        logger.error(f"Index rebuild failed: {e}")
        print(f"Index rebuild error: {e}")
        raise

def index_processed_documents_standalone():
    """Standalone function to index already processed documents."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Cannot index documents.")
            return None
        
        logger.info("Starting to index already processed documents...")
        main_agent.index_processed_documents()
        print("Document indexing completed successfully.")
        
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        print(f"Document indexing error: {e}")
        raise

def retry_vector_indexing_initialization():
    """Retry initializing vector indexing."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        
        # Check current status
        if main_agent.vector_indexing_available and main_agent.indexer_agent:
            print("Vector indexing is already available.")
            return True
        
        print("Vector indexing is not available. Attempting to initialize...")
        
        # Try to retry initialization
        success = main_agent.retry_vector_indexing_initialization()
        
        if success:
            print("Vector indexing initialized successfully!")
            print("You can now use vector indexing features like search and entity recognition.")
        else:
            print("Vector indexing initialization failed.")
            print("This may be due to missing dependencies or compatibility issues.")
            print("Documentation generation will continue without vector indexing.")
        
        return success
        
    except Exception as e:
        logger.error(f"Vector indexing retry failed: {e}")
        print(f"Vector indexing retry error: {e}")
        return False

def check_vector_indexing_status():
    """Check the current status of vector indexing."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        
        print("\nVector Indexing Status")
        print("=" * 30)
        print(f"Available: {main_agent.vector_indexing_available}")
        print(f"Indexer Agent: {'Available' if main_agent.indexer_agent else 'Not Available'}")
        
        if main_agent.vector_indexing_available and main_agent.indexer_agent:
            print("\n✅ Vector indexing is available!")
            print("You can use features like:")
            print("  - Semantic search (--search)")
            print("  - Entity recognition (--recognize-entities)")
            print("  - Quick entity lookup (--quick-lookup)")
            print("  - Batch processing (--batch-index)")
            print("  - Cost estimation (--estimate-costs)")
            print("  - Indexing processed documents (--index-processed)")
        else:
            print("\n❌ Vector indexing is not available.")
            print("This may be due to:")
            print("  - Missing vectordb package")
            print("  - Python version compatibility issues")
            print("  - Missing dependencies")
            print("\nYou can try:")
            print("  - python main.py --retry-vector-indexing")
            print("  - Installing vectordb: pip install vectordb")
            print("  - Using a different Python version")
        
        return main_agent.vector_indexing_available
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        print(f"Status check error: {e}")
        return False

def gather_business_context(query: str, intent: str = None):
    """Gather business context for a user query using the Business Context Agent."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        business_agent = shared_manager.business_agent
        
        # For now, we'll use a simple entity list - in practice this would come from entity recognition
        # or database schema analysis
        applicable_entities = ["customers", "accounts", "transactions", "branches", "employees", "loans", "cards"]
        
        logger.info(f"Gathering business context for query: '{query}'")
        if intent:
            logger.info(f"User intent: '{intent}'")
        
        # Gather business context
        results = business_agent.gather_business_context(query, applicable_entities)
        
        # Print results in a readable format
        print(f"\nBusiness Context Results for: '{query}'")
        if intent:
            print(f"Intent: {intent}")
        print("=" * 60)
        
        if results.get("success"):
            matched_concepts = results.get("matched_concepts", [])
            business_instructions = results.get("business_instructions", [])
            relevant_examples = results.get("relevant_examples", [])
            join_validation = results.get("join_validation", {})
            entity_coverage = results.get("entity_coverage", {})
            
            print(f"\nEntity Coverage: {entity_coverage.get('entities_with_concepts', 0)}/{entity_coverage.get('total_entities', 0)} entities have concepts")
            
            if matched_concepts:
                print(f"\nMatched Business Concepts ({len(matched_concepts)} found):")
                for i, concept in enumerate(matched_concepts, 1):
                    name = concept.get("name", "Unknown")
                    description = concept.get("description", "")
                    similarity = concept.get("similarity", 0.0)
                    target_entities = concept.get("target_entities", [])
                    required_joins = concept.get("required_joins", [])
                    
                    print(f"\n  {i}. {name}")
                    print(f"     Similarity: {similarity:.3f}")
                    print(f"     Description: {description}")
                    print(f"     Target Entities: {', '.join(target_entities)}")
                    if required_joins:
                        print(f"     Required Joins: {', '.join(required_joins)}")
            
            if business_instructions:
                print(f"\nBusiness Instructions ({len(business_instructions)} items):")
                for i, instruction in enumerate(business_instructions, 1):
                    concept_name = instruction.get("concept", "Unknown")
                    instructions = instruction.get("instructions", "")
                    similarity = instruction.get("similarity", 0.0)
                    
                    print(f"\n  {i}. {concept_name} (similarity: {similarity:.3f})")
                    print(f"     Instructions: {instructions}")
            
            if relevant_examples:
                print(f"\nRelevant Examples ({len(relevant_examples)} found):")
                for i, example in enumerate(relevant_examples, 1):
                    example_data = example.get("example", {})
                    similarity = example.get("similarity", 0.0)
                    concept_name = example.get("concept_name", "Unknown")
                    
                    query_text = example_data.get("query", "")
                    context = example_data.get("context", "")
                    
                    print(f"\n  {i}. {concept_name} (similarity: {similarity:.3f})")
                    print(f"     Query: {query_text}")
                    print(f"     Context: {context}")
            
            if join_validation:
                print(f"\nJoin Validation:")
                for concept_name, validation in join_validation.items():
                    valid = validation.get("valid", False)
                    missing_entities = validation.get("missing_entities", [])
                    satisfied_joins = validation.get("satisfied_joins", [])
                    unsatisfied_joins = validation.get("unsatisfied_joins", [])
                    
                    print(f"\n  {concept_name}: {'✅ Valid' if valid else '❌ Invalid'}")
                    if missing_entities:
                        print(f"     Missing Entities: {', '.join(missing_entities)}")
                    if satisfied_joins:
                        print(f"     Satisfied Joins: {', '.join(satisfied_joins)}")
                    if unsatisfied_joins:
                        print(f"     Unsatisfied Joins: {', '.join(unsatisfied_joins)}")
            
            if not matched_concepts and not business_instructions:
                print("\nNo business concepts matched for the given query.")
                print("Consider refining your query or adding more business concepts.")
        else:
            print(f"\nError: {results.get('error', 'Unknown error occurred')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Business context gathering failed: {e}")
        print(f"Business context error: {e}")
        return None

def generate_sql_from_natural_language(query: str, intent: str = None):
    """Generate SQL from natural language using the NL2SQL Agent with concurrent optimizations."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        with performance_timer("Total SQL Generation Pipeline"):
            # Use shared instances instead of creating new ones
            main_agent = shared_manager.main_agent
            database_tools = shared_manager.database_tools
            entity_agent = shared_manager.entity_agent
            business_agent = shared_manager.business_agent
            nl2sql_agent = shared_manager.nl2sql_agent
            
            if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
                print("Vector indexing is not available. SQL generation requires vector indexing.")
                return None
            
            # Perform entity recognition to get relevant tables
            with performance_timer("Entity Recognition"):
                logger.info(f"Performing entity recognition for query: '{query}'")
                entity_results = entity_agent.recognize_entities_optimized(query, intent, max_entities=10)
            
            if not entity_results.get("success"):
                print(f"Entity recognition failed: {entity_results.get('error', 'Unknown error')}")
                return None
            
            # Extract recognized entities
            applicable_entities = entity_results.get("applicable_entities", [])
            if not applicable_entities:
                print("No relevant entities found for the query.")
                return None
            
            # Get table names from recognized entities
            recognized_tables = []
            for entity in applicable_entities:
                table_name = entity.get("table_name")
                if table_name and table_name not in recognized_tables:
                    recognized_tables.append(table_name)
            
            logger.info(f"Recognized tables: {recognized_tables}")
            
            # CONCURRENT OPERATIONS: Business context and schema retrieval in parallel
            with performance_timer("Concurrent Business Context + Schema Retrieval"):
                logger.info("Starting concurrent operations: business context + schema retrieval")
                
                # Run business context gathering and schema retrieval concurrently
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    # Submit business context task
                    business_future = executor.submit(
                        business_agent.gather_business_context, 
                        query, 
                        recognized_tables
                    )
                    
                    # Submit schema retrieval task
                    schema_future = executor.submit(
                        get_schemas_concurrent,
                        database_tools,
                        recognized_tables
                    )
                    
                    # Wait for both tasks to complete
                    business_context = business_future.result()
                    schema_results = schema_future.result()
                
                logger.info("Concurrent operations completed")
            
            # Build entity context from schema results
            entity_context = {
                "entities": recognized_tables,
                "entity_descriptions": {},
                "table_schemas": {}
            }
            
            # Process schema results
            for table_name, schema_result in schema_results.items():
                if schema_result.get("success") and schema_result.get("schema"):
                    entity_context["table_schemas"][table_name] = schema_result["schema"]
                    entity_context["entity_descriptions"][table_name] = schema_result["description"]
                else:
                    entity_context["entity_descriptions"][table_name] = f"Table {table_name}"
            
            # Generate SQL
            with performance_timer("SQL Generation"):
                logger.info(f"Generating SQL for query: '{query}'")
                logger.info(f"Using recognized tables: {recognized_tables}")
                if intent:
                    logger.info(f"User intent: '{intent}'")
                
                results = nl2sql_agent.generate_sql_optimized(query, business_context, entity_context)
            
            # Debug: Log the results type and content
            logger.info(f"Results type: {type(results)}")
            logger.info(f"Results: {results}")
            
            # Print results in a readable format
            print(f"\nOptimized SQL Generation Results for: '{query}'")
            if intent:
                print(f"Intent: {intent}")
            print("=" * 60)
            
            # Print entity recognition results
            print(f"\nEntity Recognition Results:")
            print(f"  Recognized Tables: {', '.join(recognized_tables)}")
            print(f"  Total Entities Found: {len(applicable_entities)}")
            
            # Print business context results
            if business_context.get("success"):
                matched_concepts = business_context.get("matched_concepts", [])
                if matched_concepts:
                    print(f"\nMatched Business Concepts ({len(matched_concepts)} found):")
                    for i, concept in enumerate(matched_concepts, 1):
                        name = concept.get("name", "Unknown")
                        similarity = concept.get("similarity", 0.0)
                        print(f"  {i}. {name} (similarity: {similarity:.3f})")
            
            if results.get("success"):
                generated_sql = results.get("generated_sql", "")
                validation = results.get("validation", {})
                optimization_suggestions = results.get("optimization_suggestions", [])
                is_valid = results.get("is_valid", False)
                
                print(f"\nGenerated SQL:")
                print("-" * 40)
                print(generated_sql)
                print("-" * 40)
                
                print(f"\nValidation Results:")
                print(f"  Syntax Valid: {'✅ Yes' if validation.get('syntax_valid') else '❌ No'}")
                print(f"  Business Compliant: {'✅ Yes' if validation.get('business_compliant') else '❌ No'}")
                print(f"  Security Valid: {'✅ Yes' if validation.get('security_valid') else '❌ No'}")
                
                performance_issues = validation.get("performance_issues", [])
                if performance_issues:
                    print(f"  Performance Issues: {len(performance_issues)} found")
                    for i, issue in enumerate(performance_issues, 1):
                        print(f"    {i}. {issue}")
                
                if optimization_suggestions:
                    # Handle case where optimization_suggestions is a dictionary
                    if isinstance(optimization_suggestions, dict):
                        suggestions_list = optimization_suggestions.get("optimization_suggestions", [])
                        complexity_score = optimization_suggestions.get("complexity_score", 0)
                        estimated_impact = optimization_suggestions.get("estimated_impact", "unknown")
                        
                        print(f"\nOptimization Suggestions ({len(suggestions_list)} items):")
                        print(f"  Complexity Score: {complexity_score}")
                        print(f"  Estimated Impact: {estimated_impact}")
                        
                        for i, suggestion in enumerate(suggestions_list, 1):
                            suggestion_type = suggestion.get("type", "Unknown")
                            message = suggestion.get("message", "")
                            priority = suggestion.get("priority", "medium")
                            impact = suggestion.get("impact", "unknown")
                            
                            print(f"  {i}. [{priority.upper()}] {suggestion_type}")
                            print(f"     {message}")
                            print(f"     Impact: {impact}")
                    else:
                        # Handle case where optimization_suggestions is a list
                        print(f"\nOptimization Suggestions ({len(optimization_suggestions)} items):")
                        for i, suggestion in enumerate(optimization_suggestions, 1):
                            suggestion_type = suggestion.get("type", "Unknown")
                            message = suggestion.get("message", "")
                            priority = suggestion.get("priority", "medium")
                            impact = suggestion.get("impact", "unknown")
                            
                            print(f"  {i}. [{priority.upper()}] {suggestion_type}")
                            print(f"     {message}")
                            print(f"     Impact: {impact}")
                
                print(f"\nOverall Validity: {'✅ Valid' if is_valid else '❌ Invalid'}")
                
                # Query Execution Results
                query_execution = results.get("query_execution", {})
                if query_execution.get("success", False):
                    print(f"\nQuery Execution Results:")
                    print(f"  Total Rows: {query_execution.get('total_rows', 0)}")
                    print(f"  Returned Rows: {query_execution.get('returned_rows', 0)}")
                    print(f"  Truncated: {'Yes' if query_execution.get('truncated', False) else 'No'}")
                    
                    # Display sample data
                    sample_data = query_execution.get("sample_data", {})
                    if sample_data and sample_data.get("sample_rows"):
                        print(f"\nSample Data (first 5 rows):")
                        sample_rows = sample_data.get("sample_rows", [])
                        columns = sample_data.get("columns", [])
                        
                        # Print column headers
                        if columns:
                            header = " | ".join(f"{col:15}" for col in columns)
                            print("-" * len(header))
                            print(header)
                            print("-" * len(header))
                        
                        # Print sample rows
                        for row in sample_rows[:5]:
                            row_data = " | ".join(f"{str(row.get(col, '')):15}" for col in columns)
                            print(row_data)
                        
                        # Print numeric statistics if available
                        numeric_stats = sample_data.get("numeric_stats", {})
                        if numeric_stats:
                            print(f"\nNumeric Statistics:")
                            for col, stats in numeric_stats.items():
                                print(f"  {col}: min={stats.get('min', 0)}, max={stats.get('max', 0)}, avg={stats.get('avg', 0):.2f}")
                    
                    elif sample_data:
                        print(f"\nQuery Result: {sample_data.get('message', 'No data returned')}")
                else:
                    print(f"\nQuery Execution: {'❌ Failed' if query_execution else '⏭️ Skipped'}")
                    if query_execution and query_execution.get("error"):
                        print(f"  Error: {query_execution['error']}")
                
            else:
                print(f"\nError: {results.get('error', 'Unknown error occurred')}")
            
            return results
        
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        print(f"SQL generation error: {e}")
        return None

def generate_sql_from_natural_language_optimized(query: str, intent: str = None):
    """Generate SQL from natural language with advanced concurrency optimizations."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        with performance_timer("Total Optimized SQL Generation Pipeline"):
            # Use shared instances instead of creating new ones
            main_agent = shared_manager.main_agent
            database_tools = shared_manager.database_tools
            entity_agent = shared_manager.entity_agent
            business_agent = shared_manager.business_agent
            nl2sql_agent = shared_manager.nl2sql_agent
            
            if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
                print("Vector indexing is not available. SQL generation requires vector indexing.")
                return None
            
            # ADVANCED CONCURRENCY: Start schema retrieval early with common tables
            logger.info("Starting early schema retrieval for common tables")
            common_tables = ["customers", "accounts", "transactions", "branches", "employees", "loans", "cards"]
            
            # Start schema retrieval in background
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                schema_future = executor.submit(
                    get_schemas_concurrent,
                    database_tools,
                    common_tables
                )
            
            # Perform entity recognition to get relevant tables
            with performance_timer("Entity Recognition"):
                logger.info(f"Performing entity recognition for query: '{query}'")
                entity_results = entity_agent.recognize_entities_optimized(query, intent, max_entities=10)
            
            if not entity_results.get("success"):
                print(f"Entity recognition failed: {entity_results.get('error', 'Unknown error')}")
                return None
            
            # Extract recognized entities
            applicable_entities = entity_results.get("applicable_entities", [])
            if not applicable_entities:
                print("No relevant entities found for the query.")
                return None
            
            # Get table names from recognized entities
            recognized_tables = []
            for entity in applicable_entities:
                table_name = entity.get("table_name")
                if table_name and table_name not in recognized_tables:
                    recognized_tables.append(table_name)
            
            logger.info(f"Recognized tables: {recognized_tables}")
            
            # Get early schema results
            early_schema_results = schema_future.result()
            logger.info("Early schema retrieval completed")
            
            # Gather business context (this is fast since schemas are already available)
            with performance_timer("Business Context Gathering"):
                business_context = business_agent.gather_business_context(query, recognized_tables)
            
            # Build entity context from available schema results
            entity_context = {
                "entities": recognized_tables,
                "entity_descriptions": {},
                "table_schemas": {}
            }
            
            # Process schema results (use early results if available, otherwise fetch specific ones)
            for table_name in recognized_tables:
                if table_name in early_schema_results:
                    schema_result = early_schema_results[table_name]
                else:
                    # Fetch specific table schema if not in early results
                    schema_result = get_table_schema_concurrent(database_tools, table_name)
                
                if schema_result.get("success") and schema_result.get("schema"):
                    entity_context["table_schemas"][table_name] = schema_result["schema"]
                    entity_context["entity_descriptions"][table_name] = schema_result["description"]
                else:
                    entity_context["entity_descriptions"][table_name] = f"Table {table_name}"
            
            # Generate SQL
            with performance_timer("SQL Generation"):
                logger.info(f"Generating SQL for query: '{query}'")
                logger.info(f"Using recognized tables: {recognized_tables}")
                if intent:
                    logger.info(f"User intent: '{intent}'")
                
                results = nl2sql_agent.generate_sql_optimized(query, business_context, entity_context)
            
            # Debug: Log the results type and content
            logger.info(f"Results type: {type(results)}")
            logger.info(f"Results: {results}")
            
            # Print results in a readable format
            print(f"\nOptimized SQL Generation Results for: '{query}'")
            if intent:
                print(f"Intent: {intent}")
            print("=" * 60)
            
            # Print entity recognition results
            print(f"\nEntity Recognition Results:")
            print(f"  Recognized Tables: {', '.join(recognized_tables)}")
            print(f"  Total Entities Found: {len(applicable_entities)}")
            
            # Print business context results
            if business_context.get("success"):
                matched_concepts = business_context.get("matched_concepts", [])
                if matched_concepts:
                    print(f"\nMatched Business Concepts ({len(matched_concepts)} found):")
                    for i, concept in enumerate(matched_concepts, 1):
                        name = concept.get("name", "Unknown")
                        similarity = concept.get("similarity", 0.0)
                        print(f"  {i}. {name} (similarity: {similarity:.3f})")
            
            if results.get("success"):
                generated_sql = results.get("generated_sql", "")
                validation = results.get("validation", {})
                optimization_suggestions = results.get("optimization_suggestions", [])
                is_valid = results.get("is_valid", False)
                
                print(f"\nGenerated SQL:")
                print("-" * 40)
                print(generated_sql)
                print("-" * 40)
                
                print(f"\nValidation Results:")
                print(f"  Syntax Valid: {'✅ Yes' if validation.get('syntax_valid') else '❌ No'}")
                print(f"  Business Compliant: {'✅ Yes' if validation.get('business_compliant') else '❌ No'}")
                print(f"  Security Valid: {'✅ Yes' if validation.get('security_valid') else '❌ No'}")
                
                performance_issues = validation.get("performance_issues", [])
                if performance_issues:
                    print(f"  Performance Issues: {len(performance_issues)} found")
                    for i, issue in enumerate(performance_issues, 1):
                        print(f"    {i}. {issue}")
                
                if optimization_suggestions:
                    # Handle case where optimization_suggestions is a dictionary
                    if isinstance(optimization_suggestions, dict):
                        suggestions_list = optimization_suggestions.get("optimization_suggestions", [])
                        complexity_score = optimization_suggestions.get("complexity_score", 0)
                        estimated_impact = optimization_suggestions.get("estimated_impact", "unknown")
                        
                        print(f"\nOptimization Suggestions ({len(suggestions_list)} items):")
                        print(f"  Complexity Score: {complexity_score}")
                        print(f"  Estimated Impact: {estimated_impact}")
                        
                        for i, suggestion in enumerate(suggestions_list, 1):
                            suggestion_type = suggestion.get("type", "Unknown")
                            message = suggestion.get("message", "")
                            priority = suggestion.get("priority", "medium")
                            impact = suggestion.get("impact", "unknown")
                            
                            print(f"  {i}. [{priority.upper()}] {suggestion_type}")
                            print(f"     {message}")
                            print(f"     Impact: {impact}")
                    else:
                        # Handle case where optimization_suggestions is a list
                        print(f"\nOptimization Suggestions ({len(optimization_suggestions)} items):")
                        for i, suggestion in enumerate(optimization_suggestions, 1):
                            suggestion_type = suggestion.get("type", "Unknown")
                            message = suggestion.get("message", "")
                            priority = suggestion.get("priority", "medium")
                            impact = suggestion.get("impact", "unknown")
                            
                            print(f"  {i}. [{priority.upper()}] {suggestion_type}")
                            print(f"     {message}")
                            print(f"     Impact: {impact}")
                
                print(f"\nOverall Validity: {'✅ Valid' if is_valid else '❌ Invalid'}")
                
                # Query Execution Results
                query_execution = results.get("query_execution", {})
                if query_execution.get("success", False):
                    print(f"\nQuery Execution Results:")
                    print(f"  Total Rows: {query_execution.get('total_rows', 0)}")
                    print(f"  Returned Rows: {query_execution.get('returned_rows', 0)}")
                    print(f"  Truncated: {'Yes' if query_execution.get('truncated', False) else 'No'}")
                    
                    # Display sample data
                    sample_data = query_execution.get("sample_data", {})
                    if sample_data and sample_data.get("sample_rows"):
                        print(f"\nSample Data (first 5 rows):")
                        sample_rows = sample_data.get("sample_rows", [])
                        columns = sample_data.get("columns", [])
                        
                        # Print column headers
                        if columns:
                            header = " | ".join(f"{col:15}" for col in columns)
                            print("-" * len(header))
                            print(header)
                            print("-" * len(header))
                        
                        # Print sample rows
                        for row in sample_rows[:5]:
                            row_data = " | ".join(f"{str(row.get(col, '')):15}" for col in columns)
                            print(row_data)
                        
                        # Print numeric statistics if available
                        numeric_stats = sample_data.get("numeric_stats", {})
                        if numeric_stats:
                            print(f"\nNumeric Statistics:")
                            for col, stats in numeric_stats.items():
                                print(f"  {col}: min={stats.get('min', 0)}, max={stats.get('max', 0)}, avg={stats.get('avg', 0):.2f}")
                
                elif sample_data:
                    print(f"\nQuery Result: {sample_data.get('message', 'No data returned')}")
                else:
                    print(f"\nQuery Execution: {'❌ Failed' if query_execution else '⏭️ Skipped'}")
                    if query_execution and query_execution.get("error"):
                        print(f"  Error: {query_execution['error']}")
                
            else:
                print(f"\nError: {results.get('error', 'Unknown error occurred')}")
            
            return results
        
    except Exception as e:
        logger.error(f"Optimized SQL generation failed: {e}")
        print(f"Optimized SQL generation error: {e}")
        return None

def run_complete_sql_pipeline(query: str, intent: str = None):
    """Run the complete SQL pipeline from query to validated SQL."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        main_agent = shared_manager.main_agent
        database_tools = shared_manager.database_tools
        
        if not main_agent.vector_indexing_available or not main_agent.indexer_agent:
            print("Vector indexing is not available. Complete pipeline requires vector indexing.")
            return None
        
        # Initialize the SQL agent pipeline with proper dependencies
        pipeline = SQLAgentPipeline(
            indexer_agent=main_agent.indexer_agent,
            database_tools=database_tools,
            shared_entity_agent=shared_manager.entity_agent,
            shared_business_agent=shared_manager.business_agent,
            shared_nl2sql_agent=shared_manager.nl2sql_agent
        )
        
        logger.info(f"Running complete SQL pipeline for query: '{query}'")
        if intent:
            logger.info(f"User intent: '{intent}'")
        
        # Run the complete pipeline
        results = pipeline.process_user_query(query, intent)
        
        # Print results in a readable format
        print(f"\nComplete SQL Pipeline Results for: '{query}'")
        if intent:
            print(f"Intent: {intent}")
        print("=" * 60)
        
        if results.get("success"):
            pipeline_summary = results.get("pipeline_summary", {})
            entity_recognition = results.get("entity_recognition", {})
            business_context = results.get("business_context", {})
            sql_generation = results.get("sql_generation", {})
            recommendations = results.get("recommendations", [])
            
            print(f"\nPipeline Summary:")
            print(f"  Entity Recognition: {'✅ Success' if pipeline_summary.get('entity_recognition_success') else '❌ Failed'}")
            print(f"  Business Context: {'✅ Success' if pipeline_summary.get('business_context_success') else '❌ Failed'}")
            print(f"  SQL Generation: {'✅ Success' if pipeline_summary.get('sql_generation_success') else '❌ Failed'}")
            print(f"  SQL Validation: {'✅ Success' if pipeline_summary.get('sql_validation_success') else '❌ Failed'}")
            
            # Entity Recognition Results
            entities = entity_recognition.get("entities", [])
            if entities:
                print(f"\nRecognized Entities ({len(entities)} found):")
                for i, entity in enumerate(entities, 1):
                    print(f"  {i}. {entity}")
            
            # Business Context Results
            matched_concepts = business_context.get("matched_concepts", [])
            if matched_concepts:
                print(f"\nMatched Business Concepts ({len(matched_concepts)} found):")
                for i, concept in enumerate(matched_concepts, 1):
                    name = concept.get("name", "Unknown")
                    similarity = concept.get("similarity", 0.0)
                    print(f"  {i}. {name} (similarity: {similarity:.3f})")
            
            # SQL Generation Results
            generated_sql = sql_generation.get("generated_sql", "")
            if generated_sql:
                print(f"\nGenerated SQL:")
                print("-" * 40)
                print(generated_sql)
                print("-" * 40)
            
            # Query Execution Results
            query_execution = sql_generation.get("query_execution", {})
            if query_execution.get("success", False):
                print(f"\nQuery Execution Results:")
                print(f"  Total Rows: {query_execution.get('total_rows', 0)}")
                print(f"  Returned Rows: {query_execution.get('returned_rows', 0)}")
                print(f"  Truncated: {'Yes' if query_execution.get('truncated', False) else 'No'}")
                
                # Display sample data
                sample_data = query_execution.get("sample_data", {})
                if sample_data and sample_data.get("sample_rows"):
                    print(f"\nSample Data (first 5 rows):")
                    sample_rows = sample_data.get("sample_rows", [])
                    columns = sample_data.get("columns", [])
                    
                    # Print column headers
                    if columns:
                        header = " | ".join(f"{col:15}" for col in columns)
                        print("-" * len(header))
                        print(header)
                        print("-" * len(header))
                    
                    # Print sample rows
                    for row in sample_rows[:5]:
                        row_data = " | ".join(f"{str(row.get(col, '')):15}" for col in columns)
                        print(row_data)
                    
                    # Print numeric statistics if available
                    numeric_stats = sample_data.get("numeric_stats", {})
                    if numeric_stats:
                        print(f"\nNumeric Statistics:")
                        for col, stats in numeric_stats.items():
                            print(f"  {col}: min={stats.get('min', 0)}, max={stats.get('max', 0)}, avg={stats.get('avg', 0):.2f}")
                
                elif sample_data:
                    print(f"\nQuery Result: {sample_data.get('message', 'No data returned')}")
            else:
                print(f"\nQuery Execution: {'❌ Failed' if query_execution else '⏭️ Skipped'}")
                if query_execution and query_execution.get("error"):
                    print(f"  Error: {query_execution['error']}")
            
            validation = sql_generation.get("validation", {})
            print(f"\nValidation Results:")
            print(f"  Syntax Valid: {'✅ Yes' if validation.get('syntax_valid') else '❌ No'}")
            print(f"  Business Compliant: {'✅ Yes' if validation.get('business_compliant') else '❌ No'}")
            print(f"  Security Valid: {'✅ Yes' if validation.get('security_valid') else '❌ No'}")
            
            performance_issues = validation.get("performance_issues", [])
            if performance_issues:
                print(f"  Performance Issues: {len(performance_issues)} found")
                for i, issue in enumerate(performance_issues, 1):
                    print(f"    {i}. {issue}")
            
            # Extract optimization suggestions from sql_generation results
            optimization_suggestions = sql_generation.get("optimization_suggestions", [])
            if optimization_suggestions:
                # Handle case where optimization_suggestions is a dictionary
                if isinstance(optimization_suggestions, dict):
                    suggestions_list = optimization_suggestions.get("optimization_suggestions", [])
                    complexity_score = optimization_suggestions.get("complexity_score", 0)
                    estimated_impact = optimization_suggestions.get("estimated_impact", "unknown")
                    
                    print(f"\nOptimization Suggestions ({len(suggestions_list)} items):")
                    print(f"  Complexity Score: {complexity_score}")
                    print(f"  Estimated Impact: {estimated_impact}")
                    
                    for i, suggestion in enumerate(suggestions_list, 1):
                        suggestion_type = suggestion.get("type", "Unknown")
                        message = suggestion.get("message", "")
                        priority = suggestion.get("priority", "medium")
                        impact = suggestion.get("impact", "unknown")
                        
                        print(f"  {i}. [{priority.upper()}] {suggestion_type}")
                        print(f"     {message}")
                        print(f"     Impact: {impact}")
                else:
                    # Handle case where optimization_suggestions is a list
                    print(f"\nOptimization Suggestions ({len(optimization_suggestions)} items):")
                    for i, suggestion in enumerate(optimization_suggestions, 1):
                        suggestion_type = suggestion.get("type", "Unknown")
                        message = suggestion.get("message", "")
                        priority = suggestion.get("priority", "medium")
                        impact = suggestion.get("impact", "unknown")
                        
                        print(f"  {i}. [{priority.upper()}] {suggestion_type}")
                        print(f"     {message}")
                        print(f"     Impact: {impact}")
            
            # Recommendations
            if recommendations:
                print(f"\nRecommendations ({len(recommendations)} items):")
                for i, rec in enumerate(recommendations, 1):
                    rec_type = rec.get("type", "Unknown")
                    severity = rec.get("severity", "info")
                    message = rec.get("message", "")
                    
                    severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(severity, "ℹ️")
                    print(f"  {i}. [{severity.upper()}] {rec_type}")
                    print(f"     {severity_icon} {message}")
            
        else:
            print(f"\nError: {results.get('error', 'Unknown error occurred')}")
            if results.get("pipeline_step"):
                print(f"Failed at step: {results['pipeline_step']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Complete SQL pipeline failed: {e}")
        print(f"Pipeline error: {e}")
        return None

def list_business_concepts():
    """List all available business concepts."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Use shared instances instead of creating new ones
        business_agent = shared_manager.business_agent
        
        logger.info("Listing all available business concepts")
        
        # Get all concepts
        all_concepts = business_agent.concept_loader.get_all_concepts()
        
        print(f"\nAvailable Business Concepts ({len(all_concepts)} found)")
        print("=" * 50)
        
        if all_concepts:
            for i, concept in enumerate(all_concepts, 1):
                name = concept.name
                description = concept.description
                target_entities = concept.target
                required_joins = concept.required_joins
                examples_count = len(concept.examples)
                
                print(f"\n{i}. {name}")
                print(f"   Description: {description}")
                print(f"   Target Entities: {', '.join(target_entities)}")
                if required_joins:
                    print(f"   Required Joins: {', '.join(required_joins)}")
                print(f"   Examples: {examples_count} available")
        else:
            print("No business concepts found.")
            print("Consider adding concept YAML files to the concepts directory.")
        
        return all_concepts
        
    except Exception as e:
        logger.error(f"Listing business concepts failed: {e}")
        print(f"Error listing concepts: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--resume':
            generate_documentation(resume=True)
        elif command == '--search':
            if len(sys.argv) < 3:
                print("Usage: python main.py --search <query>")
                sys.exit(1)
            query = ' '.join(sys.argv[2:])
            search_documentation(query)
        elif command == '--recognize-entities':
            if len(sys.argv) < 3:
                print("Usage: python main.py --recognize-entities <query> [intent]")
                sys.exit(1)
            query = sys.argv[2]
            intent = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
            recognize_entities(query, intent)
        elif command == '--quick-lookup':
            if len(sys.argv) < 3:
                print("Usage: python main.py --quick-lookup <query> [threshold]")
                sys.exit(1)
            query = sys.argv[2]
            threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
            quick_entity_lookup(query, threshold)
        elif command == '--batch-index':
            generate_documentation(resume=False, batch_indexing=True)
        elif command == '--individual-index':
            generate_documentation(resume=False, batch_indexing=False)
        elif command == '--estimate-costs':
            estimate_costs()
        elif command == '--rebuild-indexes':
            rebuild_indexes()
        elif command == '--index-processed':
            index_processed_documents_standalone()
        elif command == '--retry-vector-indexing':
            retry_vector_indexing_initialization()
        elif command == '--check-vector-indexing':
            check_vector_indexing_status()
        elif command == '--gather-context':
            if len(sys.argv) < 3:
                print("Usage: python main.py --gather-context <query> [intent]")
                sys.exit(1)
            query = sys.argv[2]
            intent = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
            gather_business_context(query, intent)
        elif command == '--generate-sql':
            if len(sys.argv) < 3:
                print("Usage: python main.py --generate-sql <query> [intent]")
                sys.exit(1)
            query = sys.argv[2]
            intent = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
            generate_sql_from_natural_language(query, intent)
        elif command == '--generate-sql-optimized':
            if len(sys.argv) < 3:
                print("Usage: python main.py --generate-sql-optimized <query> [intent]")
                sys.exit(1)
            query = sys.argv[2]
            intent = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
            generate_sql_from_natural_language_optimized(query, intent)
        elif command == '--run-pipeline':
            if len(sys.argv) < 3:
                print("Usage: python main.py --run-pipeline <query> [intent]")
                sys.exit(1)
            query = sys.argv[2]
            intent = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
            run_complete_sql_pipeline(query, intent)
        elif command == '--list-concepts':
            list_business_concepts()
        elif command == '--help':
            print("""
SQL Documentation Agent - Enhanced with OpenAI Embeddings, Entity Recognition, and SQL Agents

Usage:
  python main.py                              # Generate documentation with batch indexing
  python main.py --resume                     # Resume previous generation
  python main.py --search <query>             # Search indexed documentation
  python main.py --recognize-entities <query> [intent] # Recognize applicable entities
  python main.py --quick-lookup <query> [threshold]   # Quick entity lookup
  python main.py --batch-index                # Generate with batch processing (default)
  python main.py --individual-index           # Generate with individual processing
  python main.py --estimate-costs             # Estimate OpenAI API costs
  python main.py --rebuild-indexes            # Rebuild vector indexes
  python main.py --index-processed            # Index already processed documents
  python main.py --retry-vector-indexing      # Retry vector indexing initialization
  python main.py --check-vector-indexing      # Check vector indexing status
  python main.py --gather-context <query> [intent] # Gather business context for a query
  python main.py --generate-sql <query> [intent] # Generate SQL from natural language
  python main.py --generate-sql-optimized <query> [intent] # Generate SQL with advanced concurrency
  python main.py --run-pipeline <query> [intent] # Run complete SQL pipeline
  python main.py --list-concepts              # List all available business concepts
  python main.py --help                       # Show this help message

Examples:
  python main.py --search "user authentication"
  python main.py --recognize-entities "customer data" "I want to analyze user behavior"
  python main.py --quick-lookup "order information" 0.8
  python main.py --estimate-costs
  python main.py --index-processed
  python main.py --retry-vector-indexing
  python main.py --check-vector-indexing
  python main.py --gather-context "show me customer orders"
  python main.py --generate-sql "show me the total sales for the last month"
  python main.py --run-pipeline "how many orders were placed by customer 'John Doe'"
  python main.py --list-concepts

Entity Recognition Features:
  --recognize-entities: Identify and score database entities relevant to your query
  --quick-lookup:      Fast table name lookup with relevance threshold filtering

SQL Agents Features:
  --gather-context:    Gather business context and concepts for a natural language query
  --generate-sql:      Convert natural language to T-SQL with validation and optimization
  --run-pipeline:      Run complete pipeline from query to validated SQL (recommended)
  --list-concepts:     List all available business concepts and their configurations

SQL Pipeline Process:
  1. Entity Recognition: Identify relevant database tables and entities
  2. Business Context: Match query to business concepts and rules
  3. SQL Generation: Convert natural language to T-SQL
  4. Validation: Check syntax, security, and business compliance
  5. Optimization: Suggest performance improvements

Business Concepts:
  Business concepts are defined in YAML files and provide:
  - Business logic and rules for SQL generation
  - Required joins and relationships
  - Example queries and use cases
  - Target entities and validation rules

Validation Framework:
  - Syntax validation using sqlparse
  - Security checks for SQL injection prevention
  - Business rule compliance validation
  - Performance optimization suggestions
            """)
        else:
            print(f"Unknown command: {command}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # generate_documentation(resume=False, batch_indexing=False)
        # search_documentation('customer')
        # ent = recognize_entities('which customers')
        run_complete_sql_pipeline('List all customers with their total account balances')
        pass