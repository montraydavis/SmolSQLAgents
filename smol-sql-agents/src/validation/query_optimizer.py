import logging
import sqlparse
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Provides query optimization suggestions and improvements."""
    
    def __init__(self):
        self.optimization_rules = self._load_optimization_rules()

    def analyze_performance(self, query: str, execution_plan: Dict = None) -> Dict[str, Any]:
        """Analyze query performance and suggest optimizations."""
        try:
            analysis_result = {
                "complexity_score": 0,
                "optimization_suggestions": [],
                "performance_issues": [],
                "estimated_impact": "low"
            }
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(query)
            analysis_result["complexity_score"] = complexity_score
            
            # Get optimization suggestions
            suggestions = self._get_optimization_suggestions(query)
            analysis_result["optimization_suggestions"] = suggestions
            
            # Identify performance issues
            performance_issues = self._identify_performance_issues(query)
            analysis_result["performance_issues"] = performance_issues
            
            # Estimate impact based on issues and suggestions
            impact_level = self._estimate_optimization_impact(suggestions, performance_issues)
            analysis_result["estimated_impact"] = impact_level
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {"error": str(e)}

    def suggest_index_usage(self, query: str, table_stats: Dict) -> List[Dict[str, str]]:
        """Suggest optimal index usage for query."""
        try:
            suggestions = []
            query_lower = query.lower()
            
            # Extract table names from query
            tables = self._extract_table_names(query)
            
            for table in tables:
                if table in table_stats and table_stats[table].get("exists", False):
                    row_count = table_stats[table].get("row_count", 0)
                    
                    # Suggest indexes based on query patterns
                    if "where" in query_lower and row_count > 10000:
                        suggestions.append({
                            "table": table,
                            "type": "index",
                            "message": f"Consider adding indexes on WHERE clause columns for table {table} ({row_count} rows)"
                        })
                    
                    if "join" in query_lower and row_count > 5000:
                        suggestions.append({
                            "table": table,
                            "type": "index",
                            "message": f"Consider adding indexes on JOIN columns for table {table}"
                        })
                    
                    if "order by" in query_lower and row_count > 1000:
                        suggestions.append({
                            "table": table,
                            "type": "index",
                            "message": f"Consider adding indexes on ORDER BY columns for table {table}"
                        })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting index usage: {e}")
            return [{"error": str(e)}]

    def optimize_joins(self, query: str) -> Dict[str, Any]:
        """Suggest JOIN optimization strategies."""
        try:
            optimization_result = {
                "suggestions": [],
                "join_order": [],
                "estimated_improvement": "low"
            }
            
            # Analyze JOIN structure
            join_analysis = self._analyze_join_structure(query)
            
            if join_analysis["join_count"] > 2:
                optimization_result["suggestions"].append({
                    "type": "join_order",
                    "message": "Multiple JOINs detected - consider optimizing join order for better performance"
                })
            
            if join_analysis["has_cross_join"]:
                optimization_result["suggestions"].append({
                    "type": "join_type",
                    "message": "CROSS JOIN detected - consider using INNER JOIN with proper conditions"
                })
            
            if join_analysis["has_subquery_joins"]:
                optimization_result["suggestions"].append({
                    "type": "join_style",
                    "message": "Subquery in JOIN detected - consider using EXISTS or IN for better performance"
                })
            
            # Suggest join order optimization
            if join_analysis["join_count"] > 1:
                optimization_result["join_order"] = self._suggest_join_order(query)
                optimization_result["estimated_improvement"] = "medium"
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing joins: {e}")
            return {"error": str(e)}

    def suggest_query_rewrite(self, query: str) -> Optional[str]:
        """Suggest alternative query structure for better performance."""
        try:
            query_lower = query.lower()
            rewritten_query = query
            
            # Replace SELECT * with specific columns if possible
            if "select *" in query_lower:
                # This is a simplified example - in practice you'd need schema information
                rewritten_query = rewritten_query.replace("SELECT *", "SELECT id, name, created_date")
            
            # Optimize WHERE clauses
            if "where" in query_lower and "like '%" in query_lower:
                # Suggest using full-text search or prefix matching
                rewritten_query = rewritten_query.replace("LIKE '%", "LIKE '")
            
            # Optimize subqueries
            if "in (" in query_lower and "select" in query_lower:
                # Suggest using EXISTS instead of IN with subquery
                # This is a simplified example
                pass
            
            # Only return if there are actual changes
            if rewritten_query != query:
                return rewritten_query
            
            return None
            
        except Exception as e:
            logger.error(f"Error suggesting query rewrite: {e}")
            return None

    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load query optimization rule definitions."""
        return {
            "complexity_thresholds": {
                "low": 10,
                "medium": 25,
                "high": 50
            },
            "performance_patterns": {
                "select_star": {"impact": "medium", "suggestion": "Specify only needed columns"},
                "missing_where": {"impact": "high", "suggestion": "Add WHERE clause for large tables"},
                "inefficient_joins": {"impact": "medium", "suggestion": "Optimize JOIN order and conditions"},
                "subquery_in_select": {"impact": "medium", "suggestion": "Consider using JOINs instead"}
            }
        }

    def _calculate_complexity_score(self, query: str) -> int:
        """Calculate query complexity score."""
        try:
            score = 0
            query_lower = query.lower()
            
            # Count various complexity factors
            score += query_lower.count("join") * 5
            score += query_lower.count("select") * 2
            score += query_lower.count("where") * 3
            score += query_lower.count("group by") * 4
            score += query_lower.count("order by") * 3
            score += query_lower.count("having") * 4
            score += query_lower.count("union") * 6
            score += query_lower.count("subquery") * 5
            
            # Add complexity for nested structures
            score += (query.count('(') - query.count(')')) * 2
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0

    def _get_optimization_suggestions(self, query: str) -> List[Dict[str, str]]:
        """Get specific optimization suggestions for the query."""
        try:
            suggestions = []
            query_lower = query.lower()
            
            # Check for SELECT *
            if "select *" in query_lower:
                suggestions.append({
                    "type": "performance",
                    "priority": "high",
                    "message": "Replace SELECT * with specific column names",
                    "impact": "medium"
                })
            
            # Check for missing WHERE clause
            if "from" in query_lower and "where" not in query_lower:
                suggestions.append({
                    "type": "performance",
                    "priority": "medium",
                    "message": "Consider adding WHERE clause for large tables",
                    "impact": "high"
                })
            
            # Check for inefficient JOINs
            if query_lower.count("join") > 2:
                suggestions.append({
                    "type": "performance",
                    "priority": "medium",
                    "message": "Multiple JOINs detected - consider optimizing join order",
                    "impact": "medium"
                })
            
            # Check for subqueries in SELECT
            if "select" in query_lower and "(" in query_lower:
                suggestions.append({
                    "type": "performance",
                    "priority": "low",
                    "message": "Consider using JOINs instead of subqueries in SELECT",
                    "impact": "medium"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting optimization suggestions: {e}")
            return [{"error": str(e)}]

    def _identify_performance_issues(self, query: str) -> List[Dict[str, str]]:
        """Identify specific performance issues in the query."""
        try:
            issues = []
            query_lower = query.lower()
            
            # Check for common anti-patterns
            if "select *" in query_lower:
                issues.append({
                    "type": "anti_pattern",
                    "severity": "warning",
                    "description": "SELECT * usage may return unnecessary data"
                })
            
            if "order by" in query_lower and "limit" not in query_lower:
                issues.append({
                    "type": "performance",
                    "severity": "info",
                    "description": "ORDER BY without LIMIT may process large result sets"
                })
            
            if query_lower.count("select") > 3:
                issues.append({
                    "type": "complexity",
                    "severity": "warning",
                    "description": "Multiple SELECT statements may indicate inefficient query structure"
                })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error identifying performance issues: {e}")
            return [{"error": str(e)}]

    def _estimate_optimization_impact(self, suggestions: List[Dict], issues: List[Dict]) -> str:
        """Estimate the impact of applying optimizations."""
        try:
            high_priority_count = sum(1 for s in suggestions if s.get("priority") == "high")
            high_impact_count = sum(1 for s in suggestions if s.get("impact") == "high")
            
            if high_priority_count > 0 or high_impact_count > 0:
                return "high"
            elif len(suggestions) > 2 or len(issues) > 2:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error estimating optimization impact: {e}")
            return "low"

    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from query."""
        try:
            tables = []
            query_lower = query.lower()
            
            # Simple extraction - in production you'd use proper SQL parsing
            words = query_lower.split()
            for i, word in enumerate(words):
                if word == "from" and i + 1 < len(words):
                    table_name = words[i + 1].strip(";,")
                    if table_name and not table_name.startswith("("):
                        tables.append(table_name)
                elif word == "join" and i + 1 < len(words):
                    table_name = words[i + 1].strip(";,")
                    if table_name and not table_name.startswith("("):
                        tables.append(table_name)
            
            return list(set(tables))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting table names: {e}")
            return []

    def _analyze_join_structure(self, query: str) -> Dict[str, Any]:
        """Analyze the JOIN structure of the query."""
        try:
            analysis = {
                "join_count": 0,
                "has_cross_join": False,
                "has_subquery_joins": False,
                "join_types": []
            }
            
            query_lower = query.lower()
            
            # Count JOINs
            analysis["join_count"] = query_lower.count("join")
            
            # Check for CROSS JOIN
            if "cross join" in query_lower:
                analysis["has_cross_join"] = True
                analysis["join_types"].append("CROSS")
            
            # Check for subquery JOINs
            if "join" in query_lower and "(" in query_lower:
                analysis["has_subquery_joins"] = True
            
            # Identify other join types
            if "inner join" in query_lower:
                analysis["join_types"].append("INNER")
            if "left join" in query_lower:
                analysis["join_types"].append("LEFT")
            if "right join" in query_lower:
                analysis["join_types"].append("RIGHT")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing join structure: {e}")
            return {"join_count": 0, "has_cross_join": False, "has_subquery_joins": False, "join_types": []}

    def _suggest_join_order(self, query: str) -> List[str]:
        """Suggest optimal join order based on table sizes and relationships."""
        try:
            # This is a simplified suggestion - in practice you'd need table statistics
            tables = self._extract_table_names(query)
            
            if len(tables) <= 2:
                return tables
            
            # Simple heuristic: put smaller tables first
            # In practice, you'd use actual table statistics
            return sorted(tables, key=lambda x: len(x))  # Sort by table name length as proxy for size
            
        except Exception as e:
            logger.error(f"Error suggesting join order: {e}")
            return []

    def _analyze_join_order(self, parsed_query) -> List[str]:
        """Analyze JOIN order for optimization opportunities."""
        try:
            issues = []
            
            # This would analyze the actual JOIN order in the parsed query
            # For now, return empty list as placeholder
            return issues
            
        except Exception as e:
            logger.error(f"Error analyzing join order: {e}")
            return []

    def _check_subquery_optimization(self, parsed_query) -> List[str]:
        """Check if subqueries can be optimized or rewritten."""
        try:
            issues = []
            
            # This would analyze subqueries in the parsed query
            # For now, return empty list as placeholder
            return issues
            
        except Exception as e:
            logger.error(f"Error checking subquery optimization: {e}")
            return [] 