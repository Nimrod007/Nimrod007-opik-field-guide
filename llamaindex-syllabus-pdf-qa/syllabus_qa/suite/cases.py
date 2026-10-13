"""Questions and the plain-language assertions each answer must satisfy."""

CASES = [
    {
        "question": "How much of a CS 214 project's score is lost per day it is late, and when does it stop being accepted?",
        "assertions": [
            "The answer says CS 214 projects lose 10% per day late",
            "The answer says projects are not accepted more than three days after the deadline",
        ],
    },
    {
        "question": "I am late with a BIO 150 lab report. What is the penalty?",
        "assertions": [
            "The answer states a flat 15% penalty, with submission allowed up to 72 hours late",
        ],
    },
    {
        "question": "What are the weights of the research paper and the final exam in HIST 310?",
        "assertions": [
            "The answer states the HIST 310 research paper is worth 35%",
            "The answer states the HIST 310 final exam is worth 25%",
        ],
    },
    {
        "question": "How many unexcused lab absences can I have in CS 214 before my grade drops?",
        "assertions": [
            "The answer says that after three unexcused lab absences the final grade drops by one letter grade",
        ],
    },
    {
        "question": "What happens if I miss two BIO 150 labs without an excuse?",
        "assertions": [
            "The answer says missing two or more labs without an excuse means a failing grade for the lab component",
        ],
    },
    {
        "question": "Do I need HIST 200 to take HIST 310?",
        "assertions": [
            "The answer says HIST 200 is required but can be waived with written instructor permission",
        ],
    },
    {
        "question": "Is CHEM 101 required for BIO 150?",
        "assertions": [
            "The answer says CHEM 101 is recommended but not required",
        ],
    },
    {
        "question": "How many absences are allowed in HIST 310 and what does each extra one cost?",
        "assertions": [
            "The answer says two absences are allowed without penalty",
            "The answer says each additional absence lowers participation by three points out of ten",
        ],
    },
]

# Applied to every question. The excerpts are in the task output, so the judge can check them.
GLOBAL_ASSERTIONS = [
    "Every number in the answer (percentage, day count, absence count) appears in the retrieved excerpts, so the answer invents no policy",
    "The answer draws on the course the student asked about, not on a different course's policy",
]

# Questions for the quick `ask` demo: the same wording means a different answer per course.
DEMO_QUESTIONS = [
    "What is the late work policy in CS 214?",
    "What is the late work policy in HIST 310?",
    "Is attendance mandatory in BIO 150?",
    "What is the grading breakdown for CS 214?",
]
