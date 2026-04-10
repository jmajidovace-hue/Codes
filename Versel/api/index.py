import sys
import os

# Add the root and backend directory to path so we can import modules
root_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'backend'))

from backend.main import app

# Vercel needs the app object to be named 'app'
app = app
