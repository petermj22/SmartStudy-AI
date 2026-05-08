# SmartStudy — User Guide

## Getting Started

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/SuhelMulla22/SmartStudy-AI.git
cd SmartStudy-AI

# Windows
scripts\setup.bat

# macOS/Linux
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

### 2. Launch

```bash
streamlit run frontend/app.py
```

Open your browser to **http://localhost:8501**

---

## Features

### 📊 Dashboard
Your home screen showing:
- **Today's study time** — total minutes studied
- **Focus percentage** — how focused you were
- **Session count** — number of sessions today
- **Current streak** — consecutive study days
- **Daily trend chart** — focus over the past week
- **Recent sessions** — quick access to session history

### 🎥 Live Session
Start a new study session:
1. Enter your **subject** (Math, Physics, etc.)
2. Click **Start Session**
3. Position yourself in front of the webcam
4. The system tracks your focus in real-time:
   - 🟢 **Green** = Focused
   - 🔴 **Red** = Distracted
   - 🟡 **Yellow** = Fatigued
5. Get **break alerts** when fatigue is detected
6. Click **End Session** to save your progress

### 📈 Analytics
Deep dive into your study patterns:
- **Daily focus trends** — line chart over 7/30 days
- **Productivity heatmap** — best hours × days of week
- **Subject breakdown** — time and focus per subject
- **Hourly distribution** — when you study most

### 💡 AI Insights
Personalized recommendations based on your data:
- Optimal study times
- Subject-specific tips
- Focus trend analysis
- Study habit patterns
- Break timing suggestions

### ⚙️ Settings
Customize your experience:
- **Break interval** — minutes between breaks (default: 25)
- **Alert sensitivity** — low/medium/high
- **Camera selection** — choose webcam device
- **Data management** — export or delete your data

---

## Privacy

SmartStudy processes **everything locally**:
- ✅ No internet connection required during use
- ✅ No video is ever recorded or saved
- ✅ All data stored in local SQLite database
- ✅ You can delete all data anytime from Settings
- ✅ Open-source code for full transparency

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Camera not detected | Check webcam connection, try a different Device ID in Settings |
| Low accuracy | Ensure good lighting, sit facing the camera |
| App crashes | Check `logs/` directory for error details |
| High CPU usage | Reduce camera resolution in Settings |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+R` | Refresh page |
| `Ctrl+Shift+R` | Hard refresh |

For more information, see [ARCHITECTURE.md](ARCHITECTURE.md) and [API.md](API.md).
