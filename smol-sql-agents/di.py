import os
import logging
import sys
import asyncio
import concurrent.futures
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import time
from contextlib import contextmanager

# FIXED: Consistent relative imports from sql_agents package
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
from .di import SharedInstanceManager

# Global shared instance manager
shared_manager = SharedInstanceManager()

load_dotenv()


class SharedInstanceManager:
    """Manages shared instances to avoid repeated instantiation costs."""
    
    def __init__(self):
        self._main_agent = None
        self._database_tools = None
        self._shared_llm_model = None
        self._entity_agent = None
        self._business_agent = None
        self._nl2sql_agent = None
        self._concept_loader = None
        self._concept_matcher = None
        self._initialized = False
        self.api_routes = None
    
    def initialize(self):
        """Initialize all shared instances."""
        if self._initialized:
            return
        
        logger = logging.getLogger(__name__)
        logger.info("Initializing shared instances...")
        
        try:
            self.api_routes = ApiRoutes()
            api_bp = self.api_routes.api_bp
                
            # Initialize shared LLM model first
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            from smolagents.models import OpenAIModel
            self._shared_llm_model = OpenAIModel(model_id="gpt-4o-mini", api_key=api_key)
            
            # Initialize main agent (contains indexer_agent) with shared LLM model
            self._main_agent = PersistentDocumentationAgent(shared_llm_model=self._shared_llm_model)
            
            # Initialize database tools using unified factory
            database_inspector = DatabaseInspector()
            self._database_tools = DatabaseToolsFactory.create_database_tools(database_inspector)
            
            # Initialize concept components
            concepts_dir = "src/agents/concepts/examples"
            self._concept_loader = ConceptLoader(concepts_dir)
            self._concept_matcher = ConceptMatcher(self._main_agent.indexer_agent)
            
            # Initialize agents with shared components
            self._entity_agent = EntityRecognitionAgent(
                self._main_agent.indexer_agent,
                shared_llm_model=self._shared_llm_model
            )
            
            self._business_agent = BusinessContextAgent(
                indexer_agent=self._main_agent.indexer_agent,
                concepts_dir=concepts_dir,
                shared_llm_model=self._shared_llm_model,
                shared_concept_loader=self._concept_loader,
                shared_concept_matcher=self._concept_matcher
            )
            
            self._nl2sql_agent = NL2SQLAgent(
                self._database_tools,
                shared_llm_model=self._shared_llm_model
            )
            
            self._initialized = True
            logger.info("Shared instances initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize shared instances: {e}")
            raise
    
    @property
    def main_agent(self):
        """Get the main documentation agent."""
        if not self._initialized:
            self.initialize()
        return self._main_agent
    
    @property
    def database_tools(self):
        """Get the database tools instance."""
        if not self._initialized:
            self.initialize()
        return self._database_tools
    
    @property
    def entity_agent(self):
        """Get the entity recognition agent."""
        if not self._initialized:
            self.initialize()
        return self._entity_agent
    
    @property
    def business_agent(self):
        """Get the business context agent."""
        if not self._initialized:
            self.initialize()
        return self._business_agent
    
    @property
    def nl2sql_agent(self):
        """Get the NL2SQL agent."""
        if not self._initialized:
            self.initialize()
        return self._nl2sql_agent
    
    @property
    def indexer_agent(self):
        """Get the indexer agent from main agent."""
        if not self._initialized:
            self.initialize()
        return self._main_agent.indexer_agent
    
    def reset(self):
        """Reset all shared instances (useful for testing)."""
        self._main_agent = None
        self._database_tools = None
        self._shared_llm_model = None
        self._entity_agent = None
        self._business_agent = None
        self._nl2sql_agent = None
        self._concept_loader = None
        self._concept_matcher = None
        self._initialized = False
