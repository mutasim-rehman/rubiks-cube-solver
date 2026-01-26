"""
Machine Learning Color Classifier
Classifies cube sticker colors using ML models.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from typing import List, Tuple, Dict, Optional
import cv2
import os
import pickle

class ColorClassifier:
    """
    ML-based color classifier for Rubik's cube stickers.
    Uses K-means clustering and color space analysis.
    Can be trained on custom data using KNN.
    """
    
    # Standard Rubik's cube colors (BGR format for OpenCV)
    CUBE_COLORS = {
        'R': (0, 0, 255),      # Red
        'G': (0, 255, 0),      # Green
        'B': (255, 0, 0),      # Blue
        'Y': (0, 255, 255),    # Yellow
        'O': (0, 165, 255),    # Orange
        'W': (255, 255, 255),  # White
    }
    
    # Color names for reference
    COLOR_NAMES = {
        'R': 'Red',
        'G': 'Green',
        'B': 'Blue',
        'Y': 'Yellow',
        'O': 'Orange',
        'W': 'White',
    }
    
    MODEL_FILE = "color_model.pkl"
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.knn = None
        self.trained = False
        self.load_model()
        
    def load_model(self):
        """Load trained model if available."""
        if os.path.exists(self.MODEL_FILE):
            try:
                with open(self.MODEL_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.knn = data['knn']
                    self.scaler = data['scaler']
                    self.trained = True
                print("Loaded trained color model.")
            except Exception as e:
                print(f"Failed to load model: {e}")

    def save_model(self):
        """Save trained model."""
        if self.trained and self.knn:
            try:
                with open(self.MODEL_FILE, 'wb') as f:
                    pickle.dump({
                        'knn': self.knn,
                        'scaler': self.scaler
                    }, f)
                print(f"Model saved to {self.MODEL_FILE}")
            except Exception as e:
                print(f"Failed to save model: {e}")

    def train_model(self, data_dir: str):
        """
        Train KNN model from collected data.
        data_dir: Directory containing subdirectories named by color code (R, G, B, etc.)
        """
        X = []
        y = []
        
        print("Training model from data...")
        
        for color_code in self.CUBE_COLORS.keys():
            color_dir = os.path.join(data_dir, color_code)
            if not os.path.exists(color_dir):
                continue
                
            for filename in os.listdir(color_dir):
                if not filename.endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                path = os.path.join(color_dir, filename)
                img = cv2.imread(path)
                if img is None:
                    continue
                    
                # Extract features
                features = self._extract_features(img)
                X.append(features)
                y.append(color_code)
        
        if len(X) < 6: # Need at least one sample per color ideally, but check minimal size
            print("Not enough training data found.")
            return
            
        X = np.array(X)
        y = np.array(y)
        
        # Train KNN
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.knn = KNeighborsClassifier(n_neighbors=3)
        self.knn.fit(X_scaled, y)
        self.trained = True
        
        self.save_model()
        print(f"Model trained on {len(X)} samples.")

    def _extract_features(self, image: np.ndarray) -> np.ndarray:
        """Extract color features from image."""
        # Get dominant color in BGR
        bgr = self._get_dominant_color(image)
        
        # Convert to HSV
        hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        
        # Convert to LAB (perceptually uniform)
        lab = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0][0]
        
        # Feature vector: B, G, R, H, S, V, L, A, B
        return np.concatenate([bgr, hsv, lab])

    def classify_color(self, sticker_image: np.ndarray) -> str:
        """
        Classify a single sticker's color.
        Returns color code: R, G, B, Y, O, or W
        """
        # If trained model exists, use it
        if self.trained and self.knn:
            features = self._extract_features(sticker_image)
            features_scaled = self.scaler.transform([features])
            return self.knn.predict(features_scaled)[0]
            
        # Fallback to heuristic method
        # Get dominant color in multiple color spaces
        bgr_color = self._get_dominant_color(sticker_image)
        
        # Convert to HSV for better color matching
        hsv_color = cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0]
        
        # Classify using distance in color space
        color_code = self._classify_by_distance(bgr_color, hsv_color)
        
        return color_code
    
    def _get_dominant_color(self, image: np.ndarray) -> Tuple[int, int, int]:
        """Get dominant color using K-means clustering."""
        # Reshape image to list of pixels
        pixels = image.reshape(-1, 3)
        
        # Remove black/very dark pixels (likely shadows or edges)
        brightness = np.sum(pixels, axis=1)
        pixels = pixels[brightness > 30]
        
        if len(pixels) == 0:
            return (128, 128, 128)  # Default gray
        
        # Use K-means to find dominant color
        kmeans = KMeans(n_clusters=1, random_state=42, n_init=10)
        kmeans.fit(pixels)
        dominant = kmeans.cluster_centers_[0]
        
        return tuple(map(int, dominant))
    
    def _classify_by_distance(self, bgr_color: Tuple[int, int, int], 
                             hsv_color: Tuple[int, int, int]) -> str:
        """
        Classify color by calculating distance to known cube colors.
        Uses both BGR and HSV color spaces for better accuracy.
        """
        min_distance = float('inf')
        best_color = 'W'  # Default to white
        
        bgr_color = np.array(bgr_color)
        hsv_color = np.array(hsv_color)
        
        for color_code, (b, g, r) in self.CUBE_COLORS.items():
            # Convert reference color to HSV
            ref_bgr = np.array([b, g, r])
            ref_hsv = cv2.cvtColor(np.uint8([[ref_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
            
            # Calculate weighted distance in both color spaces
            bgr_dist = np.linalg.norm(bgr_color - ref_bgr)
            hsv_dist = np.linalg.norm(hsv_color - ref_hsv)
            
            # Weight HSV more heavily (especially hue) for better color discrimination
            total_dist = 0.3 * bgr_dist + 0.7 * hsv_dist
            
            if total_dist < min_distance:
                min_distance = total_dist
                best_color = color_code
        
        return best_color
    
    def classify_face(self, face_image: np.ndarray) -> List[List[str]]:
        """
        Classify all stickers in a face (3x3 grid).
        Returns 3x3 array of color codes.
        """
        h, w = face_image.shape[:2]
        face_colors = []
        
        # Divide face into 3x3 grid
        cell_h, cell_w = h // 3, w // 3
        
        for i in range(3):
            row_colors = []
            for j in range(3):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                sticker = face_image[y1:y2, x1:x2]
                
                # Get center region to avoid edge artifacts
                center_y, center_x = sticker.shape[0] // 2, sticker.shape[1] // 2
                margin = min(sticker.shape[0], sticker.shape[1]) // 4
                center_sticker = sticker[
                    center_y - margin:center_y + margin,
                    center_x - margin:center_x + margin
                ]
                
                if center_sticker.size > 0:
                    color = self.classify_color(center_sticker)
                else:
                    color = self.classify_color(sticker)
                
                row_colors.append(color)
            face_colors.append(row_colors)
        
        return face_colors
    
    def calibrate_colors(self, sample_images: Dict[str, List[np.ndarray]]):
        """
        Calibrate color classifier using sample images.
        sample_images: Dict mapping color codes to lists of sample sticker images
        """
        # This could be used to fine-tune color thresholds
        # For now, we use the standard color matching
        pass
    
    def get_color_name(self, color_code: str) -> str:
        """Get human-readable color name."""
        return self.COLOR_NAMES.get(color_code, 'Unknown')
