#!/usr/bin/env python3
"""
Database Performance Test Script
Tests the performance improvements in DatabaseInspector
"""

import time
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.inspector import DatabaseInspector, get_database_inspector

def test_initialization_performance():
    """Test the performance difference between old and new initialization."""
    print("🔍 Testing DatabaseInspector Performance")
    print("=" * 50)
    
    # Test 1: Old style (eager loading)
    print("\n1. Testing eager loading (old style):")
    start_time = time.time()
    try:
        inspector1 = DatabaseInspector(lazy_load=False)
        eager_time = time.time() - start_time
        print(f"   ✅ Eager loading took: {eager_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Eager loading failed: {e}")
        eager_time = None
    
    # Test 2: Lazy loading (new style)
    print("\n2. Testing lazy loading (new style):")
    start_time = time.time()
    try:
        inspector2 = DatabaseInspector(lazy_load=True)
        lazy_time = time.time() - start_time
        print(f"   ✅ Lazy loading took: {lazy_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Lazy loading failed: {e}")
        lazy_time = None
    
    # Test 3: Singleton pattern
    print("\n3. Testing singleton pattern:")
    start_time = time.time()
    try:
        inspector3 = get_database_inspector(lazy_load=True)
        singleton_time = time.time() - start_time
        print(f"   ✅ Singleton creation took: {singleton_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Singleton creation failed: {e}")
        singleton_time = None
    
    # Test 4: Cache warming
    print("\n4. Testing cache warming:")
    if inspector2:
        start_time = time.time()
        try:
            inspector2.warm_up_cache()
            warm_time = time.time() - start_time
            print(f"   ✅ Cache warming took: {warm_time:.2f}s")
        except Exception as e:
            print(f"   ❌ Cache warming failed: {e}")
            warm_time = None
    
    # Test 5: Cached operations
    print("\n5. Testing cached operations:")
    if inspector2:
        start_time = time.time()
        try:
            tables = inspector2.get_all_table_names()
            cached_time = time.time() - start_time
            print(f"   ✅ Cached table names took: {cached_time:.4f}s")
            print(f"   📊 Found {len(tables)} tables")
        except Exception as e:
            print(f"   ❌ Cached operations failed: {e}")
    
    # Performance comparison
    print("\n" + "=" * 50)
    print("📊 Performance Summary:")
    if eager_time and lazy_time:
        improvement = ((eager_time - lazy_time) / eager_time) * 100
        print(f"   Lazy loading is {improvement:.1f}% faster than eager loading")
    
    if singleton_time:
        print(f"   Singleton creation: {singleton_time:.2f}s")
    
    # Cache stats
    if inspector2:
        stats = inspector2.get_cache_stats()
        print(f"   Cache stats: {stats}")

def test_connection_pool():
    """Test connection pool performance."""
    print("\n🔍 Testing Connection Pool")
    print("=" * 30)
    
    try:
        inspector = get_database_inspector()
        
        # Test multiple operations
        operations = [
            ("get_all_table_names", lambda: inspector.get_all_table_names()),
            ("get_table_schema (first table)", lambda: inspector.get_table_schema("users") if "users" in inspector.get_all_table_names() else None),
            ("get_foreign_key_relationships", lambda: inspector.get_all_foreign_key_relationships())
        ]
        
        for name, operation in operations:
            start_time = time.time()
            try:
                result = operation()
                duration = time.time() - start_time
                print(f"   ✅ {name}: {duration:.4f}s")
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
        
        # Show pool stats
        pool = inspector.engine.pool
        print(f"\n   📊 Connection Pool Stats:")
        print(f"      Pool size: {pool.size()}")
        print(f"      Checked in: {pool.checkedin()}")
        print(f"      Checked out: {pool.checkedout()}")
        print(f"      Overflow: {pool.overflow()}")
        
    except Exception as e:
        print(f"   ❌ Connection pool test failed: {e}")

if __name__ == "__main__":
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL before running this test")
        sys.exit(1)
    
    test_initialization_performance()
    test_connection_pool()
    
    print("\n✅ Performance test completed!") 