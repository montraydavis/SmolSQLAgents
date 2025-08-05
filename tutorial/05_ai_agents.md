# Chapter 5: Building AI Agents for Database Documentation

In this chapter, we'll create intelligent agents that can understand and respond to natural language queries about the database using the vector store we set up in the previous chapter.

## Understanding AI Agents

AI agents are autonomous systems that can perceive their environment, process information, and take actions to achieve specific goals. In our case, we'll build agents that can:

1. Understand natural language questions about the database
2. Retrieve relevant documentation using semantic search
3. Generate human-readable responses
4. Chain multiple operations together for complex queries

## The Agent Architecture

We'll implement a multi-agent system with the following components:

1. **Query Understanding Agent**: Interprets the user's intent
2. **Documentation Retrieval Agent**: Finds relevant documentation
3. **Response Generation Agent**: Formulates a natural language response
4. **Orchestrator**: Coordinates between agents

## Implementing the Base Agent

Let's start by creating a base agent class:

```python
# src/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import openai
import json

class BaseAgent(ABC):
    def __init__(self, model: str = "gpt-4"):
        self.model = model
    
    @abstractmethod
    async def process(self, input_data: Any, **kwargs) -> Any:
        """Process the input and return the result."""
        pass
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate a completion using the OpenAI API."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating completion: {str(e)}"
    
    def parse_json_response(self, response: str) -> Dict:
        """Parse a JSON response from the model."""
        try:
            # Extract JSON from markdown code block if present
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If parsing fails, try to extract just the JSON part
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                return json.loads(response[start:end])
            except:
                return {"error": f"Failed to parse JSON response: {response}"}
```

## Implementing the Query Understanding Agent

This agent will analyze the user's question to determine the intent and extract relevant entities.

```python
# src/agents/query_understanding_agent.py
from typing import Dict, Any
from .base_agent import BaseAgent

class QueryUnderstandingAgent(BaseAgent):
    """Agent that understands the intent behind a user's query."""
    
    async def process(self, user_query: str, **kwargs) -> Dict[str, Any]:
        system_prompt = """You are a database expert analyzing user questions. 
        Extract the intent and entities from the following question about a database.
        
        Respond in JSON format with:
        {
            "intent": "search_schema" | "explain_relationship" | "get_example_query" | "other",
            "entities": ["table1", "table2", ...],
            "action_required": "search" | "explain" | "generate_code" | "clarify",
            "certainty_score": 0.0-1.0
        }
        """
        
        response = await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_query,
            temperature=0.1  # Keep it deterministic
        )
        
        result = self.parse_json_response(response)
        result["original_query"] = user_query
        return result
```

## Implementing the Documentation Retrieval Agent

This agent will find the most relevant documentation based on the user's query.

```python
# src/agents/retrieval_agent.py
from typing import List, Dict, Any
from .base_agent import BaseAgent
from src.services.document_service import DocumentService

class RetrievalAgent(BaseAgent):
    """Agent that retrieves relevant documentation."""
    
    def __init__(self, document_service: DocumentService, **kwargs):
        super().__init__(**kwargs)
        self.document_service = document_service
    
    async def process(self, query_analysis: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Retrieve relevant documentation based on the query analysis."""
        query = query_analysis.get("original_query", "")
        entities = query_analysis.get("entities", [])
        
        # Enhance query with entities if available
        if entities:
            enhanced_query = f"{query} (Related to: {', '.join(entities)})"
        else:
            enhanced_query = query
        
        # Get relevant documents
        results = self.document_service.search_documents(
            enhanced_query,
            n_results=5
        )
        
        return {
            "query_analysis": query_analysis,
            "retrieved_docs": results,
            "search_query": enhanced_query
        }
```

## Implementing the Response Generation Agent

This agent will generate a natural language response based on the retrieved documentation.

```python
# src/agents/response_agent.py
from typing import Dict, Any, List
from .base_agent import BaseAgent

class ResponseAgent(BaseAgent):
    """Agent that generates natural language responses."""
    
    async def process(self, retrieval_result: Dict[str, Any], **kwargs) -> str:
        """Generate a response based on the retrieved documentation."""
        query = retrieval_result["query_analysis"]["original_query"]
        docs = retrieval_result.get("retrieved_docs", [])
        
        if not docs:
            return "I couldn't find any relevant documentation for your query."
        
        # Format the context
        context = "\n\n".join([
            f"Document {i+1}:\n{doc['content']}\n"
            f"Source: {doc['metadata'].get('source', 'Unknown')}\n"
            f"Relevance: {1 - doc['distance']:.2f}"
            for i, doc in enumerate(docs)
        ])
        
        system_prompt = """You are a helpful database documentation assistant. 
        Answer the user's question based on the provided context.
        Be concise but thorough in your response.
        If you don't know the answer, say so.
        """
        
        user_prompt = f"""Question: {query}
        
        Context:
        {context}
        
        Please provide a clear and helpful response."""
        
        return await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )
```

## The Orchestrator

Now, let's create an orchestrator to manage the flow between agents:

```python
# src/agents/orchestrator.py
from typing import Dict, Any, Optional
from .query_understanding_agent import QueryUnderstandingAgent
from .retrieval_agent import RetrievalAgent
from .response_agent import ResponseAgent
from src.services.document_service import DocumentService

class AgentOrchestrator:
    """Orchestrates the flow between different agents."""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.query_agent = QueryUnderstandingAgent()
        self.retrieval_agent = RetrievalAgent(self.document_service)
        self.response_agent = ResponseAgent()
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the agent pipeline."""
        # Step 1: Understand the query
        query_analysis = await self.query_agent.process(user_query)
        
        # Step 2: Retrieve relevant documentation
        retrieval_result = await self.retrieval_agent.process(query_analysis)
        
        # Step 3: Generate a response
        response = await self.response_agent.process(retrieval_result)
        
        return {
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
```

## Testing the Agent System

Let's create a test script to see our agents in action:

```python
# examples/test_agents.py
import asyncio
from src.agents.orchestrator import AgentOrchestrator

async def main():
    # Initialize the orchestrator
    orchestrator = AgentOrchestrator()
    
    # Test queries
    test_queries = [
        "How do I find users who made purchases?",
        "Show me the relationship between orders and products",
        "What tables store customer information?",
        "Generate a SQL query to find top customers"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print("-" * 80)
        
        try:
            result = await orchestrator.process_query(query)
            print(f"\nRESPONSE:")
            print(result["response"])
            
            print("\nSOURCES:")
            for i, source in enumerate(result["sources"][:3], 1):
                print(f"\nSource {i} (Relevance: {source['relevance']:.2f}):")
                print(f"Content: {source['content'][:200]}...")
                print(f"Metadata: {source['metadata']}")
                
        except Exception as e:
            print(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

In the next chapter, we'll enhance our agents with the ability to:

1. Generate and execute SQL queries
2. Handle multi-turn conversations
3. Learn from user feedback
4. Integrate with a web interface

Our agents are now capable of understanding natural language queries and retrieving relevant documentation. The system can be extended with additional agents for specific tasks like query generation, schema modification suggestions, or data analysis.
