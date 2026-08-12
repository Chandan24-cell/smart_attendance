import os
import signal
import subprocess
import sys
from flask import session

from backend.models import Setting, db
from config import IS_VERCEL, PID_FILE, STATIC_FACES_DIR


def save_setting(key, value):
    s = Setting.query.filter_by(setting_key=key).first()
    if s:
        s.setting_value = value
    else:
        db.session.add(Setting(setting_key=key, setting_value=value))


def camera_running():
    if IS_VERCEL:
        return False
    if not os.path.exists(PID_FILE):
        return False
    try:
        os.kill(int(open(PID_FILE).read().strip()), 0)
        return True
    except Exception:
        return False


def resolve_camera_source():
    if IS_VERCEL:
        return ""
    mode = Setting.query.filter_by(setting_key="camera_mode").first()
    mode = mode.setting_value if mode else "builtin"
    rtsp = Setting.query.filter_by(setting_key="rtsp_url").first()
    rtsp = rtsp.setting_value if rtsp else ""
    return "0" if mode == "builtin" else ("1" if mode == "usb" else rtsp)


def require_login():
    if "user_id" not in session:
        return False
    return True


def get_photo_path(roll_no):
    return STATIC_FACES_DIR / f"{roll_no}.jpg"


def build_period_rows():
    from backend.models import PeriodSchedule, Subject

    rows = []
    for p in PeriodSchedule.query.filter_by(is_active=True).order_by(PeriodSchedule.period_number).all():
        subj = db.session.get(Subject, p.subject_id)
        rows.append({"p": p, "subject": subj.subject_name if subj else "?"})
    return rows
