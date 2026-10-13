"""The library's catalog and a tiny keyword retriever (no embeddings, runs offline)."""
import json
import re
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "data" / "catalog.json"
STOPWORDS = {"a", "an", "the", "i", "me", "my", "for", "of", "to", "and", "or", "is", "it",
             "in", "on", "with", "that", "this", "any", "do", "you", "have", "something",
             "want", "like", "looking", "book", "books", "read", "can", "about", "some", "good"}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def score(query: str, book: dict) -> int:
    """Weighted keyword overlap: tags and genre count double, title/summary/author once."""
    q = {_stem(w) for w in _words(query)}
    strong = {_stem(w) for w in _words(" ".join(book["tags"] + [book["genre"]]))}
    weak = {_stem(w) for w in _words(" ".join([book["title"], book["summary"], book["author"]]))}
    return 2 * len(q & strong) + len(q & weak)


def search_catalog(query: str, limit: int = 3) -> list[dict]:
    """Return the best-matching books (score > 0), best first."""
    ranked = sorted(((score(query, b), b) for b in load_catalog()), key=lambda p: -p[0])
    return [b for s, b in ranked if s > 0][:limit]


def format_books(books: list[dict]) -> str:
    if not books:
        return "(no catalog matches)"
    return "\n".join(
        f"- {b['title']} by {b['author']} [{b['genre']}] "
        f"({'on the shelf' if b['available'] else 'checked out, can be reserved'}): {b['summary']}"
        for b in books
    )
