import os
import signal
import subprocess
import sys
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from backend.models import (AttendanceRecord, AttendanceSession, PeriodSchedule,
                            Subject, Setting, Student, db)
from backend.routes.utils import camera_running, require_login, resolve_camera_source, save_setting
from config import IS_VERCEL, PID_FILE, ENGINE_MANUAL_PATH, ENGINE_AUTO_PATH

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/attendance")
def attendance_page():
    if not require_login():
        return redirect(url_for("auth.login"))

    periods = PeriodSchedule.query.filter_by(is_break=False, is_active=True).order_by(PeriodSchedule.period_number).all()
    period_rows = []
    for p in periods:
        subj = db.session.get(Subject, p.subject_id)
        period_rows.append({"p": p, "subject": subj.subject_name if subj else "?"})

    today = datetime.now().strftime("%Y-%m-%d")
    sessions = AttendanceSession.query.filter_by(session_date=today).order_by(AttendanceSession.session_id.desc()).all()
    grace = Setting.query.filter_by(setting_key="default_grace_minutes").first()
    return render_template("attendance.html", period_rows=period_rows, sessions=sessions,
                           default_grace=grace.setting_value if grace else "15")


@attendance_bp.route("/start_session", methods=["POST"])
def start_session():
    if not require_login():
        return redirect(url_for("auth.login"))

    if AttendanceSession.query.filter_by(session_status="Running").first():
        flash("A session is already running. Stop it first.", "warning")
        return redirect(url_for("attendance.attendance_page"))

    sched = db.session.get(PeriodSchedule, int(request.form.get("schedule_id")))
    grace = int(request.form.get("grace_minutes") or 15)
    if not sched:
        flash("Invalid period.", "danger")
        return redirect(url_for("attendance.attendance_page"))

    now = datetime.now()
    cutoff = now + timedelta(minutes=grace)

    db.session.add(AttendanceSession(
        session_date=now.strftime("%Y-%m-%d"),
        schedule_id=sched.schedule_id,
        subject_id=sched.subject_id,
        period_number=sched.period_number,
        start_time=now.strftime("%H:%M"),
        end_time=sched.end_time,
        cutoff_time=cutoff.strftime("%H:%M"),
        session_status="Running"))
    db.session.commit()

    if IS_VERCEL:
        flash(
            "Camera processing is not available on Vercel. Use local development or a persistent server for live attendance capture.",
            "warning",
        )
        return redirect(url_for("attendance.attendance_page"))

    if not camera_running():
        source = resolve_camera_source()
        if source:
            proc = subprocess.Popen([sys.executable, ENGINE_MANUAL_PATH, str(source)])
            with open(PID_FILE, "w") as f:
                f.write(str(proc.pid))

    flash(f"Session started! Cutoff at {cutoff.strftime('%H:%M')}. Now run: python attendance.py", "success")
    return redirect(url_for("attendance.attendance_page"))


@attendance_bp.route("/stop_session/<int:sid>")
def stop_session(sid):
    if not require_login():
        return redirect(url_for("auth.login"))

    s = db.session.get(AttendanceSession, sid)
    if s and s.session_status == "Running":
        marked = {r.student_id for r in AttendanceRecord.query.filter_by(session_id=sid).all()}
        for st in Student.query.filter_by(is_active=True).all():
            if st.student_id not in marked:
                db.session.add(AttendanceRecord(session_id=sid, student_id=st.student_id, status="Absent", method="Automatic"))
        s.session_status = "Completed"
        db.session.commit()
        flash("Session finalized. Unmarked students set to Absent.", "success")
    return redirect(url_for("attendance.attendance_page"))


@attendance_bp.route("/live/<int:sid>")
def live_page(sid):
    if not require_login():
        return redirect(url_for("auth.login"))

    s = db.session.get(AttendanceSession, sid)
    records = {r.student_id: r for r in AttendanceRecord.query.filter_by(session_id=sid).all()}
    students = Student.query.filter_by(is_active=True).order_by(Student.roll_no).all()

    rows, present, late = [], 0, 0
    for st in students:
        r = records.get(st.student_id)
        status = r.status if r else "Not Detected"
        if status == "Present":
            present += 1
        elif status == "Late Not Accepted":
            late += 1
        rows.append({"s": st, "r": r, "status": status})

    subject = db.session.get(Subject, s.subject_id) if s else None
    return render_template("live.html", s=s, rows=rows, present=present, late=late, total=len(students), subject=subject)


