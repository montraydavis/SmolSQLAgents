# Chapter 6: SQL Generation and Execution

In this chapter, we'll enhance our AI agents with the ability to generate, validate, and execute SQL queries based on natural language questions. This will transform our documentation system into an interactive query assistant.

## SQL Generation Architecture

We'll implement a two-phase approach:
1. **Query Planning**: Analyze the question and generate a query plan
2. **Query Generation & Execution**: Convert the plan into executable SQL and run it

## Implementing the SQL Generation Agent

First, let's create a new agent for SQL generation:

```python
# src/agents/sql_generation_agent.py
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
import re
import json

class SQLGenerationAgent(BaseAgent):
    """Agent that generates SQL queries from natural language questions."""
    
    async def generate_sql(
        self,
        question: str,
        schema_info: Dict[str, Any],
        examples: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate SQL query based on the question and schema."""
        # Prepare schema context
        schema_context = "\n".join([
            f"Table: {table_name}\n"
            f"Columns: {', '.join([col['name'] for col in table_info['columns']])}"
            for table_name, table_info in schema_info.items()
        ])
        
        # Prepare examples if provided
        examples_context = ""
        if examples:
            examples_context = "\n\nExamples:\n" + "\n".join([
                f"Q: {ex['question']}\nA: {ex['sql']}"
                for ex in examples
            ])
        
        system_prompt = """You are a SQL expert. Generate a SQL query that answers the user's question.
        
        Follow these rules:
        1. Only generate SELECT queries unless explicitly asked to modify data
        2. Always use table aliases for clarity
        3. Include all necessary JOINs based on foreign key relationships
        4. Use proper SQL syntax for the database type
        5. If the question is ambiguous, make reasonable assumptions and note them
        """
        
        user_prompt = f"""Database Schema:
        {schema_context}
        
        {examples_context}
        
        Question: {question}
        
        Please provide the SQL query in this JSON format:
        {{
            "query": "SELECT ...",
            "tables_used": ["table1", "table2"],
            "assumptions": ["Assumption 1", "Assumption 2"],
            "description": "Brief description of what the query does"
        }}"""
        
        response = await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1  # Keep it deterministic
        )
        
        try:
            result = self.parse_json_response(response)
            # Basic validation
            if not isinstance(result, dict) or 'query' not in result:
                raise ValueError("Invalid response format")
            return result
        except Exception as e:
            return {
                "error": f"Failed to generate SQL: {str(e)}",
                "raw_response": response
            }
    
    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """Basic SQL validation."""
        # Check for common SQL injection patterns
        sql_upper = sql.upper()
        forbidden_patterns = [
            r'\b(DROP|TRUNCATE|DELETE\s+FROM|UPDATE\s+\w+\s+SET|INSERT\s+INTO)\b',
            r';\s*--',
            r'\b(EXEC\s*\(|EXECUTE\s+\w+\s*\()',
            r'\b(UNION\s+SELECT|SELECT\s+.*\bFROM\b.*\bWHERE\s+\d+\s*=\s*\d+)\b'
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return {
                    "valid": False,
                    "error": f"Query contains potentially dangerous pattern: {pattern}"
                }
        
        return {"valid": True}
```

## Implementing the Query Execution Service

Let's create a service to safely execute SQL queries:

```python
# src/services/query_execution_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, exc
from sqlalchemy.engine import Engine
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class QueryExecutionService:
    """Service for safely executing SQL queries."""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or create_engine(os.getenv("DATABASE_URL"))
        self.query_timeout = int(os.getenv("QUERY_TIMEOUT", "30"))  # seconds
    
    async def execute_query(
        self,
        sql: str,
        params: Optional[Dict] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Execute a SQL query and return the results."""
        if not sql.strip().upper().startswith("SELECT"):
            return {
                "success": False,
                "error": "Only SELECT queries are allowed"
            }
        
        # Add LIMIT if not present
        if "LIMIT" not in sql.upper() and limit > 0:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        try:
            with self.engine.connect() as connection:
                # Set statement timeout
                connection.execute(text(f"SET statement_timeout = {self.query_timeout * 1000}"))
                
                # Execute query
                result = connection.execute(text(sql), params or {})
                
                # Convert to list of dicts
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                
                # Get row count without LIMIT (approximate for performance)
                count = len(rows)
                if count == limit:
                    count = connection.execute(
                        text(f"SELECT COUNT(*) FROM ({sql.split('LIMIT')[0]}) as subq")
                    ).scalar()
                
                return {
                    "success": True,
                    "data": rows,
                    "columns": columns,
                    "row_count": count,
                    "limited": len(rows) == limit
                }
                
        except exc.SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": sql
            }
    
    async def explain_query(self, sql: str) -> Dict[str, Any]:
        """Get query execution plan."""
        explain_sql = f"EXPLAIN ANALYZE {sql}"
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(explain_sql))
                plan = "\n".join([row[0] for row in result])
                return {
                    "success": True,
                    "plan": plan
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

## Updating the Orchestrator

Let's update our orchestrator to include SQL generation and execution:

```python
# src/agents/orchestrator.py (updated)
from typing import Dict, Any, Optional, List
from .query_understanding_agent import QueryUnderstandingAgent
from .retrieval_agent import RetrievalAgent
from .response_agent import ResponseAgent
from .sql_generation_agent import SQLGenerationAgent
from src.services.document_service import DocumentService
from src.services.query_execution_service import QueryExecutionService
from src.db.schema import get_schema_info

