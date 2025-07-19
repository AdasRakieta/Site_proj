#!/usr/bin/env python3
"""
Legacy wrapper for asset minification

This script provides backward compatibility with the original minify_assets.py
interface while using the new organized utils/asset_manager.py implementation.

For new code, use utils/asset_manager.py directly.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the new asset manager
from utils.asset_manager import main

if __name__ == "__main__":
    print("Note: This is a legacy wrapper. Use 'python utils/asset_manager.py' for new code.")
    main()