import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from PIL import Image
from unidecode import unidecode

from config import VALID_IMAGE_EXTENSIONS, THUMBNAIL_SIZE
from services.cache import get_folder_cache


@dataclass
class LocalPhoto:
    photo_id: str
    display_id: str
    title: str
    path: str
    rel_path: str
    width: int
    height: int
    mtime: float
    size_bytes: int

    @property
    def url_original(self) -> str:
        return f"file://{self.path}"

    @property
    def url_thumbnail(self) -> str:
        return f"file://{self.path}"


class LocalFolderService:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).expanduser().resolve()

    def scan(self, max_photos: Optional[int] = None) -> List[LocalPhoto]:
        folder_cache = get_folder_cache()

        cached = folder_cache.get(str(self.root_path))
        if cached:
            return [self._dict_to_photo(d) for d in cached]

        photos = []
        try:
            for entry in os.scandir(self.root_path):
                if not entry.is_file():
                    continue
                ext = Path(entry.name).suffix.lower()
                if ext not in VALID_IMAGE_EXTENSIONS:
                    continue

                try:
                    stat = entry.stat()
                    width, height = self._get_image_dimensions(entry.path)
                    rel_path = entry.name
                    stem = Path(entry.name).stem
                    display_id = stem[:11] if len(stem) >= 11 else stem
                    photo_id = hashlib.md5(rel_path.encode()).hexdigest()[:12]
                    title = self._normalize_title(Path(entry.name).stem)

                    photo = LocalPhoto(
                        photo_id=photo_id,
                        display_id=display_id,
                        title=title,
                        path=entry.path,
                        rel_path=rel_path,
                        width=width,
                        height=height,
                        mtime=stat.st_mtime,
                        size_bytes=stat.st_size,
                    )
                    photos.append(photo)

                    if max_photos and len(photos) >= max_photos:
                        break
                except (PermissionError, OSError) as e:
                    print(f"Warning: Could not process {entry.path}: {e}")
                    continue
        except PermissionError:
            print(f"Warning: Permission denied accessing {self.root_path}")
            return []

        seen = set()
        unique_photos = []
        for p in photos:
            norm = self._normalize_title(p.title)
            if norm not in seen:
                seen.add(norm)
                unique_photos.append(p)
            else:
                print(f"Duplicate ignored: {p.title} ({p.path})")

        folder_cache.set(str(self.root_path), [self._photo_to_dict(p) for p in unique_photos])
        return unique_photos

    def _get_image_dimensions(self, path: str) -> tuple[int, int]:
        try:
            with Image.open(path) as img:
                return img.size
        except Exception:
            return (0, 0)

    def _normalize_title(self, title: str) -> str:
        title = unidecode(title).lower().strip()
        import re
        title = re.sub(r'[-_\s]*(copy|copia|\(\d+\))$', '', title)
        title = re.sub(r'[-_\s]+', ' ', title)
        return title.strip()

    def get_image_bytes(self, photo: LocalPhoto) -> Optional[bytes]:
        try:
            with open(photo.path, "rb") as f:
                return f.read()
        except (PermissionError, OSError, FileNotFoundError) as e:
            print(f"Error reading {photo.path}: {e}")
            return None

    def _photo_to_dict(self, photo: LocalPhoto) -> dict:
        return {
            "photo_id": photo.photo_id,
            "display_id": photo.display_id,
            "title": photo.title,
            "path": photo.path,
            "rel_path": photo.rel_path,
            "width": photo.width,
            "height": photo.height,
            "mtime": photo.mtime,
            "size_bytes": photo.size_bytes,
        }

    def _dict_to_photo(self, d: dict) -> LocalPhoto:
        return LocalPhoto(
            photo_id=d["photo_id"],
            display_id=d.get("display_id", d["photo_id"][:11]),
            title=d["title"],
            path=d["path"],
            rel_path=d["rel_path"],
            width=d["width"],
            height=d["height"],
            mtime=d["mtime"],
            size_bytes=d["size_bytes"],
        )