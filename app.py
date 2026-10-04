"""
Streamlit Cloud Deployment Entry Point

This file serves as the main entry point for Streamlit Cloud deployment.
It simply imports and runs the Chinese annotation tool.

For deployment:
1. Upload this repository to GitHub
2. Go to https://share.streamlit.io
3. Create new app, select this repository
4. Set main file path: app.py
5. Deploy!

Annotators access via: https://your-app.streamlit.app
"""

# Import the main function from the Chinese annotation app
# Streamlit Cloud will automatically run st.script_runner

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Import the main function from app_chinese
# This is the simplest way to have app.py as entry point
exec(open('annotation_tool/app_chinese.py').read())

# Note: Streamlit will run the imported code directly
