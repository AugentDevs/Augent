"""
Augent Embeddings - Semantic search and chapter detection

Uses sentence-transformers for embedding-based audio analysis:
- deep_search: Find content by meaning, not just keywords
- detect_chapters: Auto-detect topic boundaries in audio
"""

import os
import threading
import numpy as np
from typing import Dict, Any, Optional, List

from .core import transcribe_audio
from .cache import get_transcription_cache, TranscriptionCache

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class EmbeddingModelCache:
    """In-memory cache for loaded sentence-transformer models."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._model_lock = threading.Lock()
        return cls._instance

    def get(self, model_name: str = EMBEDDING_MODEL):
        """Get a cached model or load a new one."""
        with self._model_lock:
            if model_name not in self._models:
                from sentence_transformers import SentenceTransformer
                self._models[model_name] = SentenceTransformer(model_name)
            return self._models[model_name]

    def clear(self):
        """Clear all cached models."""
        with self._model_lock:
            self._models.clear()


def _get_embedding_model_cache() -> EmbeddingModelCache:
    return EmbeddingModelCache()


def _cosine_similarity(query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between a query vector and a matrix of embeddings."""
    dot = np.dot(embeddings, query.T).flatten()
    norm_q = np.linalg.norm(query)
    norm_e = np.linalg.norm(embeddings, axis=1)
    return dot / (norm_q * norm_e + 1e-8)


def _get_or_compute_embeddings(
    segments: List[Dict], audio_hash: str,
    model_name: str = EMBEDDING_MODEL
) -> np.ndarray:
    """Get embeddings from cache or compute them."""
    cache = get_transcription_cache()

    # Check cache
    cached = cache.get_embeddings(audio_hash, model_name)
    if cached is not None:
        return cached["embeddings"]

    # Compute embeddings
    model = _get_embedding_model_cache().get(model_name)
    texts = [seg["text"].strip() for seg in segments]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    # Cache them
    cache.set_embeddings(
        audio_hash, model_name, embeddings,
        segment_count=len(segments),
        embedding_dim=embeddings.shape[1]
    )

    return embeddings


def deep_search(
    audio_path: str,
    query: str,
    model_size: str = "tiny",
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Semantic search across audio transcription.

    Finds segments by meaning, not just keywords.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Get transcription (cached)
    transcription = transcribe_audio(audio_path, model_size)
    segments = transcription["segments"]

    if not segments:
        return {
            "query": query,
            "results": [],
            "total_segments": 0,
            "model_used": model_size,
        }

    # Get audio hash for embedding cache
    cache = get_transcription_cache()
    audio_hash = cache.hash_audio_file(audio_path)

    # Get or compute segment embeddings
    segment_embeddings = _get_or_compute_embeddings(segments, audio_hash)

    # Encode query
    model = _get_embedding_model_cache().get()
    query_embedding = model.encode(query, convert_to_numpy=True, show_progress_bar=False)

    # Compute similarities
    similarities = _cosine_similarity(query_embedding.reshape(1, -1), segment_embeddings)

    # Get top_k results
    top_k = min(top_k, len(segments))
    top_indices = np.argsort(-similarities)[:top_k]

    results = []
    for idx in top_indices:
        seg = segments[idx]
        start = seg["start"]
        results.append({
            "start": start,
            "end": seg["end"],
            "text": seg["text"].strip(),
            "timestamp": f"{int(start // 60)}:{int(start % 60):02d}",
            "similarity": round(float(similarities[idx]), 4),
        })

    return {
        "query": query,
        "results": results,
        "total_segments": len(segments),
        "model_used": model_size,
        "cached": transcription.get("cached", False),
    }


def detect_chapters(
    audio_path: str,
    model_size: str = "tiny",
    sensitivity: float = 0.4,
) -> Dict[str, Any]:
    """
    Auto-detect topic chapters in audio.

    Uses rolling window cosine similarity to find topic boundaries.
    sensitivity: 0.0 = many small chapters, 1.0 = few large chapters.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Get transcription (cached)
    transcription = transcribe_audio(audio_path, model_size)
    segments = transcription["segments"]

    if len(segments) < 2:
        # Single segment = single chapter
        chapter = {
            "chapter_number": 1,
            "start": segments[0]["start"] if segments else 0,
            "end": segments[0]["end"] if segments else 0,
            "start_timestamp": "0:00",
            "end_timestamp": "0:00",
            "text": segments[0]["text"].strip() if segments else "",
            "segment_count": len(segments),
        }
        return {
            "chapters": [chapter],
            "total_chapters": 1,
            "duration": transcription["duration"],
            "model_used": model_size,
            "cached": transcription.get("cached", False),
        }

    # Get audio hash for embedding cache
    cache = get_transcription_cache()
    audio_hash = cache.hash_audio_file(audio_path)

    # Get or compute segment embeddings
    embeddings = _get_or_compute_embeddings(segments, audio_hash)

    # Compute similarity between consecutive segments
    similarities = []
    for i in range(len(embeddings) - 1):
        sim = _cosine_similarity(
            embeddings[i].reshape(1, -1),
            embeddings[i + 1].reshape(1, -1)
        )[0]
        similarities.append(float(sim))

    # Find boundaries where similarity drops below threshold
    boundaries = [0]
    for i, sim in enumerate(similarities):
        if sim < sensitivity:
            boundaries.append(i + 1)

    # Build chapters
    chapters = []
    for idx, start_seg_idx in enumerate(boundaries):
        end_seg_idx = boundaries[idx + 1] if idx + 1 < len(boundaries) else len(segments)
        chapter_segments = segments[start_seg_idx:end_seg_idx]
        chapter_text = " ".join(s["text"].strip() for s in chapter_segments)
        start = chapter_segments[0]["start"]
        end = chapter_segments[-1]["end"]
        chapters.append({
            "chapter_number": idx + 1,
            "start": start,
            "end": end,
            "start_timestamp": f"{int(start // 60)}:{int(start % 60):02d}",
            "end_timestamp": f"{int(end // 60)}:{int(end % 60):02d}",
            "text": chapter_text,
            "segment_count": len(chapter_segments),
        })

    return {
        "chapters": chapters,
        "total_chapters": len(chapters),
        "duration": transcription["duration"],
        "model_used": model_size,
        "cached": transcription.get("cached", False),
    }
