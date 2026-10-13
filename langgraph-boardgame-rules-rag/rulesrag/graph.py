"""The two-node LangGraph: retrieve rules, then answer from them."""

from typing import Callable

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

SYSTEM_PROMPT = (
    "You are a rules referee for three board games. Answer the player's "
    "question using only the rulebook excerpts below. Name the game you are "
    "talking about. If the excerpts do not settle the question, say the "
    "rulebooks do not cover it. Be brief.\n\n{context}"
)


class State(TypedDict, total=False):
    question: str
    context: list[str]
    answer: str


def format_context(chunks: list[str]) -> str:
    return "\n\n---\n\n".join(chunks)


def build_graph(search: Callable[[str], list[str]], llm: BaseChatModel):
    """`search` maps a question to rule chunks; the graph never sees the store."""

    def retrieve_node(state: State) -> dict:
        return {"context": search(state["question"])}

    def generate_node(state: State) -> dict:
        reply = llm.invoke([
            ("system", SYSTEM_PROMPT.format(context=format_context(state["context"]))),
            ("user", state["question"]),
        ])
        return {"answer": reply.content}

    graph = StateGraph(State)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
