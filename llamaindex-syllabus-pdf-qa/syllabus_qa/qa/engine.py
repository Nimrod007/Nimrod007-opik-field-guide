"""Query engine, prompt and the Opik LlamaIndex callback."""

from dataclasses import dataclass

from llama_index.core import PromptTemplate, set_global_handler

from ..config import TOP_K

QA_TEMPLATE = PromptTemplate(
    "You answer students' questions about course policies using only the syllabus "
    "excerpts below. Each excerpt begins with the course it belongs to. Name the "
    "course your answer comes from, and quote numbers (percentages, days, counts) "
    "exactly. If the excerpts do not contain the answer, say so.\n"
    "---------------------\n{context_str}\n---------------------\n"
    "Question: {query_str}\nAnswer: "
)


@dataclass
class Answer:
    question: str
    text: str
    excerpts: list[str]
    files: list[str]


def enable_tracing() -> None:
    # One call installs Opik's LlamaIndex callback: every query becomes a trace with
    # retrieve (+ embedding) and synthesize (+ llm) spans in the project named by OPIK_PROJECT_NAME.
    set_global_handler("opik")


def make_engine(index):
    return index.as_query_engine(similarity_top_k=TOP_K, text_qa_template=QA_TEMPLATE)


def source_files(response) -> list[str]:
    """File names of the retrieved chunks, in rank order, without duplicates."""
    seen: list[str] = []
    for node in response.source_nodes:
        name = node.node.metadata.get("file_name", "unknown")
        if name not in seen:
            seen.append(name)
    return seen


def ask(engine, question: str) -> Answer:
    response = engine.query(question)
    return Answer(
        question=question,
        text=str(response).strip(),
        excerpts=[n.node.get_content() for n in response.source_nodes],
        files=source_files(response),
    )
