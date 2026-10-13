"""Offline tests: no provider keys, no Opik. Models are replaced by LlamaIndex mocks."""

import pathlib

import pytest
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

from syllabus_qa.pdfs import COURSES, ensure_pdfs, write_pdfs
from syllabus_qa.qa import ask, make_engine, numbers_in, source_files, unsupported_numbers
from syllabus_qa.qa.engine import QA_TEMPLATE
from syllabus_qa.suite import CASES, DEMO_QUESTIONS

COMMITTED = pathlib.Path(__file__).resolve().parents[1] / "data" / "syllabi"


@pytest.fixture()
def pdf_dir(tmp_path):
    write_pdfs(tmp_path)
    return tmp_path


def test_write_pdfs_makes_one_pdf_per_course(pdf_dir):
    names = sorted(p.name for p in pdf_dir.glob("*.pdf"))
    assert names == sorted(c.filename for c in COURSES)


def test_ensure_pdfs_regenerates_only_missing(tmp_path):
    assert len(ensure_pdfs(tmp_path)) == len(COURSES)
    (tmp_path / COURSES[0].filename).unlink()
    assert len(ensure_pdfs(tmp_path)) == len(COURSES)


def test_pdfs_are_deterministic_and_match_committed_fixtures(pdf_dir):
    for course in COURSES:
        assert (pdf_dir / course.filename).read_bytes() == (COMMITTED / course.filename).read_bytes()


def test_pdf_text_is_readable_and_names_the_course(pdf_dir):
    docs = SimpleDirectoryReader(input_files=[str(pdf_dir / "cs214-syllabus.pdf")]).load_data()
    text = " ".join(d.text for d in docs)
    assert "CS 214, 3. Late Work Policy" in text and "10%" in text


def test_every_suite_case_has_assertions_and_a_known_course():
    codes = {c.code for c in COURSES}
    for case in CASES:
        assert case["assertions"]
        assert any(code in case["question"] for code in codes)
    assert len({c["question"] for c in CASES}) == len(CASES)
    assert DEMO_QUESTIONS


def test_prompt_mentions_both_slots():
    assert "{context_str}" in QA_TEMPLATE.template and "{query_str}" in QA_TEMPLATE.template


def test_ask_returns_answer_excerpts_and_files(pdf_dir):
    Settings.llm = MockLLM()
    Settings.embed_model = MockEmbedding(embed_dim=8)
    files = [str(p) for p in sorted(pdf_dir.glob("*.pdf"))]
    index = VectorStoreIndex.from_documents(SimpleDirectoryReader(input_files=files).load_data())

    answer = ask(make_engine(index), "What is the late work policy in CS 214?")

    assert answer.text and answer.excerpts
    assert answer.files and all(f.endswith("-syllabus.pdf") for f in answer.files)
    assert len(answer.files) == len(set(answer.files))


def test_numbers_in_normalises_commas_and_percent_signs():
    assert numbers_in("Lose 10% per day, up to 3 days; 2,000 calls.") == {"10", "3", "2000"}


def test_traced_guard_runs_with_tracking_disabled():
    # @opik.track(type="guardrail") wraps this function; with OPIK_TRACK_DISABLE=true
    # it is a plain call, so unit tests need no Opik server.
    excerpts = ["Projects lose 10% per day.", "Three days maximum, 48 hours of grace."]
    assert unsupported_numbers("They lose 10% per day for up to 48 hours.", excerpts) == []
    assert unsupported_numbers("They lose 15% per day.", excerpts) == ["15"]
