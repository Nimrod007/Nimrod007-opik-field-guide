"""Text of three fictional syllabi at the fictional Halvorsen University.

The three courses deliberately answer the same policy questions (late work,
attendance, grading) with different numbers, so retrieval has to pick the right
course, not just a plausible one.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Course:
    code: str
    title: str
    instructor: str
    sections: tuple[tuple[str, tuple[str, ...]], ...]

    @property
    def filename(self) -> str:
        return self.code.lower().replace(" ", "") + "-syllabus.pdf"


COURSES: tuple[Course, ...] = (
    Course(
        code="CS 214",
        title="Data Structures and Algorithms",
        instructor="Prof. Imani Okoro",
        sections=(
            ("1. Prerequisites", (
                "Students must have earned a grade of C or better in CS 112 (Programming "
                "Fundamentals). MATH 140 (Discrete Mathematics) must be taken before or "
                "alongside CS 214. There is no instructor override for CS 112.",
            )),
            ("2. Grading Policy", (
                "Final grades are weighted as follows: programming projects 40%, midterm "
                "exam 20%, final exam 25%, weekly labs 10%, and participation 5%. A final "
                "weighted score of 90% or higher earns an A; 80% to 89.99% earns a B.",
            )),
            ("3. Late Work Policy", (
                "Programming projects lose 10% of their score for each day they are late, "
                "and are not accepted more than three days after the deadline. Each student "
                "has two grace tokens per semester; a token extends one project deadline by "
                "48 hours with no penalty. Labs cannot be submitted late.",
            )),
            ("4. Attendance Policy", (
                "Lecture attendance is encouraged but not graded. Lab sessions are mandatory: "
                "after three unexcused lab absences, the final course grade drops by one "
                "letter grade. Absences are excused with documentation from the Dean of "
                "Students.",
            )),
        ),
    ),
    Course(
        code="BIO 150",
        title="Introduction to Cell Biology",
        instructor="Prof. Tomas Brennik",
        sections=(
            ("1. Prerequisites", (
                "BIO 150 has no required prerequisites. CHEM 101 is recommended but not "
                "required, and students who have not taken it should plan on extra reading "
                "in weeks one through three.",
            )),
            ("2. Grading Policy", (
                "Final grades are weighted as follows: three unit exams at 20% each (60% in "
                "total), lab reports 25%, weekly quizzes 10%, and participation 5%. An A "
                "requires a final weighted score of 93% or higher; 90% to 92.99% earns an A-.",
            )),
            ("3. Late Work Policy", (
                "Lab reports may be submitted up to 72 hours after the deadline for a flat "
                "15% penalty, regardless of how late within that window. After 72 hours a lab "
                "report receives a zero. Weekly quizzes close at their deadline and cannot "
                "be made up.",
            )),
            ("4. Attendance Policy", (
                "Lecture attendance is optional. Lab attendance is required: missing two or "
                "more lab sessions without an excused absence results in a failing grade for "
                "the lab component, which is 25% of the course. Illness is excused with a "
                "note from Student Health.",
            )),
        ),
    ),
    Course(
        code="HIST 310",
        title="Modern European History Seminar",
        instructor="Prof. Wen-Li Aguirre",
        sections=(
            ("1. Prerequisites", (
                "HIST 200 (Historical Methods) is required, along with sophomore standing "
                "or higher. Students without HIST 200 may enroll with written permission "
                "from the instructor.",
            )),
            ("2. Grading Policy", (
                "Final grades are weighted as follows: the research paper 35%, two response "
                "essays at 15% each (30% in total), the final exam 25%, and seminar "
                "participation 10%. There is no curve; a final weighted score of 90% or "
                "higher earns an A.",
            )),
            ("3. Late Work Policy", (
                "Papers and essays lose 5% of their score per day late, up to a maximum "
                "of seven days, after which they receive a zero. A deadline extension can be "
                "requested at least 24 hours before the deadline; extensions requested "
                "later are not granted except in emergencies.",
            )),
            ("4. Attendance Policy", (
                "This is a discussion seminar and attendance is graded through the "
                "participation component. Two absences are allowed without penalty. Each "
                "additional absence lowers the participation score by three points out of "
                "ten. Arriving more than 15 minutes late counts as an absence.",
            )),
        ),
    ),
)
