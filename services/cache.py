import hashlib
import os
import pickle
from pathlib import Path
from typing import Any, Optional, List
import numpy as np
from diskcache import Cache

from config import CACHE_DIR, CACHE_TTL_DAYS, CACHE_MODEL_VERSION, FOLDER_CACHE_TTL_DAYS


class EmbeddingCache:
    def __init__(self):
        self.cache = Cache(str(CACHE_DIR))
        self.ttl_seconds = CACHE_TTL_DAYS * 24 * 60 * 60

    def _make_key(self, photo_id: str, size_label: str = "original") -> str:
        return f"emb_{CACHE_MODEL_VERSION}_{photo_id}_{size_label}"

    def get(self, photo_id: str, size_label: str = "original") -> Optional[List[np.ndarray]]:
        key = self._make_key(photo_id, size_label)
        data = self.cache.get(key)
        if data is None:
            return None
        try:
            return pickle.loads(data)
        except Exception:
            return None

    def set(self, photo_id: str, embeddings: List[np.ndarray], size_label: str = "original") -> None:
        key = self._make_key(photo_id, size_label)
        data = pickle.dumps(embeddings)
        self.cache.set(key, data, expire=self.ttl_seconds)

    def has(self, photo_id: str, size_label: str = "original") -> bool:
        key = self._make_key(photo_id, size_label)
        return key in self.cache

    def clear(self) -> None:
        self.cache.clear()

    def close(self) -> None:
        self.cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class FolderCache:
    def __init__(self):
        self.cache = Cache(str(CACHE_DIR))
        self.ttl_seconds = FOLDER_CACHE_TTL_DAYS * 24 * 60 * 60

    def _make_key(self, root_path: str) -> str:
        try:
            stat = os.stat(root_path)
            files = [
                f for f in os.listdir(root_path)
                if Path(f).suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
            ]
            path_hash = hashlib.md5(root_path.encode()).hexdigest()[:12]
            return f"folder_{path_hash}_{len(files)}_{int(stat.st_mtime)}"
        except Exception:
            path_hash = hashlib.md5(root_path.encode()).hexdigest()[:12]
            return f"folder_{path_hash}_0_0"

    def get(self, root_path: str) -> Optional[List[dict]]:
        key = self._make_key(root_path)
        data = self.cache.get(key)
        if data is None:
            return None
        try:
            return pickle.loads(data)
        except Exception:
            return None

    def set(self, root_path: str, photos_data: List[dict]) -> None:
        key = self._make_key(root_path)
        data = pickle.dumps(photos_data)
        self.cache.set(key, data, expire=self.ttl_seconds)

    def has(self, root_path: str) -> bool:
        key = self._make_key(root_path)
        return key in self.cache

    def clear(self) -> None:
        self.cache.clear()

    def close(self) -> None:
        self.cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


_embedding_cache: Optional[EmbeddingCache] = None
_folder_cache: Optional[FolderCache] = None


def get_cache() -> EmbeddingCache:
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache


def get_folder_cache() -> FolderCache:
    global _folder_cache
    if _folder_cache is None:
        _folder_cache = FolderCache()
    return _folder_cache