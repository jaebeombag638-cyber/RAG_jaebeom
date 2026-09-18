"""2~3단계: 청크를 임베딩하고 전용 ES 인덱스에 저장한다."""
import argparse
import hashlib
import json

from elasticsearch.helpers import bulk

from embedding import DIMS, MODEL_ID, ROOT, embed
from rag import INDEX, es_client, mapping


def ingest(limit):
    if limit < 0:
        raise ValueError("limit은 0(전체) 또는 양수입니다.")
    path = ROOT / "data/chunks.jsonl"
    with path.open("rb") as stream:
        fingerprint = hashlib.file_digest(stream, "sha256").hexdigest()
    meta = {"model": MODEL_ID, "dims": DIMS, "chunks_sha256": fingerprint, "limit": limit}
    client = es_client()
    if client.indices.exists(index=INDEX):
        previous = client.indices.get_mapping(index=INDEX)[INDEX]["mappings"].get("_meta", {})
        if any(previous.get(k) != v for k, v in meta.items()):
            raise ValueError("데이터·모델·범위가 다릅니다. .env의 ES_INDEX를 새 이름으로 바꾸세요.")
    else:
        client.indices.create(index=INDEX, mappings=mapping({**meta, "ready": False}),
                              settings={"number_of_shards": 1, "number_of_replicas": 0})
    client.indices.put_mapping(index=INDEX, body={"_meta": {**meta, "ready": False}})
    count, batch = 0, []
    with path.open(encoding="utf-8") as stream:
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
    ingest(parser.parse_args().limit)
