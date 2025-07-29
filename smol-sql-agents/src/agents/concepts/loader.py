import yaml
import logging
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BusinessConcept:
    """Data class representing a business concept."""
    name: str
    description: str
    target: List[str]
    instructions: str
    required_joins: List[str]
    examples: List[Dict]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BusinessConcept':
        """Create BusinessConcept from dictionary."""
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            target=data.get('target', []),
            instructions=data.get('instructions', ''),
            required_joins=data.get('required_joins', []),
            examples=data.get('examples', [])
        )

class ConceptLoader:
    """Loads and manages business concepts from YAML files."""
    
    def __init__(self, concepts_dir: str):
        self.concepts_dir = Path(concepts_dir)
        self._concepts_cache = {}
        self._load_all_concepts()

    def _load_all_concepts(self):
        """Load all concept files from the concepts directory and subdirectories."""
        try:
            if not self.concepts_dir.exists():
                logger.warning(f"Concepts directory {self.concepts_dir} does not exist. Creating it.")
                self.concepts_dir.mkdir(parents=True, exist_ok=True)
                return
            
            # Search recursively in all subdirectories for concept files
            concept_files = list(self.concepts_dir.rglob("*.yaml")) + list(self.concepts_dir.rglob("*.yml"))
            
            if not concept_files:
                logger.warning(f"No concept files found in {self.concepts_dir} or its subdirectories")
                return
            
            for file_path in concept_files:
                try:
                    concepts = self._load_concept_file(file_path)
                    for concept in concepts:
                        self._concepts_cache[concept.name] = concept
                    logger.info(f"Loaded {len(concepts)} concepts from {file_path}")
                except Exception as e:
                    logger.error(f"Error loading concepts from {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading concepts: {e}")

    def _load_concept_file(self, file_path: Path) -> List[BusinessConcept]:
        """Load concepts from a single YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'concepts' not in data:
                logger.warning(f"No 'concepts' key found in {file_path}")
                return []
            
            concepts = []
            for concept_data in data['concepts']:
                if self._validate_concept_structure(concept_data):
                    concept = BusinessConcept.from_dict(concept_data)
                    concepts.append(concept)
                else:
                    logger.warning(f"Invalid concept structure in {file_path}: {concept_data.get('name', 'unknown')}")
            
            return concepts
            
        except Exception as e:
            logger.error(f"Error loading concept file {file_path}: {e}")
            return []

    def _validate_concept_structure(self, concept_data: Dict) -> bool:
        """Validate that concept has required fields."""
        required_fields = ['name', 'description', 'target', 'instructions']
        
        for field in required_fields:
            if field not in concept_data:
                return False
        
        # Ensure target is a list
        if not isinstance(concept_data.get('target'), list):
            return False
        
        # Ensure required_joins is a list (optional field)
        if 'required_joins' in concept_data and not isinstance(concept_data['required_joins'], list):
            return False
        
        # Ensure examples is a list (optional field)
        if 'examples' in concept_data and not isinstance(concept_data['examples'], list):
            return False
        
        return True

    def get_concepts_for_entities(self, entity_names: List[str]) -> List[BusinessConcept]:
        """Get all concepts that target any of the specified entities."""
        try:
            applicable_concepts = []
            entity_set = set(entity_names)
            
            for concept in self._concepts_cache.values():
                # Check if any of the concept's target entities match the provided entities
                concept_targets = concept.target
                matching_entities = [entity for entity in concept_targets if entity in entity_set]
                
                if matching_entities:
                    applicable_concepts.append(concept)
            
            return applicable_concepts
            
        except Exception as e:
            logger.error(f"Error getting concepts for entities: {e}")
            return []

    def get_concept_by_name(self, concept_name: str) -> Optional[BusinessConcept]:
        """Retrieve a specific concept by name."""
        try:
            return self._concepts_cache.get(concept_name)
        except Exception as e:
            logger.error(f"Error getting concept by name: {e}")
            return None

    def get_all_concepts(self) -> List[BusinessConcept]:
        """Get all loaded concepts."""
        try:
            return list(self._concepts_cache.values())
        except Exception as e:
            logger.error(f"Error getting all concepts: {e}")
            return []

    def reload_concepts(self):
        """Reload all concepts from disk."""
        try:
            self._concepts_cache.clear()
            self._load_all_concepts()
            logger.info("Concepts reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading concepts: {e}") 