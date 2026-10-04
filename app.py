"""
Streamlit Cloud Deployment Entry Point

This file serves as the main entry point for Streamlit Cloud deployment.
It imports and runs the Chinese annotation tool.

For deployment:
1. Upload this repository to GitHub
2. Go to https://share.streamlit.io
3. Create new app, select this repository
4. Set main file path: app.py
5. Deploy!

Annotators access via: https://your-app.streamlit.app
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the main function from the Chinese annotation app
from annotation_tool.app_chinese import main

# Run the Streamlit app
if __name__ == "__main__":
    main()