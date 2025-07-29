import os
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

# Import smolagents components
from smolagents.agents import CodeAgent
from smolagents.models import OpenAIModel
from smolagents.tools import tool

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents to eliminate code duplication."""
    
    def __init__(self, shared_llm_model=None, additional_imports=None, agent_name="Base Agent", database_tools=None):
        """Initialize base agent with common functionality.
        
        Args:
            shared_llm_model: Optional shared LLM model instance
            additional_imports: List of additional imports for CodeAgent
            agent_name: Name of the agent for logging
            database_tools: Optional unified database tools instance
        """
        self.agent_name = agent_name
        self.database_tools = database_tools
        
        # Initialize LLM model (shared or new)
        if shared_llm_model:
            self.llm_model = shared_llm_model
        else:
            self._initialize_llm_model()
        
        # Setup agent-specific components
        self._setup_agent_components()
        
        # Setup tools - this will be overridden by subclasses
        self.tools = []
        self._setup_tools()
        
        # Integrate unified database tools if provided
        if self.database_tools:
            self._integrate_database_tools()
        
        # Validate that all tools are properly decorated
        self._validate_tools()
        
        # Initialize CodeAgent
        self.agent = CodeAgent(
            model=self.llm_model,
            tools=self.tools,
            additional_authorized_imports=additional_imports or []
        )
        
        logger.info(f"{self.agent_name} initialized")
    
    def _initialize_llm_model(self):
        """Initialize OpenAI model for the agent."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.llm_model = OpenAIModel(model_id="gpt-4o-mini", api_key=api_key)
    
    def _validate_tools(self):
        """Validate that all tools are properly decorated."""
        from smolagents.tools import Tool
        
        for i, tool_func in enumerate(self.tools):
            if not isinstance(tool_func, Tool):
                logger.error(f"Tool at index {i} is not properly decorated with @tool")
                logger.error(f"Tool: {tool_func}")
                raise ValueError(f"All tools must be instances of Tool (or decorated with @tool). Found: {type(tool_func)}")
    
    @abstractmethod
    def _setup_agent_components(self):
        """Setup agent-specific components. Override in subclasses."""
        pass
    
    @abstractmethod
    def _setup_tools(self):
        """Setup agent tools. Override in subclasses."""
        pass

    def _integrate_database_tools(self):
        """Integrate unified database tools into agent tools list."""
        if hasattr(self.database_tools, 'create_tools'):
            try:
                database_tools_list = self.database_tools.create_tools()
                self.tools.extend(database_tools_list)
                logger.info(f"Integrated {len(database_tools_list)} unified database tools into {self.agent_name}")
            except Exception as e:
                logger.error(f"Failed to integrate database tools into {self.agent_name}: {e}")
        else:
            logger.warning(f"Database tools provided to {self.agent_name} but no create_tools method found")

class CachingMixin:
    """Mixin for agents that need caching functionality."""
    
    def __init__(self, cache_size: int = 50):
        self._cache = {}
        self._cache_size = cache_size
    
    def _get_cache_key(self, key_string: str) -> str:
        """Generate a cache key from a string."""
        import hashlib
        return hashlib.md5(key_string.lower().strip().encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if available."""
        return self._cache.get(cache_key)
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache a result with size management."""
        self._cache[cache_key] = result
        
        # Limit cache size to prevent memory issues
        if len(self._cache) > self._cache_size:
            # Remove oldest entries
            oldest_keys = list(self._cache.keys())[:10]
            for key in oldest_keys:
                del self._cache[key]
    
    def clear_cache(self):
        """Clear the cache."""
        self._cache.clear()

class ValidationMixin:
    """Mixin for agents that need validation functionality."""
    
    def __init__(self):
        self.validators = {}
    
    def add_validator(self, name: str, validator):
        """Add a validator function."""
        self.validators[name] = validator
    
    def validate(self, data: Any, validator_name: str) -> bool:
        """Validate data using the specified validator."""
        if validator_name not in self.validators:
            logger.warning(f"Validator '{validator_name}' not found")
            return True  # Default to valid if no validator
        
        try:
            return self.validators[validator_name](data)
        except Exception as e:
            logger.error(f"Validation error for '{validator_name}': {e}")
            return False 