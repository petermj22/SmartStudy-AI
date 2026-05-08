# SmartStudy — System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SMARTSTUDY ARCHITECTURE                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  PRESENTATION LAYER                          │  │
│  │  Streamlit UI (Dashboard, Session, Analytics, Insights,     │  │
│  │  Settings) + Components (FocusIndicator, Timer, Charts)     │  │
│  └──────────────────────────────┬───────────────────────────────┘  │
│                                 │ Session State                     │
│  ┌──────────────────────────────┼───────────────────────────────┐  │
│  │                APPLICATION LAYER                              │  │
│  │  SessionManager (lifecycle) │ Analytics Engine (aggregation) │  │
│  │  InsightEngine (AI)         │ StudyScheduler (optimization)  │  │
│  └──────────────────────────────┼───────────────────────────────┘  │
│                                 │                                   │
│  ┌──────────────────────────────┼───────────────────────────────┐  │
│  │               CORE PROCESSING LAYER                           │  │
│  │  CameraManager → InferenceEngine → FaceDetector              │  │
│  │  FeatureExtractor → BlinkDetector → GazeTracker              │  │
│  │  FeatureBuffer → EnsembleClassifier → LSTMPredictor          │  │
│  └──────────────────────────────┼───────────────────────────────┘  │
│                                 │                                   │
│  ┌──────────────────────────────┼───────────────────────────────┐  │
│  │                  DATA LAYER                                   │  │
│  │  SQLite + SQLAlchemy ORM (WAL mode)                          │  │
│  │  [Users] [Sessions] [Frames] [Breaks] [DailyStats]          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Camera Frame (BGR) ─► RGB Convert (~1ms)
    ─► MediaPipe FaceMesh (~15ms) → 478 landmarks
    ─► FeatureExtractor (~5ms) → EAR, MAR, head pose, gaze
    ─► FeatureBuffer (circular, 900 frames)
    ─► EnsembleClassifier (RF+XGB+LGB, ~10ms)
    ─► TemporalSmoother (median filter)
    ─► LSTMPredictor (fatigue forecast, ~5ms)
    ─► Alert Engine → UI Update + DB Write
    
Total Pipeline: ~42ms average (target: <100ms) ✅
```

## ML Architecture

### Layer 1: Ensemble Classifier
- Random Forest + XGBoost + LightGBM
- Weighted soft voting by validation F1
- Input: 26 scalar features per frame
- Output: {Distracted, Focused, Fatigued} + confidence

### Layer 2: LSTM Fatigue Predictor
- BiLSTM(128) → BiLSTM(64) → Dense(1, sigmoid)
- Input: 300 frames × 7 features (10s window)
- Output: fatigue score (0-1), minutes until break
- Deployed as TFLite for on-device inference

### Layer 3: Rule Engine (Safety net)
- EAR < 0.21 for 3s → CRITICAL microsleep
- |head_yaw| > 30° → INFO looking away
- MAR > 0.6 for 3s → WARNING yawning
- blink_rate > 30/min → WARNING eye strain

## Database Schema

See `backend/database/migrations/init_schema.sql` for full schema.
Key tables: `users`, `study_sessions`, `session_frames`, `break_records`, `daily_statistics`.

## Privacy Architecture

- **Zero network calls** — verified by design, no HTTP/WebSocket imports
- **No video persistence** — frames processed in-memory, immediately discarded
- **Local SQLite** — all data in `data/smartstudy.db`
- **No PII** — only physiological metrics stored
- **Full data control** — export and delete from Settings page
