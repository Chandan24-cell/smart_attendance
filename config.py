import os
from pathlib import Path


# ============================================================
# Base directory
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# Runtime / writable directories
# ============================================================
# Vercel's deployed filesystem is read-only.
# /tmp is the writable location available to serverless functions.

IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    DATA_DIR = Path("/tmp/smart_attendance")
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Database
# ============================================================

DB_PATH = DATA_DIR / "attendance.db"


# ============================================================
# Camera PID file
# ============================================================

if IS_VERCEL:
    PID_FILE = Path("/tmp/smart_attendance/camera.pid")
else:
    PID_FILE = BASE_DIR / "camera.pid"


# ============================================================
# Face recognition models
# ============================================================

FACE_DETECTOR_MODEL = str(
    BASE_DIR / "face_models" / "face_detection_yunet.onnx"
)

FACE_RECOGNIZER_MODEL = str(
    BASE_DIR / "face_models" / "face_recognition_sface.onnx"
)


# ============================================================
# Face images
# ============================================================
# Runtime uploads must NOT be written into:
# frontend/static/faces
#
# That directory is part of the deployed Vercel filesystem
# and is read-only.

STATIC_FACES_DIR = DATA_DIR / "faces"
STATIC_FACES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Attendance engines
# ============================================================

ENGINE_MANUAL_PATH = str(
    BASE_DIR / "attendance.py"
)

ENGINE_AUTO_PATH = str(
    BASE_DIR / "auto_attendance.py"
)


# ============================================================
# Google Sheet configuration
# ============================================================

SHEET_KEYS = {
    "student": "student_sheet_link",
    "timetable": "timetable_sheet_link",
}


# ============================================================
# Security
# ============================================================
# Set SECRET_KEY in Vercel Environment Variables.
# The fallback is useful for local development only.

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key-change-this"
)