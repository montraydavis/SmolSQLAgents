# Standard library imports
from datetime import datetime
import os
import logging
import sys
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
from contextlib import contextmanager

# Third-party imports
from dotenv import load_dotenv
from flask import Blueprint, current_app, jsonify, request, Flask
from flask_cors import CORS

# Add parent directory to Python path to find src module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Local imports
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

logger = logging.getLogger(__name__)

SQL_AGENTS_AVAILABLE = True
print("✅ SQL Agents package imported successfully")

class ApiRoutes:
    def __init__(self):
        
        self.api_bp = Blueprint('api', __name__)
        self.documentation_store = None
        self.register_routes()
        self.register_error_handlers()

    def get_documentation_store(self):
        """Get the documentation store instance."""
        if self.documentation_store is None:
            from src.database.persistence import DocumentationStore
            self.documentation_store = DocumentationStore()
        return self.documentation_store

    @staticmethod
    def get_agent_manager():
        """Get the agent manager from current app."""
        agent_manager = current_app.agent_manager
        if agent_manager and hasattr(agent_manager, 'is_initialized'):
            return agent_manager if agent_manager.is_initialized() else None
        return agent_manager

    def register_routes(self):
        self.api_bp.add_url_rule('/message', view_func=self.get_message)
        self.api_bp.add_url_rule('/status', view_func=self.get_status)
        self.api_bp.add_url_rule('/query', view_func=self.execute_query, methods=['POST'])
        self.api_bp.add_url_rule('/recognize-entities', view_func=self.recognize_entities, methods=['POST'])
        self.api_bp.add_url_rule('/business-context', view_func=self.gather_business_context, methods=['POST'])
        self.api_bp.add_url_rule('/generate-sql', view_func=self.generate_sql, methods=['POST'])
        self.api_bp.add_url_rule('/search', view_func=self.search_documentation, methods=['POST'])
        self.api_bp.add_url_rule('/schema', view_func=self.get_schema)
        self.api_bp.add_url_rule('/debug/objects', view_func=self.debug_objects)
        self.api_bp.add_url_rule('/debug/database', view_func=self.debug_database)
        
        # Documentation endpoints
        self.api_bp.add_url_rule('/documentation/summaries', view_func=self.get_all_summaries)
        self.api_bp.add_url_rule('/documentation/summaries/<item_id>', view_func=self.get_summary_by_id)
        self.api_bp.add_url_rule('/documentation/tables', view_func=self.get_all_table_documentation)
        self.api_bp.add_url_rule('/documentation/tables/<table_name>', view_func=self.get_table_documentation)
        self.api_bp.add_url_rule('/documentation/relationships', view_func=self.get_all_relationship_documentation)
        self.api_bp.add_url_rule('/documentation/relationships/<relationship_id>', view_func=self.get_relationship_documentation)

    def register_error_handlers(self):
        self.api_bp.register_error_handler(400, self.bad_request)
        self.api_bp.register_error_handler(404, self.not_found)
        self.api_bp.register_error_handler(500, self.internal_server_error)

    def get_message(self):
        """Health check endpoint."""
        return jsonify({"message": "Hello from the Smol-SQL-Agents backend! 👋"})


    def get_status(self):
        """Get the status of SQL Agents and available features, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("Status endpoint called: checking SQL Agents status and environment variables.")
        try:
            agent_manager = self.get_agent_manager()
            agents_available = agent_manager is not None

            env_vars = current_app.config.get('ENV_VARS', {})
            logger.debug(f"Environment variables loaded: {env_vars}")

            status = {
                "sql_agents_available": agents_available,
                "initialized": agents_available,
                "environment": {
                    "database_url_set": bool(env_vars.get('DATABASE_URL')),
                    "openai_key_set": bool(env_vars.get('OPENAI_API_KEY'))
                },
                "agents": list(agent_manager.get_all_agents().keys()) if agent_manager else [],
                "initialization_time": getattr(agent_manager, '_initialization_time', None) if agent_manager else None,
                "factory_initialized": getattr(agent_manager, 'is_initialized', lambda: False)() if agent_manager else False
            }

            logger.info(f"Status response: {status}")
            elapsed = time.perf_counter() - start_time
            logger.info(f"get_status execution time: {elapsed:.4f} seconds")
            return jsonify(status)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Status check failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "sql_agents_available": False,
                "initialized": False
            }), 500

    def execute_query(self):
        """Execute a natural language query and return SQL + results, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("execute_query endpoint called.")
        try:
            data = request.get_json()
            logger.debug(f"Received data: {data}")
            if not data:
                logger.warning("No JSON data provided in request.")
                return jsonify({"success": False, "error": "No JSON data provided"}), 400

            query = data.get("query", "").strip()
            if not query:
                logger.warning("Query is empty in request.")
                return jsonify({"success": False, "error": "Query cannot be empty"}), 400

            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "sql": "",
                    "results": [],
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "Agent manager not available"
                })

            pipeline = agent_manager.get_sql_pipeline()
            if not pipeline:
                logger.error("SQL pipeline not available.")
                return jsonify({
                    "sql": "",
                    "results": [],
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "Pipeline not available"
                })

            logger.info(f"Processing user query: {query}")
            process_start = time.perf_counter()
            results = pipeline.process_user_query(query)
            process_elapsed = time.perf_counter() - process_start
            logger.info(f"pipeline.process_user_query execution time: {process_elapsed:.4f} seconds")

            if results.get("success"):
                sql_generation = results.get("sql_generation", {})
                generated_sql = sql_generation.get("generated_sql", "")
                query_execution = sql_generation.get("query_execution", {})

                sample_data = query_execution.get("sample_data", {})
                results_data = []

                if sample_data and sample_data.get("sample_rows"):
                    results_data = sample_data.get("sample_rows", [])

                logger.info(f"Query executed successfully. SQL: {generated_sql}")
                elapsed = time.perf_counter() - start_time
                logger.info(f"execute_query total execution time: {elapsed:.4f} seconds")
                return jsonify({
                    "sql": generated_sql,
                    "results": results_data,
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "pipeline_results": results
                })
            else:
                logger.warning(f"Query execution failed: {results.get('error', 'Unknown error')}")
                elapsed = time.perf_counter() - start_time
                logger.info(f"execute_query total execution time: {elapsed:.4f} seconds")
                return jsonify({
                    "sql": "",
                    "results": [],
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": results.get("error", "Unknown error")
                })

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Query execution failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "sql": "",
                "results": [],
                "query": data.get("query", "") if 'data' in locals() else "",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }), 500

    def recognize_entities(self):
        """Recognize applicable database entities for a user query, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("recognize_entities endpoint called.")
        try:
            data = request.get_json()
            logger.debug(f"Received data: {data}")
            if not data:
                logger.warning("No JSON data provided in request.")
                return jsonify({"success": False, "error": "No JSON data provided"}), 400

            query = data.get("query", "")
            intent = data.get("intent", None)
            max_entities = data.get("max_entities", 5)
            logger.debug(f"Recognize entities for query: '{query}', intent: '{intent}', max_entities: {max_entities}")

            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "success": False,
                    "error": "Agent manager not available",
                    "applicable_entities": []
                })

            entity_agent = agent_manager.get_entity_agent()
            if not entity_agent:
                logger.error("Entity agent not available.")
                return jsonify({
                    "success": False,
                    "error": "Entity agent not available",
                    "applicable_entities": []
                })

            process_start = time.perf_counter()
            results = entity_agent.recognize_entities(query, intent, max_entities)
            process_elapsed = time.perf_counter() - process_start
            logger.info(f"entity_agent.recognize_entities execution time: {process_elapsed:.4f} seconds")
            logger.info(f"Entities recognized: {results.get('applicable_entities', [])}")
            elapsed = time.perf_counter() - start_time
            logger.info(f"recognize_entities total execution time: {elapsed:.4f} seconds")
            return jsonify(results)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Entity recognition failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "applicable_entities": []
            }), 500

    def gather_business_context(self):
        """Gather business context for a user query, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("gather_business_context endpoint called.")
        try:
            data = request.get_json()
            logger.debug(f"Received data: {data}")
            if not data:
                logger.warning("No JSON data provided in request.")
                return jsonify({"success": False, "error": "No JSON data provided"}), 400

            query = data.get("query", "")
            intent = data.get("intent", None)
            logger.debug(f"Gather business context for query: '{query}', intent: '{intent}'")

            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "success": False,
                    "error": "Agent manager not available",
                    "matched_concepts": [],
                    "business_instructions": []
                })

            business_agent = agent_manager.get_business_agent()
            if not business_agent:
                logger.error("Business agent not available.")
                return jsonify({
                    "success": False,
                    "error": "Business agent not available",
                    "matched_concepts": [],
                    "business_instructions": []
                })

            applicable_entities = ["customers", "accounts", "transactions", "branches", "employees", "loans", "cards"]
            logger.debug(f"Default applicable entities for business context: {applicable_entities}")

            process_start = time.perf_counter()
            results = business_agent.gather_business_context(query, applicable_entities)
            process_elapsed = time.perf_counter() - process_start
            logger.info(f"business_agent.gather_business_context execution time: {process_elapsed:.4f} seconds")
            logger.info(f"Business context gathered: {results}")
            elapsed = time.perf_counter() - start_time
            logger.info(f"gather_business_context total execution time: {elapsed:.4f} seconds")
            return jsonify(results)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Business context gathering failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "matched_concepts": [],
                "business_instructions": []
            }), 500

    def generate_sql(self):
        """Generate SQL from natural language using the complete pipeline, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("generate_sql endpoint called.")
        try:
            data = request.get_json()
            logger.debug(f"Received data: {data}")
            if not data:
                logger.warning("No JSON data provided in request.")
                return jsonify({"success": False, "error": "No JSON data provided"}), 400

            query = data.get("query", "")
            intent = data.get("intent", None)
            logger.debug(f"Generate SQL for query: '{query}', intent: '{intent}'")

            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "success": False,
                    "error": "Agent manager not available",
                    "generated_sql": "",
                    "validation": {},
                    "optimization_suggestions": []
                })

            pipeline = agent_manager.get_sql_pipeline()
            if not pipeline:
                logger.error("Pipeline not available.")
                return jsonify({
                    "success": False,
                    "error": "Pipeline not available",
                    "generated_sql": "",
                    "validation": {},
                    "optimization_suggestions": []
                })

            process_start = time.perf_counter()
            results = pipeline.process_user_query(query, intent)
            process_elapsed = time.perf_counter() - process_start
            logger.info(f"pipeline.process_user_query execution time: {process_elapsed:.4f} seconds")
            logger.info(f"SQL generation results: {results}")
            elapsed = time.perf_counter() - start_time
            logger.info(f"generate_sql total execution time: {elapsed:.4f} seconds")
            return jsonify(results)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"SQL generation failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "generated_sql": "",
                "validation": {},
                "optimization_suggestions": []
            }), 500

    def search_documentation(self):
        """Search documentation using text or vector search, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("search_documentation endpoint called.")
        try:
            data = request.get_json()
            logger.debug(f"Received data: {data}")
            if not data:
                logger.warning("No JSON data provided in request.")
                return jsonify({"success": False, "error": "No JSON data provided"}), 400

            search_type = data.get("type", "text")
            query = data.get("query", "")
            logger.debug(f"Search documentation for query: '{query}', type: '{search_type}'")

            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "results": [],
                    "query": query,
                    "type": search_type,
                    "total": 0,
                    "error": "Agent manager not available"
                })

            main_agent = agent_manager.get_main_agent()
            indexer_agent = agent_manager.get_indexer_agent()

            if (main_agent and indexer_agent and
                hasattr(main_agent, 'vector_indexing_available') and
                main_agent.vector_indexing_available):

                logger.info("Using indexer agent to search documentation.")
                process_start = time.perf_counter()
                results = indexer_agent.search_documentation(query, search_type)
                process_elapsed = time.perf_counter() - process_start
                logger.info(f"indexer_agent.search_documentation execution time: {process_elapsed:.4f} seconds")
                total_results = len(results.get("tables", []) + results.get("relationships", []))
                logger.info(f"Search results: {total_results} items found.")
                elapsed = time.perf_counter() - start_time
                logger.info(f"search_documentation total execution time: {elapsed:.4f} seconds")
                return jsonify({
                    "results": results,
                    "query": query,
                    "type": search_type,
                    "total": total_results
                })
            else:
                logger.warning("Search not available: main_agent or indexer_agent missing or vector indexing not available.")
                elapsed = time.perf_counter() - start_time
                logger.info(f"search_documentation total execution time: {elapsed:.4f} seconds")
                return jsonify({
                    "results": [],
                    "query": query,
                    "type": search_type,
                    "total": 0,
                    "error": "Search not available"
                })

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Search failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "results": [],
                "query": data.get("query", "") if 'data' in locals() else "",
                "type": data.get("type", "text") if 'data' in locals() else "text",
                "total": 0,
                "error": str(e)
            }), 500

    def get_schema(self):
        """Get database schema information, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("get_schema endpoint called.")
        try:
            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "tables": [],
                    "success": False,
                    "error": "Agent manager not available"
                })

            database_tools = agent_manager.get_unified_database_tools()
            logger.debug(f"Database tools: {database_tools}")

            if database_tools and hasattr(database_tools, 'get_detailed_schema_unified'):
                logger.info("Using get_detailed_schema_unified to retrieve schema.")
                process_start = time.perf_counter()
                schema_result = database_tools.get_detailed_schema_unified()
                process_elapsed = time.perf_counter() - process_start
                logger.info(f"database_tools.get_detailed_schema_unified execution time: {process_elapsed:.4f} seconds")
                if schema_result.get("success"):
                    logger.info("Detailed schema retrieval successful.")
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"get_schema total execution time: {elapsed:.4f} seconds")
                    return jsonify({
                        "tables": schema_result.get("tables", []),
                        "relationships": schema_result.get("relationships", []),
                        "count": schema_result.get("count", 0),
                        "success": True
                    })
                else:
                    logger.error(f"Detailed schema retrieval failed: {schema_result.get('error', 'Schema retrieval failed')}")
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"get_schema total execution time: {elapsed:.4f} seconds")
                    return jsonify({
                        "tables": [],
                        "relationships": [],
                        "success": False,
                        "error": schema_result.get("error", "Schema retrieval failed")
                    }), 500

            if database_tools and hasattr(database_tools, 'get_all_tables_unified'):
                logger.info("Using get_all_tables_unified to retrieve schema.")
                process_start = time.perf_counter()
                schema_result = database_tools.get_all_tables_unified()
                process_elapsed = time.perf_counter() - process_start
                logger.info(f"database_tools.get_all_tables_unified execution time: {process_elapsed:.4f} seconds")
                if schema_result.get("success"):
                    tables = []
                    for table_name in schema_result.get("tables", []):
                        tables.append({
                            "name": table_name,
                            "schema": None,
                            "columns": [],
                            "column_count": 0,
                            "primary_key_columns": [],
                            "foreign_key_columns": [],
                            "nullable_columns": [],
                            "not_null_columns": []
                        })
                    logger.info(f"Simple schema retrieval successful. Tables: {len(tables)}")
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"get_schema total execution time: {elapsed:.4f} seconds")
                    return jsonify({
                        "tables": tables,
                        "relationships": [],
                        "count": len(tables),
                        "success": True
                    })

            logger.warning("Schema not available from database tools.")
            elapsed = time.perf_counter() - start_time
            logger.info(f"get_schema total execution time: {elapsed:.4f} seconds")
            return jsonify({
                "tables": [],
                "relationships": [],
                "success": False,
                "error": "Schema not available"
            })

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Schema retrieval failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "tables": [],
                "relationships": [],
                "success": False,
                "error": str(e)
            }), 500

    def debug_objects(self):
        """Debug endpoint to show object creation status, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("debug_objects endpoint called.")
        try:
            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "error": "Agent manager not available",
                    "objects": {}
                })

            debug_info = {
                "agent_manager_id": id(agent_manager),
                "factory_initialized": getattr(agent_manager, 'is_initialized', lambda: False)(),
                "initialization_time": getattr(agent_manager, '_initialization_time', None),
                "shared_components": {
                    "llm_model": agent_manager._shared_llm_model is not None,
                    "database_tools": agent_manager._unified_database_tools is not None,
                    "instances_count": len(agent_manager._instances),
                    "shared_components_count": len(agent_manager._shared_components)
                },
                "agent_instances": {
                    name: id(instance) for name, instance in agent_manager._instances.items()
                },
                "shared_components": {
                    name: id(component) for name, component in agent_manager._shared_components.items()
                }
            }

            logger.info(f"Debug objects info: {debug_info}")
            elapsed = time.perf_counter() - start_time
            logger.info(f"debug_objects total execution time: {elapsed:.4f} seconds")
            return jsonify(debug_info)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Debug objects failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "objects": {}
            }), 500

    def debug_database(self):
        """Debug endpoint to show database performance metrics, with verbose logging and execution time tracking."""
        start_time = time.perf_counter()
        logger.info("debug_database endpoint called.")
        try:
            agent_manager = self.get_agent_manager()
            if not agent_manager:
                logger.error("Agent manager not available.")
                return jsonify({
                    "error": "Agent manager not available",
                    "database_stats": {}
                })

            db_tools = agent_manager.get_unified_database_tools()
            if not hasattr(db_tools, 'inspector'):
                logger.error("Database inspector not available.")
                return jsonify({
                    "error": "Database inspector not available",
                    "database_stats": {}
                })

            inspector = db_tools.inspector
            logger.debug(f"Inspector object: {inspector}")
            process_start = time.perf_counter()
            cache_stats = inspector.get_cache_stats()
            process_elapsed = time.perf_counter() - process_start
            logger.info(f"inspector.get_cache_stats execution time: {process_elapsed:.4f} seconds")
            
            debug_info = {
                "database_inspector_id": id(inspector),
                "cache_stats": cache_stats,
                "connection_pool": {
                    "pool_size": inspector.engine.pool.size(),
                    "checked_in": inspector.engine.pool.checkedin(),
                    "checked_out": inspector.engine.pool.checkedout(),
                    "overflow": inspector.engine.pool.overflow()
                },
                "engine_config": {
                    "echo": inspector.engine.echo,
                    "pool_pre_ping": inspector.engine.pool._pre_ping,
                    "pool_recycle": inspector.engine.pool._recycle
                }
            }

            logger.info(f"Debug database info: {debug_info}")
            elapsed = time.perf_counter() - start_time
            logger.info(f"debug_database total execution time: {elapsed:.4f} seconds")
            return jsonify(debug_info)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Debug database failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "error": str(e),
                "database_stats": {}
            }), 500

    def get_all_summaries(self):
        """Get all AI-generated business purposes and summaries."""
        start_time = time.perf_counter()
        logger.info("get_all_summaries endpoint called.")
        
        try:
            store = self.get_documentation_store()
            
            # Get all tables and their documentation
            all_tables = store.get_all_tables()
            table_summaries = {}
            
            for table_name in all_tables:
                table_info = store.get_table_info(table_name)
                if table_info:
                    table_summaries[table_name] = {
                        "id": f"table_{table_name}",
                        "type": "table",
                        "name": table_name,
                        "business_purpose": table_info["business_purpose"],
                        "documentation": table_info["documentation"],
                        "status": table_info["status"],
                        "processed_at": table_info.get("processed_at")
                    }
            
            # Get all relationships and their documentation
            all_relationships = store.get_all_relationships()
            relationship_summaries = {}
            
            for relationship in all_relationships:
                rel_info = store.get_relationship_info(str(relationship['id']))
                if rel_info:
                    relationship_summaries[str(relationship['id'])] = {
                        "id": f"relationship_{relationship['id']}",
                        "type": "relationship",
                        "name": f"{relationship['constrained_table']}_to_{relationship['referred_table']}",
                        "relationship_type": rel_info["relationship_type"],
                        "documentation": rel_info["documentation"],
                        "status": rel_info["status"],
                        "constrained_table": relationship["constrained_table"],
                        "referred_table": relationship["referred_table"]
                    }
            
            # Combine all summaries
            all_summaries = {**table_summaries, **relationship_summaries}
            
            # Calculate statistics
            statistics = {
                "total_items": len(all_summaries),
                "tables": {
                    "total": len(table_summaries),
                    "completed": len([t for t in table_summaries.values() if t["status"] == "completed"])
                },
                "relationships": {
                    "total": len(relationship_summaries),
                    "completed": len([r for r in relationship_summaries.values() if r["status"] == "completed"])
                }
            }
            
            elapsed = time.perf_counter() - start_time
            logger.info(f"get_all_summaries total execution time: {elapsed:.4f} seconds")
            
            return jsonify({
                "success": True,
                "summaries": all_summaries,
                "statistics": statistics
            })
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"get_all_summaries failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "summaries": {},
                "statistics": {}
            }), 500

    def get_summary_by_id(self, item_id):
        """Get a specific summary by ID."""
        start_time = time.perf_counter()
        logger.info(f"get_summary_by_id endpoint called with id: {item_id}")
        
        try:
            store = self.get_documentation_store()
            
            # Parse item_id to determine type and actual ID
            if item_id.startswith("table_"):
                table_name = item_id[6:]  # Remove "table_" prefix
                table_info = store.get_table_info(table_name)
                if table_info:
                    summary = {
                        "id": item_id,
                        "type": "table",
                        "name": table_name,
                        "business_purpose": table_info["business_purpose"],
                        "documentation": table_info["documentation"],
                        "schema_data": table_info["schema_data"],
                        "status": table_info["status"],
                        "processed_at": table_info.get("processed_at")
                    }
                    
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"get_summary_by_id total execution time: {elapsed:.4f} seconds")
                    return jsonify({
                        "success": True,
                        "summary": summary
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Table '{table_name}' not found"
                    }), 404
                    
            elif item_id.startswith("relationship_"):
                relationship_id = item_id[13:]  # Remove "relationship_" prefix
                all_relationships = store.get_all_relationships()
                
                # Find the relationship by ID
                target_relationship = None
                for rel in all_relationships:
                    if str(rel['id']) == relationship_id:
                        target_relationship = rel
                        break
                
                if target_relationship:
                    rel_info = store.get_relationship_info(relationship_id)
                    if rel_info:
                        summary = {
                            "id": item_id,
                            "type": "relationship",
                            "name": f"{target_relationship['constrained_table']}_to_{target_relationship['referred_table']}",
                            "relationship_type": rel_info["relationship_type"],
                            "documentation": rel_info["documentation"],
                            "status": rel_info["status"],
                            "constrained_table": target_relationship["constrained_table"],
                            "referred_table": target_relationship["referred_table"],
                            "constrained_columns": target_relationship["constrained_columns"],
                            "referred_columns": target_relationship["referred_columns"]
                        }
                        
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"get_summary_by_id total execution time: {elapsed:.4f} seconds")
                        return jsonify({
                            "success": True,
                            "summary": summary
                        })
                
                return jsonify({
                    "success": False,
                    "error": f"Relationship '{relationship_id}' not found"
                }), 404
            else:
                return jsonify({
                    "success": False,
                    "error": f"Invalid item ID format: {item_id}"
                }), 400
                
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"get_summary_by_id failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    def get_all_table_documentation(self):
        """Get all table documentation."""
        start_time = time.perf_counter()
        logger.info("get_all_table_documentation endpoint called.")
        
        try:
            store = self.get_documentation_store()
            all_tables = store.get_all_tables()
            
            table_documentation = {}
            for table_name in all_tables:
                table_info = store.get_table_info(table_name)
                if table_info:
                    table_documentation[table_name] = {
                        "table_name": table_name,
                        "business_purpose": table_info["business_purpose"],
                        "documentation": table_info["documentation"],
                        "schema_data": table_info["schema_data"],
                        "status": table_info["status"],
                        "processed_at": table_info.get("processed_at")
                    }
            
            elapsed = time.perf_counter() - start_time
            logger.info(f"get_all_table_documentation total execution time: {elapsed:.4f} seconds")
            
            return jsonify({
                "success": True,
                "tables": table_documentation,
                "total_tables": len(table_documentation)
            })
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"get_all_table_documentation failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "tables": {},
                "total_tables": 0
            }), 500

    def get_table_documentation(self, table_name):
        """Get documentation for a specific table."""
        start_time = time.perf_counter()
        logger.info(f"get_table_documentation endpoint called for table: {table_name}")
        
        try:
            store = self.get_documentation_store()
            table_info = store.get_table_info(table_name)
            
            if table_info:
                elapsed = time.perf_counter() - start_time
                logger.info(f"get_table_documentation total execution time: {elapsed:.4f} seconds")
                
                return jsonify({
                    "success": True,
                    "table": {
                        "table_name": table_name,
                        "business_purpose": table_info["business_purpose"],
                        "documentation": table_info["documentation"],
                        "schema_data": table_info["schema_data"],
                        "status": table_info["status"],
                        "processed_at": table_info.get("processed_at")
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                }), 404
                
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"get_table_documentation failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    def get_all_relationship_documentation(self):
        """Get all relationship documentation."""
        start_time = time.perf_counter()
        logger.info("get_all_relationship_documentation endpoint called.")
        
        try:
            store = self.get_documentation_store()
            all_relationships = store.get_all_relationships()
            
            relationship_documentation = {}
            for relationship in all_relationships:
                rel_info = store.get_relationship_info(str(relationship['id']))
                if rel_info:
                    relationship_documentation[str(relationship['id'])] = {
                        "id": relationship['id'],
                        "constrained_table": relationship["constrained_table"],
                        "referred_table": relationship["referred_table"],
                        "constrained_columns": relationship["constrained_columns"],
                        "referred_columns": relationship["referred_columns"],
                        "relationship_type": rel_info["relationship_type"],
                        "documentation": rel_info["documentation"],
                        "status": rel_info["status"],
                        "processed_at": rel_info.get("processed_at")
                    }
            
            elapsed = time.perf_counter() - start_time
            logger.info(f"get_all_relationship_documentation total execution time: {elapsed:.4f} seconds")
            
            return jsonify({
                "success": True,
                "relationships": relationship_documentation,
                "total_relationships": len(relationship_documentation)
            })
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"get_all_relationship_documentation failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e),
                "relationships": {},
                "total_relationships": 0
            }), 500

    def get_relationship_documentation(self, relationship_id):
        """Get documentation for a specific relationship."""
        start_time = time.perf_counter()
        logger.info(f"get_relationship_documentation endpoint called for relationship: {relationship_id}")
        
        try:
            store = self.get_documentation_store()
            all_relationships = store.get_all_relationships()
            
            # Find the target relationship
            target_relationship = None
            for rel in all_relationships:
                if str(rel['id']) == relationship_id:
                    target_relationship = rel
                    break
            
            if target_relationship:
                rel_info = store.get_relationship_info(relationship_id)
                if rel_info:
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"get_relationship_documentation total execution time: {elapsed:.4f} seconds")
                    
                    return jsonify({
                        "success": True,
                        "relationship": {
                            "id": relationship_id,
                            "constrained_table": target_relationship["constrained_table"],
                            "referred_table": target_relationship["referred_table"],
                            "constrained_columns": target_relationship["constrained_columns"],
                            "referred_columns": target_relationship["referred_columns"],
                            "relationship_type": rel_info["relationship_type"],
                            "documentation": rel_info["documentation"],
                            "status": rel_info["status"],
                            "processed_at": rel_info.get("processed_at")
                        }
                    })
            
            return jsonify({
                "success": False,
                "error": f"Relationship '{relationship_id}' not found"
            }), 404
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"get_relationship_documentation failed after {elapsed:.4f} seconds: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    def bad_request(self, error):
        """Handle bad request errors, with verbose logging."""
        logger.warning(f"Bad request: {error}")
        return jsonify({
            "success": False,
            "error": "Bad request",
            "message": str(error.description)
        }), 400

    def not_found(self, error):
        """Handle not found errors."""
        return jsonify({
            "success": False,
            "error": "Endpoint not found",
            "message": "The requested API endpoint does not exist"
        }), 404

    def internal_server_error(self, error):
        """Handle internal server errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }), 500

# Instantiate and expose the blueprint for use in the Flask app
api_routes = ApiRoutes()
api_bp = api_routes.api_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Configure CORS
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['ENV_VARS'] = {
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY')
    }
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize agent manager at app startup
    app.agent_manager = None
    
    def initialize_agents():
        """Initialize agents once at startup."""
        if app.agent_manager is not None:
            return app.agent_manager
            
        try:
            from src.agents.factory import agent_factory
            # Initialize the factory
            agent_factory.initialize()
            app.agent_manager = agent_factory
            logger.info("Agent manager initialized successfully at startup")
            return app.agent_manager
        except Exception as e:
            logger.error(f"Failed to initialize agent manager: {e}")
            app.agent_manager = None
            return None
    
    # Initialize agents immediately
    logger.info("Starting SQL Agents initialization...")
    initialize_agents()
    if app.agent_manager:
        logger.info("✅ SQL Agents initialized successfully")
        logger.info(f"Available agents: {list(app.agent_manager.get_all_agents().keys())}")
    else:
        logger.warning("⚠️ SQL Agents initialization failed")
    
    @app.route('/')
    def index():
        """Root endpoint."""
        return jsonify({
            "message": "Smol-SQL-Agents Backend API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/message",
                "status": "/api/status",
                "query": "/api/query",
                "recognize_entities": "/api/recognize-entities",
                "business_context": "/api/business-context",
                "generate_sql": "/api/generate-sql",
                "search": "/api/search",
                "schema": "/api/schema",
                "debug_objects": "/api/debug/objects",
                "debug_database": "/api/debug/database",
                "documentation": {
                    "all_summaries": "/api/documentation/summaries",
                    "summary_by_id": "/api/documentation/summaries/{id}",
                    "all_tables": "/api/documentation/tables",
                    "table_by_name": "/api/documentation/tables/{table_name}",
                    "all_relationships": "/api/documentation/relationships",
                    "relationship_by_id": "/api/documentation/relationships/{relationship_id}"
                }
            }
        })
    
    return app

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Smol-SQL-Agents Flask server on port {port}")
    print(f"📊 API endpoints available at http://localhost:{port}/api/")
    print(f"🔍 Health check: http://localhost:{port}/api/message")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )