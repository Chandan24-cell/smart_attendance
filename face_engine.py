#The brain of AI
import cv2
import numpy as np

DETECTOR_MODEL = "face_models/face_detection_yunet.onnx"
RECOGNIZER_MODEL = "face_models/face_recognition_sface.onnx"

detector = cv2.FaceDetectorYN.create(DETECTOR_MODEL, "", (320, 320))
recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_MODEL, "")

MATCH_THRESHOLD = 0.363   # OpenCV SFace recommended cosine threshold

def detect_face(frame):
    """Find the largest face in the frame. Returns (bbox, aligned_face)."""
    h, w, _ = frame.shape
    detector.setInputSize((w, h))
    _, faces = detector.detect(frame)

    if faces is None:
        return None, None

    face = max(faces, key=lambda f: f[2] * f[3])   # largest face
    bbox = face[:4].astype(int)
    aligned = recognizer.alignCrop(frame, face)
    return bbox, aligned

def get_embedding(aligned_face):
    """Convert a face into a 128-number fingerprint (normalized)."""
    emb = recognizer.feature(aligned_face)
    emb = emb / np.linalg.norm(emb)
    return emb.flatten().tolist()

def compare(emb1, emb2):
    """Cosine similarity between two embeddings (higher = same person)."""
    a = np.array(emb1)
    b = np.array(emb2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def check_face_quality(frame, bbox):
    """Checks if the face is clear enough for enrollment."""
    x, y, w, h = bbox
    face = frame[y:y + h, x:x + w]
    if face.size == 0:
        return False, "Face lost"

    # 1. Size check (too far away)
    if w < 90 or h < 90:
        return False, "Too far - move closer"

    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

    # 2. Brightness check
    brightness = gray.mean()
    if brightness < 50:
        return False, "Too dark - improve lighting"
    if brightness > 220:
        return False, "Too bright - avoid direct light"

    # 3. Blur check (movement / out of focus)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < 50:
        return False, "Blurry - hold still"

    return True, "Good quality"