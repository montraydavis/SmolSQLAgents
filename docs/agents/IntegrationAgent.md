# Integration Agent

The Integration Agent (SQLAgentPipeline) is the central orchestrator that coordinates the complete SQL generation pipeline from natural language queries to validated SQL statements. It seamlessly integrates Entity Recognition, Business Context, and NL2SQL agents to provide end-to-end SQL generation capabilities.

## 🎯 What It Does

The Integration Agent orchestrates a multi-step pipeline for intelligent SQL generation:

- **Pipeline Orchestration**: Coordinates Entity Recognition → Business Context → SQL Generation workflow
- **Agent Integration**: Manages shared instances of Entity Recognition, Business Context, and NL2SQL agents
- **Error Handling**: Provides comprehensive error handling and fallback mechanisms for each pipeline step
- **Response Formatting**: Delivers consistent, structured responses with detailed pipeline status
- **State Management**: Maintains pipeline state and enables step-by-step debugging
- **Performance Optimization**: Uses shared agent instances to minimize resource usage

## 🔄 Pipeline Flow

```markdown
User Query → Entity Recognition → Business Context → SQL Generation → Validation → Final Response
```

1. **Entity Recognition**: Identifies relevant database tables and relationships
2. **Business Context**: Gathers business rules and domain knowledge
3. **SQL Generation**: Creates SQL queries using context and entity information
4. **Validation**: Validates SQL syntax, security, and business compliance
5. **Response Formatting**: Returns comprehensive results with pipeline status

## 🚀 Usage Examples

### Command Line Interface

```bash
# Complete pipeline processing
python main.py --pipeline "Show me customer orders from last month"

# Pipeline with custom intent
python main.py --pipeline "Get user analytics" --intent "I need to analyze user engagement metrics"

# Pipeline with specific entities
python main.py --pipeline "customer data analysis" --entities "users,orders,customers"
```

### Programmatic Usage

```python
from src.agents.integration import SQLAgentPipeline
from src.agents.factory import agent_factory

# Get pipeline from factory
pipeline = agent_factory.get_sql_pipeline()

# Process user query through complete pipeline
result = pipeline.process_user_query(
    user_query="Show me customer orders from last month",
    user_intent="I need to analyze recent customer purchasing patterns"
)

# Check pipeline results
if result["success"]:
    print(f"Generated SQL: {result['sql_generation']['generated_sql']}")
    print(f"Entities found: {result['entity_recognition']['entities']}")
    print(f"Business concepts: {result['business_context']['matched_concepts']}")
else:
    print(f"Pipeline failed: {result['error']}")
```

## 📊 Response Structure

### Complete Pipeline Response

```json
{
  "success": true,
  "pipeline_summary": {
    "entity_recognition_success": true,
    "business_context_success": true,
    "sql_generation_success": true,
    "sql_validation_success": true
  },
  "entity_recognition": {
    "entities": ["users", "orders", "customers"],
    "confidence": 0.92
  },
  "business_context": {
    "matched_concepts": [
      {
        "name": "customer_analytics",
        "description": "Customer behavior analysis",
        "similarity": 0.85
      }
    ],
    "business_instructions": [
      {
        "concept": "customer_analytics",
        "instructions": "Use customer_id for joins, filter by date ranges",
        "similarity": 0.85
      }
    ]
  },
  "sql_generation": {
    "generated_sql": "SELECT c.customer_name, o.order_date, o.total_amount FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_date >= DATEADD(month, -1, GETDATE())",
    "is_valid": true,
    "validation": {
      "syntax_valid": true,
      "business_compliant": true,
      "security_valid": true,
      "performance_issues": []
    },
    "query_execution": {
      "success": true,
      "total_rows": 150,
      "sample_data": {...}
    }
  }
}
```

### Pipeline Error Response

```json
{
  "success": false,
  "error": "Entity recognition failed",
  "step": "entity_recognition",
  "details": "No relevant entities found for the query"
}
```

## 🧠 Pipeline Algorithm

The Integration Agent implements a sophisticated multi-step pipeline:

### Step 1: Entity Recognition
```python
def _execute_entity_recognition(self, user_query: str, user_intent: str):
    # Use Entity Recognition Agent to identify relevant tables
    entity_results = self.entity_agent.recognize_entities_optimized(
        user_query, user_intent, max_entities=10
    )
    # Extract and validate entity information
    return self._format_entity_results(entity_results)
```

