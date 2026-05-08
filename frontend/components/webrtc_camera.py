"""
SmartStudy WebRTC Real-Time Camera Component
Production-grade live streaming with MediaPipe overlay.

Uses streamlit-webrtc for real video, with graceful fallback
to OpenCV-based capture if webrtc is unavailable.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

import cv2
import numpy as np
import streamlit as st

# Lazy imports for optional deps
_HAS_WEBRTC = False
try:
    from streamlit_webrtc import (
        RTCConfiguration,
        VideoProcessorBase,
        WebRtcMode,
        webrtc_streamer,
    )
    import av
    _HAS_WEBRTC = True
except ImportError:
    RTCConfiguration = None
    VideoProcessorBase = object
    WebRtcMode = None
    webrtc_streamer = None
    av = None

from frontend.ui.icons import icon


# ── RTC Config for free STUN servers ──────────────────────────
RTC_CONFIG_DICT = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
    ]
}

# ── Overlay drawing constants ─────────────────────────────────
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SMALL = cv2.FONT_HERSHEY_PLAIN

STATE_COLORS_BGR = {
    0: (52, 211, 153),   # Focused → green
    1: (36, 191, 251),   # Distracted → yellow/amber
    2: (113, 113, 248),  # Fatigued → red
    -1: (148, 163, 184), # Unknown → gray
}

STATE_LABELS = {
    0: "FOCUSED",
    1: "DISTRACTED",
    2: "FATIGUED",
    -1: "DETECTING...",
}


def draw_hud_overlay(
    frame: np.ndarray,
    state: int = -1,
    confidence: float = 0.0,
    attention: float = 0.0,
    ear: float = 0.0,
    blink_rate: float = 0.0,
    head_yaw: float = 0.0,
    fatigue: float = 0.0,
    fps: float = 0.0,
    face_detected: bool = False,
) -> np.ndarray:
    """Draw professional HUD overlay on video frame."""
    output = frame.copy()
    h, w = output.shape[:2]

    if not face_detected:
        # No-face overlay
        overlay = output.copy()
        cv2.rectangle(overlay, (0, 0), (w, 52), (15, 23, 42), -1)
        cv2.addWeighted(overlay, 0.85, output, 0.15, 0, output)
        cv2.circle(output, (18, 26), 8, (100, 100, 100), -1)
        cv2.putText(output, "NO FACE DETECTED", (34, 32), FONT, 0.60, (150, 160, 170), 1, cv2.LINE_AA)
        cv2.putText(output, "Position yourself in front of the camera",
                    (w // 2 - 180, h // 2), FONT, 0.50, (100, 120, 140), 1, cv2.LINE_AA)
        return output

    color = STATE_COLORS_BGR.get(state, (148, 163, 184))
    label = STATE_LABELS.get(state, "UNKNOWN")

    # ── 1. Status header bar ──────────────────────────────────
    overlay = output.copy()
    cv2.rectangle(overlay, (0, 0), (w, 52), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.85, output, 0.15, 0, output)

    # Status dot
    cv2.circle(output, (18, 26), 8, color, -1)
    cv2.circle(output, (18, 26), 8, (255, 255, 255), 1)
    cv2.putText(output, label, (34, 32), FONT, 0.65, color, 2, cv2.LINE_AA)

    # Confidence
    conf_text = f"{confidence * 100:.0f}% conf"
    cv2.putText(output, conf_text, (w // 2 - 40, 32), FONT, 0.50, (200, 210, 220), 1, cv2.LINE_AA)

    # FPS (top right)
    fps_text = f"{fps:.0f} fps"
    fps_x = w - len(fps_text) * 9 - 10
    cv2.putText(output, fps_text, (fps_x, 32), FONT, 0.50, (100, 150, 200), 1, cv2.LINE_AA)

    # ── 2. Attention score bar (bottom) ───────────────────────
    bar_h = 6
    bar_y = h - bar_h - 2
    bar_fill = int(attention / 100 * w)
    bar_color = (
        (52, 211, 153) if attention > 60
        else (36, 191, 251) if attention > 40
        else (113, 113, 248)
    )
    cv2.rectangle(output, (0, bar_y), (w, h), (20, 30, 50), -1)
    cv2.rectangle(output, (0, bar_y), (bar_fill, h), bar_color, -1)
    att_text = f"Attention: {attention:.0f}%"
    cv2.putText(output, att_text, (8, h - 10), FONT, 0.40, (255, 255, 255), 1, cv2.LINE_AA)

    # ── 3. Right panel — metrics ──────────────────────────────
    panel_x = w - 140
    panel_items = [
        (f"EAR  {ear:.3f}",
         (52, 211, 153) if ear > 0.25 else (113, 113, 248)),
        (f"BLINK {blink_rate:.0f}/m",
         (52, 211, 153) if blink_rate < 25 else (113, 113, 248)),
        (f"YAW  {head_yaw:+.1f}\u00b0",
         (52, 211, 153) if abs(head_yaw) < 20 else (113, 113, 248)),
        (f"FTGE  {fatigue * 100:.0f}%",
         (52, 211, 153) if fatigue < 0.4 else (113, 113, 248)),
    ]

    for i, (text, c) in enumerate(panel_items):
        y_pos = 80 + i * 28
        cv2.rectangle(output, (panel_x - 4, y_pos - 16), (w - 4, y_pos + 8), (15, 23, 42), -1)
        cv2.putText(output, text, (panel_x, y_pos), FONT, 0.42, c, 1, cv2.LINE_AA)

    # ── 4. Microsleep critical flash ──────────────────────────
    if ear < 0.18 and face_detected:
        overlay2 = output.copy()
        cv2.rectangle(overlay2, (0, 0), (w, h), (0, 0, 200), -1)
        cv2.addWeighted(overlay2, 0.25, output, 0.75, 0, output)
        cv2.putText(output, "MICROSLEEP DETECTED",
                    (w // 2 - 140, h // 2), FONT, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    return output


# ══════════════════════════════════════════════════════════════
# WebRTC Video Processor (used when streamlit-webrtc is available)
# ══════════════════════════════════════════════════════════════

class FocusVideoProcessor(VideoProcessorBase):
    """
    WebRTC video processor that runs the full ML pipeline on each frame.
    Thread-safe: results pushed to queue for main Streamlit thread.
    """

    def __init__(self) -> None:
        self._frame_count: int = 0
        self._fps: float = 30.0
        self._last_time: float = time.time()
        self._lock = threading.Lock()
        self.result_queue: queue.Queue = queue.Queue(maxsize=3)

        # Lazy-load inference engine
        self._engine = None
        self._engine_loaded = False

    def _ensure_engine(self):
        """Lazy-load the inference engine (heavy import)."""
        if not self._engine_loaded:
            try:
                from backend.core.inference_engine import InferenceEngine
                import streamlit as st
                
                # Fetch calibration from preferences if available
                calibration = None
                try:
                    from backend.database.db_manager import DatabaseManager
                    # In a thread, st.session_state might be tricky, but we can try to access db directly if needed
                    # For safety, we just fetch what we can. Usually, db is at frontend.app.py scope.
                    # Alternatively, if we get it from st.session_state (if it's accessible):
                    if 'db_manager' in st.session_state:
                        user = st.session_state.db_manager.get_user()
                        prefs = user.get_preferences() if user else {}
                        if 'baseline_ear' in prefs:
                            calibration = {
                                "baseline_ear": prefs.get("baseline_ear", 0.3),
                                "baseline_mar": prefs.get("baseline_mar", 0.1),
                                "baseline_blink_rate": prefs.get("baseline_blink_rate", 15.0)
                            }
                except Exception:
                    pass
                    
                self._engine = InferenceEngine(calibration=calibration)
                self._engine_loaded = True
            except Exception as e:
                self._engine_loaded = True  # Don't retry
                self._engine = None

    def recv(self, frame):
        """Process each incoming WebRTC frame."""
        img = frame.to_ndarray(format="bgr24")
        self._frame_count += 1

        # FPS
        now = time.time()
        dt = now - self._last_time
        if dt > 0:
            self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt)
        self._last_time = now

        # Process
        self._ensure_engine()
        result = None
        if self._engine is not None:
            try:
                result = self._engine.process_frame(img, self._frame_count)
            except Exception:
                result = None

        # Draw overlay
        if result is not None and result.face_detected:
            annotated = draw_hud_overlay(
                img,
                state=getattr(result, 'focus_state', -1),
                confidence=getattr(result, 'confidence', 0),
                attention=getattr(result, 'attention_score', 0),
                ear=getattr(result, 'ear', 0),
                blink_rate=getattr(result, 'blink_rate', 0),
                head_yaw=getattr(result, 'head_yaw', 0),
                fatigue=getattr(result, 'fatigue_score', 0),
                fps=self._fps,
                face_detected=True,
            )
        else:
            annotated = draw_hud_overlay(img, fps=self._fps, face_detected=False)

        # Try to capture thumbnail
        if result is not None and result.face_detected:
            try:
                import streamlit as st
                thumb_recorder = st.session_state.get("thumb_recorder")
                if thumb_recorder:
                    thumb_recorder.try_capture(
                        bgr_frame=img,
                        focus_state=getattr(result, 'focus_state', -1),
                        attention=getattr(result, 'attention_score', 0),
                        ear=getattr(result, 'ear', 0),
                        fatigue=getattr(result, 'fatigue_score', 0)
                    )
            except Exception:
                pass

        # Push result to queue
        if result is not None:
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.result_queue.put_nowait(result)
            except queue.Full:
                pass

        return av.VideoFrame.from_ndarray(annotated, format="bgr24")


# ══════════════════════════════════════════════════════════════
# Public API — render camera component
# ══════════════════════════════════════════════════════════════

def render_webrtc_camera(key: str = "smartstudy_camera") -> Optional[Any]:
    """
    Render the WebRTC camera stream with ML overlay.

    Falls back to a simulated camera view if streamlit-webrtc
    is not installed (e.g., missing native av/aiortc libs).

    Returns:
        Latest InferenceResult from video processor, or None
    """

    if _HAS_WEBRTC:
        return _render_webrtc_mode(key)
    else:
        return _render_fallback_mode(key)


def _render_webrtc_mode(key: str) -> Optional[Any]:
    """Render using actual WebRTC streaming."""
    rtc_config = RTCConfiguration(RTC_CONFIG_DICT)

    ctx = webrtc_streamer(
        key=key,
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_config,
        video_processor_factory=FocusVideoProcessor,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280, "min": 640},
                "height": {"ideal": 720, "min": 480},
                "frameRate": {"ideal": 30, "min": 15},
            },
            "audio": False,
        },
        async_processing=True,
    )

    # Status indicator
    if ctx.state.playing:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:8px 14px;
                    background:rgba(16,185,129,0.08);border-radius:10px;
                    border:1px solid rgba(16,185,129,0.2);margin-top:8px;">
            <div style="width:8px;height:8px;background:#10B981;border-radius:50%;
                        box-shadow:0 0 8px rgba(16,185,129,0.6);
                        animation:orb-breathe 2s ease-in-out infinite;"></div>
            <span style="font-size:12px;font-weight:700;color:#34D399;
                         letter-spacing:0.04em;">Camera Active · AI Processing Live</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:8px 14px;
                    background:rgba(139,92,246,0.05);border-radius:10px;
                    border:1px solid rgba(139,92,246,0.12);margin-top:8px;">
            {icon('camera', 16, '#8B5CF6')}
            <span style="font-size:12px;color:#94A3B8;">
                Click "START" above to begin live focus monitoring
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Get result from processor queue
    if ctx.video_processor and ctx.state.playing:
        try:
            return ctx.video_processor.result_queue.get_nowait()
        except queue.Empty:
            return None

    return None


def _render_fallback_mode(key: str) -> Optional[Any]:
    """
    Fallback mode: render a professional simulated camera HUD.
    Used when streamlit-webrtc is not available.
    The session page already has its own camera simulation,
    so this just renders the status card.
    """
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;padding:10px 14px;
                background:rgba(251,191,36,0.06);border-radius:10px;
                border:1px solid rgba(251,191,36,0.15);margin-top:8px;">
        {icon('camera', 16, '#FBBF24')}
        <span style="font-size:12px;color:#FBBF24;font-weight:600;">
            WebRTC unavailable — using session page camera simulation
        </span>
    </div>
    <div style="font-size:11px;color:#64748B;margin-top:6px;padding:0 14px;">
        Install <code>streamlit-webrtc</code> and <code>av</code> for live camera overlay.
    </div>
    """, unsafe_allow_html=True)

    return None
