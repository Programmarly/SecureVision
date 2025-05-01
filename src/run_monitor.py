# run_monitor.py
from services.folder_monitor import VideoFolderMonitor
from services.queue_worker import start_frame_consumers
import asyncio
from app import websocket_broadcast  

BASE_PATH = "data"


