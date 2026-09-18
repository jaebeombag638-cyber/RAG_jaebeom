# 제주 상점 RAG 실습

제주 상점 JSONL을 정제하고 BGE-M3 임베딩, Elasticsearch 9.5.3 RRF 검색, LangChain 답변 연결, Streamlit 화면까지 배우는 실습입니다. ES 교육을 막 마친 학습자를 기준으로 설명합니다.

**현재 상태:** 전체 53,917개 전처리와 소규모 실제 임베딩 검사를 완료했습니다. 개편 후 모의 자동 검사 10개를 통과했습니다. 실제 ES·Kibana 색인·검색과 실제 LLM 답변은 미검증입니다. API 키는 실습 중 로컬 `.env`에 입력하도록 준비했으며 현재 호출은 보류합니다.

- [실행 안내](docs/README.md)
- [작업 지침](AGENTS.md)
- [Kibana 검증 요청](docs/kibana.http)

Windows / Python 3.12 기준으로 프로젝트 폴더에서 실행합니다. 이미 설치했다면 환경을 다시 만들 필요는 없습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r setup\requirements.txt
.\.venv\Scripts\python.exe practice\verify.py
```

자동 검사는 자체 임시 예시를 사용하므로 원본·모델 다운로드·ES·API 키가 필요 없습니다. 실제 실행 순서는 교재 본문 10번을 따릅니다. 기존 Ubuntu ES·Kibana 9.5.3을 우선 사용하고, Kibana에서 전용 인덱스를 만든 뒤 Python으로 임베딩·적재합니다. Docker는 별도 연습 환경이 필요할 때만 사용합니다.

원본·생성 데이터·실행 로그·모델 캐시·가상환경·`.env`는 저장소에 없습니다. 원본 JSONL은 별도로 준비하고 문서의 입력 경로를 실제 위치로 바꾸세요.
