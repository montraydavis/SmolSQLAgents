# NL2SQL Agent

The NL2SQL Agent is an intelligent component that converts natural language queries into validated SQL statements. It combines LLM-powered query generation with comprehensive validation including syntax checking, security analysis, performance optimization, and business compliance verification.

## 🎯 What It Does

The NL2SQL Agent provides sophisticated natural language to SQL conversion:

- **Query Generation**: Converts natural language to T-SQL using GPT-4 with context awareness
- **Parallel Validation**: Simultaneously validates syntax, security, performance, and business compliance
- **Caching System**: Implements intelligent caching to avoid redundant validation for similar queries
- **Query Execution**: Tests generated SQL with sample data and provides execution results
- **Error Recovery**: Handles generation failures with detailed error reporting and suggestions
- **Business Integration**: Incorporates business context and domain knowledge into SQL generation

## 🔄 Processing Flow

```markdown
Natural Language Query → Context Building → LLM Generation → SQL Extraction → Parallel Validation → Query Execution → Final Response
```

1. **Context Building**: Combines user query with business context and entity information
2. **LLM Generation**: Uses GPT-4 to generate SQL with schema and business rules
3. **SQL Extraction**: Extracts clean SQL from LLM response using multiple patterns
4. **Parallel Validation**: Simultaneously validates syntax, security, performance, and business rules
5. **Query Execution**: Tests SQL with sample data and provides execution statistics
6. **Response Formatting**: Returns comprehensive results with validation details

## 🚀 Usage Examples

### Command Line Interface

```bash
# Generate SQL from natural language
python main.py --nl2sql "Show me customer orders from last month"

# Generate SQL with business context
python main.py --nl2sql "customer analytics" --context "business_rules.yaml"

# Generate SQL with specific entities
python main.py --nl2sql "user metrics" --entities "users,orders,profiles"
```

### Programmatic Usage

```python
from src.agents.nl2sql import NL2SQLAgent
from src.agents.factory import agent_factory

# Get NL2SQL agent from factory
nl2sql_agent = agent_factory.get_nl2sql_agent()

# Generate SQL with business context
business_context = {
    "matched_concepts": [
        {"name": "customer_analytics", "instructions": "Use customer_id for joins"}
    ],
    "business_instructions": [
        {"concept": "customer_analytics", "instructions": "Filter by date ranges"}
    ]
}

entity_context = {
    "entities": ["customers", "orders"],
    "entity_descriptions": {
        "customers": "Customer account information",
        "orders": "Customer order data"
    },
    "confidence_scores": {"customers": 0.9, "orders": 0.8}
}

result = nl2sql_agent.generate_sql_optimized(
    user_query="Show me customer orders from last month",
    business_context=business_context,
    entity_context=entity_context
)

if result["success"]:
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Validation: {result['validation']}")
    print(f"Execution: {result['query_execution']}")
else:
    print(f"Generation failed: {result['error']}")
```

## 📊 Response Structure

### Successful SQL Generation Response

```json
{
  "success": true,
  "generated_sql": "SELECT c.customer_name, o.order_date, o.total_amount FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_date >= DATEADD(month, -1, GETDATE()) ORDER BY o.order_date DESC",
  "validation": {
    "syntax_valid": true,
    "business_compliant": true,
    "security_valid": true,
    "performance_issues": []
  },
  "query_execution": {
    "success": true,
    "total_rows": 150,
    "returned_rows": 150,
    "truncated": false,
    "sample_data": {
      "sample_rows": [
        {"customer_name": "John Doe", "order_date": "2024-01-15", "total_amount": 299.99},
        {"customer_name": "Jane Smith", "order_date": "2024-01-14", "total_amount": 149.50}
      ],
      "columns": ["customer_name", "order_date", "total_amount"],
      "numeric_stats": {
        "total_amount": {
          "min": 25.00,
          "max": 599.99,
          "avg": 187.45
        }
      }
    }
  },
  "is_valid": true
}
```

### Validation Error Response

```json
{
  "success": true,
  "generated_sql": "SELECT * FROM customers WHERE customer_id = 123",
  "validation": {
    "syntax_valid": true,
    "business_compliant": false,
    "security_valid": false,
    "performance_issues": ["No WHERE clause optimization", "Missing indexes"]
  },
  "query_execution": {
    "success": false,
    "error": "Access denied: Insufficient permissions"
  },
  "is_valid": false
}
```

### Generation Error Response

```json
{
  "success": false,
  "error": "No valid SQL generated from LLM response",
  "generated_sql": "",
  "is_valid": false
}
```

