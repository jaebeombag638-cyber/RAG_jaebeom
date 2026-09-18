# 제주 RAG 실습 작업 지침

- 작업 루트는 `C:\RAG_jaebeom`이다. 구현·설정·검증 기록은 이 안에 둔다. 기존 `C:\embedding_1`은 비교 및 선택적 모델 캐시 참조용이다.
- 공통 실습 방식은 `$practice-project-guide` 스킬을 사용한다. 목록에 없으면 `C:\Users\USER\.codex\skills\practice-project-guide\SKILL.md`를 읽는다. 프로젝트 내 원본은 `setup/skills/practice-project-guide/SKILL.md`다.
- 먼저 `docs/README.md`, `docs/Rag실습.md`의 이어하기 프롬프트와 검증 상태, 작업 대상 코드, `setup/requirements.txt`를 확인한다.
- 코드는 `practice/`, 설치 설정은 `setup/`, 문서는 `docs/`, 실행 증거는 `artifacts/`에 둔다. Python은 `.\.venv\Scripts\python.exe`로 실행한다.
- 임베딩은 현재 BGE-M3 CPU dense 1024차원이다. 변경할 때는 매핑·색인·질문 임베딩의 일치를 검증한다.
- API 키와 실제 LLM 호출은 사용자가 보류를 해제할 때까지 보류한다. `.env`의 비밀 값을 출력하거나 문서에 복사하지 않는다.
- ES·Kibana·RRF의 실제 검증 상태는 실행 증거로 갱신한다. Trial을 자동 활성화하지 않는다. 모의 검사나 화면 준비를 최종 시연 완료로 표시하지 않는다.
- 학습 문서의 기준본은 `docs/Rag실습.md`다. 코드 변경 시 문서의 코드 부록을 동기화한다. 문서를 바꾸면 사용자가 요청한 바탕화면 `Rag실습.md` 사본도 동기화하고 기존 다른 내용은 백업한다.
