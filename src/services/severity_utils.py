import cv2
import numpy as np
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def compute_optical_flow(prev_frame, curr_frame):
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    return np.mean(magnitude)

def compute_frame_difference(prev_frame, curr_frame):
    diff = cv2.absdiff(prev_frame, curr_frame)
    return np.mean(diff)

def detect_aggressive_poses(frame, prev_keypoints=None):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)
    
    if results.pose_landmarks:
        keypoints = np.array([[lm.x, lm.y] for lm in results.pose_landmarks.landmark])
        movement_speed = np.linalg.norm(keypoints - prev_keypoints) if prev_keypoints is not None else 0
        return movement_speed, keypoints

    return 0, None

def compute_severity(prev_frame, curr_frame, prev_keypoints):
    if prev_frame is None:
        return 0, "Low", None
    
    motion_intensity = compute_optical_flow(prev_frame, curr_frame)
    frame_diff_intensity = compute_frame_difference(prev_frame, curr_frame)
    pose_aggression, new_keypoints = detect_aggressive_poses(curr_frame, prev_keypoints)

    severity_score = (motion_intensity * 0.5) + (frame_diff_intensity * 0.3) + (pose_aggression * 0.2)
    severity_score = np.clip(severity_score * 10, 0, 100)

    if severity_score >= 60:
        severity_level = "High"
    elif severity_score >= 25:
        severity_level = "Medium"
    else:
        severity_level = "Low"

    return severity_score, severity_level, new_keypoints
