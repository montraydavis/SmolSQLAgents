# Development Setup

This guide will help you set up a development environment for smol-sql-agents.

## Prerequisites

- Python 3.8+
- Git
- Poetry (for dependency management)
- Docker (for local database testing)

## Setup Instructions

### 1. Fork and Clone the Repository

```bash
git clone https://github.com/yourusername/smol-sql-agents.git
cd smol-sql-agents
```

### 2. Set Up Python Environment

```bash
# Install Poetry if you haven't already
pip install poetry

# Install dependencies
poetry install --with dev

# Activate the virtual environment
poetry shell
```

### 3. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```ini
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db

# OpenAI
OPENAI_API_KEY=your_api_key_here

# Logging
LOG_LEVEL=DEBUG
```

### 5. Start Local Services

```bash
# Start PostgreSQL in Docker
docker-compose up -d postgres

# Run database migrations
alembic upgrade head
```

## Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_agents.py -v
```

## Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8

# Type checking
mypy src
```

## Documentation

We use MkDocs for documentation:

```bash
# Install docs dependencies
pip install -r docs/requirements.txt

# Serve docs locally
mkdocs serve
```

## Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Add your commit message"
   ```

3. Push your changes:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a pull request on GitHub

## Debugging

### VS Code Launch Configuration

Add this to your `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "envFile": "${workspaceFolder}/.env"
        }
    ]
}
```

### Common Issues

1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check `.env` file for correct credentials
   - Run `alembic upgrade head` to apply migrations

2. **Dependency Issues**
   - Run `poetry install` to ensure all dependencies are installed
  - Delete `poetry.lock` and run `poetry install` if needed

## Performance Profiling

```python
import cProfile
import pstats

def profile_function():
    # Your code here
    pass

if __name__ == "__main__":
    with cProfile.Profile() as pr:
        profile_function()
    
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats(10)  # Show top 10 time-consuming functions
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a release tag:
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push origin v1.0.0
   ```
4. Create a GitHub release with release notes

## Getting Help

- Check the [GitHub Issues](https://github.com/yourusername/smol-sql-agents/issues)
- Join our [Discord/Slack] channel
- Contact the maintainers at [email/contact info]
