"""Loading and formatting the handbook: pure functions, no model calls."""

import pathlib

DOCS_DIR = pathlib.Path(__file__).parent / "docs"
TOP_K = 2  # sections handed to the model; small keeps CPU inference fast


def load_sections(docs_dir: pathlib.Path = DOCS_DIR) -> list[str]:
    """Split every markdown file into one chunk per '##' section.

    Each chunk is prefixed with its document title so the embedding knows
    which chapter it came from.
    """
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        title = title.lstrip("# ").strip()
        for section in sections:
            chunks.append(f"{title}\n\n## {section.strip()}")
    return chunks


def format_context(sections: list[str]) -> str:
    """Join retrieved sections into the context block of the prompt."""
    return "\n\n---\n\n".join(sections)
