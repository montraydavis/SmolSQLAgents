import os
import logging
from sqlalchemy import create_engine, inspect, MetaData
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseInspector:
    """A toolkit for inspecting a SQL database schema using SQLAlchemy."""

    def __init__(self):
        """Initializes the database engine and inspector."""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set.")
        
        logger.info("Initializing database connection")
        self.engine = create_engine(db_url)
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        logger.info("Database inspector initialized successfully")

    def get_all_table_names(self) -> list[str]:
        """Retrieves a list of all user-defined table names in the public schema, excluding system tables."""
        try:
            tables = self.inspector.get_table_names()
            # Exclude system tables (e.g., those starting with 'pg_' or 'sql_')
            user_tables = [t for t in tables if not (t.startswith('pg_') or t.startswith('spt_') or t.startswith('MSreplication_'))]
            logger.info(f"Found {len(user_tables)} user tables in database")
            return user_tables
        except Exception as e:
            logger.error(f"Failed to retrieve table names: {e}")
            raise

    def get_table_schema(self, table_name: str) -> dict:
        """Retrieves the detailed schema for a specific table.
        
        Args:
            table_name: The name of the table to retrieve schema for.
            
        Returns:
            A dictionary containing the table schema with columns and constraints.
        """
        try:
            columns = self.inspector.get_columns(table_name)
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            pk_columns = pk_constraint.get('constrained_columns', [])
            
            schema = {
                'table_name': table_name,
                'columns': []
            }
            
            for col in columns:
                schema['columns'].append({
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'primary_key': col['name'] in pk_columns,
                    'default': col.get('default')
                })
            
            logger.info(f"Retrieved schema for table: {table_name}")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to retrieve schema for table {table_name}: {e}")
            raise

    def get_all_foreign_key_relationships(self) -> list[dict]:
        """Retrieves all foreign key relationships across the entire database."""
        try:
            relationships = []
            tables = self.get_all_table_names()
            
            for table in tables:
                fks = self.inspector.get_foreign_keys(table)
                for fk in fks:
                    relationships.append({
                        'constrained_table': table,
                        'constrained_columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    })
            
            logger.info(f"Found {len(relationships)} foreign key relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to retrieve foreign key relationships: {e}")
            raise
