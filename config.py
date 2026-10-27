import os
from pathlib import Path

# InsightFace settings
INSIGHTFACE_MODEL = "buffalo_s"
INSIGHTFACE_DET_SIZE = (640, 640)
INSIGHTFACE_CTX_ID = -1  # CPU only

# Threshold para cosine distance (menor = mais rigoroso)
FACE_MATCH_THRESHOLD_DEFAULT = 0.4
FACE_MATCH_THRESHOLD_MIN = 0.2
FACE_MATCH_THRESHOLD_MAX = 0.6

# Cache versioning (invalida ao trocar modelo)
CACHE_MODEL_VERSION = "buffalo_s_v1"
CACHE_DIR = Path.home() / ".locate-me" / "cache"
CACHE_TTL_DAYS = 30

# Local folder settings
LOCAL_IMAGES_PATH = os.getenv("LOCAL_IMAGES_PATH", "")
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
THUMBNAIL_SIZE = (200, 200)
WARN_PHOTO_LIMIT = 500
FOLDER_CACHE_TTL_DAYS = 7

# Flickr link settings (optional)
DEFAULT_FLICKR_USERNAME = "pythonbrasil"
DEFAULT_FLICKR_ALBUM_ID = "72177720336294038"

# Processing
MAX_WORKERS = 4

STREAMLIT_CONFIG = {
    "page_title": "Locate-Me - Face Match em Pasta Local",
    "page_icon": "🔍",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}