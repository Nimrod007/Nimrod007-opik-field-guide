"""Load the PDFs and build an in-memory LlamaIndex vector index."""

import pathlib

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from ..config import EMBED_MODEL, LLM_MODEL
from ..pdfs import ensure_pdfs


def configure_models() -> None:
    Settings.llm = OpenAI(model=LLM_MODEL, temperature=0.0)
    Settings.embed_model = OpenAIEmbedding(model=EMBED_MODEL)
    # Small chunks: roughly one policy section each, so a late-work question
    # retrieves the late-work paragraph of several courses, not whole pages.
    Settings.chunk_size = 256
    Settings.chunk_overlap = 32


def build_index(pdf_dir: pathlib.Path) -> VectorStoreIndex:
    files = ensure_pdfs(pdf_dir)
    # PDF parsing comes from llama-index-readers-file; each node keeps its file_name metadata.
    documents = SimpleDirectoryReader(input_files=[str(f) for f in files]).load_data()
    return VectorStoreIndex.from_documents(documents)
