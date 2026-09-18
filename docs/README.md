# 실습 시작 안내

[Rag실습.md](Rag실습.md)는 튜터 규칙·커리큘럼·개념·실행법·검증 상태·전체 코드를 모은 기준 교재입니다. Work에 첨부하고 `튜터 시작 규칙대로 0차시를 시작해줘.`라고 입력하세요.

설치는 [루트 README](../README.md), 전체 실행은 **교재 본문 10번**, 실제 검증 기록은 **본문 14번**에서 확인합니다. 처음부터 모든 코드를 읽을 필요는 없습니다.

설치와 전처리를 마쳤다면 준비 화면을 실행할 수 있습니다.

```powershell
cd C:\RAG_jaebeom
.\.venv\Scripts\python.exe -m streamlit run practice\app.py --server.address 127.0.0.1
```

준비 화면은 실제 검색 결과가 아닙니다. ES·Kibana 9.5.3 연결 → Kibana 인덱스 생성 → Python 색인 → RRF 검증 후, 실습 중 `.env`에 API 키를 입력하고 생성 체크를 켭니다. 키 입력 후 앱을 재시작합니다. 현재 실제 검색·LLM 시연은 미검증이며 API 호출은 보류 중입니다.
