"""Embed the rule chunks into an in-memory vector store and search it."""

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

from .corpus import Chunk, load_chunks


def build_store(embeddings: Embeddings, chunks: list[Chunk] | None = None) -> InMemoryVectorStore:
    chunks = chunks if chunks is not None else load_chunks()
    return InMemoryVectorStore.from_texts([c.content for c in chunks], embeddings)


def retrieve(store: InMemoryVectorStore, question: str, k: int = 3) -> list[str]:
    """Return the text of the k chunks most similar to the question."""
    retriever = store.as_retriever(search_kwargs={"k": k})
    return [doc.page_content for doc in retriever.invoke(question)]
