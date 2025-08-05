# Smol-SQL-Agents API Documentation

## Overview

The Smol-SQL-Agents backend provides a RESTful API for natural language to SQL conversion, database schema exploration, and AI-powered documentation search. All endpoints are prefixed with `/api` and return JSON responses.

**Base URL**: `http://localhost:5000`

---

## 📋 Table of Contents

- [Health & Status Endpoints](#health--status-endpoints)
- [Query Processing Endpoints](#query-processing-endpoints)
- [Documentation & Schema Endpoints](#documentation--schema-endpoints)
- [Debug Endpoints](#debug-endpoints)
- [Error Handling](#error-handling)

---

## 🏥 Health & Status Endpoints

### GET `/api/message`

**Health check endpoint**

**Input**: None

**Output**:

```json
{
  "message": "Hello from the Smol-SQL-Agents backend! 👋"
}
```

**Status Codes**: 200

---

### GET `/api/status`

**Get SQL Agents status and system information**

**Input**: None

**Output**:

```json
{
  "sql_agents_available": true,
  "initialized": true,
  "environment": {
    "database_url_set": true,
    "openai_key_set": true
  },
  "agents": ["main_agent", "indexer_agent", "entity_agent", "business_agent"],
  "initialization_time": "2024-01-15T10:30:00",
  "factory_initialized": true
}
```

**Error Response** (500):

```json
{
  "error": "Error message",
  "sql_agents_available": false,
  "initialized": false
}
```

---

## 🔍 Query Processing Endpoints

### POST `/api/query`

**Execute natural language query and return SQL + results**

**Input**:

```json
{
  "query": "Show me the top 10 customers by total spending"
}
```

**Output** (Success):

```json
{
  "sql": "SELECT c.name, SUM(o.total) as total_spending FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY total_spending DESC LIMIT 10;",
  "results": [
    {
      "name": "John Doe",
      "total_spending": 1500.00
    }
  ],
  "query": "Show me the top 10 customers by total spending",
  "timestamp": "2024-01-15T10:30:00",
  "success": true,
  "pipeline_results": {
    "entity_recognition": {...},
    "business_context": {...},
    "sql_generation": {...}
  }
}
```

**Error Response** (400/500):

```json
{
  "sql": "",
  "results": [],
  "query": "query text",
  "timestamp": "2024-01-15T10:30:00",
  "success": false,
  "error": "Error message"
}
```

---

### POST `/api/recognize-entities`

**Recognize applicable database entities for a user query**

**Input**:

```json
{
  "query": "Find customers who made purchases",
  "intent": "customer_analysis",
  "max_entities": 5
}
```

**Output** (Success):

```json
{
  "success": true,
  "applicable_entities": [
    {
      "name": "customers",
      "confidence": 0.95,
      "reason": "Directly mentioned in query"
    },
    {
      "name": "orders",
      "confidence": 0.88,
      "reason": "Related to purchases"
    }
  ]
}
```

**Error Response** (400/500):

```json
{
  "success": false,
  "error": "Error message",
  "applicable_entities": []
}
```

---

### POST `/api/business-context`

**Gather business context for a user query**

**Input**:

```json
{
  "query": "Analyze customer spending patterns",
  "intent": "business_analytics"
}
```

**Output** (Success):

```json
{
  "success": true,
  "matched_concepts": [
    {
      "name": "customer_analytics",
      "similarity": 0.92
    },
    {
      "name": "revenue_tracking",
      "similarity": 0.88
    }
  ],
  "business_instructions": [
    {
      "concept": "customer_analytics",
      "instructions": "Focus on high-value customers and spending trends"
    }
  ]
}
```

**Error Response** (400/500):

```json
{
  "success": false,
  "error": "Error message",
  "matched_concepts": [],
  "business_instructions": []
}
```

---

### POST `/api/generate-sql`

**Generate SQL from natural language using the complete pipeline**

**Input**:

```json
{
  "query": "Find customers who spent more than $1000",
  "intent": "customer_segmentation"
}
```

**Output** (Success):

```json
{
  "success": true,
  "generated_sql": "SELECT * FROM customers WHERE total_spending > 1000",
  "validation": {
    "syntax_valid": true,
    "business_compliant": true,
    "security_valid": true,
    "performance_issues": []
  },
  "optimization_suggestions": [
    {
      "type": "Index Optimization",
      "priority": "medium",
      "impact": "20% performance improvement",
      "message": "Consider adding index on total_spending"
    }
  ]
}
```

**Error Response** (400/500):

```json
{
  "success": false,
  "error": "Error message",
  "generated_sql": "",
  "validation": {},
  "optimization_suggestions": []
}
```

---

## 📚 Documentation & Schema Endpoints

### POST `/api/search`

**Search documentation using text or vector search**

**Input**:

```json
{
  "query": "customer information",
  "type": "text"
}
```

**Alternative Input** (Vector Search):

```json
{
  "query": "How to find customer data and their purchase history",
  "type": "vector"
}
```

**Output** (Success):

```json
{
  "results": {
    "tables": [
      {
        "name": "customers",
        "description": "Customer information table",
        "columns": ["id", "name", "email", "created_at"],
        "relevance_score": 0.95
      }
    ],
    "relationships": [
      {
        "from_table": "customers",
        "to_table": "orders",
        "relationship_type": "one-to-many",
        "description": "Customer can have multiple orders"
      }
    ]
  },
  "query": "customer information",
  "type": "text",
  "total": 2
}
```

**Error Response** (400/500):

```json
{
  "results": [],
  "query": "search query",
  "type": "text",
  "total": 0,
  "error": "Error message"
}
```

---

### GET `/api/schema`

**Get database schema information**

**Input**: None

**Output** (Success):

```json
{
  "tables": [
    {
      "name": "customers",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "nullable": false,
          "primary_key": true
        },
        {
          "name": "name",
          "type": "VARCHAR(255)",
          "nullable": false,
          "primary_key": false
        }
      ]
    }
  ],
  "success": true
}
```

**Error Response** (500):

```json
{
  "tables": [],
  "success": false,
  "error": "Error message"
}
```

---

## 🐛 Debug Endpoints

### GET `/api/debug/objects`

**Debug endpoint to show object creation status**

**Input**: None

**Output** (Success):

```json
{
  "agent_manager_id": 140234567890,
  "factory_initialized": true,
  "initialization_time": "2024-01-15T10:30:00",
  "shared_components": {
    "llm_model": true,
    "database_tools": true,
    "instances_count": 5,
    "shared_components_count": 2
  },
  "agent_instances": {
    "main_agent": 140234567891,
    "indexer_agent": 140234567892,
    "entity_agent": 140234567893
  },
  "shared_components": {
    "concept_loader": 140234567894,
    "concept_matcher": 140234567895
  }
}
```

**Error Response** (500):

```json
{
  "error": "Error message",
  "objects": {}
}
```

---

### GET `/api/debug/database`

**Debug endpoint to show database performance metrics**

**Input**: None

**Output** (Success):

```json
{
  "database_inspector_id": 140234567896,
  "cache_stats": {
    "table_names_cached": true,
    "table_schemas_cached": 15,
    "relationships_cached": true,
    "initialization_time": 2.5
  },
  "connection_pool": {
    "pool_size": 5,
    "checked_in": 3,
    "checked_out": 2,
    "overflow": 0
  },
  "engine_config": {
    "echo": false,
    "pool_pre_ping": true,
    "pool_recycle": 3600
  }
}
```

**Error Response** (500):

```json
{
  "error": "Error message",
  "database_stats": {}
}
```

---

## 🏠 Root Endpoint

### GET `/`

**Root endpoint with API information**

**Input**: None

**Output**:

```json
{
  "message": "Smol-SQL-Agents Backend API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/api/message",
    "status": "/api/status",
    "query": "/api/query",
    "schema": "/api/schema"
  }
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format

All endpoints return consistent error responses with the following structure:

```json
{
  "success": false,
  "error": "Error description",
  "message": "Additional error details"
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Endpoint doesn't exist |
| 500 | Internal Server Error - Server-side error |

### Common Error Scenarios

#### Agent Manager Not Available

```json
{
  "success": false,
  "error": "Agent manager not available"
}
```

#### No JSON Data Provided

```json
{
  "success": false,
  "error": "No JSON data provided"
}
```

#### Query Cannot Be Empty

```json
{
  "success": false,
  "error": "Query cannot be empty"
}
```

---

## 🔧 Environment Variables

The API requires the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Database connection string | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | Yes |
| `SECRET_KEY` | Flask secret key | No (defaults to 'dev-secret-key') |
| `PORT` | Server port | No (defaults to 5000) |
| `FLASK_ENV` | Flask environment | No (defaults to production) |

---

## 📝 Usage Examples

### cURL Examples

**Health Check**:

```bash
curl http://localhost:5000/api/message
```

**Execute Query**:

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the top 10 customers"}'
```

**Search Documentation**:

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "customer data", "type": "text"}'
```

**Get Schema**:

```bash
curl http://localhost:5000/api/schema
```

### JavaScript/Fetch Examples

**Execute Query**:

```javascript
const response = await fetch('http://localhost:5000/api/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'Show me the top 10 customers'
  })
});

const data = await response.json();
console.log(data.sql); // Generated SQL
console.log(data.results); // Query results
```

**Search Documentation**:

```javascript
const response = await fetch('http://localhost:5000/api/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'customer information',
    type: 'vector'
  })
});

const data = await response.json();
console.log(data.results.tables); // Found tables
console.log(data.results.relationships); // Found relationships
```

---

## 🚀 Getting Started

1. **Set Environment Variables**:

   ```bash
   export DATABASE_URL="your_database_connection_string"
   export OPENAI_API_KEY="your_openai_api_key"
   ```

2. **Start the Server**:

   ```bash
   cd smol-sql-agents/backend
   python app.py
   ```

3. **Test Health Check**:

   ```bash
   curl http://localhost:5000/api/message
   ```

4. **Check Status**:

   ```bash
   curl http://localhost:5000/api/status
   ```

---

## 📊 API Status Monitoring

Use the `/api/status` endpoint to monitor:

- SQL Agents availability
- System initialization status
- Environment configuration
- Available agents list
- Initialization timing

---

*Last updated: January 2024*
