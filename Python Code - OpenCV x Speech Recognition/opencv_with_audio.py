import cv2
import mediapipe as mp
import requests
import time
import threading
import speech_recognition as sr

ESP_IP = "http://172.20.10.2/"  # Replace with your ESP8266 IP address

# === Shared State ===
updated_states = {}
prev_states = {8: None, 12: None, 16: None, 20: None, 4: None}
lock = threading.Lock()

# === Finger Mapping ===
finger_name_map = {
    "thumb": 4,
    "index": 8,
    "middle": 12,
    "ring": 16,
    "pinky": 20,
}

# === Hand Gesture Function ===
def is_finger_closed(landmarks, finger):
    if finger == 4:
        return landmarks[finger].x < landmarks[finger - 1].x
    return landmarks[finger].y > landmarks[finger - 2].y

# === ESP8266 Send Function ===
def send_to_esp(changes):
    command = "&".join([f"F{finger}={state}" for finger, state in changes.items()])
    full_url = f"{ESP_IP}?{command}"
    print("Sending:", full_url)
    try:
        response = requests.get(full_url, timeout=3)
        if response.status_code == 200:
            print("✅ Data sent successfully")
        else:
            print("⚠️ ESP8266 responded with status:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("❌ Failed to send data:", e)

# === Hand Tracking Thread ===
def hand_tracking_loop():
    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

    global updated_states

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cqv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        local_changes = {}

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                for finger in prev_states:
                    is_closed = is_finger_closed(landmarks, finger)
                    if prev_states[finger] is None or prev_states[finger] != is_closed:
                        prev_states[finger] = is_closed
                        local_changes[finger] = "Closed" if is_closed else "Open"

        # Update shared state and send
        if local_changes:
            with lock:
                updated_states.update(local_changes)
            send_to_esp(local_changes)
            time.sleep(0.2)

        cv2.imshow("Hand Gesture Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# === Voice Command Thread ===
def voice_command_loop():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.2
    mic = sr.Microphone(device_index=14)  # Use the correct device index for your mic

    print("🎙️ Voice control ready. Say 'stop program' to exit.")

    while True:
        with mic as source:
            print("\n🎤 Listening for voice command...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                audio = recognizer.listen(source, timeout=5)
            except sr.WaitTimeoutError:
                print("⏱️ No voice detected, retrying...")
                continue

        try:
            command = recognizer.recognize_google(audio)
            print("🗣️ You said:", command)

            if "stop program" in command.lower():
                print("🛑 Voice command to stop detected. Exiting.")
                break

            words = command.lower().split()
            for name, index in finger_name_map.items():
                if name in words:
                    if "down" in words or "close" in words:
                        with lock:
                            updated_states[index] = "Closed"
                        send_to_esp({index: "Closed"})
                    elif "up" in words or "open" in words:
                        with lock:
                            updated_states[index] = "Open"
                        send_to_esp({index: "Open"})
                    break

        except sr.UnknownValueError:
            print("🤖 Couldn't understand what you said.")
        except sr.RequestError as e:
            print(f"🚫 API error: {e}")

# === Run Threads ===
hand_thread = threading.Thread(target=hand_tracking_loop)
voice_thread = threading.Thread(target=voice_command_loop)

hand_thread.start()
voice_thread.start()

hand_thread.join()
voice_thread.join()

print("✅ Program finished.")
