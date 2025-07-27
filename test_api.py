#!/usr/bin/env python3
"""
Test script to check API authentication
"""

import requests
import sys

def test_security_api():
    """Test the security API endpoint"""
    try:
        # Test without authentication
        print("Testing /api/security without authentication...")
        response = requests.get('http://localhost:8080/api/security')
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Response: {response.text[:200]}...")
        
        # Test main security page
        print("\nTesting /security page...")
        response = requests.get('http://localhost:8080/security')
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Response: {response.text[:200]}...")
        
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_security_api()
