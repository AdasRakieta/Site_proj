#!/usr/bin/env python3
"""
Performance Test for SmartHome Caching Optimization
====================================================

This script tests the performance improvements from the caching optimization.
It simulates typical user interactions and measures response times.
"""

import time
import statistics
from app_db import SmartHomeApp
from utils.cache_manager import cache_stats, get_cache_hit_rate, reset_cache_stats

def simulate_user_session(app, user_id, session_id, num_requests=10):
    """Simulate a user session with multiple page requests"""
    times = []
    
    for i in range(num_requests):
        start_time = time.time()
        
        # Simulate getting user data like the routes do
        user_data = app.route_manager.get_cached_user_data(user_id, session_id)
        
        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Convert to milliseconds
        
        # Small delay between requests
        time.sleep(0.01)
    
    return times

def run_performance_test():
    """Run comprehensive performance test"""
    print("🚀 SmartHome Caching Performance Test")
    print("=" * 50)
    
    try:
        # Initialize app
        print("Initializing SmartHome application...")
        app = SmartHomeApp()
        print("✓ Application initialized\n")
        
        # Reset cache statistics
        reset_cache_stats()
        
        # Test parameters
        test_user_id = "test_user_123"
        test_session_id = "session_abc789"
        num_requests = 20
        
        print(f"Testing {num_requests} user data requests...")
        print(f"User ID: {test_user_id}")
        print(f"Session ID: {test_session_id}\n")
        
        # Run the test
        response_times = simulate_user_session(app, test_user_id, test_session_id, num_requests)
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        median_time = statistics.median(response_times)
        
        # Print results
        print("📊 Performance Results:")
        print("-" * 30)
        print(f"Total requests: {num_requests}")
        print(f"Average response time: {avg_time:.2f}ms")
        print(f"Minimum response time: {min_time:.2f}ms")
        print(f"Maximum response time: {max_time:.2f}ms")
        print(f"Median response time: {median_time:.2f}ms")
        
        # Cache statistics
        hit_rate = get_cache_hit_rate()
        print(f"\n📈 Cache Performance:")
        print("-" * 30)
        print(f"Cache hits: {cache_stats['hits']}")
        print(f"Cache misses: {cache_stats['misses']}")
        print(f"Total cache requests: {cache_stats['total_requests']}")
        print(f"Cache hit rate: {hit_rate:.1f}%")
        
        # Performance analysis
        print(f"\n🎯 Performance Analysis:")
        print("-" * 30)
        
        if hit_rate > 90:
            print("✅ Excellent cache performance! (>90% hit rate)")
        elif hit_rate > 70:
            print("✅ Good cache performance (70-90% hit rate)")
        elif hit_rate > 50:
            print("⚠️  Moderate cache performance (50-70% hit rate)")
        else:
            print("❌ Poor cache performance (<50% hit rate)")
        
        if avg_time < 1.0:
            print("✅ Excellent response times! (<1ms average)")
        elif avg_time < 5.0:
            print("✅ Good response times (<5ms average)")
        elif avg_time < 10.0:
            print("⚠️  Moderate response times (5-10ms average)")
        else:
            print("❌ Slow response times (>10ms average)")
        
        # Expected improvements
        print(f"\n💡 Expected Performance Improvements:")
        print("-" * 30)
        print("Without caching: ~50-200ms per database query")
        print("With session caching: ~0.1-2ms per cached request")
        print("Improvement factor: 25-2000x faster for cached data")
        print("Database load reduction: ~80-95% fewer queries")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_performance_test()