### Step 2: Business Context Gathering
```python
def _gather_business_context(self, user_query: str, entity_results: Dict):
    # Extract entities from recognition results
    entities = self._extract_entities(entity_results)
    # Use Business Context Agent to gather domain knowledge
    business_context = self.business_agent.gather_business_context(
        user_query, entities
    )
    return business_context
```

### Step 3: SQL Generation
```python
def _generate_sql(self, user_query: str, business_context: Dict, entity_context: Dict):
    # Build entity context for SQL generation
    entity_context_for_sql = self._build_entity_context(entity_results)
    # Use NL2SQL Agent to generate validated SQL
    sql_results = self.nl2sql_agent.generate_sql_optimized(
        user_query, business_context, entity_context_for_sql
    )
    return sql_results
```

### Step 4: Response Formatting
```python
def _format_final_response(self, entity_results: Dict, business_context: Dict, sql_results: Dict):
    # Combine all pipeline results into comprehensive response
    return {
        "success": True,
        "pipeline_summary": {...},
        "entity_recognition": {...},
        "business_context": {...},
        "sql_generation": {...}
    }
```

## ⚙️ Configuration

### Environment Variables

```env
# Required for pipeline components
OPENAI_API_KEY="your-api-key-here"

# Required for database connection
DATABASE_URL="your-database-connection-string"

# Optional: Pipeline settings
EMBEDDING_BATCH_SIZE="100"
EMBEDDING_MAX_RETRIES="3"

# Optional: Logging configuration
LOG_LEVEL="INFO"
LOG_FILE="pipeline.log"
```

### Initialization Parameters

```python
SQLAgentPipeline(
    indexer_agent,                    # Required: SQLIndexerAgent instance
    database_tools,                   # Required: DatabaseTools instance
    shared_entity_agent=None,         # Optional: Shared EntityRecognitionAgent
    shared_business_agent=None,       # Optional: Shared BusinessContextAgent
    shared_nl2sql_agent=None         # Optional: Shared NL2SQLAgent
)

# Method parameters
process_user_query(
    user_query,                       # Required: Natural language query
    user_intent=None                  # Optional: Specific user intent
)
```

## 🎯 Use Cases

### 1. Complete SQL Generation Pipeline

Generate SQL from natural language with full context:

```python
# Process complex business query
result = pipeline.process_user_query(
    user_query="Show me customer retention rates by month",
    user_intent="I need to analyze customer loyalty patterns for Q4 planning"
)

if result["success"]:
    sql = result["sql_generation"]["generated_sql"]
    print(f"Generated SQL: {sql}")
    
    # Check validation results
    validation = result["sql_generation"]["validation"]
    if validation["syntax_valid"] and validation["business_compliant"]:
        print("SQL is valid and business-compliant")
```

### 2. Step-by-Step Pipeline Debugging

Debug individual pipeline steps:

```python
# Step 1: Entity Recognition
entity_results = pipeline._execute_entity_recognition(
    "customer analytics", "I need user behavior data"
)
print(f"Found entities: {entity_results['entities']}")

# Step 2: Business Context
business_context = pipeline._gather_business_context(
    "customer analytics", entity_results
)
print(f"Business concepts: {business_context['matched_concepts']}")

# Step 3: SQL Generation
entity_context = pipeline._build_entity_context(entity_results)
sql_results = pipeline._generate_sql(
    "customer analytics", business_context, entity_context
)
print(f"Generated SQL: {sql_results['generated_sql']}")
```

### 3. Pipeline Performance Monitoring

Monitor pipeline performance and success rates:

```python
# Track pipeline performance
pipeline_results = []
queries = ["customer data", "order analysis", "user metrics"]

for query in queries:
    result = pipeline.process_user_query(query)
    pipeline_results.append({
        "query": query,
        "success": result["success"],
        "pipeline_summary": result.get("pipeline_summary", {}),
        "entities_found": len(result.get("entity_recognition", {}).get("entities", [])),
        "sql_generated": bool(result.get("sql_generation", {}).get("generated_sql"))
    })

# Analyze results
success_rate = sum(1 for r in pipeline_results if r["success"]) / len(pipeline_results)
print(f"Pipeline success rate: {success_rate:.2%}")
```

