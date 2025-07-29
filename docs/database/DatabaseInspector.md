# Database Inspector

The Database Inspector is a SQLAlchemy-based component that provides comprehensive database schema introspection capabilities. It automatically discovers and analyzes database structures, extracting table information, column details, and relationship mappings while filtering out system-specific tables.

## 🎯 What It Does

The Database Inspector performs automated database schema discovery and analysis:

- **Schema Discovery**: Automatically identifies all user-defined tables in the database
- **Column Analysis**: Extracts detailed column information including types, constraints, and nullability
- **Primary Key Detection**: Identifies primary key columns and constraints for each table
- **Relationship Mapping**: Discovers all foreign key relationships across the database
- **System Table Filtering**: Excludes database system tables from analysis
- **Cross-Platform Support**: Works with multiple database systems through SQLAlchemy

## 🔄 Inspection Flow

```markdown
Database Connection → SQLAlchemy Engine → Schema Reflection → Metadata Extraction → Filtered Results
```

1. **Connection Establishment**: Creates SQLAlchemy engine from DATABASE_URL
2. **Schema Reflection**: Uses SQLAlchemy inspector to reflect database metadata
3. **Table Discovery**: Identifies all tables and filters out system tables
4. **Column Analysis**: Extracts detailed schema information for each table
5. **Relationship Discovery**: Maps foreign key constraints across all tables
6. **Result Formatting**: Structures data for consumption by documentation agents

## 🚀 Usage Examples

### Command Line Interface

```bash
# Database inspection is automatically performed during documentation generation
python main.py

# Resume functionality relies on previous inspection results
python main.py --resume
```

### Programmatic Usage

```python
from src.database.inspector import DatabaseInspector

# Initialize the inspector
inspector = DatabaseInspector()

# Get all user-defined table names
tables = inspector.get_all_table_names()
print(f"Found {len(tables)} user tables: {tables}")

# Get detailed schema for a specific table
user_schema = inspector.get_table_schema("users")
print(f"Users table has {len(user_schema['columns'])} columns")

# Discover all foreign key relationships
relationships = inspector.get_all_foreign_key_relationships()
print(f"Found {len(relationships)} foreign key relationships")

# Example: Process all tables
for table_name in tables:
    schema = inspector.get_table_schema(table_name)
    print(f"\nTable: {schema['table_name']}")
    
    # Show primary keys
    pk_columns = [col['name'] for col in schema['columns'] if col['primary_key']]
    print(f"Primary Keys: {pk_columns}")
    
    # Show column details
    for column in schema['columns']:
        nullable = "NULL" if column['nullable'] else "NOT NULL"
        print(f"  {column['name']}: {column['type']} {nullable}")
```

## 📊 Response Structure

### Table Names Response

```python
[
    "users",
    "orders", 
    "products",
    "categories",
    "order_items"
]
```

### Table Schema Response

```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "nullable": false,
      "primary_key": true,
      "default": null
    },
    {
      "name": "username",
      "type": "VARCHAR(50)",
      "nullable": false,
      "primary_key": false,
      "default": null
    },
    {
      "name": "email",
      "type": "VARCHAR(255)",
      "nullable": false,
      "primary_key": false,
      "default": null
    },
    {
      "name": "created_at",
      "type": "TIMESTAMP",
      "nullable": true,
      "primary_key": false,
      "default": "CURRENT_TIMESTAMP"
    }
  ]
}
```

### Foreign Key Relationships Response

```json
[
  {
    "constrained_table": "orders",
    "constrained_columns": ["user_id"],
    "referred_table": "users",
    "referred_columns": ["id"]
  },
  {
    "constrained_table": "order_items", 
    "constrained_columns": ["order_id"],
    "referred_table": "orders",
    "referred_columns": ["id"]
  },
  {
    "constrained_table": "order_items",
    "constrained_columns": ["product_id"],
    "referred_table": "products", 
    "referred_columns": ["id"]
  }
]
```

