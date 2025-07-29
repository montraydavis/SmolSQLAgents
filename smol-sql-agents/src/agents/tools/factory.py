"""
Database tools factory for creating unified database tool instances.
"""

from .shared import DatabaseTools

class DatabaseToolsFactory:
    """Factory for creating database tools instances."""
    
    @staticmethod
    def create_database_tools(database_inspector):
        """Create a database tools instance.
        
        Args:
            database_inspector: Database inspector instance
            
        Returns:
            DatabaseTools: Configured database tools instance
        """
        return DatabaseTools(database_inspector) 