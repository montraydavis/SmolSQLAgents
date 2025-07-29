#!/usr/bin/env python3
"""
Simple test script to verify the SQL agents structure.
Run with: python -m run_tests
"""

import os
import sys
import logging

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_basic_imports():
    """Test basic imports without relative imports."""
    print("Testing basic imports...")
    
    try:
        # Test direct imports
        import yaml
        print("✓ yaml import successful")
        
        import sqlparse
        print("✓ sqlparse import successful")
        
        # Test our modules
        from agents.concepts.loader import ConceptLoader
        print("✓ ConceptLoader import successful")
        
        from validation.business_validator import BusinessValidator
        print("✓ BusinessValidator import successful")
        
        from validation.tsql_validator import TSQLValidator
        print("✓ TSQLValidator import successful")
        
        from validation.query_optimizer import QueryOptimizer
        print("✓ QueryOptimizer import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_concept_loader():
    """Test the concept loader functionality."""
    print("\nTesting concept loader...")
    
    try:
        from agents.concepts.loader import ConceptLoader
        
        # Create a concept loader
        concepts_dir = os.path.join(src_dir, "agents", "concepts")
        loader = ConceptLoader(concepts_dir)
        
        # Test getting all concepts
        all_concepts = loader.get_all_concepts()
        print(f"✓ Concept loader initialized, found {len(all_concepts)} concepts")
        
        return True
        
    except Exception as e:
        print(f"✗ Concept loader test failed: {e}")
        return False

def test_validators():
    """Test the validators."""
    print("\nTesting validators...")
    
    try:
        from validation.business_validator import BusinessValidator
        from validation.tsql_validator import TSQLValidator
        from validation.query_optimizer import QueryOptimizer
        
        # Test business validator
        business_validator = BusinessValidator()
        print("✓ Business validator initialized")
        
        # Test T-SQL validator
        tsql_validator = TSQLValidator()
        print("✓ T-SQL validator initialized")
        
        # Test query optimizer
        query_optimizer = QueryOptimizer()
        print("✓ Query optimizer initialized")
        
        # Test basic validation
        test_query = "SELECT * FROM customers"
        syntax_result = tsql_validator.validate_syntax(test_query)
        print(f"✓ T-SQL validation test: {syntax_result.get('valid', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Validator test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("SQL Agents Structure Test")
    print("=" * 40)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        test_basic_imports,
        test_concept_loader,
        test_validators
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