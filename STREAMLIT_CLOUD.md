# Streamlit Cloud Deployment

## Quick Deploy

1. Go to https://share.streamlit.io
2. Click "New app"
3. Repository: select this repo
4. Branch: master
5. Main file path: `annotation_tool/app_chinese.py`
6. Deploy!

## After Deploy

Share the Streamlit Cloud URL with annotators:
- They open the URL
- Enter annotator ID (e.g., A001, A002)
- Start annotating!

## Data Storage

**Important:** Current version uses local file storage (`data/annotation_db/`).
This won't persist on Streamlit Cloud's ephemeral filesystem.

For production use, consider:
1. Streamlit Cloud with persistent storage
2. Render with PostgreSQL
3. Custom deployment with database
