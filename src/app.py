import shutil
import cv2
import os
import time
import threading
import atexit
from watchdog.observers import Observer
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from services.payload_for_register import PayloadForRegister
from services.folder_monitor import VideoFolderMonitor
import asyncio
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from fastapi import WebSocket, WebSocketDisconnect


app = FastAPI()

BASE_PATH = "data"  # Centralized base folder path
observer = Observer()  # Global observer instance
websocket_clients = set()  # Track connected WebSocket clients



def create_folder(email, cctv_names):
    """Creates user folder and subfolders for each CCTV feed."""
    email = email.split("@")[0]  # Extract username from email
    user_folder = os.path.join(BASE_PATH, email, "videos")
    
    os.makedirs(user_folder, exist_ok=True)

    for cctv_name in cctv_names:
        cctv_folder = os.path.join(user_folder, cctv_name.replace(" ", "").lower())
        os.makedirs(cctv_folder, exist_ok=True)

    print(f"Folder structure created for {email}")

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    print("WebSocket client connected.")

    try:
        while True:
            await websocket.receive_text()  # Keeps connection alive
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        print("WebSocket client disconnected.")


@app.post("/upload_data")
async def upload_data(payload: PayloadForRegister):
    """API endpoint to register a user, create directories, and start monitoring CCTV feeds."""
    email = payload.email
    cctv_names = payload.cctv_names  # Now a list of strings

    # Create folders for each CCTV feed
    create_folder(email, cctv_names)

    return JSONResponse(content={"message": "CCTV feeds registered successfully", "email": email, "cctv_feeds": cctv_names})


@app.get("/delete_data")
async def delete_data(email: str):
    """API endpoint to delete a user's data."""
    email = email.split("@")[0]
    user_folder = os.path.join(BASE_PATH, email)

    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
        print(f"Deleted: {user_folder}")
        return JSONResponse(content={"message": "Data deleted successfully"})
    
    return JSONResponse(content={"message": "Data not found"})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy"})


def start_monitoring():
    """Starts the folder monitoring for all existing user folders."""
    print("Starting monitoring")
    for user_folder in os.listdir(BASE_PATH):
        user_path = os.path.join(BASE_PATH, user_folder, "videos")
        if os.path.isdir(user_path):
            print(f"Monitoring folder: {user_path}")
            event_handler = VideoFolderMonitor(BASE_PATH, lambda message: asyncio.run(websocket_broadcast(message)))
            observer.schedule(event_handler, user_path, recursive=True)


    # Monitor existing user folders
    for user_folder in os.listdir(BASE_PATH):
        user_path = os.path.join(BASE_PATH, user_folder, "videos")
        if os.path.isdir(user_path):
            print(f"Monitoring folder: {user_path}")
            observer.schedule(event_handler, user_path, recursive=True)

    observer.start()
    print("Folder monitoring started.")

async def websocket_broadcast(message: str):
    disconnected_clients = []
    for client in websocket_clients:
        try:
            await client.send_text(message)
        except WebSocketDisconnect:
            disconnected_clients.append(client)

    for dc in disconnected_clients:
        websocket_clients.remove(dc)


# Run monitoring when the app starts
def run_monitoring():
    monitoring_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitoring_thread.start()


# Ensure the observer stops properly on exit
def stop_monitoring():
    observer.stop()
    observer.join()


# Start monitoring when the script runs
run_monitoring()
atexit.register(stop_monitoring)  # Cleanup observer on shutdown
