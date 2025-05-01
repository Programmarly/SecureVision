import cv2
import os
import time
import threading
from services.queue_worker import frame_queue

def extract_and_save_frames(video_path, output_folder, frame_interval=30, delay=0.1):
    """
    Extracts frames from a video and saves them periodically to simulate real-time streaming.

    :param video_path: Path to the video file.
    :param output_folder: Directory where frames will be saved.
    :param frame_interval: Number of frames to skip between extractions.
    :param delay: Time delay (in seconds) between saving frames to simulate real-time.
    """
    os.makedirs(output_folder, exist_ok=True)  # Ensure output directory exists
    
    print(f"Starting extraction to {output_folder}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Unable to open video file {video_path}")
        return

    frame_count = 0
    saved_frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        if frame_count % frame_interval == 0:  # Save every `frame_interval` frames
            frame_filename = os.path.join(output_folder, f"frame_{saved_frame_count:05d}.jpg")

            cv2.imwrite(frame_filename, frame)  # Save frame
            frame_queue.put(frame_filename, timeout=2)
            print(f"Saved: {frame_filename}")

            saved_frame_count += 1
            time.sleep(delay)  # Simulate real-time delay

        frame_count += 1

    cap.release()
    print(f"Frame extraction completed for {output_folder}.")

# Create threads for each extraction task
def run_concurrent_extractions():
    video_path = "/Users/harshkhanpara/workspace/capstone/SecureVision/src/uploads/1032211147/Fighting014_x264A.mp4"  # Update with your video path
    output_folder = "/Users/harshkhanpara/workspace/capstone/SecureVision/src/data/1032211147/videos/fighting014_x264a"
    # output_folder1 = "E:\\Capstone\\src\\data\\harshit\\videos\\office"
    extract_and_save_frames(
        video_path,
        output_folder,
        frame_interval=30,
        delay=0.7
    )
    # Create thread for first extraction
    # thread1 = threading.Thread(
    #     target=extract_and_save_frames,
    #     args=(video_path, output_folder, 30, 0.7)
    # )
    
    # Create thread for second extraction
    # thread2 = threading.Thread(
    #     target=extract_and_save_frames,
    #     args=(video_path, output_folder1, 20, 0.7)
    # )
    
    # Start both threads
    # thread1.start()
    # thread2.start()
    
    # Wait for both threads to complete
    # thread1.join()
    # thread2.join()
    
    print("All extractions completed.")

# Run the concurrent extraction
if __name__ == "__main__":
    run_concurrent_extractions()