class AgentOrchestrator:
    """Orchestrates the flow between different agents with SQL capabilities."""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.query_agent = QueryUnderstandingAgent()
        self.retrieval_agent = RetrievalAgent(self.document_service)
        self.response_agent = ResponseAgent()
        self.sql_agent = SQLGenerationAgent()
        self.query_service = QueryExecutionService()
        self.schema_info = None
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get and cache schema information."""
        if self.schema_info is None:
            # This is a simplified example - in practice, you'd want to format
            # the schema info in a way that's useful for SQL generation
            engine = create_database_engine()
            self.schema_info = get_schema_info(engine)
        return self.schema_info
    
    async def process_query(self, user_query: str, execute_sql: bool = False) -> Dict[str, Any]:
        """Process a user query with optional SQL execution."""
        # Step 1: Understand the query
        query_analysis = await self.query_agent.process(user_query)
        
        # Step 2: Generate SQL if it's a data question
        sql_result = None
        if query_analysis.get("action_required") == "generate_code":
            schema_info = await self.get_schema_info()
            sql_result = await self.sql_agent.generate_sql(
                question=user_query,
                schema_info=schema_info
            )
            
            # If SQL was generated and execution is requested
            if execute_sql and "query" in sql_result:
                execution_result = await self.query_service.execute_query(
                    sql_result["query"]
                )
                sql_result["execution_result"] = execution_result
        
        # Step 3: Retrieve relevant documentation
        retrieval_result = await self.retrieval_agent.process(query_analysis)
        
        # Step 4: Generate a response
        response = await self.response_agent.process({
            "query_analysis": query_analysis,
            "sql_generation": sql_result,
            "retrieval_result": retrieval_result
        })
        
        # Prepare the full result
        result = {
            "query": user_query,
            "query_analysis": query_analysis,
            "response": response,
            "sources": [
                {
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "relevance": 1 - doc["distance"]
                }
                for doc in retrieval_result.get("retrieved_docs", [])
            ]
        }
        
        # Add SQL generation results if available
        if sql_result:
            result["sql_generation"] = {
                "query": sql_result.get("query"),
                "tables_used": sql_result.get("tables_used", []),
                "assumptions": sql_result.get("assumptions", []),
                "description": sql_result.get("description", "")
            }
            
            if "execution_result" in sql_result:
                result["execution_result"] = {
                    "success": sql_result["execution_result"]["success"],
                    "row_count": sql_result["execution_result"].get("row_count", 0),
                    "limited": sql_result["execution_result"].get("limited", False)
                }
        
        return result
```

## Testing SQL Generation and Execution

Let's create a test script to see our enhanced system in action:

```python
# examples/test_sql_generation.py
import asyncio
from src.agents.orchestrator import AgentOrchestrator

async def main():
    # Initialize the orchestrator
    orchestrator = AgentOrchestrator()
    
    # Test queries
    test_queries = [
        "Show me the top 5 customers by total spending",
        "List all products that are out of stock",
        "Find orders placed in the last 7 days",
        "What's the average order value by month?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print("-" * 80)
        
        try:
            # First, get the SQL without executing
            result = await orchestrator.process_query(query, execute_sql=False)
            
            print("\nGENERATED SQL:")
            print(result["sql_generation"]["query"])
            
            print("\nASSUMPTIONS:")
            for assumption in result["sql_generation"].get("assumptions", []):
                print(f"- {assumption}")
            
            # Ask user if they want to execute the query
            if input("\nExecute this query? (y/n): ").lower() == 'y':
                result = await orchestrator.process_query(query, execute_sql=True)
                
                if "execution_result" in result and result["execution_result"]["success"]:
                    print("\nQUERY EXECUTED SUCCESSFULLY")
                    print(f"Rows returned: {result['execution_result']['row_count']}")
                    # In a real app, you'd want to display the results in a nice format
                else:
                    print("\nQUERY EXECUTION FAILED")
                    print(result.get("sql_generation", {}).get("error", "Unknown error"))
            
            print("\nRESPONSE:")
            print(result["response"])
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Security Considerations

When implementing SQL generation and execution, security is paramount:

1. **Query Validation**: Always validate generated SQL before execution
2. **Read-Only Access**: Use a database user with read-only permissions
3. **Query Timeouts**: Set reasonable timeouts to prevent long-running queries
4. **Result Limiting**: Always limit the number of rows returned
5. **Input Sanitization**: Never directly interpolate user input into SQL
6. **Error Handling**: Don't expose database errors directly to users

## Next Steps

In the next chapter, we'll enhance our system with:
1. Multi-turn conversation support
2. Query result visualization
3. User feedback collection
4. Performance optimization techniques

Our system can now understand natural language questions, generate SQL queries, and execute them safely. The next step is to make the interaction more conversational and provide better visualization of the results.
