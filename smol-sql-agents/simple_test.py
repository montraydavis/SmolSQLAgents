#!/usr/bin/env python3
"""
Simple test script that avoids relative imports to test the basic structure.
"""

import os
import sys
import logging

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_direct_imports():
    """Test direct imports without relative imports."""
    print("Testing direct imports...")
    
    try:
        # Test external libraries
        import yaml
        print("✓ yaml import successful")
        
        import sqlparse
        print("✓ sqlparse import successful")
        
        # Test our validation modules directly
        import validation.business_validator
        print("✓ business_validator module import successful")
        
        import validation.tsql_validator
        print("✓ tsql_validator module import successful")
        
        import validation.query_optimizer
        print("✓ query_optimizer module import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_validation_classes():
    """Test validation class instantiation."""
    print("\nTesting validation classes...")
    
    try:
        from validation.business_validator import BusinessValidator
        from validation.tsql_validator import TSQLValidator
        from validation.query_optimizer import QueryOptimizer
        
        # Test business validator
        business_validator = BusinessValidator()
        print("✓ Business validator instantiated")
        
        # Test T-SQL validator
        tsql_validator = TSQLValidator()
        print("✓ T-SQL validator instantiated")
        
        # Test query optimizer
        query_optimizer = QueryOptimizer()
        print("✓ Query optimizer instantiated")
        
        return True
        
    except Exception as e:
        print(f"✗ Validation class test failed: {e}")
        return False

def test_validation_functionality():
    """Test basic validation functionality."""
    print("\nTesting validation functionality...")
    
    try:
        from validation.tsql_validator import TSQLValidator
        
        tsql_validator = TSQLValidator()
        
        # Test syntax validation
        test_query = "SELECT * FROM customers"
        result = tsql_validator.validate_syntax(test_query)
        print(f"✓ Syntax validation test: {result.get('valid', False)}")
        
        # Test performance patterns
        performance_issues = tsql_validator.check_performance_patterns(test_query)
        print(f"✓ Performance pattern check: {len(performance_issues)} issues found")
        
        # Test security validation
        security_result = tsql_validator.validate_security(test_query)
        print(f"✓ Security validation test: {security_result.get('valid', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Validation functionality test failed: {e}")
        return False

def test_query_optimizer():
    """Test query optimizer functionality."""
    print("\nTesting query optimizer...")
    
    try:
        from validation.query_optimizer import QueryOptimizer
        
        optimizer = QueryOptimizer()
        
        # Test performance analysis
        test_query = "SELECT * FROM customers"
        analysis = optimizer.analyze_performance(test_query)
        print(f"✓ Performance analysis: complexity score {analysis.get('complexity_score', 0)}")
        
        # Test optimization suggestions
        suggestions = optimizer._get_optimization_suggestions(test_query)
        print(f"✓ Optimization suggestions: {len(suggestions)} suggestions")
        
        return True
        
    except Exception as e:
        print(f"✗ Query optimizer test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("SQL Agents Structure Test (Simple)")
    print("=" * 40)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        test_direct_imports,
        test_validation_classes,
        test_validation_functionality,
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