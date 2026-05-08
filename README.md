# 🎯 SmartStudy v2.0
### AI-Powered Study Session Optimizer & Focus Assistant

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success)](README.md)
[![Status](https://img.shields.io/badge/Status-Beta-yellow)](README.md)

> Real-time focus monitoring using webcam AI — all processing happens on your device.
> No cloud. No subscriptions. No data leaves your computer.

---

## ⚡ Quick Start (3 Commands)

```bash
# 1. Clone
git clone https://github.com/your-team/smartstudy.git
cd smartstudy

# 2. Install
pip install -r requirements.txt

# 3. Launch
python run.py
```

Opens at: **http://localhost:8501**

---

## 📋 Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python    | 3.10+   | 3.11+       |
| RAM       | 8 GB    | 16 GB       |
| CPU       | Intel i5 8th Gen | Intel i7 10th Gen |
| Webcam    | 720p 30fps | 1080p 60fps |
| Storage   | 2 GB free | 5 GB free |
| OS        | Windows 10, macOS 11, Ubuntu 20.04 | Latest |

---

## 🔑 Key Features

| Feature | Technology | Accuracy |
|---------|-----------|----------|
| Face Detection | MediaPipe (468 landmarks) | 99% detection rate |
| Focus Classification | Ensemble ML + Kalman Filter | ~91% after calibration |
| Fatigue Prediction | LSTM (TFLite) | 5-min advance warning |
| Online Learning | River (Hoeffding Tree) | Personalizes per user |
| Break Recommendation | Rule-based + AI | Adaptive intervals |
| Desktop Notifications | plyer | Cross-platform |
| Session Replay | Frame snapshots + MP4/PDF | Local storage |
| Data Encryption | AES-256 (cryptography) | Military-grade |

---

## 🌐 Works 100% Offline

After first setup, SmartStudy requires **zero internet connection**.

All models, databases, and processing are local:

```
mediapipe models    → cached after first run
ML models           → ml_training/trained_models/
database            → data/smartstudy.db
logs                → logs/
```

---

## 🏗️ Project Structure

```
smartstudy/
├── run.py                    ← START HERE
├── requirements.txt          ← All dependencies
├── setup.bat                 ← Windows setup
├── setup.sh                  ← macOS/Linux setup
├── frontend/
│   ├── app.py               ← Main Streamlit app
│   ├── pages/               ← Dashboard, Analytics, Coach, History, Settings
│   ├── components/          ← Camera, Sound, Health Check, Feedback
│   └── ui/                  ← Theme, Icons, Charts
├── backend/
│   ├── core/                ← Camera, Inference, Session Manager
│   ├── ml/                  ← Ensemble, LSTM, Kalman, Online Learner
│   ├── vision/              ← Face Detection, Features, Blink, Gaze
│   ├── database/            ← SQLite Models, Manager
│   └── analytics/           ← Aggregator, Insights, Scheduler
├── ml_training/
│   ├── train_ensemble.py    ← Train focus classifier
│   ├── train_lstm.py        ← Train fatigue predictor
│   └── trained_models/      ← Saved model files
├── config/
│   ├── app_config.yaml
│   └── model_config.yaml
└── data/                    ← Created automatically
    ├── smartstudy.db
    ├── reports/
    └── replays/
```

---

## 🧪 Training Your Own Models

```bash
# Step 1: Record labeled sessions (run the app, study for 2-3 hours)
# Step 2: Export your data from Settings > Export

# Step 3: Train
python ml_training/train_ensemble.py --data ml_training/datasets/
python ml_training/train_lstm.py --data ml_training/datasets/

# Step 4: Restart app — new models load automatically
```

---

## 🔧 Setup Scripts

**Windows:**
```batch
setup.bat
```

**macOS / Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

---

## 👥 Team

**Department of Computer Science & Engineering (AI & ML)**
D. Y. Patil Agriculture & Technical University, Talsande
Academic Year 2025-26

| Role | Responsibility |
|------|---------------|
| Student 1 | CV Pipeline, MediaPipe |
| Student 2 | ML Models, Training |
| Student 3 | Frontend, UI/UX |
| Student 4 | Database, Analytics |
| Student 5 | Integration, Testing |

---

## 📄 License

MIT License — Open Source
