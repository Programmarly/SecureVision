import os
import cv2
import numpy as np
from watchdog.events import FileSystemEventHandler
from services.severity_utils import compute_severity
from services.violence_inference import ViolenceClassifier
import time

class VideoFolderMonitor(FileSystemEventHandler):
    def __init__(self, base_folder, websocket_broadcast):
        self.base_folder = base_folder
        self.prev_frames = {}
        self.prev_keypoints = {}
        self.violence_classifier = ViolenceClassifier()
        self.processed_files = set()  # Track processed files to avoid duplicates
        self.websocket_broadcast = websocket_broadcast  # 👈 new callback


    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith((".jpg", ".png")):
            # Check if file exists before processing
            if os.path.exists(event.src_path):
                print(f"New frame detected: {event.src_path}")
                self.process_frame(event.src_path)
            # else:
                # print(f"File detection event received but file not found: {event.src_path}")

    def process_frame(self, frame_path):
        folder_name = os.path.basename(os.path.dirname(frame_path))
        email = os.path.basename(os.path.basename(os.path.dirname(os.path.dirname(frame_path))))
    
        
        frame = None

        # Wait until the file is ready to be read (retry loop)
        for attempt in range(5):
            if not os.path.exists(frame_path):
                return

            frame = cv2.imread(frame_path)
            if frame is not None:
                break
            else:
                time.sleep(0.1)  # Wait 100ms and retry

        if frame is None:
            return  # Exit if the frame could not be read

        # Violence Prediction
        violence_label, violence_confidence = self.violence_classifier.predict(frame)

        # Apply confidence threshold - if below 0.51, treat as "Normal Videos"
        if violence_confidence < 0.51:
            violence_label = "Normal Videos"
            violence_confidence = 1.0 - violence_confidence  # Optional: adjust confidence for normal videos

        # Severity Calculation
        prev_frame = self.prev_frames.get(folder_name)
        prev_keypoints = self.prev_keypoints.get(folder_name)

        if prev_frame is not None:
            severity_score, severity_level, new_keypoints = compute_severity(prev_frame, frame, prev_keypoints)

            # Only log if violence is detected or severity is high/critical
            if violence_label != "Normal Videos" or severity_level in ["High", "Critical"]:
                log_time = time.strftime("%Y-%m-%d %H:%M:%S")
                # print(f"[{log_time}] CCTV: {folder_name} | Violence: {violence_label} ({violence_confidence:.2f}) | Severity: {severity_score:.2f} ({severity_level})")
                log_message = f"[{log_time}] Email: {email}@gmail.com | CCTV: {folder_name} | Violence: {violence_label} ({violence_confidence:.2f}) | Severity: {severity_score:.2f} ({severity_level})"
                print(log_message)
                self.websocket_broadcast(log_message)

            self.prev_keypoints[folder_name] = new_keypoints

        self.prev_frames[folder_name] = frame

        try:
            os.remove(frame_path)
        except Exception:
            pass  # Silently ignore deletion errors
