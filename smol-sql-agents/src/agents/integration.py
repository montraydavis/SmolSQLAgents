import logging
from typing import Dict, List, Any

# Import smolagents tools
from smolagents.tools import tool

# Import base classes
from .base import BaseAgent

logger = logging.getLogger(__name__)

class SQLAgentPipeline(BaseAgent):
    """Streamlined SQL agent pipeline with consistent dictionary structures."""
    
    def __init__(self, indexer_agent=None, database_tools=None, 
                 shared_entity_agent=None, shared_business_agent=None, shared_nl2sql_agent=None):
        # Store dependencies
        self.indexer_agent = indexer_agent
        self.database_tools = database_tools
        
        # Initialize base agent with unified database tools
        super().__init__(
            additional_imports=['json'],
            agent_name="SQL Agent Pipeline",
            database_tools=self.database_tools
        )
        
        # Initialize agents
        self._initialize_agents(shared_entity_agent, shared_business_agent, shared_nl2sql_agent)
    
    def _setup_agent_components(self):
        """Setup agent-specific components."""
        pass
    
    def _setup_tools(self):
        """Setup essential pipeline tools."""
        self.tools = []
        
        # Removed @tool functions - converted to private methods:
        # execute_entity_recognition -> _execute_entity_recognition
        # gather_business_context -> _gather_business_context  
        # generate_sql -> _generate_sql
        # format_final_response -> _format_final_response
    
    def _initialize_agents(self, shared_entity_agent, shared_business_agent, shared_nl2sql_agent):
        """Initialize pipeline agents."""
        try:
            from .entity_recognition import EntityRecognitionAgent
            from .business import BusinessContextAgent
            from .nl2sql import NL2SQLAgent
        except ImportError as e:
            logger.error(f"Failed to import required agents: {e}")
            raise
        
        # Use shared agents or create new ones
        self.entity_agent = shared_entity_agent or EntityRecognitionAgent(self.indexer_agent)
        self.business_agent = shared_business_agent or BusinessContextAgent(self.indexer_agent)
        self.nl2sql_agent = shared_nl2sql_agent or NL2SQLAgent(self.database_tools)
    
    def _execute_entity_recognition(self, user_query: str, user_intent: str) -> Dict[str, Any]:
        """Execute entity recognition step."""
        logger.info("Executing entity recognition...")
        
        entity_results = self.entity_agent.recognize_entities_optimized(user_query, user_intent, max_entities=10)
        
        if not isinstance(entity_results, dict):
            logger.error(f"Entity recognition returned {type(entity_results)}, expected dict")
            return {
                "success": False,
                "error": "Entity recognition returned invalid type",
                "applicable_entities": [],
                "entities": []
            }
        
        if entity_results.get("success", False):
            applicable_entities = entity_results.get("applicable_entities", [])
            entities = [
                entity.get("table_name") if isinstance(entity, dict) else entity
                for entity in applicable_entities
                if entity
            ]
            entity_results["entities"] = entities
            logger.info(f"Found entities: {entities}")
        else:
            logger.warning("Entity recognition returned no results")
            entity_results["entities"] = []
        
        return entity_results
    
    def _gather_business_context(self, user_query: str, entity_results: Dict) -> Dict[str, Any]:
        """Gather business context step."""
        logger.info("Gathering business context...")
        
        if not isinstance(entity_results, dict):
            logger.error(f"Entity results must be a dictionary, got {type(entity_results)}")
            return self._default_business_context()
        
        # Extract entities directly - no fallbacks or nested structure handling
        applicable_entities = entity_results.get("applicable_entities", [])
        entities_list = entity_results.get("entities", [])
        
        # Extract entity names
        entities = []
        for entity in applicable_entities:
            if isinstance(entity, dict):
                table_name = entity.get("table_name")
                if table_name:
                    entities.append(table_name)
            elif isinstance(entity, str):
                entities.append(entity)
        
        # Use entities_list as fallback only if no applicable_entities found
        if not entities and entities_list:
            entities = [entity for entity in entities_list if isinstance(entity, str)]
        
        if not entities:
            logger.warning("No entities found for business context gathering")
            return self._default_business_context()
        
        logger.info(f"Using entities for business context: {entities}")
        business_context = self.business_agent.gather_business_context(user_query, entities)
        
        if not isinstance(business_context, dict):
            logger.error(f"Business context agent returned {type(business_context)}, expected dict")
            return self._default_business_context()
        
        return business_context
    
    def _generate_sql(self, user_query: str, business_context: Dict, entity_context: Dict) -> Dict[str, Any]:
        """Generate SQL step."""
        logger.info("Generating SQL query...")
        
        if not isinstance(business_context, dict) or not isinstance(entity_context, dict):
            logger.error("Business context and entity context must be dictionaries")
            return {
                "success": False,
                "error": "Invalid context types",
                "generated_sql": "",
                "is_valid": False
            }
        
        entity_context_for_sql = {
            "entities": entity_context.get("entities", []),
            "entity_descriptions": entity_context.get("entity_descriptions", {}),
            "confidence_scores": entity_context.get("confidence_scores", {})
        }
        
        sql_results = self.nl2sql_agent.generate_sql_optimized(user_query, business_context, entity_context_for_sql)
        
        if not isinstance(sql_results, dict):
            logger.error(f"SQL generation returned {type(sql_results)}, expected dict")
            return {
                "success": False,
                "error": "SQL generation returned invalid type",
                "generated_sql": "",
                "is_valid": False
            }
        
        return sql_results
    
    def _format_final_response(self, entity_results: Dict, business_context: Dict, sql_results: Dict) -> Dict[str, Any]:
        """Format final response step."""
        return {
            "success": True,
            "pipeline_summary": {
                "entity_recognition_success": entity_results.get("success", False),
                "business_context_success": business_context.get("success", False),
                "sql_generation_success": sql_results.get("success", False),
                "sql_validation_success": sql_results.get("is_valid", False)
            },
            "entity_recognition": {
                "entities": entity_results.get("entities", []),
                "confidence": entity_results.get("confidence", 0.0)
            },
            "business_context": {
                "matched_concepts": business_context.get("matched_concepts", []),
                "business_instructions": business_context.get("business_instructions", [])
            },
            "sql_generation": {
                "generated_sql": sql_results.get("generated_sql"),
                "is_valid": sql_results.get("is_valid", False),
                "validation": sql_results.get("validation", {}),
                "query_execution": sql_results.get("query_execution", {})
            }
        }
    
    def _default_business_context(self) -> Dict[str, Any]:
        """Return default business context structure."""
        return {
            "success": True,
            "matched_concepts": [],
            "business_instructions": [],
            "join_validation": {},
            "relevant_examples": [],
            "entity_coverage": {"entities_with_concepts": 0, "total_entities": 0}
        }
    
    def _build_entity_context(self, entity_results: Dict) -> Dict[str, Any]:
        """Build entity context from entity recognition results."""
        applicable_entities = entity_results.get("applicable_entities", [])
        entities_list = entity_results.get("entities", [])
        
        entities = []
        entity_descriptions = {}
        confidence_scores = {}
        
        # Process applicable_entities
        for entity in applicable_entities:
            if isinstance(entity, dict):
                table_name = entity.get("table_name")
                if table_name:
                    entities.append(table_name)
                    entity_descriptions[table_name] = entity.get("business_purpose", "")
                    confidence_scores[table_name] = entity.get("relevance_score", 0.0)
        
        # Process entities_list as fallback
        if not entities and entities_list:
            for entity in entities_list:
                if isinstance(entity, str):
                    entities.append(entity)
                    entity_descriptions[entity] = f"Table {entity}"
                    confidence_scores[entity] = 0.5
        
        return {
            "entities": entities,
            "entity_descriptions": entity_descriptions,
            "confidence_scores": confidence_scores
        }
    
    def process_user_query(self, user_query: str, user_intent: str = None) -> Dict[str, Any]:
        """Complete pipeline from user query to validated SQL."""
        logger.info(f"Starting pipeline for query: {user_query}")
        
        # Step 1: Entity Recognition
        entity_results = self._execute_entity_recognition(user_query, user_intent or user_query)
        if not entity_results.get("success", False):
            return {"success": False, "error": "Entity recognition failed", "step": "entity_recognition"}
        
        # Step 2: Business Context Gathering
        business_context = self._gather_business_context(user_query, entity_results)
        if not business_context.get("success", False):
            return {"success": False, "error": "Business context gathering failed", "step": "business_context"}
        
        # Step 3: SQL Generation
        entity_context = self._build_entity_context(entity_results)
        sql_results = self._generate_sql(user_query, business_context, entity_context)
        if not sql_results.get("success", False):
            return {"success": False, "error": "SQL generation failed", "step": "sql_generation"}
        
        # Step 4: Format Final Response
        final_response = self._format_final_response(entity_results, business_context, sql_results)
        
        logger.info("Pipeline completed successfully")
        return final_response