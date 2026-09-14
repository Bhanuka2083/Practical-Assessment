import os
import sys

# Add the project root directory to sys.path so 'app' can be imported cleanly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))

for path in (current_dir, parent_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.main import app