"""Vercel Serverless entrypoint for MSANII Python backend."""
import os, sys

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from msanii import create_app

app = create_app()
