
#!/usr/bin/env python3
"""
Stock Market Analyst - Main Application Entry Point
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the organized main
from src.core.main import main

if __name__ == "__main__":
    main()
