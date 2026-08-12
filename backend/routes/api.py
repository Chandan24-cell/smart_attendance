from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.models import AttendanceRecord, AttendanceSession, DetectionLog, PeriodSchedule, Setting, Student, Subject, db
from backend.routes.utils import require_login

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/events")
def api_events():
    since = request.args.get("since", 0, type=int)
    logs = DetectionLog.query.filter(DetectionLog.log_id > since).order_by(DetectionLog.log_id).limit(20).all()
    return jsonify([{
        "id": l.log_id,
        "type": l.event_type,
        "name": l.name,
        "roll": l.roll_no,
        "time": l.detected_at.strftime("%d %b %H:%M:%S")
    } for l in logs])


@api_bp.route("/api/ask")
def api_ask():
    q = (request.args.get("q", "") or "").strip().lower()
    if not q:
        return jsonify({"answer": "Please ask a supported question.", "table": []})

    allowed = [
        "today's summary",
        "student attendance",
        "students below 75",
        "absentees of last session",
        "not enrolled",
        "last sync time",
        "periods today",
    ]
    if q not in allowed and "attendance %" not in q and "summary" not in q and "below" not in q and "absentees" not in q and "not enrolled" not in q and "last sync" not in q and "periods" not in q:
        return jsonify({"answer": "Unsupported request.", "table": []})

    if "today's summary" in q or "summary" in q:
        total_students = Student.query.count()
        enrolled_students = Student.query.filter_by(enrollment_status="Enrolled").count()
        today = datetime.now().strftime("%Y-%m-%d")
        sessions_today = AttendanceSession.query.filter_by(session_date=today).count()
        return jsonify({
            "answer": f"Today has {total_students} students, {enrolled_students} enrolled, and {sessions_today} session records to review.",
            "table": [
                {"label": "Students", "value": total_students},
                {"label": "Enrolled", "value": enrolled_students},
                {"label": "Sessions today", "value": sessions_today},
            ],
        })

    if "student attendance" in q or "attendance %" in q:
        student = None
        for term in q.split():
            if term.isdigit():
                student = Student.query.filter_by(roll_no=term).first()
                break
        if not student:
            student = Student.query.filter(Student.student_name.ilike(f"%{q}%")) .first()
        if student:
            records = AttendanceRecord.query.filter_by(student_id=student.student_id).all()
            present = sum(1 for r in records if r.status == "Present")
            pct = round(present / len(records) * 100, 1) if records else 0
            return jsonify({
                "answer": f"{student.student_name} has {pct}% attendance across {len(records)} recorded sessions.",
                "table": [{"label": "Roll", "value": student.roll_no}, {"label": "Present", "value": present}, {"label": "Total", "value": len(records)}, {"label": "Percent", "value": f"{pct}%"}],
            })
        return jsonify({"answer": "No matching student found.", "table": []})

    if "below" in q and "75" in q:
        rows = []
        for student in Student.query.filter_by(is_active=True).order_by(Student.roll_no).all():
            records = AttendanceRecord.query.filter_by(student_id=student.student_id).all()
            present = sum(1 for r in records if r.status == "Present")
            pct = round(present / len(records) * 100, 1) if records else 0
            if pct < 75:
                rows.append({"roll": student.roll_no, "name": student.student_name, "pct": f"{pct}%"})
        return jsonify({
            "answer": f"There are {len(rows)} students below the 75% threshold.",
            "table": rows[:8],
        })

    if "absentees" in q:
        session = AttendanceSession.query.order_by(AttendanceSession.session_id.desc()).first()
        if not session:
            return jsonify({"answer": "No sessions are available yet.", "table": []})
        rows = []
        for record in AttendanceRecord.query.filter_by(session_id=session.session_id, status="Absent").all():
            student = Student.query.get(record.student_id)
            if student:
                rows.append({"roll": student.roll_no, "name": student.student_name})
        return jsonify({"answer": f"The latest session has {len(rows)} absentees.", "table": rows[:10]})

    if "not enrolled" in q:
        rows = []
        for student in Student.query.filter_by(is_active=True).order_by(Student.roll_no).all():
            if student.enrollment_status != "Enrolled":
                rows.append({"roll": student.roll_no, "name": student.student_name, "status": student.enrollment_status})
        return jsonify({"answer": f"There are {len(rows)} students not enrolled.", "table": rows[:10]})

    if "last sync" in q:
        setting = Setting.query.filter_by(setting_key="last_sync_at").first()
        last_sync = setting.setting_value if setting else "No sync yet"
        return jsonify({"answer": f"The last sync time was {last_sync}.", "table": []})

    if "periods" in q:
        rows = []
        for period in PeriodSchedule.query.filter_by(is_active=True).order_by(PeriodSchedule.period_number).all():
            subject = Subject.query.get(period.subject_id)
            rows.append({"period": f"P{period.period_number}", "subject": subject.subject_name if subject else "-", "time": f"{period.start_time}-{period.end_time}"})
        return jsonify({"answer": f"There are {len(rows)} periods today.", "table": rows})

    return jsonify({"answer": "Supported request received.", "table": []})
