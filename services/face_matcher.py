import io
import gc
import insightface
import numpy as np
import cv2
from PIL import Image
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    INSIGHTFACE_MODEL,
    INSIGHTFACE_DET_SIZE,
    INSIGHTFACE_CTX_ID,
    FACE_MATCH_THRESHOLD_DEFAULT,
    MAX_WORKERS,
)
from services.cache import get_cache


@dataclass
class FaceData:
    embedding: np.ndarray
    bbox: np.ndarray
    det_score: float
    kps: Optional[np.ndarray]


@dataclass
class FaceMatch:
    photo_id: str
    display_id: str
    title: str
    url_original: str
    url_thumbnail: str
    distance: float
    similarity_percent: float


_matcher_instance: Optional[insightface.app.FaceAnalysis] = None


def get_matcher() -> insightface.app.FaceAnalysis:
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = insightface.app.FaceAnalysis(
            name=INSIGHTFACE_MODEL,
            providers=['CPUExecutionProvider']
        )
        _matcher_instance.prepare(ctx_id=INSIGHTFACE_CTX_ID, det_size=INSIGHTFACE_DET_SIZE)
    return _matcher_instance


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return np.array(image)


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return 1.0 - float(np.dot(a, b))


def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(embedding)
    if norm > 0:
        return embedding / norm
    return embedding


def get_face_embeddings(image: np.ndarray) -> List[FaceData]:
    matcher = get_matcher()
    faces = matcher.get(image)
    if not faces:
        return []

    result = []
    for face in faces:
        emb = face.embedding.astype(np.float32)
        emb = _normalize_embedding(emb)
        result.append(FaceData(
            embedding=emb,
            bbox=face.bbox.astype(np.float32),
            det_score=float(face.det_score),
            kps=face.kps.astype(np.float32) if face.kps is not None else None,
        ))
    return result


def get_largest_face(faces: List[FaceData]) -> FaceData:
    return max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))


def get_reference_embedding(image_bytes: bytes) -> Tuple[Optional[np.ndarray], int, str]:
    image = load_image_from_bytes(image_bytes)
    faces = get_face_embeddings(image)
    num_faces = len(faces)

    if num_faces == 0:
        return None, 0, "Nenhum rosto detectado na imagem de referência"

    if num_faces > 1:
        largest = get_largest_face(faces)
        return largest.embedding, num_faces, f"Múltiplos rostos detectados ({num_faces}), usando o principal"

    return faces[0].embedding, 1, "Rosto detectado com sucesso"


def process_photo(
    photo: object,
    reference_embedding: np.ndarray,
    threshold: float,
    image_loader: Callable[[object], Optional[bytes]]
) -> Optional[FaceMatch]:
    cache = get_cache()

    photo_id = getattr(photo, 'photo_id', None)
    if photo_id is None:
        return None

    if cache.has(photo_id):
        cached_embeddings = cache.get(photo_id)
        if cached_embeddings:
            embeddings = cached_embeddings
        else:
            embeddings = []
    else:
        image_bytes = image_loader(photo)
        if not image_bytes:
            return None
        image = load_image_from_bytes(image_bytes)
        faces = get_face_embeddings(image)
        embeddings = [f.embedding for f in faces]
        if embeddings:
            cache.set(photo_id, embeddings)

    if not embeddings:
        return None

    distances = [cosine_distance(emb, reference_embedding) for emb in embeddings]
    min_distance = min(distances)

    if min_distance < threshold:
        similarity = (1.0 - min_distance) * 100
        return FaceMatch(
            photo_id=photo_id,
            display_id=getattr(photo, 'display_id', photo_id[:11]),
            title=getattr(photo, 'title', 'Sem título'),
            url_original=getattr(photo, 'url_original', getattr(photo, 'path', '')),
            url_thumbnail=getattr(photo, 'url_thumbnail', getattr(photo, 'path', '')),
            distance=min_distance,
            similarity_percent=similarity,
        )
    return None


def find_matches(
    photos: List[object],
    reference_embedding: np.ndarray,
    threshold: float,
    image_loader: Callable[[object], Optional[bytes]],
    progress_callback=None
) -> List[FaceMatch]:
    matches = []
    total = len(photos)
    processed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_photo = {
            executor.submit(process_photo, photo, reference_embedding, threshold, image_loader): photo
            for photo in photos
        }

        for future in as_completed(future_to_photo):
            processed += 1
            result = future.result()
            if result:
                matches.append(result)

            if progress_callback:
                progress_callback(processed, total, len(matches))

            gc.collect()

    matches.sort(key=lambda m: m.distance)
    return matches