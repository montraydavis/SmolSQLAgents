# Configuration Reference

This document provides a comprehensive reference for all configuration options available in smol-sql-agents.

## Environment Variables

### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | Database connection string (e.g., `postgresql://user:pass@host:port/dbname`) |
| `DB_POOL_SIZE` | No | 5 | Connection pool size |
| `DB_MAX_OVERFLOW` | No | 10 | Maximum overflow size for connection pool |

### LLM Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4` | OpenAI model to use |
| `OPENAI_TEMPERATURE` | No | `0.1` | Sampling temperature (0-2) |
| `OPENAI_MAX_TOKENS` | No | `2048` | Maximum number of tokens to generate |

### Logging Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | No | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | Log message format |

### Agent Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_TIMEOUT` | No | `30` | Agent execution timeout in seconds |
| `MAX_RETRIES` | No | `3` | Maximum number of retries for agent operations |

## Configuration File

You can also use a `config.yaml` file in your project root:

```yaml
database:
  url: ${DATABASE_URL}
  pool_size: 5
  max_overflow: 10

openai:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  temperature: 0.1
  max_tokens: 2048

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

agent:
  timeout: 30
  max_retries: 3
```

## Programmatic Configuration

You can also configure the application programmatically:

```python
from smol_sql_agents import configure

configure(
    database_url="postgresql://user:pass@localhost:5432/dbname",
    openai_api_key="your-api-key",
    log_level="INFO",
    agent_timeout=30
)
```

## Best Practices

1. **Sensitive Information**: Never commit API keys or database credentials to version control. Use environment variables for sensitive data.
2. **Environment-Specific Configs**: Maintain separate configurations for development, testing, and production environments.
3. **Validation**: The application validates all configuration values on startup and will raise descriptive errors for invalid values.
4. **Performance Tuning**: Adjust pool sizes and timeouts based on your application's requirements and database capabilities.

## Troubleshooting

- **Connection Issues**: Verify your database URL and network connectivity
- **Authentication Failures**: Double-check API keys and database credentials
- **Performance Problems**: Adjust pool sizes and timeouts as needed

For more information, see the [Troubleshooting Guide](../troubleshooting/README.md).
