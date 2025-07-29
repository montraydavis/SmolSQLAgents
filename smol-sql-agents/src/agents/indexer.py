import json
import logging
import os
from typing import Dict, List, Optional, Any

# Import smolagents components
from smolagents.agents import CodeAgent
from smolagents.models import OpenAIModel
from smolagents.tools import tool

# Import vector components
from ..vector.store import SQLVectorStore

logger = logging.getLogger(__name__)

class SQLIndexerAgent:
    """Streamlined vector indexing agent with consistent dictionary returns."""
    
    def __init__(self, vector_store: SQLVectorStore, shared_llm_model=None):
        self.vector_store = vector_store
        self.embeddings_client = vector_store.embeddings_client
        
        # Use shared LLM model if provided
        if shared_llm_model:
            self.llm_model = shared_llm_model
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.llm_model = OpenAIModel(model_id="gpt-4o-mini", api_key=api_key)
        
        # Initialize vector indexes
        try:
            self.vector_store.create_table_index()
            self.vector_store.create_relationship_index()
        except Exception as e:
            logger.error(f"Failed to initialize vector indexes: {e}")
            raise
        
        # Create tools
        self._setup_tools()
        
        # Initialize CodeAgent
        self.agent = CodeAgent(
            model=self.llm_model,
            tools=self.tools,
            additional_authorized_imports=['json']
        )
        
        logger.info("SQL indexer agent initialized")
    
    def _setup_tools(self):
        """Setup essential indexing tools."""
        
        @tool
        def index_table_documentation(table_data: Dict) -> Dict:
            """Index table documentation with OpenAI embeddings.
            
            Args:
                table_data: Dictionary containing table documentation data including name, business_purpose, schema, and type.
                
            Returns:
                Dictionary with success status and result information.
            """
            try:
                if not self._validate_table_data(table_data):
                    return {
                        "success": False,
                        "error": "Invalid table documentation format"
                    }
                
                table_name = table_data.get("name")
                if not table_name:
                    return {"success": False, "error": "Table name is required"}
                
                self.vector_store.add_table_document(table_name, table_data)
                
                return {
                    "success": True,
                    "message": f"Successfully indexed table: {table_name}",
                    "table_name": table_name
                }
                
            except Exception as e:
                logger.error(f"Failed to index table documentation: {e}")
                return {"success": False, "error": str(e)}

        @tool
        def index_relationship_documentation(relationship_data: Dict) -> Dict:
            """Index relationship documentation with OpenAI embeddings.
            
            Args:
                relationship_data: Dictionary containing relationship documentation data including id, name, type, documentation, tables, and doc_type.
                
            Returns:
                Dictionary with success status and result information.
            """
            try:
                if not self._validate_relationship_data(relationship_data):
                    return {
                        "success": False,
                        "error": "Invalid relationship documentation format"
                    }
                
                relationship_id = relationship_data.get("id") or f"{relationship_data.get('name')}_rel"
                self.vector_store.add_relationship_document(relationship_id, relationship_data)
                
                return {
                    "success": True,
                    "message": f"Successfully indexed relationship: {relationship_id}",
                    "relationship_id": relationship_id
                }
                
            except Exception as e:
                logger.error(f"Failed to index relationship documentation: {e}")
                return {"success": False, "error": str(e)}

        @tool
        def search_documentation(query: str, doc_type: str = "all") -> Dict:
            """Search indexed documentation using OpenAI embeddings.
            
            Args:
                query: The search query to find relevant documentation.
                doc_type: Type of documentation to search ("all", "table", or "relationship").
                
            Returns:
                Dictionary with search results including tables and relationships.
            """
            try:
                if doc_type not in ["all", "table", "relationship"]:
                    return {
                        "success": False,
                        "error": f"Invalid doc_type: {doc_type}"
                    }
                
                results = []
                rel_results = []
                
                if doc_type in ["all", "table"]:
                    results = self.vector_store.search_tables(query)
                
                if doc_type in ["all", "relationship"]:
                    rel_results = self.vector_store.search_relationships(query)
                
                return {
                    "success": True,
                    "query": query,
                    "doc_type": doc_type,
                    "tables": results,
                    "relationships": rel_results,
                    "total_results": len(results) + len(rel_results)
                }
                
            except Exception as e:
                logger.error(f"Failed to search documentation: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "tables": [],
                    "relationships": [],
                    "total_results": 0
                }

        @tool
        def get_indexing_status() -> Dict:
            """Get the current status of vector indexes."""
            try:
                table_count = self.vector_store.table_index.collection.count() if self.vector_store.table_index else 0
                rel_count = self.vector_store.relationship_index.collection.count() if self.vector_store.relationship_index else 0
                
                return {
                    "success": True,
                    "table_index_count": table_count,
                    "relationship_index_count": rel_count,
                    "total_indexed_documents": table_count + rel_count
                }
                
            except Exception as e:
                logger.error(f"Failed to get indexing status: {e}")
                return {"success": False, "error": str(e)}

        self.tools = [
            index_table_documentation,
            index_relationship_documentation,
            search_documentation,
            get_indexing_status
        ]
    
    def process_indexing_instruction(self, instruction: str) -> Dict:
        """Process natural language indexing instructions."""
        try:
            prompt = f"""
            Process this indexing instruction: {instruction}
            
            Available operations:
            1. Index table documentation
            2. Index relationship documentation  
            3. Search existing documentation
            4. Get indexing status
            
            Use Python syntax: True/False (not true/false).
            Return a JSON response with the operation results.
            """
            
            result = self.agent.run(prompt)
            
            # Ensure result is a dictionary
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {result}")
                    return {"success": False, "error": "Invalid JSON response"}
            
            if not isinstance(result, dict):
                logger.error(f"Expected dict, got {type(result)}")
                return {"success": False, "error": "Invalid response type"}
            
            # Ensure success field exists
            if "success" not in result:
                result["success"] = True
            
            return result
                
        except Exception as e:
            logger.error(f"Failed to process indexing instruction: {e}")
            return {"success": False, "error": str(e)}
    
    def index_table_documentation(self, table_data: Dict) -> bool:
        """Index table documentation."""
        result = self.process_indexing_instruction(
            f"Index table documentation: {json.dumps(table_data)}"
        )
        return result.get("success", False)
    
    def index_relationship_documentation(self, relationship_data: Dict) -> bool:
        """Index relationship documentation."""
        result = self.process_indexing_instruction(
            f"Index relationship documentation: {json.dumps(relationship_data)}"
        )
        return result.get("success", False)
    
    def search_documentation(self, query: str, doc_type: str = "all") -> Dict:
        """Search documentation using OpenAI embeddings."""
        try:
            if doc_type not in ["all", "table", "relationship"]:
                return {
                    "tables": [],
                    "relationships": [],
                    "total_results": 0,
                    "error": f"Invalid doc_type: {doc_type}"
                }
            
            results = {"tables": [], "relationships": [], "total_results": 0}
            
            if doc_type in ["all", "table"]:
                table_results = self.vector_store.search_tables(query)
                results["tables"] = table_results
                results["total_results"] += len(table_results)
                
            if doc_type in ["all", "relationship"]:
                rel_results = self.vector_store.search_relationships(query)
                results["relationships"] = rel_results
                results["total_results"] += len(rel_results)
                
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"tables": [], "relationships": [], "total_results": 0, "error": str(e)}
    
    def batch_index_tables(self, tables_data: List[Dict]) -> Dict[str, bool]:
        """Efficiently index multiple tables."""
        results = {}
        for table_data in tables_data:
            table_name = table_data.get("name", "unknown")
            results[table_name] = self.index_table_documentation(table_data)
        return results
    
    def batch_index_relationships(self, relationships_data: List[Dict]) -> Dict[str, bool]:
        """Efficiently index multiple relationships."""
        results = {}
        for rel_data in relationships_data:
            rel_id = rel_data.get("id") or f"{rel_data.get('name', 'unknown')}_rel"
            results[rel_id] = self.index_relationship_documentation(rel_data)
        return results
    
    def _validate_table_data(self, table_data: Dict) -> bool:
        """Validate table documentation data structure."""
        required_fields = ["name", "business_purpose", "schema", "type"]
        return all(field in table_data for field in required_fields)
    
    def _validate_relationship_data(self, relationship_data: Dict) -> bool:
        """Validate relationship documentation data structure."""
        required_fields = ["name", "type", "documentation", "tables"]
        return all(field in relationship_data for field in required_fields)