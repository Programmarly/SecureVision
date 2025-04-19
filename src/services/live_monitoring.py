import cv2
import os
import time
import threading

def capture_frames_from_ip_webcam(ip_url, output_folder, frame_interval=30, delay=0.1):
    """
    Captures frames from an IP webcam stream and saves them to a directory.

    :param ip_url: URL of the IP webcam stream (e.g., "http://<IP>:<PORT>/video").
    :param output_folder: Directory where frames will be saved.
    :param frame_interval: Number of frames to skip between extractions.
    :param delay: Time delay (in seconds) between saving frames.
    """
    os.makedirs(output_folder, exist_ok=True)

    print(f"Connecting to IP webcam at {ip_url}")
    cap = cv2.VideoCapture(ip_url)
    if not cap.isOpened():
        print(f"Error: Unable to connect to IP webcam at {ip_url}")
        return

    frame_count = 0
    saved_frame_count = 0

    print(f"Starting frame capture. Frames will be saved to {output_folder}")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read frame from IP webcam.")
            break

        if frame_count % frame_interval == 0:
            frame_filename = os.path.join(output_folder, f"frame_{saved_frame_count:05d}.jpg")
            cv2.imwrite(frame_filename, frame)
            print(f"Saved: {frame_filename}")
            saved_frame_count += 1
            time.sleep(delay)

        frame_count += 1

    cap.release()
    print(f"Frame capture completed. Frames saved in {output_folder}.")


# Launch the function in a separate thread
def start_capture_in_thread(ip_url, output_folder, frame_interval=30, delay=0.1):
    capture_thread = threading.Thread(
        target=capture_frames_from_ip_webcam,
        args=(ip_url, output_folder, frame_interval, delay),
        daemon=True  # Daemon thread will stop when main program exits
    )
    capture_thread.start()
    print("Capture thread started.")


