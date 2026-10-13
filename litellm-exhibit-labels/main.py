"""Write the same exhibit labels with two models, routed through LiteLLM."""

import logging
import os
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Pick up keys from a local .env, or the repo-root one two levels up.
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# This machine may point Anthropic traffic at a dev proxy; LiteLLM needs the real API.
os.environ.pop("ANTHROPIC_BASE_URL", None)
# The Opik project every trace lands in; must be set before the callback is created.
os.environ["OPIK_PROJECT_NAME"] = "litellm-exhibit-labels"

import litellm  # noqa: E402
import opik  # noqa: E402
from litellm.integrations.opik.opik import OpikLogger  # noqa: E402

from labels import MODELS, Call, build_prompt, format_table, load_artifacts, summarize, word_count  # noqa: E402


# OpikLogger is LiteLLM's built-in Opik callback: every completion() becomes a
# trace with one llm span carrying model, provider, token usage and estimated cost.
# Built outside an event loop, OpikLogger logs a harmless "no running event loop"
# error and falls back to sending each call synchronously; mute just that noise.
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
litellm.callbacks = [OpikLogger()]
logging.getLogger("LiteLLM").setLevel(logging.WARNING)


def write_label(short_name: str, artifact: dict) -> Call:
    start = time.perf_counter()
    response = litellm.completion(
        model=MODELS[short_name],
        messages=[{"role": "user", "content": build_prompt(artifact)}],
        # Tags and metadata ride along onto the Opik trace, so the table can be
        # filtered by model or artifact instead of parsing prompts.
        metadata={"opik": {"tags": [short_name, artifact["id"]],
                           "metadata": {"artifact": artifact["name"]}}},
    )
    latency = time.perf_counter() - start
    text = response.choices[0].message.content or ""
    call = Call(
        model=short_name,
        artifact_id=artifact["id"],
        latency_s=latency,
        cost_usd=response._hidden_params.get("response_cost") or 0.0,
        tokens=response.usage.total_tokens,
        words=word_count(text),
    )
    print(f"  {artifact['id']} [{latency:5.2f}s ${call.cost_usd:.6f} {call.words:3d}w] "
          f"{text.splitlines()[0][:60]}")
    return call


def main() -> None:
    artifacts = load_artifacts()
    calls: list[Call] = []
    for short_name in MODELS:
        print(f"\n=== {short_name} ===")
        calls += [write_label(short_name, a) for a in artifacts]
    print("\n" + format_table(summarize(calls)))
    # Callback sends are batched in the background; flush so nothing is lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
