#!/usr/bin/env python3
"""
Test script to verify the SQL agents structure is working correctly.
This script tests imports and basic initialization of all components.
"""

import os
import sys
import logging

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_imports():
    """Test that all components can be imported successfully."""
    print("Testing imports...")
    
    try:
        # Test agent imports
        from agents import (
            BusinessContextAgent, 
            NL2SQLAgent, 
            SQLAgentPipeline,
            EntityRecognitionAgent,
            SQLIndexerAgent
        )
        print("✓ Agent imports successful")
        
        # Test concept imports
        from agents.concepts import ConceptLoader, ConceptMatcher, BusinessConcept
        print("✓ Concept imports successful")
        
        # Test validation imports
        from validation import BusinessValidator, TSQLValidator, QueryOptimizer
        print("✓ Validation imports successful")
        
        # Test database tools import
        from database.tools import DatabaseTools
        print("✓ Database tools import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during imports: {e}")
        return False

def test_concept_loader():
    """Test the concept loader functionality."""
    print("\nTesting concept loader...")
    
    try:
        from agents.concepts import ConceptLoader
        
        # Create a concept loader with a test directory
        concepts_dir = os.path.join(src_dir, "agents", "concepts")
        loader = ConceptLoader(concepts_dir)
        
        # Test getting all concepts
        all_concepts = loader.get_all_concepts()
        print(f"✓ Concept loader initialized, found {len(all_concepts)} concepts")
        
        return True
        
    except Exception as e:
        print(f"✗ Concept loader test failed: {e}")
        return False

def test_business_validator():
    """Test the business validator functionality."""
    print("\nTesting business validator...")
    
    try:
        from validation import BusinessValidator
        
        validator = BusinessValidator()
        print("✓ Business validator initialized")
        
        # Test basic validation
        test_query = "SELECT * FROM customers"
        validation_result = validator.validate_against_concepts(test_query, [])
        print(f"✓ Business validation test completed: {validation_result.get('valid', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Business validator test failed: {e}")
        return False

def test_tsql_validator():
    """Test the T-SQL validator functionality."""
    print("\nTesting T-SQL validator...")
    
    try:
        from validation import TSQLValidator
        
        validator = TSQLValidator()
        print("✓ T-SQL validator initialized")
        
        # Test basic validation
        test_query = "SELECT * FROM customers"
        validation_result = validator.validate_syntax(test_query)
        print(f"✓ T-SQL validation test completed: {validation_result.get('valid', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ T-SQL validator test failed: {e}")
        return False

def test_query_optimizer():
    """Test the query optimizer functionality."""
    print("\nTesting query optimizer...")
    
    try:
        from validation import QueryOptimizer
        
        optimizer = QueryOptimizer()
        print("✓ Query optimizer initialized")
        
        # Test basic optimization
        test_query = "SELECT * FROM customers"
        optimization_result = optimizer.analyze_performance(test_query)
        print(f"✓ Query optimization test completed: {optimization_result.get('complexity_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Query optimizer test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("SQL Agents Structure Test")
    print("=" * 40)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        test_imports,
        test_concept_loader,
        test_business_validator,
        test_tsql_validator,
        test_query_optimizer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The SQL agents structure is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main()) 