### 4. Custom Pipeline Configuration

Configure pipeline with specific agent instances:

```python
# Create custom agent instances
from src.agents.entity_recognition import EntityRecognitionAgent
from src.agents.business import BusinessContextAgent
from src.agents.nl2sql import NL2SQLAgent

custom_entity_agent = EntityRecognitionAgent(indexer_agent)
custom_business_agent = BusinessContextAgent(indexer_agent)
custom_nl2sql_agent = NL2SQLAgent(database_tools)

# Create pipeline with custom agents
custom_pipeline = SQLAgentPipeline(
    indexer_agent=indexer_agent,
    database_tools=database_tools,
    shared_entity_agent=custom_entity_agent,
    shared_business_agent=custom_business_agent,
    shared_nl2sql_agent=custom_nl2sql_agent
)
```

## 🔍 Integration with Other Agents

The Integration Agent orchestrates all other agents:

- **Entity Recognition Agent**: Identifies relevant database entities
- **Business Context Agent**: Gathers domain knowledge and business rules
- **NL2SQL Agent**: Generates and validates SQL queries
- **Indexer Agent**: Provides semantic search capabilities
- **Database Tools**: Enables schema inspection and query execution

## 🎖️ Advanced Features

### Intelligent Error Handling

- Comprehensive error tracking for each pipeline step
- Graceful degradation when individual steps fail
- Detailed error reporting with actionable feedback
- Automatic retry mechanisms for transient failures

### Performance Optimization

- Shared agent instances to minimize resource usage
- Caching of intermediate results for repeated queries
- Parallel processing where possible
- Memory-efficient processing for large datasets

### Pipeline Monitoring

- Real-time pipeline status tracking
- Step-by-step success/failure reporting
- Performance metrics and timing information
- Detailed logging for debugging and optimization

### Response Consistency

- Standardized response format across all pipeline steps
- Comprehensive status reporting for each component
- Detailed validation results and error information
- Structured data for easy integration with other systems

## 📈 Performance Characteristics

- **Pipeline Response Time**: 5-15 seconds for complete pipeline execution
- **Entity Recognition**: 1-3 seconds for entity identification
- **Business Context**: 2-5 seconds for context gathering
- **SQL Generation**: 3-8 seconds for query generation and validation
- **Memory Usage**: Efficient memory management with shared components
- **Scalability**: Handles complex queries with multiple entities and business rules

## 🚦 Prerequisites

1. **All Agent Components**: Requires functional Entity Recognition, Business Context, and NL2SQL agents
2. **Database Connection**: Accessible database with schema information
3. **OpenAI API Access**: Valid API key for LLM processing
4. **Vector Indexing**: Functional vector store for semantic search
5. **Dependencies**: All required packages from requirements.txt

## 🔧 Error Handling

### Common Error Scenarios

1. **Entity Recognition Failures**: No relevant entities found for query
2. **Business Context Errors**: Unable to match business concepts
3. **SQL Generation Issues**: Invalid SQL syntax or business rule violations
4. **Validation Failures**: Security, performance, or compliance issues

### Error Response Handling

```python
# Handle pipeline errors
try:
    result = pipeline.process_user_query("complex query")
    
    if not result["success"]:
        error_step = result.get("step", "unknown")
        error_message = result.get("error", "Unknown error")
        
        if error_step == "entity_recognition":
            print(f"Entity recognition failed: {error_message}")
            # Fallback to manual entity specification
        elif error_step == "business_context":
            print(f"Business context failed: {error_message}")
            # Continue with minimal business context
        elif error_step == "sql_generation":
            print(f"SQL generation failed: {error_message}")
            # Provide alternative query suggestions
            
except Exception as e:
    print(f"Pipeline execution failed: {e}")
    # Implement fallback mechanisms
```

### Recovery Mechanisms

1. **Entity Recognition Fallback**: Use table name matching when semantic search fails
2. **Business Context Fallback**: Continue with minimal context when concept matching fails
3. **SQL Generation Fallback**: Provide simplified queries when complex generation fails
4. **Validation Bypass**: Allow execution with warnings when validation fails

---

The Integration Agent provides the complete orchestration layer for intelligent SQL generation, seamlessly coordinating multiple specialized agents to deliver accurate, validated SQL queries from natural language input with comprehensive business context and domain knowledge. 