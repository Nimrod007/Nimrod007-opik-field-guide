"""Score the seed prompt on the labeled plant problems."""

import pathlib

import dotenv
from openai import OpenAI

from plant_classifier import SEED_SYSTEM, classify, label_accuracy, load_problems

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")


def main() -> None:
    client = OpenAI()
    problems = load_problems()
    scores = [label_accuracy(p["label"], classify(client, SEED_SYSTEM, p["text"])) for p in problems]
    print(f"seed prompt accuracy: {sum(scores) / len(scores):.3f} on {len(problems)} descriptions")


if __name__ == "__main__":
    main()
