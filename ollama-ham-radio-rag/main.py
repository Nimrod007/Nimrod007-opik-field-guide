"""Fully local RAG over the Larkspur Valley ham-radio handbook.

nomic-embed-text embeds the handbook, llama3.2:1b answers from the retrieved
sections, and both run in Ollama on this machine. No cloud model, no provider key.
"""

import os
import pathlib

PROJECT_NAME = "ollama-ham-radio-rag"
# Opik reads the target project from this variable; set it before opik is imported.
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)

import dotenv

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import ChatOllama, OllamaEmbeddings
from opik.integrations.langchain import OpikTracer

from handbook import TOP_K, format_context, load_sections

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = "llama3.2:1b"
EMBED_MODEL = "nomic-embed-text"

QUESTIONS = [
    "Which frequency and tone do I use to reach the LV-2 repeater?",
    "What SWR is too high to keep transmitting?",
    "How should I check in to the emergency net?",
    "Can I use Q-codes during an emergency net activation?",
]

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the Larkspur Valley Amateur Radio Club handbook assistant. Answer "
     "using only the handbook excerpts below. If they do not cover the question, "
     "say so. Answer in at most three sentences.\n\n{context}"),
    ("human", "{question}"),
])


def build_retriever():
    store = InMemoryVectorStore.from_texts(
        load_sections(), OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_URL)
    )
    return store.as_retriever(search_kwargs={"k": TOP_K})


def build_chain(retriever):
    def search_handbook(question: str) -> str:
        return format_context([d.page_content for d in retriever.invoke(question)])

    llm = ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_URL, temperature=0, num_predict=200)
    chain = (
        {"context": search_handbook, "question": RunnablePassthrough()}
        | PROMPT | llm | StrOutputParser()
    )
    return chain.with_config({"run_name": "ask_the_handbook"})


def main() -> None:
    chain = build_chain(build_retriever())
    # OpikTracer is a LangChain callback: each chain.invoke becomes one trace
    # named after the run (ask_the_handbook), with prompt and ChatOllama as child spans.
    tracer = OpikTracer(project_name=PROJECT_NAME, tags=["ollama", "local-rag"])
    for question in QUESTIONS:
        answer = chain.invoke(question, config={"callbacks": [tracer]})
        print(f"Q: {question}\nA: {answer}\n")
    # Traces are sent from a background thread; flush so none are lost at exit.
    tracer.flush()


if __name__ == "__main__":
    main()
