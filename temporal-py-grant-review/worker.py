"""Worker process: runs workflows and activities and exports its own Opik spans."""

import asyncio
import signal

import opik
from temporalio.client import Client
from temporalio.worker import Worker

import config
from activities import (
    check_budget_activity,
    check_eligibility_activity,
    score_rubric_activity,
    write_letter_activity,
)
from workflows import GrantReviewWorkflow


async def main() -> None:
    client = await Client.connect(config.TEMPORAL_ADDRESS)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    async with Worker(
        client,
        task_queue=config.TASK_QUEUE,
        workflows=[GrantReviewWorkflow],
        activities=[check_eligibility_activity, score_rubric_activity, check_budget_activity, write_letter_activity],
    ):
        print("READY", flush=True)
        await stop.wait()
    # The worker is a separate OS process with its own Opik batching queue; without this
    # flush, spans from the last activities can be lost when the process exits.
    opik.flush_tracker()


if __name__ == "__main__":
    asyncio.run(main())
