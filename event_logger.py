from models import db, DetectionLog

def log_event(event_type, student=None, session_id=None, camera_source=""):
    db.session.add(DetectionLog(
        event_type=event_type,
        student_id=student["id"] if student else None,
        roll_no=student["roll"] if student else "",
        name=student["name"] if student else "",
        session_id=session_id,
        camera_source=camera_source))
    db.session.commit()
