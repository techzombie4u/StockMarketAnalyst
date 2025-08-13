# conftest.py (at project root)
import sys, os

root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "src"))
