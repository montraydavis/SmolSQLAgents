# Agents

Agents are the core components of smol-sql-agents that handle different types of natural language to SQL conversions and database interactions.

## Agent Types

### 1. Base Agent

The foundation for all agents, providing common functionality.

**Key Features:**

- Shared initialization
- Common error handling
- Logging and monitoring
- Base prompt templates

### 2. NL2SQL Agent

Converts natural language queries into SQL.

**Usage Example:**

```python
from smol_sql_agents import NL2SQLAgent

agent = NL2SQLAgent()
result = agent.execute(
    query="Show me all orders over $1000 from last month",
    schema=database_schema
)
```

**Features:**

- Natural language understanding
- SQL generation
- Query validation
- Schema-aware query building

### 3. Business Agent

Specialized in generating business insights from data.

**Usage Example:**

```python
from smol_sql_agents import BusinessAgent

agent = BusinessAgent()
insights = agent.analyze(
    question="What are the sales trends for this quarter?",
    schema=database_schema
)
```

**Features:**

- Business metric calculation
- Trend analysis
- KPI reporting
- Data visualization suggestions

### 4. Analytics Agent

Performs complex data analysis tasks.

**Usage Example:**

```python
from smol_sql_agents import AnalyticsAgent

agent = AnalyticsAgent()
analysis = agent.analyze(
    question="Perform cohort analysis on our user base",
    schema=database_schema
)
```

**Features:**

- Statistical analysis
- Pattern recognition
- Predictive modeling
- Data segmentation

## Agent Lifecycle

1. **Initialization**
   - Load configuration
   - Initialize LLM client
   - Set up database connections

2. **Execution**
   - Parse user query
   - Generate SQL
   - Execute query
   - Process results

3. **Response**
   - Format output
   - Add explanations
   - Include metadata

## Custom Agents

You can create custom agents by extending the `BaseAgent` class:

```python
from smol_sql_agents import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_type = "custom"
    
    async def execute(self, query: str, **kwargs):
        # Custom implementation
        pass
```

## Agent Configuration

Agents can be configured using environment variables or programmatically:

```python
from smol_sql_agents import NL2SQLAgent

agent = NL2SQLAgent(
    model_name="gpt-4",
    temperature=0.1,
    max_retries=3,
    timeout=30
)
```

## Error Handling

Agents implement robust error handling:

- Invalid SQL generation
- Database connection issues
- Rate limiting
- Timeout handling

## Performance Considerations

- **Caching**: Query results and embeddings are cached
- **Batching**: Multiple operations in single transactions
- **Async**: Non-blocking operations for better throughput

## Best Practices

1. **Agent Selection**: Choose the most specific agent for your task
2. **Error Handling**: Implement appropriate error handling for agent operations
3. **Monitoring**: Track agent performance and usage
4. **Testing**: Test agents with various query types and edge cases

## Related Documentation

- [Architecture Overview](./architecture.md)
- [Prompt Engineering](./prompt_engineering.md)
- [API Reference](../api/agents/README.md)