## 🧠 Processing Algorithm

The NL2SQL Agent implements a sophisticated multi-stage processing pipeline:

### Stage 1: Context Building
```python
def _build_query_prompt(self, user_query: str, business_context: Dict, entity_context: Dict):
    # Combine user query with business rules and entity information
    schema_info = self._format_schema_info(entity_context.get("table_schemas", {}))
    business_instructions = business_context.get("business_instructions", [])
    
    return f"""
    Generate T-SQL for: {user_query}
    Schema: {schema_info}
    Business Rules: {business_instructions}
    Instructions: Use tools to verify schema and test query
    """
```

### Stage 2: LLM Generation
```python
def generate_sql_optimized(self, user_query: str, business_context: Dict, entity_context: Dict):
    # Build comprehensive prompt
    prompt = self._build_query_prompt(user_query, business_context, entity_context)
    
    # Generate SQL using LLM
    response = self.agent.run(prompt)
    generated_sql = self._extract_sql_from_response(response)
    
    # Check cache for validation results
    cache_key = self._get_cache_key(f"{generated_sql}:{hash(str(business_context))}")
    cached_validation = self._get_cached_result(cache_key)
    
    if cached_validation:
        return self._format_response_with_cache(generated_sql, cached_validation)
    
    # Perform parallel validation
    return self._execute_parallel_validation(generated_sql, business_context)
```

### Stage 3: Parallel Validation
```python
def _execute_parallel_validation(self, sql: str, business_context: Dict):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            "syntax": executor.submit(self.validate, sql, "syntax"),
            "business": executor.submit(self._check_business_compliance, sql, business_context),
            "security": executor.submit(self.validate, sql, "security"),
            "performance": executor.submit(self.validate, sql, "performance"),
            "execution": executor.submit(self._execute_query_impl, sql, 100)
        }
        
        results = {name: future.result() for name, future in futures.items()}
        return self._format_validation_response(sql, results)
```

### Stage 4: SQL Extraction
```python
def _extract_sql_from_response(self, response) -> Optional[str]:
    # Multiple extraction patterns for robust SQL extraction
    patterns = [
        r'```sql\s*(.*?)\s*```',           # Code blocks
        r'final_answer\s*\(\s*["\']([^"\']*)["\']',  # Tool calls
        r'SELECT.*?;',                      # Direct SQL
        r'FROM.*?WHERE.*?',                # Partial SQL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None
```

## ⚙️ Configuration

### Environment Variables

```env
# Required for LLM processing
OPENAI_API_KEY="your-api-key-here"

# Required for database connection
DATABASE_URL="your-database-connection-string"

# Optional: Caching settings
CACHE_SIZE="50"
CACHE_TTL="3600"

# Optional: Validation settings
VALIDATION_TIMEOUT="30"
MAX_EXECUTION_ROWS="100"

# Optional: Logging configuration
LOG_LEVEL="INFO"
LOG_FILE="nl2sql.log"
```

### Initialization Parameters

```python
NL2SQLAgent(
    database_tools,              # Required: DatabaseTools instance
    shared_llm_model=None        # Optional: Shared LLM model instance
)

# Method parameters
generate_sql_optimized(
    user_query,                  # Required: Natural language query
    business_context,            # Required: Business context dictionary
    entity_context              # Required: Entity context dictionary
)
```

## 🎯 Use Cases

### 1. Basic SQL Generation

Generate SQL from simple natural language queries:

```python
# Simple query generation
result = nl2sql_agent.generate_sql_optimized(
    user_query="Show me all customers",
    business_context={},
    entity_context={"entities": ["customers"]}
)

if result["success"]:
    print(f"SQL: {result['generated_sql']}")
    print(f"Valid: {result['is_valid']}")
```

### 2. Complex Business Queries

Generate SQL with business rules and domain knowledge:

```python
# Complex business query
business_context = {
    "matched_concepts": [
        {
            "name": "customer_retention",
            "instructions": "Calculate customer retention rates by month"
        }
    ],
    "business_instructions": [
        {
            "concept": "customer_retention",
            "instructions": "Use customer_id for joins, filter active customers only"
        }
    ]
}

result = nl2sql_agent.generate_sql_optimized(
    user_query="Calculate customer retention rates by month",
    business_context=business_context,
    entity_context={"entities": ["customers", "orders"]}
)
```

### 3. Query Validation and Testing

Validate and test generated SQL:

