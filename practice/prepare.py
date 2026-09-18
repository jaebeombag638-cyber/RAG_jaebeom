"""1~2단계: 원본 JSONL을 검증하고 상점별 청크를 저장한다. 외부 호출 없음."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["상호명", "지점명", "상권업종대분류명", "상권업종중분류명",
          "상권업종소분류명", "시군구명", "행정동명", "법정동명",
          "도로명주소", "지번주소", "층정보"]


def clean(value):
    """의미를 바꾸지 않고 앞뒤·연속 공백만 정리한다."""
    return " ".join(("" if value is None else str(value)).split())


def prepare(source):
    output = ROOT / "data"
    output.mkdir(exist_ok=True)
    stats, seen = Counter(), {}
    with source.open("rb") as raw:
        digest = hashlib.file_digest(raw, "sha256").hexdigest()
    with source.open(encoding="utf-8-sig") as src, \
            (output / "chunks.jsonl").open("w", encoding="utf-8") as dst, \
            (output / "issues.jsonl").open("w", encoding="utf-8") as issues:
        for line_no, line in enumerate(src, 1):
            stats["lines"] += 1
            try:
                if not line.strip():
                    raise ValueError("빈 줄")
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("JSON 객체가 아님")
                if any(not isinstance(v, (str, int, float, type(None))) for v in row.values()):
                    raise ValueError("예상하지 못한 중첩 필드")
                cleaned = {k: clean(v) for k, v in row.items()}
                stats["trimmed_fields"] += sum(
                    isinstance(row[k], str) and v != row[k] for k, v in cleaned.items())
                shop_id = cleaned.get("상가업소번호")
                if not shop_id or not cleaned.get("상호명"):
                    raise ValueError("업소번호 또는 상호명 누락")
                if cleaned.get("시도명") != "제주특별자치도":
                    raise ValueError("제주도 외 지역 또는 지역 누락")
                if not (cleaned.get("도로명주소") or cleaned.get("지번주소")):
                    raise ValueError("주소 누락")
                if shop_id in seen:
                    reason = "동일 중복" if seen[shop_id] == cleaned else "업소번호 충돌: 첫 행 유지"
                    raise ValueError(reason)
                text = "\n".join(f"{k}: {cleaned[k]}" for k in FIELDS if cleaned.get(k))
                if len(text) > 1500:
                    raise ValueError("예상보다 긴 상점 정보: 수동 확인 필요")
                seen[shop_id] = cleaned
                chunk = {"chunk_id": f"{shop_id}:0", "shop_id": shop_id,
                         "name": cleaned["상호명"], "text": text,
                         "source": source.name, "source_line": line_no,
                         "source_sha256": digest}
                dst.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                stats["chunks"] += 1
                stats["max_text_chars"] = max(stats["max_text_chars"], len(text))
            except (ValueError, TypeError) as exc:
                stats["excluded"] += 1
                issues.write(json.dumps({"line": line_no, "reason": str(exc)}, ensure_ascii=False) + "\n")
    report = {"source": str(source.resolve()), "sha256": digest,
              "format": "UTF-8 JSONL", **stats}
    (output / "preprocess_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    prepare(parser.parse_args().source)