## ⚙️ Configuration

### Environment Variables

```env
# Required: Database connection string
DATABASE_URL="mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=master;Trusted_Connection=yes"

# Alternative examples for different databases:
# PostgreSQL
# DATABASE_URL="postgresql://user:password@localhost:5432/database"

# MySQL  
# DATABASE_URL="mysql+pymysql://user:password@localhost:3306/database"

# SQLite
# DATABASE_URL="sqlite:///path/to/database.db"

# Optional: Logging configuration
LOG_LEVEL="INFO"
LOG_FILE="inspector.log"
```

### Supported Database Systems

- **SQL Server**: Via `pyodbc` driver with ODBC connection strings
- **PostgreSQL**: Via `psycopg2-binary` driver
- **MySQL**: Via `pymysql` driver  
- **SQLite**: Built-in support
- **Oracle**: Via `cx_Oracle` driver (additional setup required)

## 🎯 Use Cases

### 1. Database Discovery

Automatically discover and catalog database structures:

```python
inspector = DatabaseInspector()

# Get overview of database
tables = inspector.get_all_table_names()
relationships = inspector.get_all_foreign_key_relationships()

print(f"Database contains:")
print(f"  - {len(tables)} user tables")
print(f"  - {len(relationships)} foreign key relationships")

# Analyze table complexity
for table in tables:
    schema = inspector.get_table_schema(table)
    column_count = len(schema['columns'])
    pk_count = sum(1 for col in schema['columns'] if col['primary_key'])
    
    print(f"  {table}: {column_count} columns, {pk_count} primary keys")
```

### 2. Schema Analysis

Perform detailed analysis of table structures:

```python
# Analyze column types across database
type_distribution = {}
nullable_stats = {"nullable": 0, "not_nullable": 0}

for table_name in inspector.get_all_table_names():
    schema = inspector.get_table_schema(table_name)
    
    for column in schema['columns']:
        # Track column types
        col_type = str(column['type']).split('(')[0]  # Remove length specifications
        type_distribution[col_type] = type_distribution.get(col_type, 0) + 1
        
        # Track nullability
        if column['nullable']:
            nullable_stats["nullable"] += 1
        else:
            nullable_stats["not_nullable"] += 1

print("Column type distribution:", type_distribution)
print("Nullability statistics:", nullable_stats)
```

### 3. Relationship Analysis

Map and analyze database relationships:

```python
# Build relationship graph
relationships = inspector.get_all_foreign_key_relationships()

# Group by parent table
parent_tables = {}
child_tables = {}

for rel in relationships:
    parent = rel['referred_table']
    child = rel['constrained_table']
    
    if parent not in parent_tables:
        parent_tables[parent] = []
    parent_tables[parent].append(child)
    
    if child not in child_tables:
        child_tables[child] = []
    child_tables[child].append(parent)

# Find tables with most relationships
most_connected = max(parent_tables.items(), key=lambda x: len(x[1]))
print(f"Most connected table: {most_connected[0]} (parent to {len(most_connected[1])} tables)")

# Find orphan tables (no relationships)
all_tables = set(inspector.get_all_table_names())
connected_tables = set(parent_tables.keys()) | set(child_tables.keys())
orphan_tables = all_tables - connected_tables
print(f"Orphan tables (no relationships): {orphan_tables}")
```

### 4. Data Quality Assessment

Assess schema quality and design patterns:

```python
# Check for common design patterns and potential issues
issues = []

for table_name in inspector.get_all_table_names():
    schema = inspector.get_table_schema(table_name)
    
    # Check for primary key
    has_pk = any(col['primary_key'] for col in schema['columns'])
    if not has_pk:
        issues.append(f"Table '{table_name}' has no primary key")
    
    # Check for common audit columns
    column_names = [col['name'].lower() for col in schema['columns']]
    if 'created_at' not in column_names and 'created_date' not in column_names:
        issues.append(f"Table '{table_name}' missing created timestamp")
    
    # Check for ID column naming
    id_columns = [col for col in schema['columns'] if col['name'].lower() == 'id']
    if not id_columns and has_pk:
        pk_columns = [col['name'] for col in schema['columns'] if col['primary_key']]
        if len(pk_columns) == 1 and not pk_columns[0].endswith('_id'):
            issues.append(f"Table '{table_name}' has unusual primary key name: {pk_columns[0]}")

print("Schema quality issues found:")
for issue in issues:
    print(f"  - {issue}")
```

