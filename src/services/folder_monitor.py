import os
import cv2
import numpy as np
from watchdog.events import FileSystemEventHandler
from services.severity_utils import compute_severity
from services.violence_inference import ViolenceClassifier
import time
import yagmail
from datetime import datetime
import pytz


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


    @staticmethod
    def shoot_email(
        email: str,
        folder_name: str,
        violence_label: str,
        violence_confidence: float,
        severity_score: float,
        severity_level: str
    ):
        # Format confidence and score as percentages
        confidence_percent = f"{violence_confidence}%"
        severity_percent = f"{severity_score}%"
        
        # Current date and time
        timezone = pytz.timezone("Asia/Kolkata")  # or your desired timezone
        current_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        
        # Email subject
        subject = f"Violence Detection Alert - {severity_level} severity detected"
        
        # HTML email content
        html_content = f"""
<html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; text-align: center;">
        <div style="max-width: 650px; margin: 0 auto; background: linear-gradient(to bottom right, #ffffff, #f9fbfd); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.12); overflow: hidden;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #d9534f, #c9302c); color: white; padding: 20px 25px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">🚨 Violence Detection Alert</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 25px;">
                <!-- Timestamp -->
                <div style="text-align: center; font-size: 14px; color: #555; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
                    <strong>Time of detection:</strong> {timezone} {current_time}
                </div>
                
                <!-- Summary Title -->
                <div style="text-align: center; margin-bottom: 20px; font-size: 18px; color: #333; font-weight: bold;">
                    📊 Detection Summary
                </div>
                
                <!-- Summary Table -->
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <tr style="background-color: #17a2b8; color: white;">
                        <th style="padding: 12px 15px; text-align: left; width: 40%;">Parameter</th>
                        <th style="padding: 12px 15px; text-align: left;">Value</th>
                    </tr>
                    <tr style="background-color: #f2f7f9;">
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;"><strong>📁 Location Detected:</strong></td>
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;">{folder_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;"><strong>⚠ Violence detected:</strong></td>
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;">{violence_label}</td>
                    </tr>
                    <tr style="background-color: #f2f7f9;">
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;"><strong>🔍 Confidence level:</strong></td>
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;">{confidence_percent}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;"><strong>🔥 Severity score:</strong></td>
                        <td style="padding: 10px 15px; border-bottom: 1px solid #e9ecef;">{severity_percent} / 100</td>
                    </tr>
                    <tr style="background-color: #f2f7f9;">
                        <td style="padding: 10px 15px;"><strong>🚦 Severity level:</strong></td>
                        <td style="padding: 10px 15px; font-weight: bold; color: {('#d9534f' if severity_level.lower() == 'high' else '#f0ad4e' if severity_level.lower() == 'medium' else '#5bc0de')};">{severity_level}</td>
                    </tr>
                </table>
                
                <!-- Actions -->
                <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin-bottom: 20px; border-radius: 4px; text-align: left;">
                    <strong style="font-size: 16px; display: block; margin-bottom: 10px;">✅ Recommended Actions</strong>
                    <ul style="padding-left: 18px; margin: 8px 0 0 0; font-size: 14px;">
                        <li style="margin-bottom: 8px;">🔍 Review the potential risk at: <strong>{folder_name}</strong></li>
                        <li style="margin-bottom: 8px;">🚨 Take appropriate action based on severity level</li>
                        <li style="margin-bottom: 8px;">📞 Contact the security team if necessary</li>
                    </ul>
                </div>
                
                <!-- Footer -->
                <div style="font-size: 12px; color: #6c757d; text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
                    This is an automated message. Please do not reply directly to this email.
                </div>
            </div>
        </div>
    </body>
</html>
"""        
        # Initialize yagmail
        yag = yagmail.SMTP("noahipynb@gmail.com", "jetn yxxe jvks noti")
        
        # Send email
        yag.send(
            to=email+'@gmail.com',
            subject=subject,
            contents=html_content
        )

    def process_frame(self, frame_path):
        folder_name = os.path.basename(os.path.dirname(frame_path))
        email = os.path.basename(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(frame_path)))))
    
        
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
                if(violence_label != "Normal Videos" and severity_level in ["High", "Critical","Medium"]):
                    # Send email alert
                    self.shoot_email(
                        email=email,
                        folder_name=folder_name,
                        violence_label=violence_label,
                        violence_confidence=violence_confidence,
                        severity_score=severity_score,
                        severity_level=severity_level
                    )
                self.websocket_broadcast(log_message)

            self.prev_keypoints[folder_name] = new_keypoints

        self.prev_frames[folder_name] = frame

        try:
            os.remove(frame_path)
        except Exception:
            pass  # Silently ignore deletion errors
