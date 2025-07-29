
import sqlite3
import json
import logging
from typing import Dict
from jinja2 import Environment, BaseLoader

logger = logging.getLogger(__name__)

class DocumentationFormatter:
    """Generates formatted documentation from stored data."""
    
    def __init__(self, db_path: str = "__bin__/data/documentation.db"):
        self.db_path = db_path
        self.templates = {
            'markdown': self._markdown_template(),
            'html': self._html_template()
        }
    
    def generate_documentation(self, format_type: str = 'markdown') -> str:
        """Generate complete documentation in specified format."""
        logger.info(f"Generating documentation in {format_type} format")
        
        data = self._load_documentation_data()
        template = Environment(loader=BaseLoader()).from_string(
            self.templates.get(format_type, self.templates['markdown'])
        )
        
        result = template.render(**data)
        logger.info(f"Documentation generated successfully ({len(result)} characters)")
        return result
    
    def _load_documentation_data(self) -> Dict:
        """Load all documentation data from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            # Load table documentation
            cursor = conn.execute("""
                SELECT DISTINCT table_name, schema_data, business_purpose, documentation
                FROM table_metadata 
                WHERE status = 'completed'
                AND table_name NOT IN (
                    SELECT t2.table_name 
                    FROM table_metadata t2 
                    WHERE t2.table_name = table_metadata.table_name 
                    AND t2.rowid > table_metadata.rowid
                )
                ORDER BY table_name
            """)
            
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    'name': row[0],
                    'schema': json.loads(row[1]),
                    'purpose': row[2],
                    'documentation': row[3]
                })
            
            # Load relationship documentation  
            cursor = conn.execute("""
                SELECT DISTINCT constrained_table, constrained_columns, referred_table, 
                       referred_columns, relationship_type, documentation
                FROM relationship_metadata
                WHERE status = 'completed'
                AND id NOT IN (
                    SELECT r2.id 
                    FROM relationship_metadata r2 
                    WHERE r2.constrained_table = relationship_metadata.constrained_table
                    AND r2.referred_table = relationship_metadata.referred_table
                    AND r2.id > relationship_metadata.id
                )
                ORDER BY constrained_table, referred_table
            """)
            
            relationships = []
            for row in cursor.fetchall():
                relationships.append({
                    'constrained_table': row[0],
                    'constrained_columns': json.loads(row[1]),
                    'referred_table': row[2],
                    'referred_columns': json.loads(row[3]),
                    'type': row[4],
                    'documentation': row[5]
                })
            
            # Load generation metadata
            cursor = conn.execute("""
                SELECT started_at, completed_at, total_tables, total_relationships
                FROM generation_metadata
                ORDER BY id DESC LIMIT 1
            """)
            
            metadata = cursor.fetchone()
            
            return {
                'tables': tables,
                'relationships': relationships,
                'metadata': {
                    'started_at': metadata[0] if metadata else None,
                    'completed_at': metadata[1] if metadata else None,
                    'total_tables': metadata[2] if metadata else 0,
                    'total_relationships': metadata[3] if metadata else 0
                }
            }
    
    def _markdown_template(self) -> str:
        """Markdown template for documentation generation."""
        return """# Database Knowledge Base

Generated on: {{ metadata.completed_at or 'In Progress' }}
Total Tables: {{ metadata.total_tables }}
Total Relationships: {{ metadata.total_relationships }}

# Tables

{% for table in tables %}
## {{ table.name }}

{{ table.purpose }}

| Column | Type | Primary Key | Nullable |
|--------|------|-------------|----------|
{% for column in table.schema.columns -%}
| {{ column.name }} | {{ column.type }} | {{ 'Yes' if column.primary_key else 'No' }} | {{ 'Yes' if column.nullable else 'No' }} |
{% endfor %}

{{ table.documentation }}

{% endfor %}

# Relationships

{% for rel in relationships %}
### {{ rel.constrained_table }}.{{ rel.constrained_columns|join(',') }} → {{ rel.referred_table }}.{{ rel.referred_columns|join(',') }}

{{ rel.documentation }}

{% endfor %}
"""
    
    def _html_template(self) -> str:
        """HTML template for documentation generation."""
        return """<!DOCTYPE html>
<html>
<head>
    <title>Database Knowledge Base</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metadata { background-color: #f9f9f9; padding: 10px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Database Knowledge Base</h1>
    
    <div class="metadata">
        <strong>Generated:</strong> {{ metadata.completed_at or 'In Progress' }}<br>
        <strong>Tables:</strong> {{ metadata.total_tables }}<br>
        <strong>Relationships:</strong> {{ metadata.total_relationships }}
    </div>
    
    <h1>Tables</h1>
    {% for table in tables %}
    <h2>{{ table.name }}</h2>
    <p>{{ table.purpose }}</p>
    
    <table>
        <tr><th>Column</th><th>Type</th><th>Primary Key</th><th>Nullable</th></tr>
        {% for column in table.schema.columns %}
        <tr>
            <td>{{ column.name }}</td>
            <td>{{ column.type }}</td>
            <td>{{ 'Yes' if column.primary_key else 'No' }}</td>
            <td>{{ 'Yes' if column.nullable else 'No' }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <div>{{ table.documentation }}</div>
    {% endfor %}
    
    <h1>Relationships</h1>
    {% for rel in relationships %}
    <h3>{{ rel.constrained_table }}.{{ rel.constrained_columns|join(',') }} → {{ rel.referred_table }}.{{ rel.referred_columns|join(',') }}</h3>
    <p>{{ rel.documentation }}</p>
    {% endfor %}
</body>
</html>"""
