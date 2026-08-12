from datetime import datetime

from flask import Blueprint, redirect, render_template, session, url_for

from backend.models import AttendanceRecord, AttendanceSession, PeriodSchedule, Student, Subject, db
from backend.routes.utils import require_login

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("auth.login"))

    total_students = Student.query.count()
    enrolled_students = Student.query.filter_by(enrollment_status="Enrolled").count()
    total_subjects = Subject.query.count()
    total_periods = PeriodSchedule.query.count()
    all_students = Student.query.filter_by(is_active=True).order_by(Student.roll_no).all()
    not_enrolled = total_students - enrolled_students
    today = datetime.now().strftime("%Y-%m-%d")
    sessions_today = AttendanceSession.query.filter_by(session_date=today).count()
    summary_sentence = (
        f"You have {total_students} students, {enrolled_students} enrolled, and {sessions_today} sessions planned for today; "
        f"the next step is to {'close the enrollment gap' if not_enrolled else 'keep the attendance flow steady'}."
    )
    suggested_actions = []
    if not_enrolled:
        suggested_actions.append(f"{not_enrolled} students not enrolled - Enroll now")
    if sessions_today:
        suggested_actions.append("Review today's live session flow")
    else:
        suggested_actions.append("Start a session to begin tracking")

    recent_sessions = AttendanceSession.query.order_by(AttendanceSession.session_id.desc()).limit(3).all()
    absence_alerts = []
    for student in all_students:
        streak = 0
        for session in recent_sessions:
            record = AttendanceRecord.query.filter_by(session_id=session.session_id, student_id=student.student_id).first()
            if record and record.status == "Absent":
                streak += 1
            else:
                break
        if streak >= 3:
            absence_alerts.append(student)

    return render_template("dashboard.html",
                           total_students=total_students,
                           enrolled_students=enrolled_students,
                           total_subjects=total_subjects,
                           total_periods=total_periods,
                           students=all_students,
                           summary_sentence=summary_sentence,
                           suggested_actions=suggested_actions,
                           absence_alerts=absence_alerts,
                           period_rows=[{"p": p, "subject": (db.session.get(Subject, p.subject_id).subject_name if db.session.get(Subject, p.subject_id) else "?")} for p in PeriodSchedule.query.filter_by(is_active=True).order_by(PeriodSchedule.period_number).all()])
