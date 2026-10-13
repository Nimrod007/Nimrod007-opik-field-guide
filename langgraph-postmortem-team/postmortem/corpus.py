"""The offline evidence: three markdown files, searched by rarity-weighted keywords."""

import math
import pathlib
import re

import opik

DATA_DIR = pathlib.Path(__file__).parents[1] / "data"

# Words that appear everywhere in an incident and would otherwise dominate ranking.
STOPWORDS = frozenset(
    "the a an and or of to in for is are was were be been what how why when which who "
    "did does do with on by as at it its if from that this these those not no so any "
    "some during after before between across about into over".split()
)


def load_sections(filename: str) -> list[dict]:
    """One searchable entry per '##' section of a data file."""
    title, *sections = (DATA_DIR / filename).read_text().split("\n## ")
    return [
        {"source": filename, "heading": s.split("\n", 1)[0].strip(), "text": s.strip()}
        for s in sections
    ]


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


def rank(query: str, sections: list[dict], k: int) -> list[dict]:
    """Rank sections by how many rare query terms they contain (a tiny IDF)."""
    terms = tokens(query)

    def rarity(term: str) -> float:
        containing = sum(1 for s in sections if term in s["text"].lower())
        return math.log(len(sections) / containing) + 0.1 if containing else 0.0

    def score(section: dict) -> float:
        words = tokens(section["text"])
        return sum(rarity(t) for t in terms if t in words)

    return sorted(sections, key=score, reverse=True)[:k]


# type="tool": the lookup shows up as its own tool span under the investigator that called it,
# so you can see exactly which excerpts that agent was given before its LLM call.
@opik.track(name="search_evidence", type="tool")
def search_evidence(query: str, files: list[str], k: int = 4) -> list[dict]:
    pool = [s for f in files for s in load_sections(f)]
    return rank(query, pool, k)
