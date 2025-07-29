import json
import logging
from typing import Dict, List, Any
from smolagents.tools import tool

# Import base classes
from .base import BaseAgent
from ..database.inspector import DatabaseInspector
from ..database.persistence import DocumentationStore
from ..agents.indexer import SQLIndexerAgent
from ..vector.store import SQLVectorStore
from .tools.factory import DatabaseToolsFactory

logger = logging.getLogger(__name__)

class PersistentDocumentationAgent(BaseAgent):
    """Streamlined core documentation agent with consistent dictionary returns."""
    
    def __init__(self, shared_llm_model=None):
        # Initialize agent-specific components
        self.db_inspector = DatabaseInspector()
        self.store = DocumentationStore()
        
        # Initialize unified database tools
        self.database_tools = DatabaseToolsFactory.create_database_tools(self.db_inspector)
        
        # Initialize vector store with error handling
        try:
            self.indexer_agent = SQLIndexerAgent(SQLVectorStore(), shared_llm_model=shared_llm_model)
            self.vector_indexing_available = True
            logger.info("Vector indexing initialized successfully")
        except Exception as e:
            logger.warning(f"Vector indexing not available: {e}")
            self.indexer_agent = None
            self.vector_indexing_available = False
        
        # Initialize base agent with unified database tools
        super().__init__(
            shared_llm_model=shared_llm_model,
            additional_imports=['json'],
            agent_name="Core Documentation Agent",
            database_tools=self.database_tools
        )
    
    def _setup_agent_components(self):
        """Setup agent-specific components."""
        pass
    
    def _setup_tools(self):
        """Setup essential documentation tools."""
        self.tools = []
        
        # Database tools will be integrated automatically by BaseAgent
        # No need to manually add them here
    
    def process_table_documentation(self, table_name: str):
        """Process and index documentation for a single table."""
        logger.info(f"Processing table: {table_name}")
        
        prompt = f"""
        Generate documentation for database table: {table_name}
        
        Steps:
        1. Call get_table_schema_unified_tool("{table_name}") to get table schema
        2. Analyze table name and columns to infer business purpose
        3. Return JSON with business purpose and schema data
        
        Return JSON format:
        {{
            "business_purpose": "Clear description of table's purpose",
            "schema_data": {{ 
                "table_name": "name",
                "columns": [...]
            }}
        }}

        Use Python syntax: True/False (not true/false).
        Return valid JSON only.
        """
        
        try:
            result = self.agent.run(prompt)
            
            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for table {table_name}")
                    raise ValueError(f"Invalid JSON response for table {table_name}")
            
            if not isinstance(result, dict):
                logger.error(f"Expected dict for table {table_name}, got {type(result)}")
                raise ValueError(f"Invalid response type for table {table_name}")
            
            # Validate required fields
            if "business_purpose" not in result or "schema_data" not in result:
                logger.error(f"Missing required fields for table {table_name}")
                raise ValueError(f"Missing required fields for table {table_name}")
            
            # Ensure proper types
            if not isinstance(result["business_purpose"], str):
                result["business_purpose"] = str(result["business_purpose"])
            if not isinstance(result["schema_data"], dict):
                raise ValueError(f"schema_data must be dict for table {table_name}")
            
            business_purpose = result["business_purpose"]
            schema_data = result["schema_data"]
            documentation = f"## {table_name}\n\n{business_purpose}"
            
            # Save to documentation store
            self.store.save_table_documentation(
                table_name, schema_data, business_purpose, documentation
            )
            
            # Index with vector store if available
            if self.vector_indexing_available and self.indexer_agent:
                try:
                    self._index_processed_table(table_name, result)
                except Exception as e:
                    logger.error(f"Vector indexing failed for table {table_name}: {e}")
            else:
                logger.info(f"Skipping vector indexing for table {table_name}")
            
            logger.info(f"Completed processing table: {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to process table {table_name}: {e}")
            raise
    
    def process_relationship_documentation(self, relationship: dict):
        """Process and index documentation for a single relationship."""
        rel_id = relationship['id']
        logger.info(f"Processing relationship: {rel_id}")
        
        prompt = f"""
        Analyze this database relationship and generate documentation:
        
        From: {relationship['constrained_table']}.{relationship['constrained_columns']}
        To: {relationship['referred_table']}.{relationship['referred_columns']}
        
        Return JSON format:
        {{
            "relationship_type": "one-to-one|one-to-many|many-to-many",
            "documentation": "Clear explanation of business relationship"
        }}

        Use Python syntax: True/False (not true/false).
        Return valid JSON only.
        """
        
        try:
            result = self.agent.run(prompt)
            
            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for relationship {rel_id}")
                    raise ValueError(f"Invalid JSON response for relationship {rel_id}")
            
            if not isinstance(result, dict):
                logger.error(f"Expected dict for relationship {rel_id}, got {type(result)}")
                raise ValueError(f"Invalid response type for relationship {rel_id}")
            
            # Validate required fields
            if "relationship_type" not in result or "documentation" not in result:
                logger.error(f"Missing required fields for relationship {rel_id}")
                raise ValueError(f"Missing required fields for relationship {rel_id}")
            
            # Ensure proper types
            if not isinstance(result["relationship_type"], str):
                result["relationship_type"] = str(result["relationship_type"])
            if not isinstance(result["documentation"], str):
                result["documentation"] = str(result["documentation"])
            
            relationship_type = result["relationship_type"]
            documentation = result["documentation"]
            
            # Save to documentation store
            self.store.save_relationship_documentation(
                rel_id, relationship_type, documentation
            )
            
            # Index with vector store if available
            if self.vector_indexing_available and self.indexer_agent:
                try:
                    self._index_processed_relationship(relationship, result)
                except Exception as e:
                    logger.error(f"Vector indexing failed for relationship {rel_id}: {e}")
            else:
                logger.info(f"Skipping vector indexing for relationship {rel_id}")
            
            logger.info(f"Completed processing relationship: {rel_id}")
            
        except Exception as e:
            logger.error(f"Failed to process relationship {rel_id}: {e}")
            raise
            
    def _index_processed_table(self, table_name: str, data: dict):
        """Index table documentation using vector store."""
        try:
            table_data = {
                "name": table_name,
                "business_purpose": data["business_purpose"],
                "schema": data["schema_data"],
                "type": "table"
            }
            
            success = self.indexer_agent.index_table_documentation(table_data)
            if not success:
                raise ValueError(f"Failed to index table documentation for {table_name}")
                
        except Exception as e:
            logger.error(f"Failed to index table documentation for {table_name}: {e}")
            raise
            
    def _index_processed_relationship(self, relationship: dict, data: dict):
        """Index relationship documentation using vector store."""
        try:
            rel_id = str(relationship["id"])
            rel_name = f"{relationship['constrained_table']}_{relationship['referred_table']}_rel"
            
            rel_data = {
                "name": rel_name,
                "type": data["relationship_type"],
                "documentation": data["documentation"],
                "tables": [relationship["constrained_table"], relationship["referred_table"]],
                "doc_type": "relationship"
            }
            
            success = self.indexer_agent.index_relationship_documentation(rel_data)
            if not success:
                raise ValueError(f"Failed to index relationship documentation for {rel_name}")
                
        except Exception as e:
            logger.error(f"Failed to index relationship documentation for {relationship['id']}: {e}")
            raise
    
    def index_processed_documents(self):
        """Index all processed documents that haven't been indexed yet."""
        if not self.vector_indexing_available or not self.indexer_agent:
            logger.warning("Vector indexing not available")
            return
        
        logger.info("Indexing processed documents...")
        
        # Get all processed tables and relationships
        all_tables = self.store.get_all_tables()
        all_relationships = self.store.get_all_relationships()
        
        logger.info(f"Found {len(all_tables)} tables and {len(all_relationships)} relationships")
        
        # Index tables
        indexed_tables = 0
        for table_name in all_tables:
            try:
                table_info = self.store.get_table_info(table_name)
                if table_info:
                    table_data = {
                        "name": table_name,
                        "business_purpose": table_info.get("business_purpose", ""),
                        "schema": table_info.get("schema_data", {}),
                        "type": "table"
                    }
                    
                    success = self.indexer_agent.index_table_documentation(table_data)
                    if success:
                        indexed_tables += 1
                        
            except Exception as e:
                logger.error(f"Error indexing table {table_name}: {e}")
        
        # Index relationships
        indexed_relationships = 0
        for relationship in all_relationships:
            try:
                rel_id = relationship.get("id", "unknown")
                rel_info = self.store.get_relationship_info(rel_id)
                
                if rel_info:
                    rel_data = {
                        "id": rel_id,
                        "name": rel_id,
                        "type": rel_info.get("relationship_type", ""),
                        "documentation": rel_info.get("documentation", ""),
                        "tables": [relationship.get("constrained_table"), relationship.get("referred_table")],
                        "doc_type": "relationship"
                    }
                    
                    success = self.indexer_agent.index_relationship_documentation(rel_data)
                    if success:
                        indexed_relationships += 1
                        
            except Exception as e:
                logger.error(f"Error indexing relationship {rel_id}: {e}")
        
        logger.info(f"Indexing completed: {indexed_tables} tables, {indexed_relationships} relationships")
    
    def retry_vector_indexing_initialization(self):
        """Retry initializing vector indexing if previously unavailable."""
        if self.vector_indexing_available and self.indexer_agent:
            logger.info("Vector indexing already available")
            return True
        
        try:
            logger.info("Attempting to initialize vector indexing...")
            self.indexer_agent = SQLIndexerAgent(SQLVectorStore(), shared_llm_model=self.llm_model)
            self.vector_indexing_available = True
            logger.info("Vector indexing initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Vector indexing initialization failed: {e}")
            self.indexer_agent = None
            self.vector_indexing_available = False
            return False