@attendance_bp.route("/correction")
def correction_page():
    if not require_login():
        return redirect(url_for("auth.login"))

    sid = request.args.get("sid", type=int)
    sessions = AttendanceSession.query.order_by(AttendanceSession.session_id.desc()).all()
    rows, selected = [], None
    if sid:
        selected = db.session.get(AttendanceSession, sid)
        records = {r.student_id: r for r in AttendanceRecord.query.filter_by(session_id=sid).all()}
        for st in Student.query.filter_by(is_active=True).order_by(Student.roll_no).all():
            rows.append({"st": st, "rec": records.get(st.student_id)})

    logs = db.session.query().filter_by().all()
    return render_template("correction.html", sessions=sessions, rows=rows, selected=selected, sid=sid, logs=logs)


@attendance_bp.route("/update_attendance", methods=["POST"])
def update_attendance():
    if not require_login():
        return redirect(url_for("auth.login"))

    sid = int(request.form.get("session_id"))
    student_id = int(request.form.get("student_id"))
    new_status = request.form.get("new_status")
    reason = request.form.get("reason", "").strip()

    if not reason:
        flash("Reason is required for every manual update.", "warning")
        return redirect(url_for("attendance.correction_page", sid=sid))

    rec = AttendanceRecord.query.filter_by(session_id=sid, student_id=student_id).first()

    if rec:
        old_status = rec.status
        rec.status = new_status
        rec.method = "Manual"
        rec.updated_by = session["username"]
        rec.update_reason = reason
        rec.updated_at = datetime.now()
    else:
        old_status = "No Record"
        rec = AttendanceRecord(session_id=sid, student_id=student_id, status=new_status,
                               method="Manual", updated_by=session["username"],
                               update_reason=reason)
        db.session.add(rec)
        db.session.flush()

    from backend.models import AuditLog
    db.session.add(AuditLog(attendance_id=rec.attendance_id, old_status=old_status,
                            new_status=new_status, reason=reason,
                            changed_by=session["username"]))
    db.session.commit()

    flash(f"Attendance updated to '{new_status}'. Change logged in audit trail.", "success")
    return redirect(url_for("attendance.correction_page", sid=sid))


@attendance_bp.route("/camera")
def camera_page():
    if not require_login():
        return redirect(url_for("auth.login"))
    mode = Setting.query.filter_by(setting_key="camera_mode").first()
    rtsp = Setting.query.filter_by(setting_key="rtsp_url").first()
    return render_template("camera.html", mode=mode.setting_value if mode else "builtin",
                           rtsp=rtsp.setting_value if rtsp else "",
                           running=camera_running())


@attendance_bp.route("/camera/save", methods=["POST"])
def camera_save():
    if not require_login():
        return redirect(url_for("auth.login"))
    save_setting("camera_mode", request.form.get("camera_mode", "builtin"))
    save_setting("rtsp_url", request.form.get("rtsp_url", "").strip())
    db.session.commit()
    flash("Camera settings saved.", "success")
    return redirect(url_for("attendance.camera_page"))


@attendance_bp.route("/camera/start")
def camera_start():
    if not require_login():
        return redirect(url_for("auth.login"))
    if camera_running():
        flash("Camera engine is already running.", "warning")
        return redirect(url_for("attendance.camera_page"))

    if IS_VERCEL:
        flash(
            "Camera access is unavailable on Vercel because the runtime cannot access local hardware. Use browser capture or run locally.",
            "warning",
        )
        return redirect(url_for("attendance.camera_page"))

    mode = Setting.query.filter_by(setting_key="camera_mode").first()
    mode = mode.setting_value if mode else "builtin"
    rtsp = Setting.query.filter_by(setting_key="rtsp_url").first()
    rtsp = rtsp.setting_value if rtsp else ""

    source = "0" if mode == "builtin" else ("1" if mode == "usb" else rtsp)
    if not source:
        flash("Please save an RTSP URL for CCTV mode.", "danger")
        return redirect(url_for("attendance.camera_page"))

    proc = subprocess.Popen([sys.executable, ENGINE_AUTO_PATH, str(source)])
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    flash("Camera engine started.", "success")
    return redirect(url_for("attendance.camera_page"))


@attendance_bp.route("/camera/stop")
def camera_stop():
    if not require_login():
        return redirect(url_for("auth.login"))
    if IS_VERCEL:
        flash("Camera background processes are not supported on Vercel.", "warning")
        return redirect(url_for("attendance.camera_page"))
    if os.path.exists(PID_FILE):
        try:
            os.kill(int(open(PID_FILE).read().strip()), signal.SIGTERM)
        except Exception:
            pass
        os.remove(PID_FILE)
    flash("Camera engine stopped.", "success")
    return redirect(url_for("attendance.camera_page"))