## 🔍 Integration with Other Components

The Database Inspector provides foundational data for the entire system:

- **Core Agent**: Uses inspection results to identify tables and relationships for documentation
- **Documentation Store**: Receives inspection data for session initialization
- **Batch Manager**: Processes tables and relationships discovered by the inspector
- **Entity Recognition**: Searches among tables identified by the inspector

## 🎖️ Advanced Features

### System Table Filtering

Automatically excludes database-specific system tables:

- **SQL Server**: Tables starting with `spt_`, `MSreplication_`
- **PostgreSQL**: Tables starting with `pg_`
- **General**: Any table starting with system prefixes

### Cross-Platform Compatibility

- **Driver Abstraction**: Uses SQLAlchemy for database-agnostic operations
- **Connection Pooling**: Efficient connection management
- **Error Handling**: Database-specific error handling and recovery
- **Metadata Caching**: Optimized metadata reflection and caching

### Schema Reflection Optimization

- **Lazy Loading**: Metadata loaded only when needed
- **Selective Reflection**: Can reflect specific tables or schemas
- **Connection Reuse**: Efficient connection pooling for multiple operations
- **Memory Management**: Optimized memory usage for large schemas

## 📈 Performance Characteristics

- **Connection Time**: Sub-second connection establishment for local databases
- **Schema Reflection**: 1-5 seconds for typical databases (100-500 tables)
- **Large Databases**: Handles databases with 1000+ tables efficiently
- **Memory Usage**: Minimal memory footprint with lazy loading
- **Network Efficiency**: Optimized queries minimize network round trips

## 🚦 Prerequisites

1. **Database Access**: Valid database connection with read permissions
2. **SQLAlchemy Driver**: Appropriate database driver installed (pyodbc, psycopg2, etc.)
3. **Network Connectivity**: Access to database server if remote
4. **Schema Permissions**: READ access to information_schema or equivalent
5. **Dependencies**: SQLAlchemy and database-specific drivers from requirements.txt

## 🔧 Error Handling

### Common Error Scenarios

1. **Connection Failures**: Database server unavailable or credentials invalid
2. **Permission Issues**: Insufficient privileges to read schema information
3. **Driver Problems**: Missing or incompatible database drivers
4. **Network Issues**: Timeout or connectivity problems with remote databases
5. **Schema Changes**: Database schema modifications during inspection

### Error Recovery

```python
try:
    inspector = DatabaseInspector()
    tables = inspector.get_all_table_names()
    print(f"Successfully connected to database with {len(tables)} tables")
    
except ValueError as e:
    if "DATABASE_URL" in str(e):
        print("Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL with your database connection string")
    else:
        print(f"Configuration error: {e}")
        
except Exception as e:
    print(f"Database connection failed: {e}")
    print("Please check:")
    print("  - Database server is running")
    print("  - Connection string is correct")
    print("  - Network connectivity")
    print("  - Database permissions")
```

### Connection String Examples

```python
# SQL Server with Windows Authentication
DATABASE_URL = "mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;Trusted_Connection=yes"

# SQL Server with SQL Authentication  
DATABASE_URL = "mssql+pyodbc://user:password@localhost/mydb?driver=ODBC+Driver+17+for+SQL+Server"

# PostgreSQL
DATABASE_URL = "postgresql://user:password@localhost:5432/mydb"

# MySQL
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/mydb"

# SQLite
DATABASE_URL = "sqlite:///path/to/database.db"
```
