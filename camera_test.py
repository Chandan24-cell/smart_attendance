import cv2

def check_camera(index):
    """Test if a camera works at this index."""
    cap = cv2.VideoCapture(index)
    ok = cap.isOpened()
    if ok:
        ret, frame = cap.read()
        ok = ret
    cap.release()
    return ok

# ---------- Detect all available cameras ----------
print("Scanning for cameras...")
available = [i for i in range(3) if check_camera(i)]

if not available:
    print("❌ No working camera found. Check macOS camera permissions.")
    exit(1)

print(f"✅ Available cameras detected: {available}")
print("   (Usually: 0 = MacBook built-in, 1 = USB webcam)")

current = 0
cap = cv2.VideoCapture(available[current])

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame.")
        break

    # On-screen labels
    cv2.putText(frame, f"Active Camera Index: {available[current]}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, "Press 'c' = switch camera | 'q' = quit",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    cv2.imshow("Smart Attendance - Camera Switch Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        # Switch to next available camera
        current = (current + 1) % len(available)
        cap.release()
        cap = cv2.VideoCapture(available[current])
        print(f"🔄 Switched to camera index {available[current]}")

cap.release()
cv2.destroyAllWindows()
print("Camera closed safely.")