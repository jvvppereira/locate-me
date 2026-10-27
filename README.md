# Locate-Me - Face Match in Local Folder

Find photos of yourself in local folders using face recognition.

## 🚀 Quick Setup

### 1. Install Python Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> **Note**: InsightFace model (buffalo_s ~130MB) downloads automatically on first run.

### 2. Configure Image Folder (optional)
Set `LOCAL_IMAGES_PATH` in `.env`:
```bash
cp .env.example .env
# Edit .env:
LOCAL_IMAGES_PATH=/path/to/your/photos
```
Or enter path directly in the UI.

### 3. Run
```bash
streamlit run app.py
```

## 📖 How to Use

1. **Step 1 - Folder**: Enter path to folder with photos
   - Pre-filled from `LOCAL_IMAGES_PATH` if set
   - Override in UI if needed
   - Root folder only (non-recursive)
   - Formats: JPG, JPEG, PNG, WebP, BMP, TIFF

2. **Step 2 - Reference**: Upload a face photo

3. **Step 3 - Results**:
   - Adjust **Similarity Threshold** (0.2-0.6, default 0.4)
   - **Optional Flickr Link Config** (see below)
   - Click **Process** to find matches
   - View results in thumbnail grid
   - Use **Re-process** to adjust threshold without re-upload
   - Download CSV results

### Flickr Links (Optional)
In Step 3, configure to link thumbnails to Flickr:
- **Flickr Username** (default: `pythonbrasil`)
- **Album ID** (default: `72177720336294038`)

If both provided, thumbnails link to:
`https://www.flickr.com/photos/{username}/{display_id}/in/album-{album_id}/`

If either empty → links to local `file://` path.

## ⚙️ Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Model | InsightFace buffalo_s | CPU, ~130MB |
| Threshold | Cosine distance (0.2-0.6) | Lower = stricter |
| Default threshold | 0.4 | Balanced |
| Photo limit warning | 500 | Performance warning |
| Embedding cache TTL | 30 days | `~/.locate-me/cache` |
| Folder cache TTL | 7 days | Auto-invalidates on folder change |
| Workers | 4 | Parallel processing |
| Deduplication | Filename stem | Removes `_copy`, `(1)`, etc. |

### Threshold Guide

| Value | Similarity | Use Case |
|-------|------------|----------|
| 0.25 | 75%+ | Very strict |
| 0.35 | 65%+ | Strict |
| **0.40** | **60%+** | **Default (recommended)** |
| 0.45 | 55%+ | Moderate |
| 0.50 | 50%+ | Permissive |
| 0.55+ | <50% | Many false positives |

## 🛠️ Stack

- **UI**: Streamlit
- **Face Recognition**: InsightFace (SCRFD + ArcFace, ONNX)
- **Cache**: diskcache
- **Processing**: ThreadPoolExecutor (async with progress bar)

## 📁 Project Structure

```
locate-me/
├── app.py                 # Entry point
├── config.py              # Configuration
├── requirements.txt
├── .env.example
├── services/
│   ├── local_folder.py    # Local folder scanner
│   ├── face_matcher.py    # InsightFace pipeline
│   └── cache.py           # Embedding + folder cache
└── ui/
    ├── components.py      # Streamlit components
    └── steps/             # 3-step UI flow
```

## 🧹 Cache Management

### Clear All Caches
```bash
rm -rf ~/.locate-me/cache
```

### Clear Folder Cache Only (force re-scan)
```bash
touch /path/to/your/photos
```

### Cache Behavior
- **Embedding cache**: Stores face embeddings per photo (key: `emb_buffalo_s_v1_{photo_id}`)
- **Folder cache**: Stores file metadata (key includes folder mtime + file count)
- **Auto-invalidation**: Folder cache invalidates when file count or mtime changes
- **Manual clear**: Use commands above if stale data appears

## 📝 Notes

- Folder not monitored for changes during session
- Thumbnails generated on-demand with Pillow (no separate cache)
- Permission errors ignored silently
- Cache keys versioned by model (`buffalo_s_v1`)
- Photo IDs use MD5 hash; display IDs use first 11 chars of filename stem