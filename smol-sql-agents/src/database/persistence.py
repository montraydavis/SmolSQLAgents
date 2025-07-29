import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DocumentationStore:
    """SQLite-based persistence layer for documentation generation."""
    
    def __init__(self, db_path: str = "__bin__/data/documentation.db"):
        """Initialize the documentation store."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        logger.info(f"Documentation store initialized at {db_path}")
    
    def _init_database(self):
        """Create the necessary tables for documentation storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS processing_state (
                    id INTEGER PRIMARY KEY,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,  -- 'pending', 'completed', 'failed'
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                );
                
                CREATE TABLE IF NOT EXISTS table_metadata (
                    table_name TEXT PRIMARY KEY,
                    schema_data TEXT NOT NULL,  -- JSON
                    business_purpose TEXT,
                    documentation TEXT,         -- Generated markdown section
                    processed_at TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS relationship_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    constrained_table TEXT NOT NULL,
                    constrained_columns TEXT NOT NULL,  -- JSON array
                    referred_table TEXT NOT NULL,
                    referred_columns TEXT NOT NULL,     -- JSON array
                    relationship_type TEXT,             -- inferred type
                    documentation TEXT,                 -- Generated markdown section
                    processed_at TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS generation_metadata (
                    id INTEGER PRIMARY KEY,
                    source_database_url TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    total_tables INTEGER,
                    total_relationships INTEGER,
                    status TEXT DEFAULT 'in_progress'
                );
            """)
            logger.info("Database schema initialized")
    
    def start_generation_session(self, db_url: str, tables: List[str], 
                                relationships: List[Dict]) -> int:
        """Start a new documentation generation session."""
        with sqlite3.connect(self.db_path) as conn:
            # Get already completed tables
            cursor = conn.execute("""
                SELECT table_name FROM table_metadata 
                WHERE status = 'completed'
            """)
            completed_tables = {row[0] for row in cursor.fetchall()}
            
            # Get already completed relationships
            cursor = conn.execute("""
                SELECT id FROM relationship_metadata 
                WHERE status = 'completed'
            """)
            completed_relationships = {row[0] for row in cursor.fetchall()}
            
            # Start new session
            cursor = conn.execute("""
                INSERT INTO generation_metadata 
                (source_database_url, started_at, total_tables, total_relationships)
                VALUES (?, ?, ?, ?)
            """, (db_url, datetime.now(), len(tables), len(relationships)))
            
            session_id = cursor.lastrowid
            
            # Initialize table processing states - only for non-completed tables
            for table in tables:
                if table not in completed_tables:
                    conn.execute("""
                        INSERT OR REPLACE INTO table_metadata (table_name, schema_data, status)
                        VALUES (?, ?, 'pending')
                    """, (table, "{}"))
            
            # Initialize relationship processing states - only for non-completed relationships
            for rel in relationships:
                if rel.get('id') not in completed_relationships:
                    conn.execute("""
                        INSERT OR REPLACE INTO relationship_metadata 
                        (constrained_table, constrained_columns, referred_table, referred_columns, status)
                        VALUES (?, ?, ?, ?, 'pending')
                    """, (rel["constrained_table"], 
                         json.dumps(rel["constrained_columns"]),
                         rel["referred_table"],
                         json.dumps(rel["referred_columns"])))
            
            logger.info(f"Started generation session {session_id} with {len(tables)} tables and {len(relationships)} relationships")
            return session_id
    
    def save_table_documentation(self, table_name: str, schema_data: Dict, 
                                business_purpose: str, documentation: str):
        """Save processed table documentation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE table_metadata 
                SET schema_data = ?, business_purpose = ?, documentation = ?,
                    processed_at = ?, status = 'completed'
                WHERE table_name = ?
            """, (json.dumps(schema_data), business_purpose, documentation,
                  datetime.now(), table_name))
            logger.info(f"Saved documentation for table: {table_name}")
    
    def save_relationship_documentation(self, relationship_id: int, 
                                      relationship_type: str, documentation: str):
        """Save processed relationship documentation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE relationship_metadata
                SET relationship_type = ?, documentation = ?, 
                    processed_at = ?, status = 'completed'
                WHERE id = ?
            """, (relationship_type, documentation, datetime.now(), relationship_id))
            logger.info(f"Saved documentation for relationship: {relationship_id}")
    
    def get_pending_tables(self) -> List[str]:
        """Get list of tables that still need processing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT table_name FROM table_metadata 
                WHERE status = 'pending' 
                AND table_name NOT IN (
                    SELECT table_name FROM table_metadata 
                    WHERE status = 'completed'
                )
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def get_pending_relationships(self) -> List[Dict]:
        """Get list of relationships that still need processing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, constrained_table, constrained_columns, 
                       referred_table, referred_columns
                FROM relationship_metadata 
                WHERE status = 'pending'
                AND id NOT IN (
                    SELECT id FROM relationship_metadata 
                    WHERE status = 'completed'
                )
            """)
            return [{
                'id': row[0],
                'constrained_table': row[1],
                'constrained_columns': json.loads(row[2]),
                'referred_table': row[3], 
                'referred_columns': json.loads(row[4])
            } for row in cursor.fetchall()]
    
    def get_generation_progress(self) -> Dict:
        """Get current progress statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Get table progress
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM table_metadata GROUP BY status
            """)
            table_stats = dict(cursor.fetchall())
            
            # Get relationship progress
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM relationship_metadata GROUP BY status  
            """)
            rel_stats = dict(cursor.fetchall())
            
            return {
                'tables': table_stats,
                'relationships': rel_stats
            }
            
    def is_table_processed(self, table_name: str) -> bool:
        """Check if a table has already been processed.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if the table has been processed, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            # First check what records exist for this table
            cursor = conn.execute("""
                SELECT table_name, status FROM table_metadata 
                WHERE table_name = ?
            """, (table_name,))
            all_records = cursor.fetchall()
            logger.debug(f"Found records for table {table_name}: {all_records}")
            
            # Now check for completed status
            cursor = conn.execute("""
                SELECT status FROM table_metadata 
                WHERE table_name = ? AND status = 'completed'
            """, (table_name,))
            result = cursor.fetchone()
            is_processed = result is not None
            logger.debug(f"Table {table_name} processed status: {is_processed}, result: {result}")
            return is_processed
    
    def is_relationship_processed(self, relationship: Dict) -> bool:
        """Check if a relationship has already been processed.
        
        Args:
            relationship: Dictionary containing relationship info with constrained_table,
                        constrained_columns, referred_table, and referred_columns
            
        Returns:
            bool: True if the relationship has been processed, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status FROM relationship_metadata 
                WHERE constrained_table = ?
                AND constrained_columns = ?
                AND referred_table = ?
                AND referred_columns = ?
                AND status = 'completed'
            """, (
                relationship['constrained_table'],
                json.dumps(relationship['constrained_columns']),
                relationship['referred_table'],
                json.dumps(relationship['referred_columns'])
            ))
            result = cursor.fetchone()
            logger.debug(f"Relationship {relationship['constrained_table']} -> {relationship['referred_table']} processed status: {result is not None}")
            return result is not None
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Get complete information for a table including schema, business purpose, and documentation.
        
        Args:
            table_name: Name of the table to retrieve information for
            
        Returns:
            Optional[Dict]: Table information or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT schema_data, business_purpose, documentation, status
                FROM table_metadata 
                WHERE table_name = ?
            """, (table_name,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "table_name": table_name,
                    "schema_data": json.loads(result[0]) if result[0] else {},
                    "business_purpose": result[1] or "",
                    "documentation": result[2] or "",
                    "status": result[3]
                }
            return None
    
    def get_relationship_info(self, relationship_id: str) -> Optional[Dict]:
        """Get complete information for a relationship including type and documentation.
        
        Args:
            relationship_id: ID of the relationship to retrieve information for
            
        Returns:
            Optional[Dict]: Relationship information or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT relationship_type, documentation, status
                FROM relationship_metadata 
                WHERE id = ?
            """, (relationship_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": relationship_id,
                    "relationship_type": result[0] or "",
                    "documentation": result[1] or "",
                    "status": result[2]
                }
            return None
    
    def get_all_tables(self) -> List[str]:
        """Get all processed tables from the database.
        
        Returns:
            List[str]: List of all table names that have been processed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT table_name FROM table_metadata 
                WHERE status = 'completed'
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def get_all_relationships(self) -> List[Dict]:
        """Get all processed relationships from the database.
        
        Returns:
            List[Dict]: List of all processed relationships
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, constrained_table, constrained_columns, 
                       referred_table, referred_columns
                FROM relationship_metadata 
                WHERE status = 'completed'
            """)
            return [{
                'id': row[0],
                'constrained_table': row[1],
                'constrained_columns': json.loads(row[2]),
                'referred_table': row[3], 
                'referred_columns': json.loads(row[4])
            } for row in cursor.fetchall()]
