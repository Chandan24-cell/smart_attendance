# Smart Attendance System

AI-powered, camera-based classroom attendance with live Google Sheets sync, cutoff rules, audit logs, analytics and automated monthly email reports.

![Python](https://img.shields.io/badge/Python-3-blue)
![Flask](https://img.shields.io/badge/Flask-app--factory-black)
![OpenCV](https://img.shields.io/badge/OpenCV-YuNet%20%2B%20SFace-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Screenshots

| Login | Dashboard |
|---|---|
| `docs/screenshots/login.png` | `docs/screenshots/dashboard.png` |

| Live Engine | Reports |
|---|---|
| `docs/screenshots/live_engine.png` | `docs/screenshots/reports.png` |

## Features

**Admin & data source**
- Admin authentication with hashed passwords.
- Live master data: admin pastes two Google Sheet links (Students + Timetable) on the Data Source page.
- Manual sync buttons with sync logs.
- Deploying to a new college needs zero code changes.

**Enrollment & recognition**
- Browser face enrollment with a camera picker (built-in or USB).
- Quality gates on enrollment: distance, brightness, blur.
- Stores a 128-dim SFace embedding plus a small cropped photo.
- Recognition pipeline: OpenCV YuNet detection → SFace embedding → cosine similarity (match threshold 0.363; enrolled users measured around 0.81).

**Attendance engine**
- Manual sessions with a default 15-minute grace/cutoff window; camera auto-starts with the session.
- Full-day AUTO mode: reads the timetable, auto-creates sessions, applies cutoff = start + grace.
- Marks "Late – Not Accepted" after cutoff, blocks duplicate check-ins.
- Auto-finalizes absentees at period end and idles during breaks/off-hours.
- Camera support: laptop built-in, USB webcam, CCTV/IP via RTSP URL.

**On-screen feedback**
- Large banners: "PRESENT – ATTENDANCE ACCEPTED", "LATE – NOT ACCEPTED", "NOT ENROLLED / UNKNOWN", "Unclear face".

**Dashboard**
- Real-time popup notifications for new events only, dismissible.
- Full student table and full timetable view.
- Campus background with parallax and glass panels.

**Advanced UI/UX (six stages)**
- Morphological: state transitions.
- Generative: time-of-day greeting, template NLG daily summary, suggested-action chips.
- Adaptive: dark/light mode, density control, responsive layout.
- Multimodal: voice announcements and voice commands via Web Speech API.
- Spatial: depth, parallax, glassmorphism.
- Agentic: Attendance Copilot chat backed by a read-only whitelisted `/api/ask` endpoint.

**Corrections & audit**
- Admin correction requires a mandatory reason.
- Immutable audit log for all corrections.

**Analytics**
- Chart.js bar and doughnut charts.
- Subject-wise and student-wise attendance percentages.
- CSV export, date-wise records page.
- Per-student profile with history and overall percentage.

**Reporting**
- 30-day attendance CSV emailed via Gmail SMTP (App Password).
- Manual send and automatic send every 30 days.

## How it works

1. Admin logs in and pastes the Students and Timetable Google Sheet links on the Data Source page.
2. Admin syncs the sheets; data lands in SQLite and a sync log entry is recorded.
3. Students enroll their faces through the browser; embeddings and cropped photos are stored.
4. Admin starts a manual session, or switches on full-day AUTO mode.
5. AUTO mode reads the timetable and auto-creates sessions, computing cutoff = start + grace.
6. The camera feed runs YuNet detection, then SFace embedding, then cosine similarity matching.
7. Each match is classified as present, late, unknown, or unclear, and shown on screen with duplicate checks applied.
8. At period end, absentees are auto-finalized; the dashboard, analytics, and email reports reflect the results.

## Architecture

```
Google Sheets (Students + Timetable)
            │
            ▼
        Sync Service
            │
            ▼
          SQLite
            │
   ┌────────┴────────┐
   ▼                  ▼
Camera / Engine   Dashboard
(YuNet + SFace)   (real-time)
   │                  │
   └────────┬─────────┘
            ▼
   Reports / Email (SMTP)
```

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask (app factory + blueprints) |
| Database | SQLAlchemy + SQLite |
| Computer vision | OpenCV (YuNet + SFace ONNX) |
| Data processing | pandas |
| Frontend | Bootstrap 5, vanilla JS/CSS |
| Charts | Chart.js |
| Voice | Web Speech API |
| Email | smtplib (Gmail SMTP) |

## Project structure

```
smart_attendance/
├── run.py
├── config.py
├── requirements.txt
├── .gitignore
├── README.md
├── CHANGELOG.md
├── backend/
│   ├── __init__.py            # app factory
│   ├── models.py
│   ├── routes/                # blueprints
│   ├── services/
│   │   ├── sync_service.py
│   │   ├── face_engine.py
│   │   ├── event_logger.py
│   │   ├── report_mailer.py
│   │   └── attendance_engine.py
│   └── engines/
│       ├── manual_engine.py
│       └── auto_engine.py
├── frontend/
│   ├── templates/              # incl. split-screen login + base layout
│   └── static/
│       ├── css/
│       ├── js/
│       ├── img/
│       ├── faces/
│       └── ai_models/
├── scripts/                    # dev tools
├── data/
│   └── attendance.db
└── docs/                       # report, PPT, screenshots
```

## Getting started

**Prerequisites**
- Python 3
- A Google account to host the Students and Timetable sheets
- A Gmail account with an App Password, if email reports are needed

**Setup**

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Download the YuNet and SFace ONNX models from the OpenCV Model Zoo and place them in `frontend/static/ai_models/`.

Create the two Google Sheets (Students, Timetable) and share each as "anyone with the link".

Run the app:

```bash
python run.py
```

Log in with the default admin credentials, then:

1. Go to Data Source and paste the two Google Sheet links.
2. Click Sync.
3. Enroll student faces.
4. Start a manual session, or switch on AUTO mode.

Optionally, add a Gmail App Password in settings to enable automated email reports.

## Daily usage

- Start the engine once at the beginning of the day (manual session or AUTO mode).
- Everything else runs automatically: cutoffs, duplicate blocking, absentee finalization.
- Review the dashboard and reports as needed.

## Default credentials & security notes

- Default login: `admin` / `admin123`. Change this after first login.
- The Gmail App Password used for reports is not the same as the real account password.
- Faces are stored as embeddings, not raw images, aside from the small enrollment crop.

## Testing snapshot

- Match threshold set at 0.363; enrolled users measured around 0.81 similarity.
- Cutoff enforcement verified.
- Duplicate-check blocking verified.
- Unknown-face handling verified.
- Audit log immutability verified.

## Limitations & future work

**Current limitations**
- Recognition accuracy depends on lighting conditions.
- Assumes a single entry point (door) per classroom.

**Future work**
- Liveness / anti-spoof detection.
- Multi-classroom cloud deployment.
- Mobile app.
- SMS alerts.

## Docs

See `docs/` for the project report, presentation, and screenshots.

## Author & license

Built as a college project. Licensed under MIT.
