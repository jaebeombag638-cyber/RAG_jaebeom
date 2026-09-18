"""BGE-M3 CPU 모델을 재사용하여 문서와 질문을 임베딩한다."""
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)
MODEL_ID = "BAAI/bge-m3"
DIMS = 1024


@lru_cache(maxsize=1)
def load_model():
    # 준비 화면에서는 무거운 모델 라이브러리까지 읽을 필요가 없다.
    from sentence_transformers import SentenceTransformer

    cache = os.getenv("MODEL_CACHE") or str(ROOT / ".cache/huggingface/hub")
    return SentenceTransformer(os.getenv("MODEL_PATH") or MODEL_ID,
                               device="cpu", cache_folder=cache)


def embed(texts):
    if not isinstance(texts, list):
        raise TypeError("문자열 리스트가 필요합니다.")
    if any(not isinstance(t, str) or not t.strip() for t in texts):
        raise ValueError("빈 문자열은 임베딩할 수 없습니다.")
    if not texts:
        return []
    vectors = load_model().encode(texts, batch_size=8, normalize_embeddings=True,
                                  convert_to_numpy=True, show_progress_bar=False)
    if vectors.shape != (len(texts), DIMS) or not np.isfinite(vectors).all():
        raise ValueError("벡터 개수·차원·값을 확인하세요.")
    if not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-4):
        raise ValueError("벡터 정규화 확인이 필요합니다.")
    return vectors.tolist()
