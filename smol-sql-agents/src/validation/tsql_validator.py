import logging
import sqlparse
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class TSQLValidator:
    """Validates T-SQL syntax, best practices, and performance considerations."""
    
    def __init__(self):
        self.forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER']
        self.performance_patterns = self._load_performance_patterns()

    def validate_syntax(self, query: str) -> Dict[str, Any]:
        """Validate T-SQL syntax and structure."""
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Parse the query
            try:
                parsed_statements = sqlparse.parse(query)
                if not parsed_statements:
                    validation_result["valid"] = False
                    validation_result["errors"].append("Empty query")
                    return validation_result
                
                # Check each statement
                for statement in parsed_statements:
                    statement_validation = self._validate_statement(statement)
                    if not statement_validation["valid"]:
                        validation_result["valid"] = False
                        validation_result["errors"].extend(statement_validation["errors"])
                    
                    if statement_validation["warnings"]:
                        validation_result["warnings"].extend(statement_validation["warnings"])
                
            except Exception as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Syntax parsing error: {str(e)}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating syntax: {e}")
            return {"valid": False, "error": str(e)}

    def check_performance_patterns(self, query: str) -> List[Dict[str, str]]:
        """Check for common performance anti-patterns."""
        try:
            issues = []
            query_lower = query.lower()
            
            # Check for SELECT *
            if self._check_select_star_usage(query_lower):
                issues.append({
                    "type": "performance",
                    "severity": "warning",
                    "message": "SELECT * usage detected - consider specifying only needed columns"
                })
            
            # Check for missing WHERE clause in large table queries
            if "from" in query_lower and "where" not in query_lower:
                issues.append({
                    "type": "performance",
                    "severity": "warning",
                    "message": "No WHERE clause detected - consider adding filters for large tables"
                })
            
            # Check for potential N+1 query patterns
            if query_lower.count("select") > 3:
                issues.append({
                    "type": "performance",
                    "severity": "info",
                    "message": "Multiple SELECT statements detected - consider using JOINs or subqueries"
                })
            
            # Check for missing indexes hints
            if "join" in query_lower and "index" not in query_lower:
                issues.append({
                    "type": "performance",
                    "severity": "info",
                    "message": "JOIN detected without index hints - verify proper indexing"
                })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error checking performance patterns: {e}")
            return [{"type": "error", "severity": "error", "message": str(e)}]

    def validate_security(self, query: str) -> Dict[str, Any]:
        """Check for SQL injection risks and forbidden operations."""
        try:
            security_result = {
                "valid": True,
                "risks": [],
                "forbidden_operations": []
            }
            
            query_upper = query.upper()
            
            # Check for forbidden keywords
            for keyword in self.forbidden_keywords:
                if keyword in query_upper:
                    security_result["valid"] = False
                    security_result["forbidden_operations"].append(keyword)
            
            # Check for potential SQL injection patterns
            injection_patterns = [
                "exec(", "execute(", "sp_", "xp_", "openrowset", "opendatasource"
            ]
            
            for pattern in injection_patterns:
                if pattern in query_upper:
                    security_result["risks"].append(f"Potential SQL injection risk: {pattern}")
            
            # Check for dynamic SQL patterns
            if "exec" in query_upper or "execute" in query_upper:
                security_result["risks"].append("Dynamic SQL execution detected")
            
            # Check for system table access
            system_tables = ["sys.", "information_schema.", "master.", "tempdb."]
            for table in system_tables:
                if table in query_upper:
                    security_result["risks"].append(f"System table access: {table}")
            
            return security_result
            
        except Exception as e:
            logger.error(f"Error validating security: {e}")
            return {"valid": False, "error": str(e)}

    def suggest_improvements(self, query: str) -> List[Dict[str, str]]:
        """Suggest query improvements for readability and performance."""
        try:
            suggestions = []
            query_lower = query.lower()
            
            # Check for proper aliasing
            if "from" in query_lower and "as" not in query_lower:
                suggestions.append({
                    "type": "readability",
                    "message": "Consider using table aliases for better readability"
                })
            
            # Check for proper column aliasing
            if "select" in query_lower and "as" not in query_lower:
                suggestions.append({
                    "type": "readability",
                    "message": "Consider aliasing calculated columns for clarity"
                })
            
            # Check for proper indentation
            if query.count('\n') < 3:
                suggestions.append({
                    "type": "readability",
                    "message": "Consider proper query formatting and indentation"
                })
            
            # Check for ORDER BY without LIMIT
            if "order by" in query_lower and "limit" not in query_lower:
                suggestions.append({
                    "type": "performance",
                    "message": "Consider adding LIMIT clause when using ORDER BY"
                })
            
            # Check for proper JOIN syntax
            if "join" in query_lower and "on" not in query_lower:
                suggestions.append({
                    "type": "syntax",
                    "message": "JOIN detected without ON clause - verify join conditions"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            return [{"type": "error", "message": str(e)}]

    def _load_performance_patterns(self) -> Dict[str, str]:
        """Load performance anti-pattern definitions."""
        return {
            "select_star": "SELECT * usage without specific columns",
            "missing_where": "No WHERE clause on large table queries",
            "multiple_selects": "Multiple SELECT statements instead of JOINs",
            "missing_indexes": "JOINs without proper index considerations",
            "no_limit": "ORDER BY without LIMIT clause"
        }

    def _check_select_star_usage(self, query_lower: str) -> bool:
        """Check for inefficient SELECT * usage."""
        try:
            # Look for SELECT * pattern
            if "select *" in query_lower:
                # Check if it's in a subquery or main query
                select_parts = query_lower.split("select")
                for part in select_parts[1:]:  # Skip first empty part
                    if part.strip().startswith("*"):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking SELECT * usage: {e}")
            return False

    def _analyze_where_clause(self, parsed_query) -> List[str]:
        """Analyze WHERE clause for optimization opportunities."""
        try:
            issues = []
            
            def analyze_where_tokens(tokens):
                for token in tokens:
                    if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'WHERE':
                        # Analyze the WHERE clause
                        where_conditions = []
                        for sibling in token.parent.tokens:
                            if sibling.ttype is sqlparse.tokens.Whitespace:
                                continue
                            if sibling.ttype is sqlparse.tokens.Keyword and sibling.value.upper() == 'WHERE':
                                continue
                            where_conditions.append(str(sibling))
                        
                        where_text = ' '.join(where_conditions).lower()
                        
                        # Check for common issues
                        if "like '%" in where_text:
                            issues.append("LIKE with leading wildcard may not use indexes efficiently")
                        
                        if "or" in where_text and "and" in where_text:
                            issues.append("Complex OR/AND conditions may benefit from query restructuring")
                        
                        if "is null" in where_text:
                            issues.append("NULL checks may benefit from proper indexing")
                    
                    # Recursively check child tokens
                    for child in token.tokens:
                        analyze_where_tokens(child)
            
            analyze_where_tokens(parsed_query)
            return issues
            
        except Exception as e:
            logger.error(f"Error analyzing WHERE clause: {e}")
            return []

    def _validate_statement(self, statement) -> Dict[str, Any]:
        """Validate a single SQL statement."""
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Check for basic structure
            statement_text = str(statement).strip()
            if not statement_text:
                validation_result["valid"] = False
                validation_result["errors"].append("Empty statement")
                return validation_result
            
            # Check for required keywords
            if not any(keyword in statement_text.upper() for keyword in ["SELECT", "FROM"]):
                validation_result["valid"] = False
                validation_result["errors"].append("Missing required SELECT and FROM clauses")
            
            # Check for balanced parentheses
            if statement_text.count('(') != statement_text.count(')'):
                validation_result["valid"] = False
                validation_result["errors"].append("Unbalanced parentheses")
            
            # Check for proper semicolon usage
            if statement_text.endswith(';'):
                validation_result["warnings"].append("Semicolon at end of statement")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating statement: {e}")
            return {"valid": False, "error": str(e)} 