"""
SmartStudy Session Replay System
Records frame thumbnails and generates session summaries.
100% offline — all processing local.
"""

from __future__ import annotations

import io
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger
from PIL import Image


@dataclass
class ReplayFrame:
    """A single stored frame snapshot."""
    timestamp: float
    frame_number: int
    focus_state: int
    attention_score: float
    ear: float
    fatigue_score: float
    thumbnail_bytes: bytes
    thumbnail_size: Tuple[int, int] = (160, 90)


class SessionThumbnailRecorder:
    """
    Records frame thumbnails at configurable intervals.
    Storage: 160x90 JPEG @ 70% ≈ 4KB/frame.
    60-min session @ 1 frame/10s = 360 frames ≈ 1.4MB.
    """

    def __init__(
        self,
        capture_interval_seconds: float = 10.0,
        thumbnail_width: int = 160,
        thumbnail_height: int = 90,
        jpeg_quality: int = 70,
    ) -> None:
        self.interval = capture_interval_seconds
        self.thumb_w = thumbnail_width
        self.thumb_h = thumbnail_height
        self.quality = jpeg_quality
        self._frames: List[ReplayFrame] = []
        self._last_capture = 0.0
        self._frame_count = 0

    def try_capture(
        self, bgr_frame: np.ndarray, focus_state: int,
        attention: float, ear: float, fatigue: float,
    ) -> bool:
        """Capture thumbnail if interval has elapsed. Returns True if captured."""
        now = time.time()
        if now - self._last_capture < self.interval:
            return False

        self._frame_count += 1
        self._last_capture = now

        thumb = cv2.resize(bgr_frame, (self.thumb_w, self.thumb_h))

        # Annotate with state indicator bar
        state_colors = {0: (0, 165, 255), 1: (0, 200, 100), 2: (0, 0, 220)}
        color = state_colors.get(focus_state, (100, 100, 100))
        cv2.rectangle(thumb, (0, 0), (self.thumb_w, 12), color, -1)

        state_labels = {0: "DIST", 1: "FOCUS", 2: "FTGE"}
        cv2.putText(
            thumb, f"{state_labels.get(focus_state, '?')} {attention:.0f}%",
            (3, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (255, 255, 255), 1,
        )

        _, jpeg = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        jpeg_bytes = jpeg.tobytes()

        self._frames.append(ReplayFrame(
            timestamp=now, frame_number=self._frame_count,
            focus_state=focus_state, attention_score=attention,
            ear=ear, fatigue_score=fatigue, thumbnail_bytes=jpeg_bytes,
        ))
        return True

    def get_frames(self) -> List[ReplayFrame]:
        return self._frames.copy()

    def clear(self) -> None:
        self._frames.clear()
        self._last_capture = 0.0
        self._frame_count = 0


class SessionReplayEngine:
    """Session replay viewer and export engine."""

    def __init__(self, db_manager) -> None:
        self.db = db_manager

    def get_session_frames(self, session_id: str) -> List[ReplayFrame]:
        """Load stored thumbnails for a session."""
        raw = self.db.get_session_frames(session_id)
        frames = []
        for r in raw:
            thumb_bytes = r.get("thumbnail_bytes")
            if thumb_bytes:
                frames.append(ReplayFrame(
                    timestamp=r.get("timestamp", 0),
                    frame_number=r.get("frame_number", 0),
                    focus_state=r.get("focus_state", -1),
                    attention_score=r.get("attention_score", 0),
                    ear=r.get("ear", 0),
                    fatigue_score=r.get("fatigue_score", 0),
                    thumbnail_bytes=thumb_bytes,
                ))
        return frames

    def decode_thumbnail(self, frame: ReplayFrame) -> np.ndarray:
        """Decode JPEG bytes to numpy RGB array."""
        nparr = np.frombuffer(frame.thumbnail_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def generate_summary_video(
        self, frames: List[ReplayFrame], output_path: str,
        fps: float = 4.0, target_size: Tuple[int, int] = (640, 360),
    ) -> Path:
        """Generate MP4 summary video from thumbnails. Pure OpenCV, offline."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output), fourcc, fps, target_size)

        state_colors = {0: (0, 165, 255), 1: (52, 211, 153), 2: (68, 68, 239)}
        state_labels = {0: "DISTRACTED", 1: "FOCUSED", 2: "FATIGUED"}

        for frame in frames:
            img_rgb = self.decode_thumbnail(frame)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_resized = cv2.resize(img_bgr, target_size)

            color = state_colors.get(frame.focus_state, (128, 128, 128))

            # Bottom info bar
            cv2.rectangle(img_resized,
                (0, target_size[1] - 35), (target_size[0], target_size[1]),
                (15, 23, 42), -1)
            cv2.putText(img_resized,
                f"{state_labels.get(frame.focus_state, 'UNKNOWN')} | "
                f"Attn: {frame.attention_score:.0f}% | EAR: {frame.ear:.3f}",
                (8, target_size[1] - 12), cv2.FONT_HERSHEY_SIMPLEX,
                0.45, color, 1, cv2.LINE_AA)

            writer.write(img_resized)

        writer.release()
        logger.info(f"Summary video saved: {output}")
        return output

    def generate_pdf_report(
        self, session_id: str, frames: List[ReplayFrame],
        metrics: Dict, output_path: str,
    ) -> Optional[Path]:
        """Generate PDF session report. Requires reportlab. 100% offline."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                HRFlowable, Image as RLImage, Paragraph,
                SimpleDocTemplate, Spacer, Table, TableStyle,
            )
        except ImportError:
            logger.warning("reportlab not installed — PDF export unavailable")
            return None

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(output), pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("SmartStudy Session Report", styles["Title"]))
        story.append(Spacer(1, 0.5 * cm))

        from datetime import datetime
        meta_data = [
            ["Session ID", session_id[:8] + "..."],
            ["Date", datetime.now().strftime("%B %d, %Y - %H:%M")],
            ["Duration", f"{metrics.get('duration_minutes', 0):.0f} minutes"],
            ["Subject", metrics.get("subject", "General")],
        ]
        meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#8B5CF6")),
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 1 * cm))

        story.append(Paragraph("Performance Metrics", styles["Heading2"]))
        focus_pct = metrics.get("focus_percentage", 0)
        perf_data = [
            ["Metric", "Score", "Evaluation"],
            ["Overall Focus", f"{focus_pct:.0f}%",
             "Excellent" if focus_pct >= 85 else "Good" if focus_pct >= 60 else "Requires Improvement"],
            ["Avg. Attention", f"{metrics.get('avg_attention_score', 0):.0f}/100", ""],
            ["Rest Breaks", str(metrics.get("break_count", 0)), ""],
            ["Distraction Events", str(metrics.get("distraction_count", 0)), ""],
            ["Fatigue Events", str(metrics.get("fatigue_events", 0)), ""],
        ]
        perf_table = Table(perf_data, colWidths=[6.5*cm, 4*cm, 5.5*cm])
        perf_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8B5CF6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 12),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1,0), (1,-1), "CENTER"),
        ]))
        story.append(perf_table)

        # Add thumbnail grid (first 6 frames)
        if frames:
            story.append(Spacer(1, 1 * cm))
            story.append(Paragraph("Session Timeline Snapshots", styles["Heading2"]))
            story.append(Spacer(1, 0.5 * cm))

            thumb_row: list = []
            for i, frame in enumerate(frames[:6]):
                try:
                    pil_img = Image.fromarray(self.decode_thumbnail(frame))
                    img_buf = io.BytesIO()
                    pil_img.save(img_buf, format="JPEG", quality=85)
                except Exception as e:
                    logger.error(f"Failed to decode thumbnail for PDF: {e}")
                    continue
                img_buf.seek(0)
                rl_img = RLImage(img_buf, width=5*cm, height=2.8*cm)
                thumb_row.append(rl_img)

                if len(thumb_row) == 3 or i == len(frames[:6]) - 1:
                    while len(thumb_row) < 3:
                        thumb_row.append("")
                    story.append(Table([thumb_row], colWidths=[5.5*cm] * 3))
                    story.append(Spacer(1, 0.2 * cm))
                    thumb_row = []

        doc.build(story)
        logger.info(f"PDF report saved: {output}")
        return output
