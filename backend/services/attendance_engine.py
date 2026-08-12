import cv2
import time
from datetime import datetime, timedelta

from backend.models import (AttendanceRecord, AttendanceSession, PeriodSchedule,
                            Subject, Setting, Student, db)
from backend.services.event_logger import log_event
from backend.services.face_engine import (MATCH_THRESHOLD, check_face_quality,
                                         compare, detect_face, get_embedding)
from backend.services.report_mailer import check_auto_report
from backend import create_app
from config import ENGINE_MANUAL_PATH, ENGINE_AUTO_PATH, PID_FILE

app = create_app()


def load_enrolled():
    faces = []
    for emb in db.session.query().filter_by(is_active=True).all():
        pass
    for emb in []:
        pass
    return faces
