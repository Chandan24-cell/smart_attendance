import cv2
import time
from datetime import datetime, timedelta
from face_engine import detect_face, get_embedding, compare, MATCH_THRESHOLD, check_face_quality
from event_logger import log_event
from models import (db, Student, FaceEmbedding, AttendanceSession,
                    AttendanceRecord, PeriodSchedule, Subject, Setting)
from app import app

def load_enrolled():
    faces = []
    for emb in FaceEmbedding.query.filter_by(is_active=True).all():
        st = db.session.get(Student, emb.student_id)
        if st:
            faces.append({"id": st.student_id, "name": st.student_name,
                          "roll": st.roll_no,
                          "vector": list(map(float, emb.embedding.split(",")))})
    return faces

def hm_to_dt(hm, now):
    return now.replace(hour=int(hm[:2]), minute=int(hm[3:5]), second=0, microsecond=0)

def finalize_session(sess):
    marked = {r.student_id for r in AttendanceRecord.query.filter_by(session_id=sess.session_id).all()}
    for st in Student.query.filter_by(is_active=True).all():
        if st.student_id not in marked:
            db.session.add(AttendanceRecord(session_id=sess.session_id,
                                            student_id=st.student_id,
                                            status='Absent', method='Automatic'))
    sess.session_status = 'Completed'
    db.session.commit()
    print(f"🏁 Period {sess.period_number} finalized.")

