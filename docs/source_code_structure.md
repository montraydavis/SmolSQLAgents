# Source Code Structure

This document provides an overview of the source code organization and key components of the smol-sql-agents project.

## 📁 Project Structure

```
src/
├── __init__.py         # Package initialization
├── agents/            # Core agent implementations
├── database/          # Database interaction layer
├── output/            # Output formatters and handlers
├── prompts/           # Prompt templates and management
├── utils/             # Utility functions and helpers
├── validation/        # Data validation logic
└── vector/            # Vector operations and storage
```

## 📂 utils/ Directory

The `utils` directory contains reusable utility functions and helper classes used throughout the application.

### Key Components

- **config_loader.py**: Loads and validates configuration from environment variables
- **logger.py**: Centralized logging configuration and utilities
- **file_helpers.py**: File I/O operations and path utilities
- **async_helpers.py**: Asynchronous operation utilities and decorators
- **string_utils.py**: String manipulation and formatting helpers

### Example Usage

```python
from src.utils.logger import get_logger
from src.utils.config_loader import get_config

logger = get_logger(__name__)
config = get_config()
```

## 📂 validation/ Directory

The `validation` directory contains data validation schemas and validation logic.

### Key Components

- **schemas/**: Pydantic models for request/response validation
  - `database.py`: Database connection and query validation
  - `agent.py`: Agent configuration and execution validation
  - `vector.py`: Vector operation validation
- **validators/**: Custom validation functions
  - `sql_validator.py`: SQL syntax and safety validation
  - `data_validator.py`: Data type and format validation

### Example Usage

```python
from src.validation.schemas.database import DatabaseConnection
from src.validation.validators.sql_validator import validate_sql_query

# Validate database connection
connection = DatabaseConnection(
    host="localhost",
    port=5432,
    database="mydb",
    username="user"
)

# Validate SQL query
safe_query = validate_sql_query("SELECT * FROM users WHERE id = %s")
```

## 📂 prompts/ Directory

The `prompts` directory contains all prompt templates and prompt management logic.

### Key Components

- **templates/**: Prompt templates for different agent types
  - `sql_generation.txt`: Templates for SQL generation tasks
  - `query_understanding.txt`: Templates for natural language understanding
  - `result_explanation.txt`: Templates for explaining query results
- **prompt_manager.py**: Manages loading and rendering of prompt templates
- **prompt_utils.py**: Helper functions for prompt construction

### Example Prompt Template (`prompts/templates/sql_generation.txt`)

```markdown$s$
Given the following database schema:

{schema}

Generate a SQL query to: {user_query}

Return only the SQL query without any additional text.
```

### Example Usage

```python
from src.prompts.prompt_manager import PromptManager

pm = PromptManager()
prompt = pm.get_prompt(
    "sql_generation",
    schema=schema_info,
    user_query="Find all active users"
)
```

## 🏗️ Package Initialization

The `__init__.py` files are used to define Python packages and their public API.

### Root `__init__.py`

```python
# Core exports
from .agents import (
    BaseAgent,
    NL2SQLAgent,
    BusinessAgent,
    CoreAgent,
    EntityRecognitionAgent
)

# Database components
from .database import DatabaseInspector, DocumentationStore

# Vector operations
from .vector import VectorStore, EmbeddingsClient

__version__ = "0.1.0"
__all__ = [
    # Agents
    'BaseAgent',
    'NL2SQLAgent',
    'BusinessAgent',
    'CoreAgent',
    'EntityRecognitionAgent',
    # Database
    'DatabaseInspector',
    'DocumentationStore',
    # Vector
    'VectorStore',
    'EmbeddingsClient'
]
```

## 🔄 Module Initialization

Each subpackage (agents, database, etc.) contains its own `__init__.py` that follows a similar pattern:

```python
# agents/__init__.py
from .base_agent import BaseAgent
from .nl2sql_agent import NL2SQLAgent
from .business_agent import BusinessAgent

__all__ = [
    'BaseAgent',
    'NL2SQLAgent',
    'BusinessAgent'
]
```

## 🔍 Code Organization Principles

1. **Single Responsibility**: Each module and class has a single responsibility
2. **Separation of Concerns**: Clear boundaries between different components
3. **Dependency Injection**: Dependencies are injected where possible for testability
4. **Type Hints**: Extensive use of Python type hints for better IDE support
5. **Documentation**: All public APIs include docstrings following Google style

## 🛠️ Development Guidelines

- Add new utility functions to the appropriate module in `utils/`
- Keep validation logic in the `validation/` directory
- Store all prompt templates in the `prompts/` directory
- Update `__init__.py` files to expose new public APIs
- Maintain backward compatibility when modifying existing code

## 📚 Related Documentation

- [Database Components](./database/DatabaseInspector.md)
- [Agent Architecture](./agents/BaseAgent.md)
- [Vector Operations](./vector/VectorStore.md)
