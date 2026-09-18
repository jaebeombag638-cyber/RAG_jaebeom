"""8단계: 질문, 답변, 근거, 실행 시간을 한 화면에 표시한다."""
import json
from datetime import datetime, timezone

import streamlit as st

from embedding import ROOT
from rag import ARTIFACTS, INSTRUCTIONS, answer

st.set_page_config(page_title="제주 상점 RAG 실습", layout="wide")
st.title("제주 상점 RAG 실습")
st.caption("업로드된 상점 목록에 근거합니다. 현재 영업 여부·매출·평점은 확인할 수 없습니다.")
preview = st.toggle("준비 화면 보기 (ES·LLM 호출 없음)", value=True)
if preview:
    st.info("연결 전 미리보기입니다. 아래 자료는 원본의 첫 3개 청크이며 검색 결과나 생성 답변이 아닙니다.")
    path = ROOT / "data/chunks.jsonl"
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for _, line in zip(range(3), stream):
                doc = json.loads(line)
                with st.expander(doc["name"]):
                    st.text(doc["text"])
                    st.caption(f"{doc['source']} · {doc['source_line']}행 · {doc['chunk_id']}")
    else:
        st.warning("prepare.py를 먼저 실행하세요.")
    st.stop()

with st.form("question"):
    question = st.text_input("질문", value="투빅커피의 주소와 업종은?", max_chars=500)
    generate = st.checkbox("LLM 답변 생성 (API 키 필요)", value=False)
    submitted = st.form_submit_button("검색 / 답변")
if submitted:
    st.session_state.pop("result", None)
    try:
        with st.spinner("검색 및 답변 처리 중..."):
            st.session_state.result = answer(question, generate)
    except Exception:
        st.error("실행하지 못했습니다. ES 연결·색인 완료·RRF 라이선스·API 키와 모델 접근 권한을 확인하세요.")
        st.caption("4단계 오류는 docs/kibana.http와 명령줄 검증으로 확인할 수 있습니다.")

if "result" in st.session_state:
    result = st.session_state.result
    st.subheader("답변")
    st.text(result["answer"])
    if result["warning"]:
        st.warning(result["warning"])
    st.caption(f"상태: {result['status']} / 검색 {result['search_seconds']}초 / 전체 {result['total_seconds']}초")
    for n, doc in enumerate(result["sources"], 1):
        with st.expander(f"[{n}] {doc['name']} — {doc['chunk_id']}"):
            st.text(doc["text"])
            st.caption(f"{doc['source']} · {doc['source_line']}행 · RRF 점수 {doc['rrf_score']}")
    with st.expander("학습용: LLM에 전달하는 질문과 근거"):
        st.text(INSTRUCTIONS)
        st.code(result["prompt"], language="json")
    quality = st.selectbox("답변과 근거를 비교한 결과", ["미검토", "근거와 일치", "수정 필요"])
    note = st.text_input("검토 메모")
    if st.button("시연 결과 저장"):
        ARTIFACTS.mkdir(exist_ok=True)
        record = {**result, "quality": quality, "note": note,
                  "recorded_at": datetime.now(timezone.utc).isoformat()}
        with (ARTIFACTS / "demo_results.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        st.success("artifacts/demo_results.jsonl에 저장했습니다.")
