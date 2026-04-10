import sys
import os

# Add the root directory to path so we can import backend.main
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app

# Vercel needs the app object to be named 'app'
handler = app
