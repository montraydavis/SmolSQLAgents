# Installation Guide

This guide will help you install and set up smol-sql-agents in your environment.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for development)

## Installation Options

### Using pip (Recommended)

```bash
pip install smol-sql-agents
```

### From Source

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/smol-sql-agents.git
   cd smol-sql-agents
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install with development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

## Verify Installation

```python
import smol_sql_agents
print(smol_sql_agents.__version__)
```

## Configuration

Create a `.env` file in your project root:

```ini
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key

# Logging
LOG_LEVEL=INFO
```

## Next Steps

- [Quick Start Guide](./quick_start.md)
- [Configuration Reference](./configuration.md)
