import sys
import os

# Add the root and backend directory to path so we can import modules
# Use absolute path to ensure Vercel's environment can resolve it
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import the FastAPI instance from our backend
from backend.main import app

# Ensure Vercel sees the 'app' variable clearly
app = app
