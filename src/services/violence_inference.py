import numpy as np
import cv2
from tensorflow.keras.models import load_model

class ViolenceClassifier:
    def __init__(self, model_path="model/2d_cnn_densenet_updated.h5"):
        try:
            self.model = load_model(model_path)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model from {model_path}: {e}")
            self.model = None
        self.class_labels = [
            "Abuse", "Robbery", "Arson", "Assault", "Burglary",
            "Explosion", "Fighting", "Normal Videos", "Road Accidents",
            "Robbery", "Shooting", "Shoplifting", "Stealing", "Vandalism"
        ]
    
    def preprocess_frame(self, frame):
        """Resize, normalize and prepare a frame for prediction."""
        if frame is None:
            print("❌ Error: Received None as frame input for preprocessing.")
            return None

        # print(f"Preprocessing frame with shape: {frame.shape}")  # Debugging line
        img = cv2.resize(frame, (64, 64))  # Match model input size (64x64)
        img = img / 255.0  # Normalize pixel values to [0, 1]
        img = np.expand_dims(img, axis=0)  # Add batch dimension for model input
        # print(f"Preprocessed frame shape: {img.shape}")  # Debugging line
        return img

    def predict(self, frame):
        """Predict violence class and confidence for a given frame."""
        if self.model is None:
            print("❌ Model is not loaded. Cannot make predictions.")
            return "Error", 0.0

        processed_frame = self.preprocess_frame(frame)
        if processed_frame is None:
            return "Error", 0.0

        try:
            preds = self.model.predict(processed_frame)
            class_index = np.argmax(preds)  # Get index of highest probability
            confidence = np.max(preds)  # Get the highest confidence value
            label = self.class_labels[class_index]  # Get corresponding class label
            # print(f"Predicted: {label} with confidence: {confidence:.2f}")  # Debugging line
            return label, confidence
        except Exception as e:
            print(f"Error during prediction: {e}")
            return "Error", 0.0
