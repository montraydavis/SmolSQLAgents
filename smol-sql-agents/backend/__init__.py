# Backend package initialization
# Import key modules from src to make them available when importing from backend

from src.database.inspector import DatabaseInspector
from src.agents.core import PersistentDocumentationAgent
from src.agents.entity_recognition import EntityRecognitionAgent
from src.agents.business import BusinessContextAgent
from src.agents.nl2sql import NL2SQLAgent
from src.agents.integration import SQLAgentPipeline
from src.agents.tools.factory import DatabaseToolsFactory
from src.agents.concepts.loader import ConceptLoader
from src.agents.concepts.matcher import ConceptMatcher
from src.output.formatters import DocumentationFormatter
from src.agents.batch_manager import BatchIndexingManager

# Make these available for import
__all__ = [
    'DatabaseInspector',
    'PersistentDocumentationAgent',
    'EntityRecognitionAgent',
    'BusinessContextAgent',
    'NL2SQLAgent',
    'SQLAgentPipeline',
    'DatabaseToolsFactory',
    'ConceptLoader',
    'ConceptMatcher',
    'DocumentationFormatter',
    'BatchIndexingManager',
]
