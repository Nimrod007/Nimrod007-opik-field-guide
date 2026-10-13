"""A smolagents CodeAgent that answers questions about a brewery batch log."""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent / ".env")

from smolagents import CodeAgent, OpenAIServerModel  # noqa: E402

from brewery import BRIEFING, QUESTIONS  # noqa: E402
from tracing import PROJECT_NAME, flush_tracing, setup_tracing  # noqa: E402


def build_agent() -> CodeAgent:
    # The agent answers by writing Python; pandas is the only extra import it may use.
    return CodeAgent(
        tools=[],
        model=OpenAIServerModel(model_id="gpt-4o-mini"),
        additional_authorized_imports=["pandas"],
        max_steps=6,
    )


def ask(agent: CodeAgent, question: str) -> str:
    return str(agent.run(BRIEFING + "\nQuestion: " + question))


def main() -> None:
    provider = setup_tracing()  # must run before the agent is built so it is instrumented
    agent = build_agent()
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n=== Question {i}: {question}")
        print(f"Answer {i}: {ask(agent, question)}")
    flush_tracing(provider)
    print(f"\nDone. Open the '{PROJECT_NAME}' project in Opik.")


if __name__ == "__main__":
    main()
