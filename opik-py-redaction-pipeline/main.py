"""Run the redaction pipeline over the fictional documents in data/documents.json."""

import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from pipeline import process_document

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main() -> None:
    docs = json.loads((Path(__file__).parent / "data" / "documents.json").read_text())
    client = OpenAI()
    for doc in docs:
        result = process_document(client, doc)
        print(f"[{doc['id']}] {doc['title']}: recall={result['score']['recall']:.2f} "
              f"verify={'ok' if result['verify']['ok'] else 'LEAK'}")
        print("   ", result["redacted"])


if __name__ == "__main__":
    main()
