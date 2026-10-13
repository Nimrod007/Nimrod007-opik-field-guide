"""Embed the rule chunks into an in-memory vector store and search it."""

import opik
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

from .corpus import Chunk, load_chunks


def build_store(embeddings: Embeddings, chunks: list[Chunk] | None = None) -> InMemoryVectorStore:
    chunks = chunks if chunks is not None else load_chunks()
    return InMemoryVectorStore.from_texts([c.content for c in chunks], embeddings)


# With opik 2.2.99 the OpikTracer logged no span for the LangChain retriever run,
# leaving only the bare `retrieve` node span. Tracking this function adds an explicit tool span
# named search_rulebooks, with the question and k as input and the chunks as output.
# ignore_arguments keeps the vector store (full of embeddings) out of the span input.
@opik.track(name="search_rulebooks", type="tool", ignore_arguments=["store"])
def retrieve(store: InMemoryVectorStore, question: str, k: int = 3) -> list[str]:
    """Return the text of the k chunks most similar to the question."""
    retriever = store.as_retriever(search_kwargs={"k": k})
    return [doc.page_content for doc in retriever.invoke(question)]
