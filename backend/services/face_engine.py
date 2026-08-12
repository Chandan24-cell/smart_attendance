import cv2
import numpy as np
from config import FACE_DETECTOR_MODEL, FACE_RECOGNIZER_MODEL

# The face models are loaded once so the engine stays fast.
detector = cv2.FaceDetectorYN.create(FACE_DETECTOR_MODEL, "", (320, 320))
recognizer = cv2.FaceRecognizerSF.create(FACE_RECOGNIZER_MODEL, "")

MATCH_THRESHOLD = 0.363


def detect_face(frame):
    """Find the largest face in the frame and return aligned crop."""
    h, w, _ = frame.shape
    detector.setInputSize((w, h))
    _, faces = detector.detect(frame)

    if faces is None:
        return None, None

    face = max(faces, key=lambda f: f[2] * f[3])
    bbox = face[:4].astype(int)
    aligned = recognizer.alignCrop(frame, face)
    return bbox, aligned


def get_embedding(aligned_face):
    """Convert a face into a normalized 128-value fingerprint."""
    emb = recognizer.feature(aligned_face)
    emb = emb / np.linalg.norm(emb)
    return emb.flatten().tolist()


def compare(emb1, emb2):
    """Compute cosine similarity between two face embeddings."""
    a = np.array(emb1)
    b = np.array(emb2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def check_face_quality(frame, bbox):
    """Check if a detected face is clear enough for enrollment."""
    x, y, w, h = bbox
    face = frame[y:y + h, x:x + w]
    if face.size == 0:
        return False, "Face lost"

    if w < 90 or h < 90:
        return False, "Too far - move closer"

    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    brightness = gray.mean()
    if brightness < 50:
        return False, "Too dark - improve lighting"
    if brightness > 220:
        return False, "Too bright - avoid direct light"

    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < 50:
        return False, "Blurry - hold still"

    return True, "Good quality"
