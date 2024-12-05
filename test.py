import cv2
import dlib
import pyautogui
import pygetwindow as gw  # Library to bring the required window to the front
import win32gui
import win32con
from scipy.spatial import distance
import time

# Initialize face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
cap = cv2.VideoCapture(0)
pyautogui.FAILSAFE = False

# Function to compute Eye Aspect Ratio (EAR)
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Function to bring a window to the front based on a partial title match
def bring_window_to_front_partial_match(partial_title):
    windows = gw.getWindowsWithTitle(partial_title)
    if windows:
        window = windows[0]
        window.restore()  # Restore if minimized
        window.activate()  # Bring to front
        print(f"Activated window with partial title match: {window.title}")
    else:
        print(f"No window found with title containing '{partial_title}'")

# Constants and default settings
EAR_THRESHOLD = 0.16  # Default threshold; adjusted during calibration
DEFAULT_EAR_THRESHOLD = 0.16  # Fallback threshold if calibration fails
BLINK_FRAMES = 3  # Frames for moving average
CALIBRATION_FRAMES = 50  # Frames for calibration
blink_interval = 1.0  # Interval between blinks
MIN_WINK_DURATION = 3  # Minimum frames for an eye closure to be considered a wink

# Variables for tracking state
ear_values = []
calibration_values = []
last_blink_time = time.time()
calibrated = False
closed_eye_frames = 0  # Track consecutive frames with closed eyes

# Calibration phase to determine EAR threshold for open eyes
print("Please keep your eyes open for calibration...")
for i in range(CALIBRATION_FRAMES):
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from webcam")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    if faces:
        face = faces[0]  # Assuming only one face
        landmarks = predictor(gray, face)
        left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
        right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]
        
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear_avg = (left_ear + right_ear) / 2.0
        calibration_values.append(ear_avg)
        
        cv2.putText(frame, "Calibration in Progress", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow('Calibration', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Set threshold based on calibration or fallback to default
if calibration_values:
    EAR_THRESHOLD = sum(calibration_values) / len(calibration_values) * 0.8
    print(f"Calibrated EAR threshold: {EAR_THRESHOLD:.2f}")
else:
    EAR_THRESHOLD = DEFAULT_EAR_THRESHOLD
    print(f"Calibration failed. Using default EAR threshold: {EAR_THRESHOLD}")

cap.release()
cv2.destroyAllWindows()

# Start video processing
cap = cv2.VideoCapture(0)
target_window_partial_title = "Part_of_Target_Window_Title"  # Replace with part of the title

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from webcam")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    if faces:
        for face in faces:
            landmarks = predictor(gray, face)
            left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
            right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]
            
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear_avg = (left_ear + right_ear) / 2.0
            
            # Moving average to smooth out EAR values
            ear_values.append(ear_avg)
            if len(ear_values) > BLINK_FRAMES:
                ear_values.pop(0)
            avg_ear = sum(ear_values) / len(ear_values)

            # Check if eyes are closed
            if avg_ear < EAR_THRESHOLD:
                closed_eye_frames += 1  # Count consecutive frames with closed eyes
            else:
                # Reset if eyes open
                closed_eye_frames = 0

            # Trigger wink action if eyes closed for minimum wink duration
            current_time = time.time()
            if closed_eye_frames >= MIN_WINK_DURATION and current_time - last_blink_time >= blink_interval:
                # Bring the target window to the foreground and perform the click
                bring_window_to_front_partial_match(target_window_partial_title)
                
                # Perform double click after bringing to the front
                pyautogui.doubleClick()
                last_blink_time = current_time
                closed_eye_frames = 0  # Reset counter after a wink

            cv2.putText(frame, f'Eye State: {"Closed" if avg_ear < EAR_THRESHOLD else "Open"}',
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow('Eye Tracking', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
