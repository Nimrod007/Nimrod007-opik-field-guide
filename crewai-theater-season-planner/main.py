"""Season planner for the Alderbank Players, a fictional community theater.

Three CrewAI agents work in sequence from offline data files: a programming
dramaturg picks plays, a budget manager checks them against the money, and a
rehearsal scheduler fits the survivors into the venue calendar.
"""

from pathlib import Path

from dotenv import load_dotenv

# Load the repo-root .env (if present) before crewai reads the keys.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from crewai import Agent, Crew, Process, Task

from season_data import load_inputs

MODEL = "gpt-4o-mini"

dramaturg = Agent(
    role="Programming Dramaturg",
    goal="Shortlist a balanced five-play season from the candidate list.",
    backstory="A literary manager who balances genres, cast sizes and audience appetite.",
    llm=MODEL,
)
budget_manager = Agent(
    role="Budget Manager",
    goal="Keep the season inside the spendable budget and flag what must be cut.",
    backstory="The theater's treasurer: precise with sums, never invents a figure.",
    llm=MODEL,
)
scheduler = Agent(
    role="Rehearsal Scheduler",
    goal="Assign each approved play to a venue slot with a rehearsal start date.",
    backstory="A stage manager who counts backwards from opening night.",
    llm=MODEL,
)

shortlist_task = Task(
    name="Shortlist the plays",
    description=(
        "Choose five plays for the coming season from the candidates below, "
        "balancing genres. Use only these facts.\n\nCANDIDATES:\n{plays}"
    ),
    expected_output="A list of five plays, one line of reasoning each.",
    agent=dramaturg,
)
budget_task = Task(
    name="Check the budget",
    description=(
        "Add up the production costs of the shortlisted plays and compare them "
        "with the spendable budget. If over, name the play to swap or cut.\n\n"
        "BUDGET:\n{budget}\n\nCANDIDATES:\n{plays}"
    ),
    expected_output="The total cost, the spendable budget, and a verdict with any cut.",
    agent=budget_manager,
    context=[shortlist_task],
)
schedule_task = Task(
    name="Schedule the season",
    description=(
        "Place each approved play in one venue slot and give a rehearsal start "
        "date, respecting rehearsal weeks and slot constraints.\n\n"
        "CALENDAR:\n{calendar}\n\nCANDIDATES:\n{plays}"
    ),
    expected_output="A season calendar: play, slot, rehearsal start, opening date.",
    agent=scheduler,
    context=[shortlist_task, budget_task],
)

crew = Crew(
    agents=[dramaturg, budget_manager, scheduler],
    tasks=[shortlist_task, budget_task, schedule_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    result = crew.kickoff(inputs=load_inputs())
    print("\n=== SEASON PLAN ===\n")
    print(result)
