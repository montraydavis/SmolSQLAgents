import os
import logging
from typing import Dict, List, Any, Tuple

# Import smolagents components
from smolagents.tools import tool

# Import base classes
from .base import BaseAgent

# Import concept components
from .concepts.loader import BusinessConcept, ConceptLoader
from .concepts.matcher import ConceptMatcher

logger = logging.getLogger(__name__)

class BusinessContextAgent(BaseAgent):
    """Streamlined business context agent with consistent dictionary returns."""
    
    def __init__(self, indexer_agent=None, concepts_dir: str = "src/agents/concepts", 
                 shared_llm_model=None, shared_concept_loader=None, shared_concept_matcher=None,
                 database_tools=None):
        self.indexer_agent = indexer_agent
        
        # Use shared components if provided
        self.concept_loader = shared_concept_loader or ConceptLoader(concepts_dir)
        self.concept_matcher = shared_concept_matcher or ConceptMatcher(indexer_agent)
        
        # Initialize base agent with unified database tools
        super().__init__(
            shared_llm_model=shared_llm_model,
            additional_imports=['yaml', 'json'],
            agent_name="Business Context Agent",
            database_tools=database_tools
        )
        
        logger.info("Business Context Agent initialized")

    def _setup_agent_components(self):
        """Setup agent-specific components."""
        # Concept loader and matcher are already initialized in __init__
        pass

    def _setup_tools(self):
        """Setup essential tools for the business context agent."""
        self.tools = []
        
        @tool
        def load_concepts_for_entities(entity_names: List[str]) -> List[Dict]:
            """Load concepts for specified entities.
            
            Args:
                entity_names: List of entity names to load concepts for.
                
            Returns:
                List of concept dictionaries for the specified entities.
            """
            try:
                concepts = self.concept_loader.get_concepts_for_entities(entity_names)
                return [concept.__dict__ for concept in concepts]
            except Exception as e:
                logger.error(f"Error loading concepts: {e}")
                return []

        @tool
        def match_concepts_to_query(user_query: str, available_concepts: List[Dict]) -> List[Dict]:
            """Match concepts to user query.
            
            Args:
                user_query: The user's query to match concepts against.
                available_concepts: List of available concept dictionaries.
                
            Returns:
                List of matched concepts with similarity scores.
            """
            try:
                concepts = [BusinessConcept(**concept) for concept in available_concepts]
                matches = self.concept_matcher.match_concepts_to_query(user_query, concepts)
                return [{"concept": match[0].__dict__, "similarity": match[1]} for match in matches]
            except Exception as e:
                logger.error(f"Error matching concepts: {e}")
                return []

        @tool
        def get_concept_examples(concept_name: str, user_query: str, max_examples: int = 3) -> List[Dict]:
            """Retrieve similar examples for a concept.
            
            Args:
                concept_name: Name of the concept to get examples for.
                user_query: The user's query to find similar examples.
                max_examples: Maximum number of examples to retrieve.
                
            Returns:
                List of similar examples for the concept.
            """
            try:
                concept = self.concept_loader.get_concept_by_name(concept_name)
                if concept:
                    return self.concept_matcher.find_similar_examples(concept, user_query, max_examples)
                return []
            except Exception as e:
                logger.error(f"Error getting examples: {e}")
                return []

        # Removed @tool function - converted to private method:
        # validate_required_joins -> _validate_required_joins

        self.tools.extend([
            load_concepts_for_entities,
            match_concepts_to_query,
            get_concept_examples
        ])

    def gather_business_context(self, user_query: str, applicable_entities: List[str]) -> Dict[str, Any]:
        """Main method to gather business context."""
        try:
            logger.info(f"Gathering business context for query: {user_query}")
            logger.info(f"Applicable entities: {applicable_entities}")
            
            if not applicable_entities:
                return self._empty_business_context()
            
            # Load concepts for entities
            concepts = self.concept_loader.get_concepts_for_entities(applicable_entities)
            logger.info(f"Found {len(concepts)} concepts for entities")
            
            if not concepts:
                return self._empty_business_context()
            
            # Match concepts to user query
            matched_concepts = self.concept_matcher.match_concepts_to_query(user_query, concepts)
            logger.info(f"Matched {len(matched_concepts)} concepts to query")
            
            # Get relevant examples
            relevant_examples = []
            for concept, similarity in matched_concepts:
                examples = self.concept_matcher.find_similar_examples(concept, user_query)
                for example, example_similarity in examples:
                    relevant_examples.append({
                        "example": example,
                        "similarity": example_similarity,
                        "concept_name": concept.name
                    })
            
            # Extract business instructions
            business_instructions = [
                {
                    "concept": concept.name,
                    "instructions": concept.instructions,
                    "similarity": similarity
                }
                for concept, similarity in matched_concepts
            ]
            
            # Validate joins
            join_validation = {}
            for concept, similarity in matched_concepts:
                validation = self._validate_required_joins(applicable_entities, concept.required_joins)
                join_validation[concept.name] = validation
            
            # Calculate entity coverage
            entities_with_concepts = len(set([concept.name for concept, _ in matched_concepts]))
            entity_coverage = {
                "total_entities": len(applicable_entities),
                "entities_with_concepts": entities_with_concepts
            }
            
            # Format response
            return {
                "success": True,
                "matched_concepts": [
                    {
                        "name": concept.name,
                        "description": concept.description,
                        "target_entities": concept.target,
                        "required_joins": concept.required_joins,
                        "similarity": similarity
                    }
                    for concept, similarity in matched_concepts
                ],
                "business_instructions": business_instructions,
                "relevant_examples": relevant_examples,
                "join_validation": join_validation,
                "entity_coverage": entity_coverage
            }
            
        except Exception as e:
            logger.error(f"Error gathering business context: {e}")
            return {
                "success": False,
                "error": str(e),
                "matched_concepts": [],
                "business_instructions": [],
                "relevant_examples": [],
                "join_validation": {},
                "entity_coverage": {"total_entities": 0, "entities_with_concepts": 0}
            }

    def _validate_required_joins(self, entities: List[str], required_joins: List[str]) -> Dict:
        """Validate that required joins can be satisfied."""
        try:
            validation_result = {
                "valid": True,
                "missing_entities": [],
                "satisfied_joins": [],
                "unsatisfied_joins": []
            }
            
            # Extract entity names from join conditions
            required_entities = set()
            for join in required_joins:
                join_lower = join.lower()
                if "=" in join_lower:
                    parts = join_lower.split("=")
                    for part in parts:
                        if "." in part:
                            entity = part.split(".")[0].strip()
                            required_entities.add(entity)
            
            # Check availability
            available_entities = set(entities)
            missing_entities = required_entities - available_entities
            
            if missing_entities:
                validation_result["valid"] = False
                validation_result["missing_entities"] = list(missing_entities)
            
            # Check join satisfaction
            for join in required_joins:
                can_satisfy = all(entity in available_entities for entity in required_entities)
                if can_satisfy:
                    validation_result["satisfied_joins"].append(join)
                else:
                    validation_result["unsatisfied_joins"].append(join)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating joins: {e}")
            return {"valid": False, "error": str(e)}

    def _empty_business_context(self) -> Dict[str, Any]:
        """Return empty business context with proper structure."""
        return {
            "success": True,
            "matched_concepts": [],
            "business_instructions": [],
            "relevant_examples": [],
            "join_validation": {},
            "entity_coverage": {"total_entities": 0, "entities_with_concepts": 0}
        }