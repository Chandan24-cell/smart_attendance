from flask import Blueprint, redirect, render_template, request, url_for

from backend.models import AttendanceRecord, AttendanceSession, DetectionLog, Student, db
from backend.routes.utils import require_login

records_bp = Blueprint("records", __name__)


@records_bp.route("/records")
def records_page():
    if not require_login():
        return redirect(url_for("auth.login"))
    date_filter = request.args.get("date", "")

    dq = DetectionLog.query
    if date_filter:
        dq = dq.filter(db.func.date(DetectionLog.detected_at) == date_filter)
    logs = dq.order_by(DetectionLog.log_id.desc()).limit(500).all()

    aq = db.session.query(AttendanceRecord, AttendanceSession) \
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.session_id)
    if date_filter:
        aq = aq.filter(AttendanceSession.session_date == date_filter)
    att_rows = []
    for r, s in aq.order_by(AttendanceRecord.attendance_id.desc()).limit(500).all():
        st = db.session.get(Student, r.student_id)
        att_rows.append({"r": r, "s": s, "roll": st.roll_no if st else "", "name": st.student_name if st else ""})

    return render_template("records.html", logs=logs, att_rows=att_rows, date_filter=date_filter)
