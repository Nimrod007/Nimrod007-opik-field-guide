"""Render the syllabus text to PDF files with reportlab."""

import pathlib

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .content import COURSES, Course

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle("T", parent=_styles["Title"], fontName="Helvetica-Bold", fontSize=17)
_META = ParagraphStyle("M", parent=_styles["Normal"], fontName="Helvetica-Oblique", alignment=1, spaceAfter=14)
_HEAD = ParagraphStyle("H", parent=_styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, spaceBefore=12)
_BODY = ParagraphStyle("B", parent=_styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=14, spaceAfter=6)


def _render(course: Course, folder: pathlib.Path) -> pathlib.Path:
    path = folder / course.filename
    # invariant=1 drops creation dates, so regenerating gives byte-identical files.
    doc = SimpleDocTemplate(
        str(path), pagesize=LETTER, leftMargin=inch, rightMargin=inch,
        topMargin=inch, bottomMargin=inch, title=f"{course.code} Syllabus",
        author="Halvorsen University", invariant=1,
    )
    story = [
        Paragraph(f"{course.code}: {course.title}", _TITLE),
        Paragraph(f"Halvorsen University, Fall 2026. {course.instructor}", _META),
    ]
    for heading, paragraphs in course.sections:
        # Repeat the course code in every heading so each chunk says which course it belongs to.
        story.append(Paragraph(f"{course.code}, {heading}", _HEAD))
        story += [Paragraph(p, _BODY) for p in paragraphs]
    doc.build(story)
    return path


def write_pdfs(folder: pathlib.Path) -> list[pathlib.Path]:
    """(Re)write every syllabus PDF into `folder`."""
    folder.mkdir(parents=True, exist_ok=True)
    return [_render(course, folder) for course in COURSES]


def ensure_pdfs(folder: pathlib.Path) -> list[pathlib.Path]:
    """Return the syllabus PDFs, regenerating any that are missing."""
    missing = [c for c in COURSES if not (folder / c.filename).exists()]
    if missing:
        write_pdfs(folder)
    return sorted(folder.glob("*.pdf"))
