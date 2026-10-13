"""Client process: starts the worker as a child OS process, runs reviews, stops it."""

import asyncio
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import opik
from opik import opik_context
from temporalio.client import Client

import config
from grants import ReviewInput
from workflows import GrantReviewWorkflow


# This is the root of the distributed trace: one trace per application, opened in the
# client process. Its span becomes the parent of every span the worker creates.
@opik.track(name="grant-review", type="general")
async def review(client: Client, application: dict) -> dict:
    # get_distributed_trace_headers returns {opik_trace_id, opik_parent_span_id} for the
    # current span; they are sent as plain workflow input (no Temporal interceptor needed).
    headers = dict(opik_context.get_distributed_trace_headers())
    opik_context.update_current_span(metadata={"pid": os.getpid()})
    return await client.execute_workflow(
        GrantReviewWorkflow.run,
        ReviewInput(application, headers),
        id=f"grant-review-{application['id']}-{uuid.uuid4().hex[:6]}",
        task_queue=config.TASK_QUEUE,
    )


async def main() -> None:
    apps = json.loads((Path(__file__).parent / "data" / "applications.json").read_text())
    worker = subprocess.Popen([sys.executable, str(Path(__file__).parent / "worker.py")], stdout=subprocess.PIPE, text=True)
    try:
        assert worker.stdout.readline().strip() == "READY", "worker failed to start"
        print(f"worker pid {worker.pid}, client pid {os.getpid()}")
        client = await Client.connect(config.TEMPORAL_ADDRESS)
        for app in apps:
            result = await review(client, app)
            print(f"\n== {app['id']} {app['applicant']}: {result['decision'].upper()} (avg {result['average_score']})")
            print(result["letter"])
    finally:
        worker.send_signal(2)  # SIGINT: lets the worker drain and flush its Opik queue
        worker.wait(timeout=60)
        opik.flush_tracker()  # flush the client process's spans


if __name__ == "__main__":
    asyncio.run(main())
