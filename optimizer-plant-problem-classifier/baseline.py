"""Score the seed prompt once, with traces (no optimization) on the labeled plant problems."""

import pathlib

import dotenv
import opik

from plant_classifier import SEED_SYSTEM, classify, label_accuracy, load_problems, make_client

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")


def main() -> None:
    client = make_client()
    problems = load_problems()
    scores = [label_accuracy(p["label"], classify(client, SEED_SYSTEM, p["text"])) for p in problems]
    print(f"seed prompt accuracy: {sum(scores) / len(scores):.3f} on {len(problems)} descriptions")
    # Traces are sent from a background thread; flush so none are lost on exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