def run_engine(auto, source_arg):
    source = source_arg if not source_arg.isdigit() else int(source_arg)
    source_label = source_arg

    with app.app_context():
        enrolled = load_enrolled()
        if not enrolled:
            print("❌ No enrolled faces. Enroll from the Students page first.")
            return
        g = Setting.query.filter_by(setting_key="default_grace_minutes").first()
        default_grace = int(g.setting_value) if g else 15

    if auto:
        try:
            from report_mailer import check_auto_report
            check_auto_report()
        except Exception as e:
            print("⚠️ Auto report check skipped:", e)

    print(f"🤖 {'AUTO' if auto else 'MANUAL'} MODE running. Press 'q' to quit.")
    cap = cv2.VideoCapture(source)
    last_unknown = [0]
    last_unclear = [0]
    banner = {"until": 0, "text": "", "sub": "", "color": (0, 255, 0)}

    def set_banner(text, sub, color, seconds=4):
        banner.update({"until": time.time() + seconds, "text": text,
                       "sub": sub, "color": color})

    with app.app_context():
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Cannot read camera/stream. Retrying in 3s...")
                time.sleep(3)
                cap = cv2.VideoCapture(source)
                continue

            now = datetime.now()
            cv2.putText(frame, now.strftime("%d %b %Y  %H:%M:%S"),
                        (10, frame.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # ---------- resolve session ----------
            if auto:
                active = None
                for p in PeriodSchedule.query.filter_by(is_active=True, is_break=False).all():
                    if hm_to_dt(p.start_time, now) <= now < hm_to_dt(p.end_time, now):
                        active = p
                        break
                if active is None:
                    cv2.putText(frame, f"{now.strftime('%H:%M')} | No active period (break / off hours)",
                                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    cv2.imshow("Live Attendance Engine", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                p_start = hm_to_dt(active.start_time, now)
                p_end = hm_to_dt(active.end_time, now)
                grace = active.grace_minutes or default_grace
                cutoff_dt = p_start + timedelta(minutes=grace)
                sess = AttendanceSession.query.filter_by(
                    session_date=now.strftime("%Y-%m-%d"),
                    schedule_id=active.schedule_id).first()
                if not sess:
                    sess = AttendanceSession(
                        session_date=now.strftime("%Y-%m-%d"),
                        schedule_id=active.schedule_id, subject_id=active.subject_id,
                        period_number=active.period_number, start_time=active.start_time,
                        end_time=active.end_time, cutoff_time=cutoff_dt.strftime("%H:%M"),
                        session_status='Running')
                    db.session.add(sess)
                    db.session.commit()
                    print(f"🟢 AUTO session created: Period {active.period_number}")
                if now >= p_end and sess.session_status == 'Running':
                    finalize_session(sess)
                subj = db.session.get(Subject, active.subject_id)
                period_label = f"P{active.period_number} {subj.subject_name if subj else ''}"
            else:
                sess = AttendanceSession.query.filter_by(session_status='Running').first()
                if not sess:
                    cv2.putText(frame, "No running session - start one from dashboard",
                                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    cv2.imshow("Live Attendance Engine", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                cutoff_dt = hm_to_dt(sess.cutoff_time, now)
                period_label = f"P{sess.period_number}"

            window_open = now <= cutoff_dt
            cv2.putText(frame,
                        f"{period_label} | Cutoff {sess.cutoff_time} | "
                        + ("ACCEPTING" if window_open and sess.session_status == 'Running' else "CLOSED"),
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0) if window_open else (0, 0, 255), 2)

            # ---------- detection ----------
            bbox, aligned = detect_face(frame)

            if bbox is not None and sess.session_status == 'Running':
                x, y, w, h = bbox
                quality_ok, reason = check_face_quality(frame, bbox)

                if not quality_ok:
                    label, color = f"Unclear face: {reason}", (0, 255, 255)
                    if time.time() - last_unclear[0] > 15:
                        last_unclear[0] = time.time()
                        log_event("UNCLEAR_FACE", None, sess.session_id, source_label)
                else:
                    emb = get_embedding(aligned)
                    best, best_score = None, -1
                    for f in enrolled:
                        sc = compare(emb, f["vector"])
                        if sc > best_score:
                            best, best_score = f, sc

                    if best_score >= MATCH_THRESHOLD:
                        existing = AttendanceRecord.query.filter_by(
                            session_id=sess.session_id, student_id=best["id"]).first()

                        if not existing and window_open:
                            db.session.add(AttendanceRecord(
                                session_id=sess.session_id, student_id=best["id"],
                                status='Present', detected_time=now.strftime("%H:%M:%S"),
                                method='Automatic'))
                            db.session.commit()
                            log_event("PRESENT", best, sess.session_id, source_label)
                            print(f"✅ PRESENT: {best['name']} ({best['roll']})")
                            set_banner("PRESENT - ATTENDANCE ACCEPTED",
                                       f"{best['name']} ({best['roll']})", (0, 255, 0))
                            label, color = f"{best['name']} -> PRESENT", (0, 255, 0)
                        elif not existing and not window_open:
                            db.session.add(AttendanceRecord(
                                session_id=sess.session_id, student_id=best["id"],
                                status='Late Not Accepted',
                                detected_time=now.strftime("%H:%M:%S"), method='Automatic'))
                            db.session.commit()
                            log_event("LATE_NOT_ACCEPTED", best, sess.session_id, source_label)
                            print(f"⏰ LATE: {best['name']} ({best['roll']})")
                            set_banner("LATE - NOT ACCEPTED",
                                       f"{best['name']} ({best['roll']})", (0, 165, 255))
                            label, color = f"{best['name']} -> LATE", (0, 165, 255)
                        elif existing and existing.status == 'Present':
                            label, color = f"{best['name']} - PRESENT (marked)", (0, 255, 0)
                        else:
                            label, color = f"{best['name']} - LATE (marked)", (0, 165, 255)
                    else:
                        label, color = "NOT ENROLLED / UNKNOWN", (0, 165, 255)
                        if time.time() - last_unknown[0] > 15:
                            last_unknown[0] = time.time()
                            log_event("UNKNOWN_FACE", None, sess.session_id, source_label)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, max(y - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # ---------- BIG confirmation banner for the student ----------
            if time.time() < banner["until"]:
                fh = frame.shape[0]
                cv2.rectangle(frame, (0, fh // 2 - 70), (frame.shape[1], fh // 2 + 70), (0, 0, 0), -1)
                cv2.putText(frame, banner["text"], (20, fh // 2 - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, banner["color"], 2)
                cv2.putText(frame, banner["sub"], (20, fh // 2 + 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("Live Attendance Engine", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

