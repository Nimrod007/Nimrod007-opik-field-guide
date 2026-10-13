"""Chat widget backend for the Harbor Street Public Library (fictional).

POST /chat takes {message, session_id} and returns {reply}. Each request runs one
LangChain chain: load history + search the catalog -> prompt -> model -> parser.
"""
from pathlib import Path

from dotenv import load_dotenv
import opik
from fastapi import FastAPI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_openai import ChatOpenAI
from opik.integrations.langchain import OpikTracer
from pydantic import BaseModel

from catalog import format_books, search_catalog

# Example .env first, then the repo-root .env (existing values win).
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

PROJECT_NAME = "langchain-fastapi-library-chat"
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are Marlow, the book-recommendation assistant in the chat widget of
Harbor Street Public Library. Keep replies to 2-4 short sentences.
Recommend ONLY books from the catalog excerpt below; never invent titles. Mention whether a
book is on the shelf or must be reserved. If the excerpt has nothing suitable, say so and
suggest asking a librarian at the desk. Use earlier turns of the conversation to refine picks
(do not repeat a book you already suggested unless asked).

Catalog excerpt for the latest message:
{books}"""

HISTORY: dict[str, list[BaseMessage]] = {}  # session_id -> messages (the bot's memory)


# A named tool span for retrieval: OpikTracer can drop plain retriever runs, but an
# @opik.track(type="tool") function always shows up as a tool span with the matches as output.
@opik.track(name="search-catalog", type="tool", project_name=PROJECT_NAME)
def lookup_books(message: str) -> list[dict]:
    return search_catalog(message)


def prepare_inputs(message: str, config: RunnableConfig) -> dict:
    session_id = config["configurable"]["session_id"]
    books = lookup_books(message)
    return {"history": HISTORY.setdefault(session_id, []), "message": message,
            "books": format_books(books)}


prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), MessagesPlaceholder("history"), ("human", "{message}")]
)


def build_chain():
    # String in, string out: the root run's input/output are just the visitor's text and
    # the bot's reply.
    return (
        RunnableLambda(prepare_inputs).with_config(run_name="load-history-and-search")
        | prompt
        | ChatOpenAI(model=MODEL, temperature=0.3)
        | StrOutputParser()
    ).with_config(run_name="library-chat-turn")


app = FastAPI(title="Harbor Street Library chat")
_chain = None


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str


def run_turn(message: str, session_id: str) -> str:
    global _chain
    _chain = _chain or build_chain()
    # thread_id = the widget's session id: every turn of a visitor's conversation becomes
    # one trace in the same Opik thread (Threads tab). The tracer maps the chain to spans.
    tracer = OpikTracer(project_name=PROJECT_NAME, thread_id=session_id)
    reply = _chain.invoke(
        message, config={"configurable": {"session_id": session_id}, "callbacks": [tracer]}
    )
    HISTORY[session_id] += [HumanMessage(message), AIMessage(reply)]
    return reply


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=run_turn(req.message, req.session_id))
