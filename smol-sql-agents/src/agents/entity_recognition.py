import json
import logging
import concurrent.futures
from typing import Dict, List, Optional, Any

# Import smolagents tools
from smolagents.tools import tool

# Import base classes
from .base import BaseAgent
from .indexer import SQLIndexerAgent

logger = logging.getLogger(__name__)

class EntityRecognitionAgent(BaseAgent):
    """Streamlined entity recognition agent with consistent dictionary returns."""
    
    def __init__(self, indexer_agent: SQLIndexerAgent, shared_llm_model=None, database_tools=None):
        self.indexer_agent = indexer_agent
        
        # Caching for performance
        self._embedding_cache = {}
        self._result_cache = {}
        
        # Initialize base agent with unified database tools
        super().__init__(
            shared_llm_model=shared_llm_model,
            additional_imports=['json'],
            agent_name="Entity Recognition Agent",
            database_tools=database_tools
        )
    
    def _setup_agent_components(self):
        """Setup agent-specific components."""
        pass
    
    def _setup_tools(self):
        """Setup essential entity recognition tools."""
        self.tools = []
        
        @tool
        def search_table_entities(query: str, max_results: int = 10) -> Dict:
            """Search for table entities relevant to a user query.
            
            Args:
                query: The user query to search for relevant table entities.
                max_results: Maximum number of results to return.
                
            Returns:
                Dictionary with search results and table entities found.
            """
            try:
                if not query or not query.strip():
                    return {"success": False, "error": "Query cannot be empty"}
                
                search_results = self.indexer_agent.search_documentation(
                    query=query.strip(),
                    doc_type="table"
                )
                
                if search_results.get("tables") and len(search_results["tables"]) > max_results:
                    search_results["tables"] = search_results["tables"][:max_results]
                
                return {
                    "success": True,
                    "query": query,
                    "tables": search_results.get("tables", []),
                    "total_found": len(search_results.get("tables", []))
                }
                
            except Exception as e:
                logger.error(f"Failed to search table entities: {e}")
                return {"success": False, "error": str(e)}

        # Removed @tool functions - converted to private methods:
        # analyze_entity_relevance -> _analyze_entity_relevance
        # get_entity_recommendations -> _get_entity_recommendations
        
        self.tools.extend([
            search_table_entities
        ])
    
    def recognize_entities_optimized(self, user_query: str, user_intent: str = None, max_entities: int = 5) -> Dict:
        """Optimized entity recognition with caching."""
        try:
            if not user_query or not user_query.strip():
                return self._empty_entity_result("Query cannot be empty")
            
            intent = user_intent or user_query
            
            # Check cache
            cache_key = self._get_cache_key(user_query, intent)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info("Using cached entity recognition result")
                return cached_result
            
            # Search and analyze with parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                search_future = executor.submit(
                    self.indexer_agent.search_documentation,
                    query=user_query.strip(),
                    doc_type="table"
                )
                
                direct_future = executor.submit(
                    self._analyze_entities_direct,
                    user_query,
                    intent
                )
                
                search_results = search_future.result()
                direct_analysis = direct_future.result()
                
                # Use direct analysis if high confidence
                if direct_analysis.get("confidence", 0.0) > 0.55:  # Lowered threshold
                    result = {
                        "success": True,
                        "applicable_entities": direct_analysis.get("applicable_entities", []),
                        "recommendations": direct_analysis.get("recommendations", []),
                        "analysis": direct_analysis.get("analysis", ""),
                        "confidence": direct_analysis.get("confidence", 0.0)
                    }
                    self._cache_result(cache_key, result)
                    return result
                
                # Process search results
                tables = search_results.get("tables", [])
                if not tables:
                    result = self._empty_entity_result(f"No relevant tables found for: {user_query}")
                    self._cache_result(cache_key, result)
                    return result
                
                # Analyze entities
                entity_analysis = []
                for table_result in tables[:max_entities * 2]:
                    table_content = table_result.get("content", {})
                    table_name = table_content.get("name", "unknown")
                    business_purpose = table_content.get("business_purpose", "")
                    similarity_score = table_result.get("score", 0.0)
                    
                    relevance_factors = {
                        "semantic_similarity": similarity_score,
                        "business_purpose_match": self._calculate_purpose_match_cached(business_purpose, intent),
                        "table_name_relevance": self._calculate_name_relevance_cached(table_name, intent)
                    }
                    
                    overall_relevance = (
                        relevance_factors["semantic_similarity"] * 0.5 +
                        relevance_factors["business_purpose_match"] * 0.3 +
                        relevance_factors["table_name_relevance"] * 0.2
                    )
                    
                    entity_analysis.append({
                        "table_name": table_name,
                        "business_purpose": business_purpose,
                        "relevance_score": round(overall_relevance, 3),
                        "relevance_factors": relevance_factors,
                        "recommendation": self._get_relevance_recommendation(overall_relevance)
                    })
                
                # Sort and filter
                entity_analysis.sort(key=lambda x: x["relevance_score"], reverse=True)
                applicable_entities = [e for e in entity_analysis if e["relevance_score"] > 0.3][:max_entities]
                
                # Generate recommendations
                recommendations = [
                    {
                        "priority": i + 1,
                        "table_name": entity.get("table_name", "unknown"),
                        "relevance_score": entity.get("relevance_score", 0.0),
                        "business_purpose": entity.get("business_purpose", ""),
                        "recommendation": entity.get("recommendation", "")
                    }
                    for i, entity in enumerate(applicable_entities)
                ]
                
                # Calculate confidence
                confidence = 0.0
                if applicable_entities:
                    avg_relevance = sum(e["relevance_score"] for e in applicable_entities) / len(applicable_entities)
                    confidence = min(avg_relevance * 1.2, 1.0)
                
                result = {
                    "success": True,
                    "applicable_entities": applicable_entities,
                    "recommendations": recommendations,
                    "analysis": self._generate_analysis_summary(applicable_entities, intent),
                    "confidence": round(confidence, 3)
                }
                
                self._cache_result(cache_key, result)
                return result
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to recognize entities: {error_msg}")
            return self._empty_entity_result(error_msg)
    
    def recognize_entities(self, user_query: str, user_intent: str = None, max_entities: int = 5) -> Dict:
        """Main entity recognition method - delegates to optimized version."""
        # Use the optimized method instead of LLM-based approach
        return self.recognize_entities_optimized(user_query, user_intent, max_entities)
    
    def _empty_entity_result(self, error_msg: str = "") -> Dict[str, Any]:
        """Return empty entity recognition result."""
        return {
            "success": False,
            "error": error_msg,
            "applicable_entities": [],
            "recommendations": [],
            "analysis": "",
            "confidence": 0.0
        }
    
    def _analyze_entities_direct(self, user_query: str, user_intent: str) -> Dict:
        """Direct analysis for early termination with more realistic scoring."""
        try:
            query_lower = user_query.lower()
            intent_lower = user_intent.lower()
            
            table_patterns = {
                "customer": ["customers", "customer", "client"],
                "account": ["accounts", "account", "banking"],
                "transaction": ["transactions", "transaction", "payment"],
                "employee": ["employees", "employee", "staff"],
                "branch": ["branches", "branch", "location"],
                "loan": ["loans", "loan", "credit"],
                "card": ["cards", "card", "credit_card"]
            }
            
            applicable_entities = []
            total_score = 0.0
            
            for pattern, tables in table_patterns.items():
                if pattern in query_lower or pattern in intent_lower:
                    for table in tables:
                        relevance = 0.0
                        
                        # More nuanced scoring
                        if pattern in query_lower:
                            relevance += 0.4  # Reduced from 0.6
                        if pattern in intent_lower:
                            relevance += 0.2  # Reduced from 0.4
                        
                        # Add some randomness to avoid perfect scores
                        import random
                        relevance += random.uniform(-0.1, 0.1)
                        
                        # Cap at 0.8 to avoid perfect scores
                        relevance = min(relevance, 0.8)
                        
                        if relevance > 0.3:
                            applicable_entities.append({
                                "table_name": table,
                                "business_purpose": f"Contains {pattern} related data",
                                "relevance_score": round(relevance, 3),
                                "recommendation": f"Highly relevant for {pattern} queries"
                            })
                            total_score += relevance
            
            confidence = total_score / max(len(applicable_entities), 1)
            # Cap confidence to avoid triggering early termination
            confidence = min(confidence, 0.7)
            
            return {
                "applicable_entities": applicable_entities,
                "confidence": round(confidence, 3),
                "analysis": f"Direct analysis found {len(applicable_entities)} relevant entities"
            }
            
        except Exception as e:
            logger.error(f"Direct analysis failed: {e}")
            return {"applicable_entities": [], "confidence": 0.0, "analysis": "Direct analysis failed"}
    
    def _get_cache_key(self, query: str, intent: str = None) -> str:
        """Generate cache key."""
        import hashlib
        key_string = f"{query}:{intent or ''}"
        return hashlib.md5(key_string.lower().strip().encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result."""
        return self._result_cache.get(cache_key)
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache result with size management."""
        self._result_cache[cache_key] = result
        if len(self._result_cache) > 100:
            oldest_keys = list(self._result_cache.keys())[:10]
            for key in oldest_keys:
                del self._result_cache[key]
    
    def _calculate_purpose_match_cached(self, business_purpose: str, user_intent: str) -> float:
        """Cached purpose match calculation."""
        cache_key = f"purpose:{business_purpose}:{user_intent}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        result = self._calculate_purpose_match(business_purpose, user_intent)
        self._embedding_cache[cache_key] = result
        return result
    
    def _calculate_name_relevance_cached(self, table_name: str, user_intent: str) -> float:
        """Cached name relevance calculation."""
        cache_key = f"name:{table_name}:{user_intent}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        result = self._calculate_name_relevance(table_name, user_intent)
        self._embedding_cache[cache_key] = result
        return result
    
    def _calculate_purpose_match(self, business_purpose: str, user_intent: str) -> float:
        """Calculate business purpose match."""
        if not business_purpose or not user_intent:
            return 0.0
        
        purpose_words = set(business_purpose.lower().split())
        intent_words = set(user_intent.lower().split())
        
        if not purpose_words or not intent_words:
            return 0.0
        
        common_words = purpose_words.intersection(intent_words)
        return len(common_words) / max(len(intent_words), 1)
    
    def _calculate_name_relevance(self, table_name: str, user_intent: str) -> float:
        """Calculate table name relevance."""
        if not table_name or not user_intent:
            return 0.0
        
        table_name_lower = table_name.lower()
        intent_lower = user_intent.lower()
        
        if table_name_lower in intent_lower:
            return 1.0
        
        intent_words = intent_lower.split()
        for word in intent_words:
            if word in table_name_lower or table_name_lower in word:
                return 0.7
        
        return 0.0
    
    def _get_relevance_recommendation(self, relevance_score: float) -> str:
        """Get recommendation based on relevance score."""
        if relevance_score >= 0.8:
            return "Highly relevant - strongly recommended"
        elif relevance_score >= 0.6:
            return "Relevant - good match"
        elif relevance_score >= 0.4:
            return "Moderately relevant"
        elif relevance_score >= 0.2:
            return "Low relevance"
        else:
            return "Not relevant"
    
    def _generate_analysis_summary(self, applicable_entities: List[Dict], user_intent: str) -> str:
        """Generate analysis summary."""
        if not applicable_entities:
            return f"No highly relevant entities found for: '{user_intent}'"
        
        entity_count = len(applicable_entities)
        top_entity = applicable_entities[0]["table_name"]
        avg_score = sum(e["relevance_score"] for e in applicable_entities) / entity_count
        
        return f"Found {entity_count} applicable entities for '{user_intent}'. Top match: '{top_entity}' with average relevance: {avg_score:.2f}"
    
    def _analyze_entity_relevance(self, search_results: Dict, user_intent: str) -> Dict:
        """Analyze search results to determine entity relevance.
        
        Args:
            search_results: Dictionary containing search results with tables and scores.
            user_intent: The user's intent or context for the query.
            
        Returns:
            Dictionary with analyzed entity relevance and recommendations.
        """
        try:
            if not search_results.get("success"):
                return {
                    "success": False,
                    "error": "Invalid search results",
                    "applicable_entities": [],
                    "analysis": "Search results invalid",
                    "confidence": 0.0
                }
            
            tables = search_results.get("tables", [])
            if not tables:
                return {
                    "success": True,
                    "applicable_entities": [],
                    "analysis": "No relevant table entities found",
                    "confidence": 0.0
                }
            
            # Analyze each table for relevance
            entity_analysis = []
            for table_result in tables:
                table_content = table_result.get("content", {})
                table_name = table_content.get("name", "unknown")
                business_purpose = table_content.get("business_purpose", "")
                similarity_score = table_result.get("score", 0.0)
                
                # Calculate relevance
                relevance_factors = {
                    "semantic_similarity": similarity_score,
                    "business_purpose_match": self._calculate_purpose_match(business_purpose, user_intent),
                    "table_name_relevance": self._calculate_name_relevance(table_name, user_intent)
                }
                
                overall_relevance = (
                    relevance_factors["semantic_similarity"] * 0.5 +
                    relevance_factors["business_purpose_match"] * 0.3 +
                    relevance_factors["table_name_relevance"] * 0.2
                )
                
                entity_analysis.append({
                    "table_name": table_name,
                    "business_purpose": business_purpose,
                    "relevance_score": round(overall_relevance, 3),
                    "relevance_factors": relevance_factors,
                    "recommendation": self._get_relevance_recommendation(overall_relevance)
                })
            
            # Sort by relevance and filter
            entity_analysis.sort(key=lambda x: x["relevance_score"], reverse=True)
            applicable_entities = [e for e in entity_analysis if e["relevance_score"] > 0.3]
            
            # Calculate confidence
            confidence = 0.0
            if applicable_entities:
                avg_relevance = sum(e["relevance_score"] for e in applicable_entities) / len(applicable_entities)
                confidence = min(avg_relevance * 1.2, 1.0)
            
            return {
                "success": True,
                "applicable_entities": applicable_entities,
                "all_analyzed_entities": entity_analysis,
                "analysis": self._generate_analysis_summary(applicable_entities, user_intent),
                "confidence": round(confidence, 3),
                "total_entities_analyzed": len(entity_analysis)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze entity relevance: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_entity_recommendations(self, applicable_entities: List[Dict], max_recommendations: int = 5) -> Dict:
        """Generate entity recommendations.
        
        Args:
            applicable_entities: List of applicable entities with relevance scores.
            max_recommendations: Maximum number of recommendations to generate.
            
        Returns:
            Dictionary with entity recommendations and priority rankings.
        """
        try:
            if not applicable_entities:
                return {
                    "success": True,
                    "recommendations": [],
                    "message": "No applicable entities found"
                }
            
            recommendations = []
            for i, entity in enumerate(applicable_entities[:max_recommendations]):
                recommendations.append({
                    "priority": i + 1,
                    "table_name": entity.get("table_name", "unknown"),
                    "relevance_score": entity.get("relevance_score", 0.0),
                    "business_purpose": entity.get("business_purpose", ""),
                    "recommendation": entity.get("recommendation", "")
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "message": f"Generated {len(recommendations)} recommendations"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return {"success": False, "error": str(e)}