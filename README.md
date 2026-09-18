# 제주 상점 RAG 실습

제주 상점 JSONL을 정제하고 BGE-M3 임베딩, Elasticsearch RRF 검색, 선택적 LLM 답변, Streamlit 화면으로 연결하는 학습 프로젝트입니다.

**현재 상태:** 전체 데이터 전처리와 소규모 실제 임베딩 검사는 완료했습니다. ES·Kibana의 실제 검색 및 실제 LLM 답변 시연은 아직 검증하지 않았습니다. API 키는 빈 설정 예시만 제공합니다.

- [실행 안내](docs/README.md)
- [프로젝트 작업 지침](AGENTS.md)
- [Kibana 검증 요청](docs/kibana.http)

Windows / Python 3.12 기준으로 프로젝트 폴더에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r setup\requirements.txt
.\.venv\Scripts\python.exe practice\verify.py
```

자동 검사는 자체 임시 예시를 사용하므로 원본 데이터·모델 다운로드·ES·API 키 없이 실행됩니다. 실제 실습은 별도로 준비한 원본 JSONL을 `practice/prepare.py`에 전달해야 합니다. 원본 데이터, 생성 데이터·로그, 모델 캐시, 가상환경, `.env`는 저장소에 포함하지 않습니다. 기존 PC 경로가 문서에 나오면 본인의 원본 파일 위치로 바꿔 사용하세요.