```python
# Generate and validate SQL
result = nl2sql_agent.generate_sql_optimized(
    user_query="Get top 10 customers by order value",
    business_context={},
    entity_context={"entities": ["customers", "orders"]}
)

# Check validation results
validation = result["validation"]
if validation["syntax_valid"]:
    print("SQL syntax is valid")
if validation["security_valid"]:
    print("SQL passes security checks")
if validation["business_compliant"]:
    print("SQL complies with business rules")

# Check execution results
execution = result["query_execution"]
if execution["success"]:
    print(f"Query returned {execution['total_rows']} rows")
    print(f"Sample data: {execution['sample_data']}")
```

### 4. Caching and Performance

Leverage caching for improved performance:

```python
# First query (will be cached)
result1 = nl2sql_agent.generate_sql_optimized(
    user_query="Show customer orders",
    business_context={},
    entity_context={"entities": ["customers", "orders"]}
)

# Similar query (will use cache)
result2 = nl2sql_agent.generate_sql_optimized(
    user_query="Get customer orders",
    business_context={},
    entity_context={"entities": ["customers", "orders"]}
)

# Clear cache if needed
nl2sql_agent.clear_cache()
```

## 🔍 Integration with Other Agents

The NL2SQL Agent works seamlessly with other components:

- **Business Context Agent**: Receives business rules and domain knowledge
- **Entity Recognition Agent**: Uses identified entities for context
- **Database Tools**: Executes queries and inspects schema
- **Validation Components**: Performs syntax, security, and performance checks
- **Caching System**: Optimizes performance for repeated queries

## 🎖️ Advanced Features

### Intelligent Caching

- MD5-based cache keys for efficient storage
- Configurable cache size with automatic cleanup
- Cache invalidation based on business context changes
- Performance optimization for repeated queries

### Parallel Validation

- Concurrent validation of syntax, security, performance, and business rules
- ThreadPoolExecutor for efficient parallel processing
- Comprehensive validation reporting with detailed feedback
- Graceful handling of validation failures

### SQL Extraction Patterns

- Multiple regex patterns for robust SQL extraction
- Support for code blocks, tool calls, and direct SQL
- Fallback mechanisms for edge cases
- Detailed logging for extraction debugging

### Query Execution Testing

- Safe query execution with row limits
- Sample data generation with statistics
- Numeric analysis for quantitative results
- Error handling for execution failures

## 📈 Performance Characteristics

- **SQL Generation**: 2-5 seconds for typical queries
- **Parallel Validation**: 1-3 seconds for comprehensive validation
- **Query Execution**: 0.5-2 seconds for sample data retrieval
- **Cache Hit Rate**: 60-80% for similar queries
- **Memory Usage**: Efficient caching with automatic cleanup
- **Scalability**: Handles complex queries with multiple joins and conditions

## 🚦 Prerequisites

1. **Database Connection**: Accessible database with schema information
2. **OpenAI API Access**: Valid API key for LLM processing
3. **Database Tools**: Functional database tools for query execution
4. **Validation Components**: Syntax, security, and business validators
5. **Dependencies**: All required packages from requirements.txt

## 🔧 Error Handling

### Common Error Scenarios

1. **LLM Generation Failures**: Invalid responses, API errors, timeout issues
2. **SQL Extraction Failures**: Unable to extract SQL from LLM response
3. **Validation Errors**: Syntax errors, security violations, business rule violations
4. **Execution Failures**: Database connection issues, permission problems

### Error Response Handling

```python
# Handle generation errors
try:
    result = nl2sql_agent.generate_sql_optimized(
        user_query="complex query",
        business_context={},
        entity_context={}
    )
    
    if not result["success"]:
        error = result.get("error", "Unknown error")
        
        if "No valid SQL generated" in error:
            print("LLM failed to generate valid SQL")
            # Try with simplified prompt
        elif "Validation failed" in error:
            print("Generated SQL failed validation")
            # Provide alternative query suggestions
        elif "Execution failed" in error:
            print("Query execution failed")
            # Check database connection and permissions
            
except Exception as e:
    print(f"NL2SQL processing failed: {e}")
    # Implement fallback mechanisms
```

### Recovery Mechanisms

1. **LLM Fallback**: Retry with simplified prompts when complex generation fails
2. **Extraction Fallback**: Use multiple patterns when primary extraction fails
3. **Validation Bypass**: Allow execution with warnings when validation fails
4. **Cache Invalidation**: Clear cache when validation results are inconsistent

---

The NL2SQL Agent provides sophisticated natural language to SQL conversion with comprehensive validation, intelligent caching, and robust error handling, making it the core component for intelligent query generation in the SQL Documentation suite. 