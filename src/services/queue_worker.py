# services/queue_worker.py
from queue import Queue
import threading

# Bounded queue to limit memory usage
frame_queue = Queue(maxsize=1000)

def start_frame_consumers(video_monitor, num_consumers=4):
    """
    Start multiple consumer threads to process frames from the queue.
    """
    for i in range(num_consumers):
        thread = threading.Thread(
            target=consume_frames,
            args=(video_monitor,),
            daemon=True
        )
        thread.start()
        print(f"[QueueWorker]  Started consumer thread-{i+1}")

def consume_frames(video_monitor):
    """
    Frame processing worker thread.
    """
    while True:
        frame_path = frame_queue.get()
        if frame_path is None:
            break  # Allow graceful shutdown
        try:
            video_monitor.process_frame(frame_path)
        except Exception as e:
            print(f"[QueueWorker]  Error processing {frame_path}: {e}")
