"""The syllabus corpus: fictional course syllabi, rendered to PDF."""

from .content import COURSES, Course
from .render import ensure_pdfs, write_pdfs

__all__ = ["COURSES", "Course", "ensure_pdfs", "write_pdfs"]
