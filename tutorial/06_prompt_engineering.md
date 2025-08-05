# Chapter 6: Project Prompts Reference

This chapter documents the actual prompts used in the SQL Documentation Agents project. Each section describes a specific prompt, its purpose, and how it's used within the system.

## 1. NL2SQL Query Generation Prompt

**Location** `src/agents/nl2sql.py`  
**Purpose** Generates SQL queries from natural language requests

```python
def _build_query_prompt(self, user_query: str, business_context: Dict, entity_context: Dict) -> str:
    """Build query prompt."""
    schema_info = self._format_schema_info(entity_context.get("table_schemas", {}))
    business_instructions = business_context.get("business_instructions", [])
    
    business_context_str = ""
    if business_instructions:
        business_context_str = "Business context:\n"
        for instruction in business_instructions[:3]:  # Limit to top 3
            business_context_str += f"- {instruction.get('instructions', '')}\n"
    
    return f"""
    Generate T-SQL for the following request: {user_query}
    
    Available schema information:
    {schema_info}
    
    {business_context_str}
    
    Instructions:
    1. Use get_table_schema_unified_tool() to verify column names and table structure
    2. Test your query using execute_query_and_return_results() 
    3. Return the final SQL using final_answer()
    
    Generate clean, efficient T-SQL that answers the user's request.
    """
```

### Key Components

- **User Query** The natural language request from the user
- **Schema Information** Formatted table and column information
- **Business Context** Optional business rules or instructions
- **Tool Integration** Instructions for using available tools

### Usage Flow

1. The system receives a natural language query
2. Relevant schema information is gathered
3. Business context is applied if available
4. The prompt is constructed and sent to the LLM
5. The model generates SQL using the provided tools

## 2. Schema Information Formatter

**Location** `src/agents/nl2sql.py`  
**Purpose** Formats database schema information for use in prompts

```python
def _format_schema_info(self, table_schemas: Dict) -> str:
    """Format schema information for prompt."""
    if not table_schemas:
        return "No schema information available"
    
    schema_lines = []
    for table_name, schema in table_schemas.items():
        columns = schema.get("columns", [])
        column_names = [col.get("name", "") for col in columns if col.get("name")]
        if column_names:
            schema_lines.append(f"{table_name}: {', '.join(column_names)}")
    
    return "\n".join(schema_lines) if schema_lines else "No valid schema information"
```

### Format

```text
table1: column1, column2, column3
table2: columnA, columnB, columnC
```

## 3. SQL Response Extraction

**Location** `src/agents/nl2sql.py`  
**Purpose** Extracts SQL from various response formats

```python
def _extract_sql_from_response(self, response) -> Optional[str]:
    """Extract SQL from agent response."""
    if hasattr(response, 'text'):
        response = response.text
    
    # Handle dictionary response (from final_answer tool)
    if isinstance(response, dict):
        if 'final_sql' in response:
            return response['final_sql']
        elif 'sql' in response:
            return response['sql']
        elif 'query' in response:
            return response['query']
    
    if isinstance(response, str):
        # Extract SQL from code blocks
        import re
        sql_pattern = r'```sql\s*(.*?)\s*```'
        match = re.search(sql_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for final_answer in response
        final_answer_pattern = r'final_answer\s*\(\s*["\']([^"\']*)["\']'
        match = re.search(final_answer_pattern, response)
        if match:
            return match.group(1).strip()
    
    return None
```

### Supported Formats

1. Dictionary with `final_sql`, `sql`, or `query` keys
2. SQL code blocks (```sql ... ```)
3. `final_answer()` function calls

## 4. Validation Response Format

**Location** `src/agents/nl2sql.py`  
**Purpose** Standardizes validation results

```python
{
    "success": bool,
    "generated_sql": str,
    "validation": {
        "syntax_valid": bool,
        "business_compliant": bool,
        "security_valid": bool,
        "performance_issues": List[str]
    },
    "query_execution": Dict,
    "is_valid": bool
}
```

## 5. Business Compliance Check

**Location** `src/agents/nl2sql.py`  
**Purpose** Validates SQL against business rules

```python
def _check_business_compliance(self, query: str, business_context: Dict) -> Dict:
    """Check business compliance of query."""
    if not business_context:
        return {"valid": True, "message": "No business context provided"}
    
    try:
        result = self.business_validator.validate(query, business_context)
        return {
            "valid": result.get("valid", False),
            "message": result.get("message", ""),
            "issues": result.get("issues", [])
        }
    except Exception as e:
        logger.error(f"Business validation failed: {e}")
        return {"valid": False, "error": str(e)}
```

## 6. Query Execution

**Location** `src/agents/nl2sql.py`  
**Purpose** Executes and formats query results

```python
def _execute_query_impl(self, query: str, max_rows: int = 100) -> Dict:
    """Implementation of query execution."""
    try:
        result = self.database_tools.execute_query_safe(query, max_rows)
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Unknown error during query execution")
            }
        
        rows = result.get("rows", [])
        columns = result.get("columns", [])
        
        return {
            "success": True,
            "total_rows": len(rows),
            "returned_rows": len(rows),
            "truncated": len(rows) >= max_rows,
            "sample_data": self._create_sample_summary(rows, columns)
        }
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return {"success": False, "error": str(e)}
```

## 7. Sample Data Summary

**Location** `src/agents/nl2sql.py`  
**Purpose** Creates a summary of query results for inclusion in responses

```python
def _create_sample_summary(self, rows: List[Dict], columns: List[str]) -> Dict:
    """Create summary of sample data."""
    if not rows or not columns:
        return {"message": "No data returned"}
    
    # Get first few rows as samples
    sample_rows = rows[:5]  # Limit to 5 rows for summary
    
    # Get column statistics
    column_stats = {}
    for col in columns:
        values = [str(row.get(col, "")) for row in rows if col in row]
        col_type = "string"  # Simplified type detection
        if values:
            try:
                _ = float(values[0])
                col_type = "numeric"
            except (ValueError, TypeError):
                pass
        
        column_stats[col] = {
            "type": col_type,
            "non_null_count": len([v for v in values if v is not None and v != ""]),
            "sample_values": list(set(values[:3]))  # Show up to 3 unique values
        }
    
    return {
        "row_count": len(rows),
        "column_count": len(columns),
        "sample_rows": sample_rows,
        "column_stats": column_stats
    }
```

## Next Steps

In the next chapter, we'll explore how these prompts are integrated into the SQL generation workflow and how they interact with the database and business rules.
