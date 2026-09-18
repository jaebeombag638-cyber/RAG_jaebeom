"""외부 서비스 없이 입력 검증·연결 흐름·화면을 검사한다. 실제 ES/LLM 검증은 아님."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

import prepare
import rag
import embedding
import ingest
from embedding import embed

APP_PATH = rag.ROOT / "practice/app.py"


class PracticeChecks(unittest.TestCase):
    def setUp(self):
        # 각 검사는 원본 데이터 대신 임시 예시 3개를 사용한다.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "data").mkdir()
        self.docs = [{"chunk_id": f"TEST{i}:0", "name": f"테스트카페{i}",
                      "text": f"상호명: 테스트카페{i}\n업종: 카페",
                      "source": "test-fixture.jsonl", "source_line": i + 1}
                     for i in range(3)]
        (root / "data/chunks.jsonl").write_text(
            "\n".join(json.dumps(doc, ensure_ascii=False) for doc in self.docs), encoding="utf-8")
        for module in [rag, embedding, ingest]:
            patcher = patch.object(module, "ROOT", root)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_clean_preserves_zero(self):
        self.assertEqual(prepare.clean(0), "0")
        self.assertEqual(prepare.clean(None), "")
        self.assertEqual(prepare.clean("  카페  "), "카페")

    def test_preprocessing_errors_and_duplicates(self):
        row = {"상가업소번호": "A", "상호명": "  예시  상점 ",
               "시도명": "제주특별자치도", "도로명주소": "제주시"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.json"
            source.write_text("\n".join([json.dumps(row), json.dumps(row), "broken", "[]"]), encoding="utf-8")
            with patch.object(prepare, "ROOT", root):
                prepare.prepare(source)
            docs = (root / "data/chunks.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(docs), 1)
            self.assertEqual(json.loads(docs[0])["name"], "예시 상점")
            report = json.loads((root / "data/preprocess_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["excluded"], 3)

    def test_embedding_invalid_inputs(self):
        self.assertEqual(embed([]), [])
        for value in ["문자열", None]:
            with self.assertRaises(TypeError):
                embed(value)
        for value in [[" "], [42]]:
            with self.assertRaises(ValueError):
                embed(value)

    def test_no_evidence_never_calls_llm(self):
        with patch.object(rag, "retrieve", return_value=("질문", [], {})), patch.object(rag, "ChatOpenAI") as llm:
            self.assertEqual(rag.answer("질문", True)["status"], "no_evidence")
            llm.assert_not_called()

    def test_missing_key_never_calls_llm(self):
        with patch.object(rag, "retrieve", return_value=("질문", [{"text": "본문",
                "source": "sample", "source_line": 1, "chunk_id": "A:0"}], {})), \
                patch.dict(rag.os.environ, {"OPENAI_API_KEY": ""}), patch.object(rag, "ChatOpenAI") as llm:
            with self.assertRaises(ValueError):
                rag.answer("질문", True)
            llm.assert_not_called()

    def test_unfinished_index_blocks_embedding(self):
        es = MagicMock()
        es.indices.get_mapping.return_value = {rag.INDEX: {"mappings": {"_meta": {"ready": False}}}}
        with patch.object(rag, "es_client", return_value=es), patch.object(rag, "embed") as embedding:
            with self.assertRaises(ValueError):
                rag.retrieve("투빅커피")
            embedding.assert_not_called()

    def test_question_to_answer_mocked_services(self):
        doc = self.docs[0]
        es = MagicMock()
        es.indices.get_mapping.return_value = {rag.INDEX: {"mappings": {"_meta": {
            "model": rag.MODEL_ID, "dims": rag.DIMS, "ready": True}}}}
        es.search.return_value = {"hits": {"hits": [{"_source": doc, "_score": 0.03}]}}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(rag, "ARTIFACTS", Path(directory)), \
                patch.object(rag, "es_client", return_value=es), \
                patch.object(rag, "embed", return_value=[[0.1] * 1024]), \
                patch.dict(rag.os.environ, {"OPENAI_API_KEY": "unit-test-placeholder"}), \
                patch.object(rag, "ChatOpenAI") as llm:
            seen_messages = []
            def fake_model(value):
                seen_messages.extend(value.to_messages())
                return AIMessage(content="테스트카페0은 카페입니다. [1]")
            llm.return_value = RunnableLambda(fake_model)
            result = rag.answer("  테스트카페0   업종  ", True)
            self.assertEqual(result["question"], "테스트카페0 업종")
            self.assertEqual(result["status"], "generated")
            self.assertEqual(result["warning"], "")
            self.assertIn(doc["chunk_id"], result["prompt"])
            self.assertEqual(seen_messages[0].content, rag.INSTRUCTIONS)
            self.assertIn(doc["chunk_id"], seen_messages[1].content)
            body = es.search.call_args.kwargs["body"]
            self.assertEqual(body["retriever"]["rrf"]["retrievers"][1]["knn"]["k"], 50)
            self.assertTrue((Path(directory) / "kibana_search.http").exists())

    def test_kibana_mapping_without_server(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(ingest, "ARTIFACTS", Path(directory)), patch.object(ingest, "es_client") as es:
            ingest.write_mapping(100)
            request = (Path(directory) / "kibana_create.http").read_text(encoding="utf-8")
            body = json.loads(request.split("\n", 1)[1])
            self.assertEqual(body["mappings"]["properties"]["vector"]["dims"], 1024)
            self.assertFalse(body["mappings"]["_meta"]["ready"])
            es.assert_not_called()

    def test_index_preflight_blocks_wrong_mapping(self):
        meta = ingest.source_meta(100)
        es = MagicMock()
        es.indices.exists.return_value = False
        with self.assertRaises(ValueError):
            ingest.check_index(es, meta)
        es.indices.exists.return_value = True
        current = rag.mapping(meta)
        es.indices.get_mapping.return_value = {ingest.INDEX: {"mappings": current}}
        ingest.check_index(es, meta)
        current["properties"]["vector"]["dims"] = 3
        with self.assertRaises(ValueError):
            ingest.check_index(es, meta)

    def test_screen_preview_and_answer(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.expander), 3)
        app.toggle[0].set_value(False).run()
        with (rag.ROOT / "data/chunks.jsonl").open(encoding="utf-8") as stream:
            doc = {**json.loads(next(stream)), "rrf_score": 0.03}
        result = {"answer": "카페입니다. [1]", "warning": "", "status": "generated",
                  "search_seconds": 0.1, "total_seconds": 0.2, "prompt": "{}", "sources": [doc]}
        with patch.object(rag, "answer", return_value=result):
            app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertIn("카페입니다. [1]", [element.value for element in app.text])
        self.assertIn(doc["chunk_id"], app.expander[0].label)
        with tempfile.TemporaryDirectory() as directory, patch.object(rag, "ARTIFACTS", Path(directory)):
            app.button[1].click().run()
            saved = json.loads((Path(directory) / "demo_results.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(saved["sources"][0]["chunk_id"], doc["chunk_id"])
            self.assertEqual(saved["quality"], "미검토")


if __name__ == "__main__":
    unittest.main(verbosity=2)
