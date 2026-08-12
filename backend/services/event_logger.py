from backend.models import db, DetectionLog


def log_event(event_type, student, session_id, camera_source):
    """Record a detection event for the live monitor and records page."""
    log = DetectionLog(
        student_id=student["id"] if student else None,
        roll_no=student["roll"] if student else None,
        name=student["name"] if student else None,
        event_type=event_type,
        session_id=session_id,
        camera_source=camera_source,
    )
    db.session.add(log)
    db.session.commit()
