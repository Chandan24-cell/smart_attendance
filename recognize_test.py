import cv2
from face_engine import detect_face, get_embedding, compare, MATCH_THRESHOLD
from models import db, Student, FaceEmbedding
from app import app

def load_enrolled_faces():
    """Load all active face fingerprints from the database."""
    faces = []
    for emb in FaceEmbedding.query.filter_by(is_active=True).all():
        student = db.session.get(Student, emb.student_id)
        if student:
            vector = list(map(float, emb.embedding.split(",")))
            faces.append({"name": student.student_name,
                          "roll": student.roll_no,
                          "vector": vector})
    return faces

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
    with app.app_context():
        enrolled = load_enrolled_faces()

    print(f"📚 Loaded {len(enrolled)} enrolled face(s) from database.")
    if not enrolled:
        print("❌ No enrolled faces. Run: python enroll.py <roll_no>")
        return

    cams = available_cameras()
    if not cams:
        print("❌ No camera found.")
        return

    cam_index = cams[0]
    cap = cv2.VideoCapture(cam_index)
    print("Keys: 's' = switch camera | 'q' = quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        bbox, aligned = detect_face(frame)

        if aligned is not None:
            emb = get_embedding(aligned)

            best = None
            best_score = -1
            for f in enrolled:
                score = compare(emb, f["vector"])
                if score > best_score:
                    best_score = score
                    best = f

            x, y, w, h = bbox
            if best_score >= MATCH_THRESHOLD:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label = f"{best['name']} ({best['roll']})  score:{best_score:.2f}"
                color = (0, 255, 0)
            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
                label = f"Unknown person  score:{best_score:.2f}"
                color = (0, 165, 255)

            cv2.putText(frame, label, (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            cv2.putText(frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.putText(frame, "'s' switch camera | 'q' quit",
                    (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("Recognition Test", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s') and len(cams) > 1:
            cam_index = cams[(cams.index(cam_index) + 1) % len(cams)]
            cap.release()
            cap = cv2.VideoCapture(cam_index)
            print(f"🔄 Switched to camera {cam_index}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()