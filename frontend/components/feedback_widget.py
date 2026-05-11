"""
SmartStudy Focus Rating Widget
Non-intrusive user self-rating for online learning.
Appears every 15 minutes during active sessions.
"""

from __future__ import annotations

import time

import streamlit as st

from frontend.ui.icons import icon


def render_feedback_widget(
    online_learner,
    session_active: bool,
    elapsed_minutes: float,
) -> None:
    """Render the self-rating feedback widget. Only shows when learner requests feedback."""
    if not session_active:
        return

    if not online_learner.should_request_feedback():
        return

    tip = online_learner.get_improvement_tip()

    # Show "thanks" for 30 seconds after submission
    if "feedback_submitted" in st.session_state:
        if time.time() - st.session_state["feedback_submitted"] < 30:
            st.markdown(
                f"""
                <div style="background:rgba(16,185,129,0.08);
                            border:1px solid rgba(16,185,129,0.25);
                            border-radius:12px;padding:12px 16px;
                            display:flex;align-items:center;gap:10px;font-size:13px;">
                    {icon('check-circle', 18, '#10B981')}
                    <span style="color:#34D399;font-weight:600;">
                        Thanks! AI model updated with your feedback.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
        else:
            del st.session_state["feedback_submitted"]

    online_learner.mark_feedback_shown()

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,
                    rgba(139,92,246,0.06), rgba(34,211,238,0.06));
                    border:1px solid rgba(139,92,246,0.15);border-radius:14px;
                    padding:16px 20px;margin:12px 0;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                {icon('brain', 18, '#8B5CF6')}
                <span style="font-size:14px;font-weight:700;color:#F8FAFC;">
                    How focused are you right now?
                </span>
            </div>
            <div style="font-size:12px;color:#64748B;margin-bottom:12px;">
                {tip} — Your rating helps personalize AI detection.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rating_labels = {
        1: "Very distracted",
        2: "Somewhat off",
        3: "Moderate",
        4: "Well focused",
        5: "In the zone!",
    }

    cols = st.columns(5)
    for i, col in enumerate(cols):
        rating = i + 1
        with col:
            if st.button(
                rating_labels[rating],
                key=f"rating_{rating}_{elapsed_minutes:.0f}",
                use_container_width=True,
            ):
                online_learner.process_user_feedback(rating)
                st.session_state["feedback_submitted"] = time.time()
                st.rerun()
