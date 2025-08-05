# Quick Start Guide

This guide will help you get started with smol-sql-agents by walking you through a simple example.

## Basic Usage

### 1. Import Required Modules

```python
from smol_sql_agents import NL2SQLAgent, DatabaseInspector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
```

### 2. Initialize the Database Inspector

```python
# Initialize database inspector
db_url = os.getenv("DATABASE_URL")
inspector = DatabaseInspector(db_url)

# Get database schema
schema = inspector.get_schema()
```

### 3. Create and Run an Agent

```python
# Initialize the NL2SQL agent
agent = NL2SQLAgent()

# Execute a natural language query
result = agent.execute(
    query="Show me all active users who made a purchase in the last 30 days",
    schema=schema
)

print("Generated SQL:", result["sql"])
print("Query Results:", result["results"])
```

## Example: End-to-End Workflow

```python
from smol_sql_agents import BusinessAgent, DatabaseInspector

# Initialize components
db_inspector = DatabaseInspector(os.getenv("DATABASE_URL"))
agent = BusinessAgent()

# Analyze business data
business_insights = agent.analyze(
    question="What are our top-selling products by region?",
    schema=db_inspector.get_schema()
)

print("Analysis Results:", business_insights)
```

## Next Steps

- Learn more about [Core Concepts](../concepts/README.md)
- Explore the [API Reference](../api/README.md)
- Check out [Advanced Usage](../guides/README.md)
