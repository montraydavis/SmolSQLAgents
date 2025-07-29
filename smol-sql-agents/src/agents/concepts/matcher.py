import logging
from typing import Dict, List, Tuple
from .loader import BusinessConcept
from ...vector.embeddings import OpenAIEmbeddingsClient

logger = logging.getLogger(__name__)

class ConceptMatcher:
    """Matches business concepts to user queries using semantic similarity."""
    
    def __init__(self, indexer_agent=None):
        self.indexer_agent = indexer_agent
        self.embeddings_client = OpenAIEmbeddingsClient()

    def match_concepts_to_query(self, user_query: str, concepts: List[BusinessConcept], 
                               threshold: float = 0.5) -> List[Tuple[BusinessConcept, float]]:  # ADJUSTED TO REASONABLE LEVEL
        """Match concepts to user query based on semantic similarity of descriptions."""
        try:
            matches = []
            
            for concept in concepts:
                similarity = self._calculate_concept_similarity(user_query, concept.description)
                
                if similarity >= threshold:
                    matches.append((concept, similarity))
            
            # Sort by similarity score (highest first)
            matches.sort(key=lambda x: x[1], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching concepts to query: {e}")
            return []

    def find_similar_examples(self, concept: BusinessConcept, user_query: str, 
                             max_examples: int = 3) -> List[Dict]:
        """Find most similar examples within a concept using embeddings."""
        try:
            if not concept.examples:
                return []
            
            # Rank examples by similarity to user query
            ranked_examples = self._rank_examples_by_similarity(user_query, concept.examples)
            
            # Return top examples
            return ranked_examples[:max_examples]
            
        except Exception as e:
            logger.error(f"Error finding similar examples: {e}")
            return []

    def _calculate_concept_similarity(self, user_query: str, concept_description: str) -> float:
        """Calculate semantic similarity between user query and concept description."""
        try:
            # Use embeddings client directly for similarity calculation
            embedding1 = self.embeddings_client.generate_embedding(user_query)
            embedding2 = self.embeddings_client.generate_embedding(concept_description)
            similarity = self._cosine_similarity(embedding1, embedding2)
            
            return similarity
                
        except Exception as e:
            logger.error(f"Error calculating concept similarity: {e}")
            return 0.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import numpy as np
            
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def _rank_examples_by_similarity(self, user_query: str, examples: List[Dict]) -> List[Tuple[Dict, float]]:
        """Rank concept examples by similarity to user query."""
        try:
            ranked_examples = []
            
            for example in examples:
                example_query = example.get("query", "")
                similarity = self._calculate_concept_similarity(user_query, example_query)
                
                ranked_examples.append((example, similarity))
            
            # Sort by similarity score (highest first)
            ranked_examples.sort(key=lambda x: x[1], reverse=True)
            
            return ranked_examples
            
        except Exception as e:
            logger.error(f"Error ranking examples by similarity: {e}")
            return []

    def _simple_similarity(self, query: str, description: str) -> float:
        """Simple keyword-based similarity as fallback."""
        try:
            query_words = set(query.lower().split())
            desc_words = set(description.lower().split())
            
            if not query_words or not desc_words:
                return 0.0
            
            intersection = query_words.intersection(desc_words)
            union = query_words.union(desc_words)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating simple similarity: {e}")
            return 0.0 