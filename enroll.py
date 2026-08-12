import os
import sys
import time

import cv2

from app import app
from backend.models import FaceEmbedding, Student, db
from backend.services.face_engine import check_face_quality, detect_face, get_embedding
from config import STATIC_FACES_DIR

def available_cameras():
    cams = []
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                cams.append(i)
        cap.release()
    return cams

def main():
    if len(sys.argv) < 2:
        print("Usage:  python enroll.py <roll_no> [camera_index]")
        return

    roll_no = sys.argv[1]
    cams = available_cameras()
    if not cams:
        print("❌ No camera found.")
        return
    cam_index = int(sys.argv[2]) if len(sys.argv) > 2 else cams[0]

    STATIC_FACES_DIR.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db.create_all()
        student = Student.query.filter_by(roll_no=roll_no).first()
        if not student:
            print(f"❌ Student {roll_no} not found. Run sync first.")
            return

        print(f"🎯 Enrolling: {student.student_name} ({student.roll_no})")
        print("Keys: 'c' = capture | 's' = switch camera | 'q' = quit")

        cap = cv2.VideoCapture(cam_index)
        done_until = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            bbox, aligned = detect_face(frame)
            if aligned is not None:
                quality_ok, reason = check_face_quality(frame, bbox)
            else:
                quality_ok, reason = False, "No face"

            if aligned is not None:
                x, y, w, h = bbox
                if quality_ok:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, "Good quality - press 'c' to capture",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.putText(frame, f"Unclear face: {reason}",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            else:
                cv2.putText(frame, "No face - look at the camera",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # DONE banner after successful capture
            if time.time() < done_until:
                cv2.putText(frame, "DONE! Face enrolled successfully",
                            (frame.shape[1] // 2 - 230, frame.shape[0] // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.putText(frame, f"{student.student_name} | {student.roll_no}",
                        (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Camera {cam_index} | 'c' capture | 's' switch | 'q' quit",
                        (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Enrollment Station", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and len(cams) > 1:
                cam_index = cams[(cams.index(cam_index) + 1) % len(cams)]
                cap.release()
                cap = cv2.VideoCapture(cam_index)
                print(f"🔄 Switched to camera {cam_index}")
            elif key == ord('c'):
                if aligned is None:
                    print("❌ No face in frame.")
                elif not quality_ok:
                    print(f"❌ Face unclear: {reason}")
                else:
                    embedding = get_embedding(aligned)

                    # Save small cropped face photo for dashboard display
                    cv2.imwrite(str(STATIC_FACES_DIR / f"{student.roll_no}.jpg"), aligned)

                    FaceEmbedding.query.filter_by(student_id=student.student_id).update({"is_active": False})
                    db.session.add(FaceEmbedding(
                        student_id=student.student_id,
                        embedding=",".join(map(str, embedding))))
                    student.enrollment_status = "Enrolled"
                    db.session.commit()

                    done_until = time.time() + 2.5
                    print(f"✅ {student.student_name} enrolled! Photo saved.")

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()