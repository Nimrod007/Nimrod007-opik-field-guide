"""Run the redaction pipeline over the fictional documents in data/documents.json."""

import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from traced_pipeline import make_client, process_document_traced

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main() -> None:
    docs = json.loads((Path(__file__).parent / "data" / "documents.json").read_text())
    client = OpenAI()
    opik_client = make_client()
    for doc in docs:
        result = process_document_traced(opik_client, client, doc)
        print(f"[{doc['id']}] {doc['title']}: recall={result['score']['recall']:.2f} "
              f"verify={'ok' if result['verify']['ok'] else 'LEAK'}")
        print("   ", result["redacted"])
    # flush() blocks until the background queue is delivered; a script that exits first
    # would lose whatever is still queued.
    opik_client.flush()


if __name__ == "__main__":
    main()
