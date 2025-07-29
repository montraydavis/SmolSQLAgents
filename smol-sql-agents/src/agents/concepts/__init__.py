"""Business concepts module for SQL agents."""

# Try to import components, but make them optional for testing
try:
    from .loader import ConceptLoader, BusinessConcept
    from .matcher import ConceptMatcher
    CONCEPTS_AVAILABLE = True
except ImportError:
    CONCEPTS_AVAILABLE = False
    # Create dummy classes for testing
    class ConceptLoader:
        def __init__(self, *args, **kwargs):
            pass
        def get_concepts_for_entities(self, *args, **kwargs):
            return []
        def get_all_concepts(self):
            return []
    class BusinessConcept:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    class ConceptMatcher:
        def __init__(self, *args, **kwargs):
            pass
        def match_concepts_to_query(self, *args, **kwargs):
            return []

__all__ = ['ConceptLoader', 'BusinessConcept', 'ConceptMatcher'] 