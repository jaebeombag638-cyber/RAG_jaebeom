"""다운로드된 실제 BGE-M3로 단일·배치 출력과 순서를 확인한다. API 호출 없음."""
import json
from time import perf_counter

import numpy as np

from embedding import ROOT, embed

if __name__ == "__main__":
    texts = ["투빅커피는 제주시 연삼로 401에 있는 카페입니다.", "서귀포시의 편의점 정보입니다."]
    start = perf_counter()
    batch = np.array(embed(texts))
    single = np.array([embed([text])[0] for text in texts])
    # 별도로 계산한 각 문장과 배치의 같은 순서 결과가 같은지 확인한다.
    assert np.allclose(batch, single, atol=1e-5), "배치 순서 또는 수치 일치 오류"
    result = {"model": "BAAI/bge-m3", "shape": list(batch.shape),
              "finite": bool(np.isfinite(batch).all()),
              "norms": np.linalg.norm(batch, axis=1).tolist(),
              "single_batch_match": True, "seconds": round(perf_counter() - start, 3)}
    path = ROOT / "artifacts"
    path.mkdir(exist_ok=True)
    (path / "embedding_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
