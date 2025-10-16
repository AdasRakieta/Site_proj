"""
Manual script to update Polish cities cache
Run this to manually populate/update the city database
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.city_cache_updater import main

if __name__ == "__main__":
    print("🌍 Manual Polish Cities Cache Update")
    print("=" * 60)
    main()
