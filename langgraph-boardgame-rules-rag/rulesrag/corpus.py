"""Load the rulebooks in rules/ and cut them into one chunk per section."""

from dataclasses import dataclass
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


@dataclass(frozen=True)
class Chunk:
    game: str
    section: str
    text: str

    @property
    def content(self) -> str:
        # The game name is part of the text so "the tide track" can be
        # told apart from another game's "tide" rules at embedding time.
        return f"{self.game} / {self.section}\n{self.text}"


def split_rulebook(markdown: str) -> list[Chunk]:
    """'# Title' names the game; each '## Heading' starts a new chunk."""
    title, *sections = markdown.split("\n## ")
    game = title.splitlines()[0].lstrip("# ").strip()
    chunks = []
    for block in sections:
        heading, _, body = block.partition("\n")
        chunks.append(Chunk(game, heading.strip(), body.strip()))
    return chunks


def load_chunks(rules_dir: Path = RULES_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(rules_dir.glob("*.md")):
        chunks.extend(split_rulebook(path.read_text()))
    return chunks
