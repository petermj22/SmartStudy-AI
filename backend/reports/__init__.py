"""SmartStudy Reports Package."""
from backend.reports.report_generator import (
    generate_html_report,
    generate_pdf_report,
    generate_gif_from_frames,
)
__all__ = [
    "generate_html_report",
    "generate_pdf_report",
    "generate_gif_from_frames",
]
