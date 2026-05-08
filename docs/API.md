# SmartStudy — API Reference

## Backend Modules

### `backend.vision.FaceDetector`
```python
detector = FaceDetector(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_faces=1,
    refine_landmarks=True,
)
result: DetectionResult = detector.detect(rgb_frame)
```

**DetectionResult** fields:
| Field | Type | Description |
|-------|------|-------------|
| `detected` | bool | Face found in frame |
| `landmarks` | ndarray(478,3) | Pixel coordinates |
| `normalized_landmarks` | ndarray(478,3) | 0-1 normalized |
| `has_iris` | bool | Iris landmarks available |

---

### `backend.vision.FeatureExtractor`
```python
extractor = FeatureExtractor(face_detector)
features: FaceFeatures = extractor.extract(detection_result)
feature_dict = features.to_dict()  # 26 float values for ML
```

**FaceFeatures** key fields:
| Feature | Range | Description |
|---------|-------|-------------|
| `avg_ear` | 0.1–0.4 | Eye Aspect Ratio |
| `mar` | 0.1–0.8 | Mouth Aspect Ratio |
| `head_pitch` | -90°–90° | Up/down head tilt |
| `head_yaw` | -90°–90° | Left/right head turn |
| `gaze_stability` | 0–1 | Gaze steadiness |

---

### `backend.ml.EnsembleClassifier`
```python
classifier = EnsembleClassifier(model_dir="ml_training/trained_models")
result: ClassificationResult = classifier.predict(feature_dict)
```

**ClassificationResult** fields:
| Field | Type | Description |
|-------|------|-------------|
| `state` | int | 0=distracted, 1=focused, 2=fatigued |
| `confidence` | float | Prediction confidence 0-1 |
| `probabilities` | dict | Per-class probabilities |

---

### `backend.ml.LSTMPredictor`
```python
predictor = LSTMPredictor(model_dir="ml_training/trained_models")
result: FatigueResult = predictor.predict(feature_sequence)
```

---

### `backend.database.DatabaseManager`
```python
db = DatabaseManager(db_path="data/smartstudy.db")

# Session CRUD
session = db.create_session(subject="Math", tags=["exam"])
db.end_session(session.id, metrics={...})
sessions = db.get_recent_sessions(limit=10)

# Analytics
daily = db.get_daily_statistics()
weekly = db.get_weekly_stats()
heatmap = db.get_productivity_heatmap(days=30)

# Data management
db.delete_all_data()
export = db.export_data(start_date, end_date)
```

---

### `backend.core.SessionManager`
```python
manager = SessionManager(db_manager=db, camera_config=config)
manager.start_session(subject="Physics")
state = manager.get_current_state()  # Real-time metrics
manager.end_session()
```

---

### `backend.analytics.InsightEngine`
```python
engine = InsightEngine(db_manager=db)
insights = engine.generate_insights()  # List of personalized recommendations
```

---

### `backend.analytics.StudyScheduler`
```python
scheduler = StudyScheduler(db_manager=db)
schedule = scheduler.generate_schedule(
    subjects=["Math", "Physics"],
    available_hours=6,
)
```
