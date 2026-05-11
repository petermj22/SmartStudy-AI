"""
SmartStudy Demo Data Generator — Optimized
Creates 12 realistic sessions with thumbnails for testing.
Run: python scripts/create_demo_data.py
"""

from __future__ import annotations
import sys, random, time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def make_thumbnail(focus_state: int, attention: float, idx: int) -> bytes:
    import cv2, numpy as np
    w, h = 320, 180
    img  = np.zeros((h, w, 3), dtype=np.uint8)
    colors = {0: (30,130,200), 1: (40,180,80), 2: (60,60,200)}
    bg = tuple(max(0, c - 100) for c in colors.get(focus_state, (80,80,80)))
    img[:] = bg
    bar_c = colors.get(focus_state, (128,128,128))
    cv2.rectangle(img, (0,0), (w,22), bar_c, -1)
    labels = {0:"DISTRACTED", 1:"FOCUSED", 2:"FATIGUED"}
    cv2.putText(img, f"{labels.get(focus_state,'?')} {attention:.0f}% #{idx}",
                (6,15), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255,255,255), 1)
    # Simulated face
    cx, cy = w//2 + random.randint(-15,15), h//2 + random.randint(-5,5)
    cv2.circle(img, (cx,cy), 42, bar_c, -1)
    cv2.circle(img, (cx,cy), 42, (255,255,255), 2)
    for ex in [cx-13, cx+13]:
        eh = max(2, int((0.28 + attention/800) * 18))
        cv2.ellipse(img, (ex, cy-8), (7, eh), 0, 0, 360, (20,20,20), -1)
    # Attention bar
    fill = int(attention/100*(w-20))
    cv2.rectangle(img, (10,h-14), (w-10,h-6), (40,50,60), -1)
    if fill > 0:
        cv2.rectangle(img, (10,h-14), (10+fill,h-6), bar_c, -1)
    _, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 78])
    return jpg.tobytes()


def create_session(db, subject, days_ago, duration_min, focus_pct) -> str:
    import numpy as np
    from sqlalchemy import text

    s = db.create_session(subject=subject)
    sid = s.id
    n = min(40, max(10, int(duration_min * 0.8)))

    states, attentions = [], []
    rng = np.random.default_rng(abs(hash(subject + str(days_ago))) % 2**31)

    for i in range(n):
        prog = i / n
        wave = 0.12 * np.sin(prog * np.pi * 3)
        prob = float(np.clip(focus_pct/100 + wave + rng.normal(0, 0.06), 0, 1))
        state = 1 if prob > 0.65 else 2 if prob < 0.30 else 0
        attn  = float(np.clip(prob * 100 + rng.normal(0, 4), 0, 100))
        ear   = float(np.clip(0.27 + prob * 0.06 + rng.normal(0, 0.015), 0.15, 0.40))
        fat   = float(np.clip((1 - prob) * 0.55 + prog * 0.18, 0, 1))
        thumb = make_thumbnail(state, attn, i + 1)

        db.add_frame_with_thumbnail(
            session_id=sid,
            frame_data={
                "frame_number": i+1, "focus_state": state,
                "confidence": prob, "attention_score": attn,
                "fatigue_score": fat, "ear": ear,
                "mar": float(rng.uniform(0.25, 0.35)),
                "head_pitch": float(rng.normal(2, 4)),
                "head_yaw":   float(rng.normal(0, 6)),
                "head_roll":  float(rng.normal(0, 2)),
                "gaze_x": float(rng.normal(0, 0.04)),
                "gaze_y": float(rng.normal(0, 0.03)),
                "blink_rate": float(rng.normal(15, 4)),
                "alerts": [],
            },
            thumbnail_bytes=thumb,
        )
        states.append(state)
        attentions.append(attn)

    actual_focus = states.count(1) / len(states) * 100
    avg_attn     = float(np.mean(attentions))
    start_time   = datetime.utcnow() - timedelta(
        days=days_ago,
        hours=random.randint(8, 21),
        minutes=random.randint(0, 59),
    )
    end_time = start_time + timedelta(minutes=duration_min)

    with db.get_db_session() as dbs:
        from sqlalchemy import text as t
        dbs.execute(t(f"""
            UPDATE study_sessions SET
                end_time='{end_time.isoformat()}',
                start_time='{start_time.isoformat()}',
                duration_minutes={duration_min},
                focus_percentage={actual_focus:.1f},
                avg_attention_score={avg_attn:.1f},
                distraction_count={random.randint(1,10)},
                fatigue_events={random.randint(0,3)},
                break_count={max(1,int(duration_min//28))}
            WHERE id='{sid}'
        """))

    print(f"  [OK] {subject:<20} {duration_min:>4.0f}min  {actual_focus:>4.0f}% focus")
    return sid


def main():
    print("\n" + "="*52)
    print("  SmartStudy Demo Data Generator")
    print("="*52 + "\n")

    from backend.database.manager import DatabaseManager
    db = DatabaseManager(db_path="data/smartstudy.db")

    # Auto-migration
    try:
        from sqlalchemy import inspect, text
        insp = inspect(db.engine)
        if "session_frames" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("session_frames")]
            if "thumbnail_bytes" not in cols:
                with db.engine.connect() as conn:
                    conn.execute(text(
                        "ALTER TABLE session_frames "
                        "ADD COLUMN thumbnail_bytes BLOB"
                    ))
                    conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")

    sessions = [
        ("Mathematics",      0, 45, 83),
        ("Computer Science", 0, 38, 77),
        ("Physics",          1, 52, 72),
        ("Chemistry",        1, 30, 64),
        ("Mathematics",      2, 48, 89),
        ("Biology",          2, 35, 57),
        ("Literature",       3, 42, 80),
        ("History",          3, 55, 74),
        ("Computer Science", 4, 40, 85),
        ("Physics",          5, 33, 68),
        ("Mathematics",      5, 50, 92),
        ("General",          6, 25, 61),
    ]

    print("Creating sessions...\n")
    for subj, days, dur, focus in sessions:
        create_session(db, subj, days, dur, focus)

    print("\nUpdating statistics...")
    from datetime import datetime, timedelta
    for i in range(8):
        day = datetime.utcnow() - timedelta(days=i)
        try:
            db.update_daily_statistics(date=day)
        except Exception:
            pass

    print(f"\n{'='*52}")
    print("  [OK] 12 demo sessions created!")
    print("  [>] Run: python run.py")
    print("  [>] Go to History tab to see replays")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()
