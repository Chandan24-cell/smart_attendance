import base64
import os

import cv2
import numpy as np
from flask import Blueprint, jsonify, redirect, render_template, request, send_file, session, url_for

from backend.models import AttendanceRecord, AttendanceSession, FaceEmbedding, Student, db
from backend.routes.utils import get_photo_path, require_login
from backend.services.face_engine import check_face_quality, detect_face, get_embedding
from config import STATIC_FACES_DIR

students_bp = Blueprint("students", __name__)


@students_bp.route("/students")
def students_page():
    if not require_login():
        return redirect(url_for("auth.login"))

    students = Student.query.filter_by(is_active=True).order_by(Student.roll_no).all()
    data = []
    for s in students:
        photo_file = get_photo_path(s.roll_no)
        data.append({
            "s": s,
            "photo": f"/student_photo/{s.roll_no}.jpg" if os.path.exists(photo_file) else None,
        })
    return render_template("students.html", data=data, count=len(data))


@students_bp.route("/student_photo/<path:filename>")
def student_photo(filename):
    photo_path = STATIC_FACES_DIR / filename
    if not photo_path.exists():
        return jsonify({"ok": False, "error": "Photo not found"}), 404
    return send_file(photo_path, mimetype="image/jpeg")


@students_bp.route("/student/<int:sid>")
def student_profile(sid):
    if not require_login():
        return redirect(url_for("auth.login"))

    st = db.session.get(Student, sid)
    if not st:
        return redirect(url_for("students.students_page"))

    recs = []
    for r, s in db.session.query(AttendanceRecord, AttendanceSession) \
            .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.session_id) \
            .filter(AttendanceRecord.student_id == sid) \
            .order_by(AttendanceRecord.attendance_id.desc()).all():
        recs.append({"r": r, "s": s})

    total = len(recs)
    present = sum(1 for x in recs if x["r"].status == "Present")
    pct = round(present / total * 100, 1) if total else 0

    photo_file = get_photo_path(st.roll_no)
    photo = f"/student_photo/{st.roll_no}.jpg" if os.path.exists(photo_file) else None
    return render_template("student_profile.html", st=st, recs=recs, total=total, present=present, pct=pct, photo=photo)


@students_bp.route("/enroll_capture", methods=["POST"])
def enroll_capture():
    if not require_login():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    data = request.get_json()
    student_id = int(data.get("student_id"))
    img_b64 = data.get("image", "")
    if "," in img_b64:
        img_b64 = img_b64.split(",")[1]

    img_bytes = base64.b64decode(img_b64)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"ok": False, "error": "Student not found."})

    bbox, aligned = detect_face(frame)
    if aligned is None:
        return jsonify({"ok": False, "error": "No face detected. Look straight at the camera."})

    ok, reason = check_face_quality(frame, bbox)
    if not ok:
        return jsonify({"ok": False, "error": f"Unclear face: {reason}"})

    embedding = get_embedding(aligned)

    STATIC_FACES_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(STATIC_FACES_DIR / f"{student.roll_no}.jpg"), aligned)

    FaceEmbedding.query.filter_by(student_id=student_id).update({"is_active": False})
    db.session.add(FaceEmbedding(student_id=student_id, embedding=",".join(map(str, embedding))))
    student.enrollment_status = "Enrolled"
    db.session.commit()

    return jsonify({"ok": True, "message": f"{student.student_name} enrolled successfully!"})
