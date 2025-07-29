import logging
import sqlparse
from typing import Dict, List, Any
from ..agents.concepts.loader import BusinessConcept

logger = logging.getLogger(__name__)

class BusinessValidator:
    """Validates generated queries against business rules and concepts."""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()

    def validate_against_concepts(self, query: str, applicable_concepts: List[BusinessConcept]) -> Dict[str, Any]:
        """Validate query against business concept requirements."""
        try:
            validation_result = {
                "valid": True,
                "issues": [],
                "warnings": [],
                "concept_compliance": {}
            }
            
            for concept in applicable_concepts:
                concept_validation = self._validate_single_concept(query, concept)
                validation_result["concept_compliance"][concept.name] = concept_validation
                
                if not concept_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["issues"].extend(concept_validation["issues"])
                
                if concept_validation["warnings"]:
                    validation_result["warnings"].extend(concept_validation["warnings"])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating against concepts: {e}")
            return {
                "valid": False,
                "error": str(e),
                "issues": [],
                "warnings": []
            }

    def check_required_joins(self, query: str, required_joins: List[str]) -> Dict[str, bool]:
        """Verify that required joins are present in query."""
        try:
            parsed_query = sqlparse.parse(query)[0]
            query_joins = self._extract_joins_from_query(parsed_query)
            
            missing_joins = []
            for required_join in required_joins:
                if not self._join_exists_in_query(required_join, query_joins):
                    missing_joins.append(required_join)
            
            return {
                "valid": len(missing_joins) == 0,
                "missing_joins": missing_joins,
                "found_joins": query_joins
            }
            
        except Exception as e:
            logger.error(f"Error checking required joins: {e}")
            return {"valid": False, "error": str(e)}

    def validate_business_logic(self, query: str, business_instructions: List[str]) -> Dict[str, Any]:
        """Check if query follows business logic instructions."""
        try:
            validation_result = {
                "valid": True,
                "issues": [],
                "warnings": []
            }
            
            for instruction in business_instructions:
                instruction_check = self._check_instruction_compliance(query, instruction)
                if not instruction_check["compliant"]:
                    validation_result["valid"] = False
                    validation_result["issues"].append(instruction_check["issue"])
                elif instruction_check["warning"]:
                    validation_result["warnings"].append(instruction_check["warning"])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating business logic: {e}")
            return {"valid": False, "error": str(e)}

    def check_data_privacy_compliance(self, query: str) -> Dict[str, Any]:
        """Ensure query doesn't expose sensitive data inappropriately."""
        try:
            privacy_issues = []
            
            # Check for potential sensitive data patterns
            sensitive_patterns = [
                "password", "ssn", "credit_card", "social_security",
                "phone", "email", "address", "birth_date"
            ]
            
            query_lower = query.lower()
            for pattern in sensitive_patterns:
                if pattern in query_lower:
                    privacy_issues.append(f"Query may expose sensitive data: {pattern}")
            
            # Check for SELECT * usage which might expose unnecessary data
            if "select *" in query_lower:
                privacy_issues.append("SELECT * may expose unnecessary sensitive data")
            
            return {
                "compliant": len(privacy_issues) == 0,
                "issues": privacy_issues
            }
            
        except Exception as e:
            logger.error(f"Error checking data privacy compliance: {e}")
            return {"compliant": False, "error": str(e)}

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load business validation rules configuration."""
        return {
            "required_patterns": {
                "customer_lifetime_value": ["SUM", "COUNT", "customer"],
                "sales_performance_analysis": ["SUM", "AVG", "sales"],
                "inventory_analysis": ["COUNT", "SUM", "inventory"]
            },
            "forbidden_patterns": {
                "customer_lifetime_value": ["DELETE", "UPDATE", "DROP"],
                "sales_performance_analysis": ["DELETE", "UPDATE", "DROP"],
                "inventory_analysis": ["DELETE", "UPDATE", "DROP"]
            }
        }

    def _validate_single_concept(self, query: str, concept: BusinessConcept) -> Dict[str, Any]:
        """Validate query against a single business concept."""
        try:
            validation_result = {
                "valid": True,
                "issues": [],
                "warnings": []
            }
            
            # Check required joins
            if concept.required_joins:
                join_validation = self.check_required_joins(query, concept.required_joins)
                if not join_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Missing required joins: {join_validation['missing_joins']}")
            
            # Check business logic compliance
            if concept.instructions:
                logic_validation = self.validate_business_logic(query, [concept.instructions])
                if not logic_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["issues"].extend(logic_validation["issues"])
                
                if logic_validation["warnings"]:
                    validation_result["warnings"].extend(logic_validation["warnings"])
            
            # Check for required aggregation patterns
            if hasattr(concept, 'name') and concept.name in self.validation_rules["required_patterns"]:
                required_patterns = self.validation_rules["required_patterns"][concept.name]
                query_lower = query.lower()
                
                for pattern in required_patterns:
                    if pattern.lower() not in query_lower:
                        validation_result["warnings"].append(f"Expected pattern '{pattern}' not found in query")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating single concept: {e}")
            return {"valid": False, "error": str(e)}

    def _extract_joins_from_query(self, parsed_query) -> List[str]:
        """Extract JOIN clauses from parsed SQL."""
        try:
            joins = []
            
            def extract_joins_from_token(token):
                if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'JOIN':
                    # Get the join condition from surrounding tokens
                    join_condition = ""
                    for sibling in token.parent.tokens:
                        if sibling.ttype is sqlparse.tokens.Whitespace:
                            continue
                        if sibling.ttype is sqlparse.tokens.Keyword and sibling.value.upper() == 'ON':
                            # Get the condition after ON
                            for next_token in sibling.parent.tokens:
                                if next_token.ttype is sqlparse.tokens.Whitespace:
                                    continue
                                if next_token.ttype is sqlparse.tokens.Keyword and next_token.value.upper() == 'ON':
                                    continue
                                join_condition += str(next_token)
                            break
                        join_condition += str(sibling)
                    
                    if join_condition.strip():
                        joins.append(join_condition.strip())
                
                # Recursively check child tokens
                for child in token.tokens:
                    extract_joins_from_token(child)
            
            extract_joins_from_token(parsed_query)
            return joins
            
        except Exception as e:
            logger.error(f"Error extracting joins from query: {e}")
            return []

    def _join_exists_in_query(self, required_join: str, query_joins: List[str]) -> bool:
        """Check if a required join exists in the query joins."""
        try:
            # Simple string matching for join conditions
            required_join_normalized = required_join.replace(" ", "").lower()
            
            for query_join in query_joins:
                query_join_normalized = query_join.replace(" ", "").lower()
                if required_join_normalized in query_join_normalized:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if join exists: {e}")
            return False

    def _check_instruction_compliance(self, query: str, instruction: str) -> Dict[str, Any]:
        """Check if query complies with a business instruction."""
        try:
            instruction_lower = instruction.lower()
            query_lower = query.lower()
            
            # Check for time-based analysis instructions
            if "time" in instruction_lower or "date" in instruction_lower:
                if not any(word in query_lower for word in ["date", "time", "year", "month", "day"]):
                    return {
                        "compliant": False,
                        "issue": "Time-based analysis required but no date/time filtering found",
                        "warning": None
                    }
            
            # Check for aggregation instructions
            if "calculate" in instruction_lower or "sum" in instruction_lower:
                if not any(func in query_lower for func in ["sum(", "count(", "avg(", "max(", "min("]):
                    return {
                        "compliant": False,
                        "issue": "Aggregation required but no aggregation functions found",
                        "warning": None
                    }
            
            # Check for grouping instructions
            if "group" in instruction_lower:
                if "group by" not in query_lower:
                    return {
                        "compliant": False,
                        "issue": "Grouping required but no GROUP BY clause found",
                        "warning": None
                    }
            
            return {
                "compliant": True,
                "issue": None,
                "warning": None
            }
            
        except Exception as e:
            logger.error(f"Error checking instruction compliance: {e}")
            return {"compliant": False, "error": str(e)}

    def _check_aggregation_compliance(self, query: str, concept_instructions: str) -> bool:
        """Verify aggregations follow business concept guidelines."""
        try:
            # This is a simplified check - in production you'd have more sophisticated logic
            query_lower = query.lower()
            instructions_lower = concept_instructions.lower()
            
            # Check if aggregation is required but missing
            if any(word in instructions_lower for word in ["calculate", "sum", "total", "average"]):
                if not any(func in query_lower for func in ["sum(", "count(", "avg(", "max(", "min("]):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking aggregation compliance: {e}")
            return False 