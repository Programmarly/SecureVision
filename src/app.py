import shutil
import cv2
import os
import time
import threading
import atexit
from watchdog.observers import Observer
from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from services.payload_for_register import PayloadForRegister
from services.folder_monitor import VideoFolderMonitor
import asyncio
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from fastapi import WebSocket, WebSocketDisconnect
import json
from pydantic import BaseModel, field_validator, ValidationError
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from loader import extract_and_save_frames


app = FastAPI()

BASE_PATH = "data"  # Centralized base folder path
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
observer = Observer()  # Global observer instance
websocket_clients = set()  # Track connected WebSocket clients

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust based on your frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_folder(email, cctv_names):
    """Creates user folder and subfolders for each CCTV feed."""
    email = email.split("@")[0]  # Extract username from email
    user_folder = os.path.join(BASE_PATH, email, "videos")
    
    os.makedirs(user_folder, exist_ok=True)

    for cctv_name in cctv_names:
        cctv_folder = os.path.join(user_folder, cctv_name.replace(" ", "").lower())
        os.makedirs(cctv_folder, exist_ok=True)

    print(f"Folder structure created for {email}")

# @app.get("/start-loader/{email}")
# def async start_loader(email: str):
#     """Starts the loader for a specific user."""
#     email = email.split("@")[0]
#     threads = []
#     for file in files:
#         filename_wo_ext = os.path.splitext(file.filename)[0]
#         cctv_name = filename_wo_ext.lower().replace(" ", "_").replace("cctv_", "")

#         input_video_path = os.path.join(UPLOAD_DIR, file.filename)
#         output_frames_dir = os.path.join(
#             BASE_PATH,
#             email.split("@")[0],
#             "videos",
#             cctv_name,
#             "frames"
#         )
#         os.makedirs(output_frames_dir, exist_ok=True)

#         thread = threading.Thread(
#             target=extract_and_save_frames,
#             args=(input_video_path, output_frames_dir, 20, 0.7)
#         )
#         threads.append(thread)
#         thread.start()

#     for thread in threads:
#         thread.join()


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time logs."""

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
async def upload_data(
    email: str = Form(...),
    files: List[UploadFile] = File(...)
):
    print(f"Received email: {email}")
    print(f"Received files: {[file.filename for file in files]}")

    # Extract clean cctv names
    cctv_names_list = []
    for file in files:
        filename_wo_ext = os.path.splitext(file.filename)[0]
        cleaned_name = filename_wo_ext.lower().replace(" ", "_").replace("cctv_", "")
        cctv_names_list.append(cleaned_name)

    try:
        payload = PayloadForRegister(email=email, cctv_names=cctv_names_list)
    except ValidationError as e:
        return JSONResponse(content={"error": e.errors()}, status_code=422)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    saved_files = []
    
    # Split email and create path
    email_parts = email.split("@")[0]
    upload_dir = os.path.join(UPLOAD_DIR, email_parts)
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        upload_path = os.path.join(upload_dir, file.filename)
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)

    # Create per-user folder structure
    create_folder_structure(email, cctv_names_list)

    # Begin frame extraction into `data/<user>/videos/<cctv_name>/frames`
    # threads = []
    # for file in files:
    #     filename_wo_ext = os.path.splitext(file.filename)[0]
    #     cctv_name = filename_wo_ext.lower().replace(" ", "_").replace("cctv_", "")

    #     input_video_path = os.path.join(UPLOAD_DIR, file.filename)
    #     output_frames_dir = os.path.join(
    #         BASE_PATH,
    #         email.split("@")[0],
    #         "videos",
    #         cctv_name,
    #         "frames"
    #     )
    #     os.makedirs(output_frames_dir, exist_ok=True)

    #     thread = threading.Thread(
    #         target=extract_and_save_frames,
    #         args=(input_video_path, output_frames_dir, 20, 0.7)
    #     )
    #     threads.append(thread)
    #     thread.start()

    # for thread in threads:
    #     thread.join()

    return JSONResponse(content={
        "message": "Videos uploaded and frames extracted successfully.",
        "email": payload.email,
        "cctv_feeds": payload.cctv_names,
        "filenames": saved_files
    })


def create_folder_structure(email: str, cctv_names: List[str]):
    username = email.split("@")[0]
    base_path = os.path.join(BASE_PATH, username, "videos")

    for cctv in cctv_names:
        frames_path = os.path.join(base_path, cctv)
        os.makedirs(frames_path, exist_ok=True)

    print(f"[INFO] Created folders in {base_path}")


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
    #Create base folder if it doesn't exist
    os.makedirs(BASE_PATH, exist_ok=True)
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
