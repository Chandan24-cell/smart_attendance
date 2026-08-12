import csv
import io
from flask import Blueprint, flash, redirect, render_template, request, Response, url_for

from backend.models import AttendanceRecord, AttendanceSession, Setting, Student, Subject, db
from backend.routes.utils import require_login, save_setting
from backend.services.report_mailer import send_30day_report

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
def reports_page():
    if not require_login():
        return redirect(url_for("auth.login"))

    sessions = AttendanceSession.query.order_by(AttendanceSession.session_id.desc()).all()
    sid = request.args.get("sid", type=int)
    if not sid and sessions:
        sid = sessions[0].session_id
    selected = db.session.get(AttendanceSession, sid) if sid else None

    labels, present_data, absent_data = [], [], []
    for s in sessions:
        labels.append(f"P{s.period_number} ({s.session_date[5:]})")
        present_data.append(AttendanceRecord.query.filter_by(session_id=s.session_id, status="Present").count())
        absent_data.append(AttendanceRecord.query.filter_by(session_id=s.session_id, status="Absent").count())

    pie = {"Present": 0, "Late": 0, "Absent": 0, "NotDetected": 0}
    if selected:
        records = AttendanceRecord.query.filter_by(session_id=sid).all()
        for r in records:
            if r.status == "Present":
                pie["Present"] += 1
            elif r.status == "Late Not Accepted":
                pie["Late"] += 1
            elif r.status == "Absent":
                pie["Absent"] += 1
        pie["NotDetected"] = Student.query.filter_by(is_active=True).count() - len(records)

    student_rows = []
    for st in Student.query.filter_by(is_active=True).order_by(Student.roll_no).all():
        recs = AttendanceRecord.query.filter_by(student_id=st.student_id).all()
        present = sum(1 for r in recs if r.status == "Present")
        pct = round(present / len(recs) * 100, 1) if recs else 0
        student_rows.append({"st": st, "total": len(recs), "present": present, "pct": pct})

    subject_rows = []
    for subj in Subject.query.filter_by(is_active=True).all():
        sess_ids = [s.session_id for s in AttendanceSession.query.filter_by(subject_id=subj.subject_id).all()]
        if not sess_ids:
            continue
        recs = AttendanceRecord.query.filter(AttendanceRecord.session_id.in_(sess_ids)).all()
        present = sum(1 for r in recs if r.status == "Present")
        pct = round(present / len(recs) * 100, 1) if recs else 0
        subject_rows.append({"name": subj.subject_name, "total": len(recs), "present": present, "pct": pct})

    def gs(k):
        s = Setting.query.filter_by(setting_key=k).first()
        return s.setting_value if s else ""

    email_settings = {"smtp_email": gs("smtp_email"), "smtp_password": gs("smtp_password"), "report_email_to": gs("report_email_to")}
    return render_template("reports.html", sessions=sessions, sid=sid, selected=selected,
                           labels=labels, present_data=present_data, absent_data=absent_data,
                           pie=pie, student_rows=student_rows, subject_rows=subject_rows,
                           email_settings=email_settings)


@reports_bp.route("/export/<int:sid>")
def export_csv(sid):
    if not require_login():
        return redirect(url_for("auth.login"))

    records = AttendanceRecord.query.filter_by(session_id=sid).all()
    students = {st.student_id: st for st in Student.query.all()}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["roll_no", "name", "status", "detected_time", "method", "reason"])
    for r in records:
        st = students.get(r.student_id)
        writer.writerow([st.roll_no if st else "", st.student_name if st else "",
                         r.status, r.detected_time or "", r.method, r.update_reason or ""])

    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename=attendance_session_{sid}.csv"})


@reports_bp.route("/report_email_settings", methods=["POST"])
def report_email_settings():
    if not require_login():
        return redirect(url_for("auth.login"))
    for key in ["smtp_email", "smtp_password", "report_email_to"]:
        save_setting(key, request.form.get(key, "").strip())
    db.session.commit()
    flash("📧 Email report settings saved.", "success")
    return redirect(url_for("reports.reports_page"))


@reports_bp.route("/send_report_now")
def send_report_now():
    if not require_login():
        return redirect(url_for("auth.login"))
    ok, msg = send_30day_report()
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("reports.reports_page"))
