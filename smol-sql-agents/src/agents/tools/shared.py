"""
Shared tools framework for SQL agents.
Provides unified tools for database operations, validation, caching, and utilities.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from smolagents.tools import tool

logger = logging.getLogger(__name__)

class DatabaseTools:
    """Unified database operations for all agents."""
    
    def __init__(self, database_inspector=None):
        """Initialize database tools.
        
        Args:
            database_inspector: Database inspector instance
        """
        self.database_inspector = database_inspector
    
    def get_table_schema_unified(self, table_name: str) -> Dict[str, Any]:
        """Get unified table schema information.
        
        Args:
            table_name: Name of the table to get schema for
            
        Returns:
            Dict: Table schema information with standardized format
        """
        try:
            if not self.database_inspector:
                return {
                    "success": False,
                    "error": "Database inspector not available",
                    "details": "This tool requires a database inspector to be provided"
                }
            
            schema = self.database_inspector.get_table_schema(table_name)
            if not schema:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found",
                    "details": "The specified table does not exist in the database"
                }
            
            return {
                "success": True,
                "table_name": table_name,
                "schema": schema,
                "columns": schema.get("columns", []),
                "primary_key": schema.get("primary_key"),
                "foreign_keys": schema.get("foreign_keys", []),
                "description": schema.get("description", f"Table {table_name}")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Exception occurred while getting table schema"
            }
    
    def get_all_tables_unified(self) -> Dict[str, Any]:
        """Get all table names in unified format.
        
        Returns:
            Dict: List of all table names with standardized format
        """
        try:
            if not self.database_inspector:
                return {
                    "success": False,
                    "error": "Database inspector not available",
                    "details": "This tool requires a database inspector to be provided"
                }
            
            table_names = self.database_inspector.get_all_table_names()
            if not table_names:
                return {
                    "success": True,
                    "tables": [],
                    "count": 0,
                    "message": "No tables found in database"
                }
            
            return {
                "success": True,
                "tables": table_names,
                "count": len(table_names),
                "message": f"Found {len(table_names)} tables"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Exception occurred while getting table names"
            }
    
    def get_relationships_unified(self) -> Dict[str, Any]:
        """Get all foreign key relationships in unified format.
        
        Returns:
            Dict: List of all relationships with standardized format
        """
        try:
            if not self.database_inspector:
                return {
                    "success": False,
                    "error": "Database inspector not available",
                    "details": "This tool requires a database inspector to be provided"
                }
            
            relationships = self.database_inspector.get_all_foreign_key_relationships()
            if not relationships:
                return {
                    "success": True,
                    "relationships": [],
                    "count": 0,
                    "message": "No foreign key relationships found"
                }
            
            return {
                "success": True,
                "relationships": relationships,
                "count": len(relationships),
                "message": f"Found {len(relationships)} foreign key relationships"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Exception occurred while getting relationships"
            }
    
    def execute_query_safe(self, query: str, max_rows: int = 100) -> Dict[str, Any]:
        """Execute query safely with unified format.
        
        Args:
            query: SQL query to execute
            max_rows: Maximum number of rows to return
            
        Returns:
            Dict: Query execution results with standardized format
        """
        try:
            if not self.database_inspector:
                return {
                    "success": False,
                    "error": "Database inspector not available",
                    "details": "This tool requires a database inspector to be provided"
                }
            
            # Use the database inspector's engine to execute the query
            from sqlalchemy import text
            with self.database_inspector.engine.connect() as connection:
                # Add row limiting for safety
                if "TOP" not in query.upper() and "SELECT" in query.upper():
                    # For SQL Server, add TOP clause
                    select_index = query.upper().find("SELECT")
                    if select_index != -1:
                        after_select = query[select_index + 6:].lstrip()
                        query = query[:select_index + 6] + f" TOP {max_rows} " + after_select
                
                result = connection.execute(text(query))
                rows = result.fetchall()
                columns = result.keys()
                
                # Convert to list of dictionaries
                row_dicts = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "rows": row_dicts,
                    "columns": list(columns),
                    "total_rows": len(row_dicts),
                    "returned_rows": len(row_dicts),
                    "truncated": len(row_dicts) >= max_rows
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Exception occurred while executing query"
            }
    
    def create_tools(self):
        """Create tool functions for this database tools instance."""
        database_tools_instance = self
        
        @tool
        def get_table_schema_unified_tool(table_name: str) -> Dict[str, Any]:
            """Get unified table schema information.
            
            Args:
                table_name: Name of the table to get schema for
                
            Returns:
                Dict: Table schema information with standardized format
            """
            return database_tools_instance.get_table_schema_unified(table_name)
        
        @tool
        def get_all_tables_unified_tool() -> Dict[str, Any]:
            """Get all table names in unified format.
            
            Returns:
                Dict: List of all table names with standardized format
            """
            return database_tools_instance.get_all_tables_unified()
        
        @tool
        def get_relationships_unified_tool() -> Dict[str, Any]:
            """Get all foreign key relationships in unified format.
            
            Returns:
                Dict: List of all relationships with standardized format
            """
            return database_tools_instance.get_relationships_unified()
        
        return [
            get_table_schema_unified_tool,
            get_all_tables_unified_tool,
            get_relationships_unified_tool
        ]

class ValidationTools:
    """Unified validation tools for all agents."""
    
    @staticmethod
    @tool
    def validate_input_unified(input_data: Any, expected_type: str) -> Dict[str, Any]:
        """Validate input data against expected type.
        
        Args:
            input_data: Data to validate
            expected_type: Expected type (str, list, dict, etc.)
            
        Returns:
            Dict: Validation result with standardized format
        """
        try:
            if expected_type == "str" and isinstance(input_data, str):
                return {"valid": True, "message": "Input is valid string"}
            elif expected_type == "list" and isinstance(input_data, list):
                return {"valid": True, "message": "Input is valid list"}
            elif expected_type == "dict" and isinstance(input_data, dict):
                return {"valid": True, "message": "Input is valid dictionary"}
            else:
                return {"valid": False, "error": f"Expected {expected_type}, got {type(input_data).__name__}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    @staticmethod
    @tool
    def validate_query_safety(query: str) -> Dict[str, Any]:
        """Validate SQL query for safety concerns.
        
        Args:
            query: SQL query to validate
            
        Returns:
            Dict: Safety validation result
        """
        try:
            # Basic SQL injection prevention checks
            dangerous_keywords = [
                "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"
            ]
            
            query_upper = query.upper()
            issues = []
            
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    issues.append(f"Contains potentially dangerous keyword: {keyword}")
            
            if issues:
                return {
                    "safe": False,
                    "issues": issues,
                    "recommendation": "Review query for security concerns"
                }
            else:
                return {
                    "safe": True,
                    "message": "Query appears safe for execution"
                }
        except Exception as e:
            return {"safe": False, "error": str(e)}
    
    @staticmethod
    @tool
    def validate_required_params(params: Dict, required_keys: List[str]) -> Dict[str, Any]:
        """Validate that required parameters are present.
        
        Args:
            params: Parameters to validate
            required_keys: List of required keys
            
        Returns:
            Dict: Validation result
        """
        try:
            missing_keys = [key for key in required_keys if key not in params]
            if missing_keys:
                return {"valid": False, "error": f"Missing required parameters: {missing_keys}"}
            return {"valid": True, "message": "All required parameters present"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

class CachingTools:
    """Unified caching tools for all agents."""
    
    def __init__(self, cache_size: int = 100):
        """Initialize caching tools.
        
        Args:
            cache_size: Maximum number of cached items
        """
        self._cache = {}
        self._cache_size = cache_size
    
    def get_cached_result(self, cache_key: str) -> Dict[str, Any]:
        """Get cached result if available.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Dict: Cached result or None if not found
        """
        try:
            result = self._cache.get(cache_key)
            if result:
                return {"success": True, "cached": True, "data": result}
            else:
                return {"success": True, "cached": False, "data": None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cache_result(self, cache_key: str, data: Any, ttl: int = 1800) -> Dict[str, Any]:
        """Cache a result with TTL.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
            
        Returns:
            Dict: Caching result
        """
        try:
            import time
            self._cache[cache_key] = {
                "data": data,
                "timestamp": time.time(),
                "ttl": ttl
            }
            
            # Limit cache size
            if len(self._cache) > self._cache_size:
                # Remove oldest entries
                oldest_keys = list(self._cache.keys())[:10]
                for key in oldest_keys:
                    del self._cache[key]
            
            return {"success": True, "message": "Result cached successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear the cache.
        
        Returns:
            Dict: Clear operation result
        """
        try:
            self._cache.clear()
            return {"success": True, "message": "Cache cleared successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class UtilityTools:
    """Unified utility tools for all agents."""
    
    @staticmethod
    @tool
    def format_response_unified(data: Any, format_type: str = "json") -> Dict[str, Any]:
        """Format response data in specified format.
        
        Args:
            data: Data to format
            format_type: Format type (json, text, etc.)
            
        Returns:
            Dict: Formatted response
        """
        try:
            if format_type == "json":
                return {"success": True, "data": data, "format": "json"}
            elif format_type == "text":
                return {"success": True, "data": str(data), "format": "text"}
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    @tool
    def log_operation_unified(operation: str, details: Dict = None) -> Dict[str, Any]:
        """Log an operation for debugging and monitoring.
        
        Args:
            operation: Name of the operation
            details: Additional details to log
            
        Returns:
            Dict: Logging result
        """
        try:
            log_message = f"Operation: {operation}"
            if details:
                log_message += f" | Details: {details}"
            
            logger.info(log_message)
            return {"success": True, "message": "Operation logged successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    @tool
    def safe_execute_unified(func_name: str, func_args: Dict = None) -> Dict[str, Any]:
        """Safely execute a function with error handling.
        
        Args:
            func_name: Name of the function to execute
            func_args: Arguments for the function
            
        Returns:
            Dict: Execution result
        """
        try:
            # This is a placeholder - actual implementation will depend on the agent
            return {
                "success": False,
                "error": "Function execution not implemented",
                "details": "This tool requires agent-specific implementation"
            }
        except Exception as e:
            return {"success": False, "error": str(e)} 