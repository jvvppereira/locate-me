from .cache import EmbeddingCache, FolderCache, get_cache, get_folder_cache
from .local_folder import LocalFolderService, LocalPhoto
from .face_matcher import (
    FaceMatch,
    FaceData,
    get_reference_embedding,
    find_matches,
    process_photo,
    cosine_distance,
)

__all__ = [
    "EmbeddingCache",
    "FolderCache",
    "get_cache",
    "get_folder_cache",
    "LocalFolderService",
    "LocalPhoto",
    "FaceMatch",
    "FaceData",
    "get_reference_embedding",
    "find_matches",
    "process_photo",
    "cosine_distance",
]