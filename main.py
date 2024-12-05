import cv2
import mediapipe as mp
import pyautogui
import pygame
import time
from scipy.spatial import distance
from collections import deque
import speech_recognition as sr
from gtts import gTTS
import threading
import os

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp.solutions.face_mesh.FaceMesh(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Screen parameters
screen_width, screen_height = pyautogui.size()
pyautogui.FAILSAFE = False

# Thresholds
EAR_THRESHOLD = 0.2   # Threshold for eye closure detection
CLOSED_EAR_DURATION = 0.15  # Minimum duration for confirmed eye closure (for wink detection)
mouse_speed = 0.5  # Reduced mouse speed for smoother movement

# State for wink detection and mouse movement
left_eye_closed = False
right_eye_closed = False
last_blink_time = time.time()
last_eye_pos = None
mouse_paused = False

# Calculate Eye Aspect Ratio (EAR)
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# Play audio feedback
def play_feedback(text):
    try:
        tts = gTTS(text, lang="ar")
        tts.save("feedback.mp3")
        
        pygame.mixer.init()
        pygame.mixer.music.load("feedback.mp3")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        os.remove("feedback.mp3")
    except Exception as e:
        print(f"Error playing sound: {e}")

# Voice command listener
def listen_for_command():
    recognizer = sr.Recognizer()
    play_feedback("النظام جاهز للاستماع")
    while True:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)  # Faster adaptation
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=2)
                command = recognizer.recognize_google(audio, language="ar")
                if command.lower() == "انقر":
                    pyautogui.click()
                    play_feedback("تم النقر")
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError:
                print("API unavailable")
            except Exception as e:
                print(f"Audio Error: {e}")

# Start voice command listener in a separate thread
command_thread = threading.Thread(target=listen_for_command)
command_thread.daemon = True
command_thread.start()

# Safely move the mouse
def move_mouse_safely(new_x, new_y):
    new_x = min(max(10, new_x), screen_width - 10)
    new_y = min(max(10, new_y), screen_height - 10)
    pyautogui.moveTo(new_x, new_y, duration=0.1)  # Slow down for smoother movement

# Start video capture
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame for face and eye tracking
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Get eye landmarks
            left_eye_points = [face_landmarks.landmark[i] for i in [33, 133, 160, 159, 144, 153]]
            right_eye_points = [face_landmarks.landmark[i] for i in [362, 263, 387, 386, 373, 380]]

            # Calculate EAR for both eyes
            left_ear = eye_aspect_ratio([(p.x, p.y) for p in left_eye_points])
            right_ear = eye_aspect_ratio([(p.x, p.y) for p in right_eye_points])

            # Detect if each eye is closed or open for wink detection
            current_time = time.time()
            if left_ear < EAR_THRESHOLD:
                left_eye_closed = True
            elif left_eye_closed and left_ear >= EAR_THRESHOLD:
                # Left eye was closed and now opened (wink detected)
                pyautogui.click()
                play_feedback("تم النقر بسبب غمزة العين اليسرى")
                left_eye_closed = False
                last_blink_time = current_time

            if right_ear < EAR_THRESHOLD:
                right_eye_closed = True
            elif right_eye_closed and right_ear >= EAR_THRESHOLD:
                # Right eye was closed and now opened (wink detected)
                pyautogui.click()
                play_feedback("تم النقر بسبب غمزة العين اليمنى")
                right_eye_closed = False
                last_blink_time = current_time

            # Mouse movement based on eye direction
            if last_eye_pos is not None and not mouse_paused:
                dx = sum(p.x for p in left_eye_points + right_eye_points) - sum(p[0] for p in last_eye_pos)
                dy = sum(p.y for p in left_eye_points + right_eye_points) - sum(p[1] for p in last_eye_pos)
                # Smoother mouse movement calculation
                new_x = pyautogui.position()[0] + dx * mouse_speed * screen_width
                new_y = pyautogui.position()[1] + dy * mouse_speed * screen_height
                move_mouse_safely(new_x, new_y)

            # Update last eye position
            last_eye_pos = [(p.x, p.y) for p in left_eye_points + right_eye_points]
            mp_drawing.draw_landmarks(frame, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)

    # Display EAR status for debugging
    cv2.putText(frame, f'Left Eye: {"Closed" if left_eye_closed else "Open"}', 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f'Right Eye: {"Closed" if right_eye_closed else "Open"}', 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow('Eye Tracking', frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera and close window
cap.release()
cv2.destroyAllWindows()
