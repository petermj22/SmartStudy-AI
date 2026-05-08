-- ============================================================
-- SmartStudy Database Schema — Version 1.0.0
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences     TEXT DEFAULT '{}',
    calibration     TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP,
    duration_minutes    REAL,
    subject             TEXT DEFAULT 'General',
    tags                TEXT DEFAULT '[]',
    notes               TEXT DEFAULT '',
    focus_percentage    REAL DEFAULT 0.0,
    avg_attention_score REAL DEFAULT 0.0,
    distraction_count   INTEGER DEFAULT 0,
    fatigue_events      INTEGER DEFAULT 0,
    break_count         INTEGER DEFAULT 0,
    focused_seconds     REAL DEFAULT 0.0,
    distracted_seconds  REAL DEFAULT 0.0,
    fatigued_seconds    REAL DEFAULT 0.0,
    avg_ear             REAL,
    avg_blink_rate      REAL,
    peak_focus_hour     INTEGER,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_frames (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES study_sessions(id) ON DELETE CASCADE,
    timestamp       TIMESTAMP NOT NULL,
    frame_number    INTEGER,
    focus_state     INTEGER NOT NULL,
    confidence      REAL DEFAULT 0.0,
    attention_score REAL DEFAULT 0.0,
    fatigue_score   REAL DEFAULT 0.0,
    ear             REAL DEFAULT 0.0,
    mar             REAL DEFAULT 0.0,
    head_pitch      REAL DEFAULT 0.0,
    head_yaw        REAL DEFAULT 0.0,
    head_roll       REAL DEFAULT 0.0,
    gaze_x          REAL DEFAULT 0.0,
    gaze_y          REAL DEFAULT 0.0,
    blink_rate      REAL DEFAULT 0.0,
    alerts          TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS break_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL REFERENCES study_sessions(id) ON DELETE CASCADE,
    break_start         TIMESTAMP NOT NULL,
    break_end           TIMESTAMP,
    duration_minutes    REAL,
    break_type          TEXT DEFAULT 'manual',
    was_recommended     INTEGER DEFAULT 0,
    trigger_type        TEXT,
    user_accepted       INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS daily_statistics (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date                    DATE NOT NULL,
    total_study_minutes     REAL DEFAULT 0.0,
    session_count           INTEGER DEFAULT 0,
    avg_focus_percentage    REAL DEFAULT 0.0,
    total_breaks            INTEGER DEFAULT 0,
    subject_distribution    TEXT DEFAULT '{}',
    hourly_distribution     TEXT DEFAULT '{}',
    best_session_id         TEXT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON study_sessions(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_sessions_subject ON study_sessions(user_id, subject);
CREATE INDEX IF NOT EXISTS idx_frames_session ON session_frames(session_id);
CREATE INDEX IF NOT EXISTS idx_frames_timestamp ON session_frames(timestamp);
CREATE INDEX IF NOT EXISTS idx_breaks_session ON break_records(session_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_user_date ON daily_statistics(user_id, date);

INSERT OR IGNORE INTO users (id, name, preferences, calibration)
VALUES (
    'default_user',
    'Student',
    '{"break_interval": 25, "break_duration": 5, "sensitivity": "medium", "notifications": true, "sound": true, "theme": "light"}',
    '{}'
);
