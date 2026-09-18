"""2~3단계: 청크를 임베딩하고 전용 ES 인덱스에 저장한다."""
import argparse
import hashlib
import json

from elasticsearch.helpers import bulk

from embedding import DIMS, MODEL_ID, ROOT, embed
from rag import ARTIFACTS, INDEX, es_client, mapping


def source_meta(limit):
    if limit < 0:
        raise ValueError("limit은 0(전체) 또는 양수입니다.")
    path = ROOT / "data/chunks.jsonl"
    with path.open("rb") as stream:
        fingerprint = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"model": MODEL_ID, "dims": DIMS, "chunks_sha256": fingerprint, "limit": limit}


def write_mapping(limit):
    """서버 호출 없이 Kibana Dev Tools용 인덱스 생성 요청을 저장한다."""
    body = {"settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": mapping({**source_meta(limit), "ready": False})}
    ARTIFACTS.mkdir(exist_ok=True)
    target = ARTIFACTS / "kibana_create.http"
    target.write_text(f"PUT /{INDEX}\n" + json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Kibana Dev Tools에서 실행하세요: {target}")


def check_index(client, meta):
    if not client.indices.exists(index=INDEX):
        raise ValueError("먼저 --write-mapping으로 요청을 만들고 Kibana에서 인덱스를 생성하세요.")
    actual = client.indices.get_mapping(index=INDEX)[INDEX]["mappings"]
    if any(actual.get("_meta", {}).get(k) != v for k, v in meta.items()):
        raise ValueError("데이터·모델·범위가 다릅니다. 새 ES_INDEX로 생성 요청을 다시 준비하세요.")
    expected = mapping(meta)["properties"]
    fields = actual.get("properties", {})
    if actual.get("dynamic") != "strict" or any(
            fields.get(k, {}).get("type") != v["type"] for k, v in expected.items()):
        raise ValueError("Kibana에서 생성한 필드 매핑을 확인하세요.")
    vector = fields["vector"]
    if any(vector.get(k) != expected["vector"][k] for k in ["dims", "index", "similarity"]) or \
            vector.get("index_options", {}).get("type") != "int8_hnsw":
        raise ValueError("벡터 차원·검색·양자화 설정이 실습 매핑과 다릅니다.")


def ingest(limit):
    meta = source_meta(limit)
    client = es_client()
    check_index(client, meta)
    client.indices.put_mapping(index=INDEX, body={"_meta": {**meta, "ready": False}})
    count, batch = 0, []
    with (ROOT / "data/chunks.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if limit and count >= limit:
                break
            batch.append(json.loads(line))
            count += 1
            if len(batch) == 32:
                send_batch(client, batch)
                batch = []
                print(f"색인: {count}", flush=True)
    if batch:
        send_batch(client, batch)
    client.indices.refresh(index=INDEX)
    stored = client.count(index=INDEX)["count"]
    if stored != count or not count:
        raise ValueError(f"청크 수 불일치 또는 빈 데이터: 입력 {count}, 저장 {stored}")
    client.indices.put_mapping(index=INDEX, body={"_meta": {**meta, "ready": True}})
    print(f"검증 완료: {stored}개. 같은 설정으로 재실행하면 같은 ID를 덮어씁니다.")


def send_batch(client, batch):
    vectors = embed([doc["text"] for doc in batch])
    bulk(client, [{"_index": INDEX, "_id": doc["chunk_id"],
                   "_source": {**doc, "vector": vector}}
                  for doc, vector in zip(batch, vectors, strict=True)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=100, help="기본 100개, 0이면 전체")
    parser.add_argument("--write-mapping", action="store_true", help="Kibana용 인덱스 생성 요청만 작성")
    args = parser.parse_args()
    if args.write_mapping:
        write_mapping(args.limit)
    else:
        ingest(args.limit)
