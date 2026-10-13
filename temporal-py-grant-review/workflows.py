from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from grants import ActivityInput, ReviewInput, average, decide

SHORT = dict(start_to_close_timeout=timedelta(seconds=60))
# The ledger lookup is flaky: retry after 1s, up to 4 attempts.
FLAKY = RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=4)


@workflow.defn
class GrantReviewWorkflow:
    @workflow.run
    async def run(self, inp: ReviewInput) -> dict:
        # Opik's trace headers travel as plain data in the workflow input and are
        # copied onto each activity input, so worker spans join the client's trace.
        def call(extra: dict | None = None) -> ActivityInput:
            return ActivityInput(inp.application, inp.trace_headers, extra or {})

        eligibility = await workflow.execute_activity("check_eligibility_activity", call(), result_type=dict, **SHORT)
        scores = budget = None
        if eligibility["eligible"]:
            scores = await workflow.execute_activity("score_rubric_activity", call(), result_type=dict, **SHORT)
            budget = await workflow.execute_activity(
                "check_budget_activity", call(), result_type=dict, retry_policy=FLAKY, **SHORT
            )
        decision = decide(eligibility, scores, budget)
        letter = await workflow.execute_activity(
            "write_letter_activity",
            call({"decision": decision, "eligibility": eligibility, "scores": scores, "budget": budget}),
            result_type=str,
            **SHORT,
        )
        return {
            "application_id": inp.application["id"],
            "decision": decision,
            "average_score": average(scores) if scores else None,
            "scores": scores,
            "budget": budget,
            "letter": letter,
        }
