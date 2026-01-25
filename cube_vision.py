"""
Computer Vision Module for Cube Face Detection
Detects and extracts cube faces from images or webcam feed.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class CubeFaceDetector:
    """
    Detects Rubik's cube faces from images.
    Uses contour detection to find square regions.
    """
    
    def __init__(self):
        self.face_size = 3  # 3x3 grid
        
    def detect_faces(self, image_path: str) -> List[np.ndarray]:
        """
        Detect all 6 cube faces from an image.
        Returns list of 6 face images (3x3 grid regions).
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        return self._extract_faces(img)
    
    def detect_faces_from_frame(self, frame: np.ndarray) -> List[np.ndarray]:
        """Detect faces from a video frame."""
        return self._extract_faces(frame)
    
    def _extract_faces(self, img: np.ndarray) -> List[np.ndarray]:
        """
        Extract 6 cube faces from image.
        This is a simplified version - in production, you'd use more sophisticated
        detection to find the actual cube faces.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find square-like contours (potential cube faces)
        squares = []
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                if area > 1000:  # Minimum area threshold
                    squares.append(approx)
        
        # If we found faces, extract them
        # For now, return a placeholder that expects manual face input
        # In a real implementation, you'd use perspective transform to extract faces
        faces = []
        
        # This is a simplified approach - you may need to manually select faces
        # or use a more sophisticated detection method
        if len(squares) >= 1:
            # For demonstration, we'll extract regions
            # In production, implement proper face extraction
            h, w = img.shape[:2]
            # Divide image into regions (simplified)
            # This assumes faces are arranged in a cross pattern
            face_regions = self._divide_into_regions(img)
            faces = face_regions[:6]  # Take first 6 regions
        
        return faces if len(faces) == 6 else []
    
    def _divide_into_regions(self, img: np.ndarray) -> List[np.ndarray]:
        """
        Divide image into potential face regions.
        This is a helper method - in production, use proper cube detection.
        """
        h, w = img.shape[:2]
        regions = []
        
        # Simple grid division (this is a placeholder)
        # Real implementation would detect actual cube faces
        cell_h, cell_w = h // 3, w // 3
        
        for i in range(3):
            for j in range(3):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                region = img[y1:y2, x1:x2]
                if region.size > 0:
                    regions.append(region)
        
        return regions
    
    def extract_stickers(self, face_image: np.ndarray) -> List[np.ndarray]:
        """
        Extract individual stickers (3x3 grid) from a face image.
        Returns list of 9 sticker images.
        """
        h, w = face_image.shape[:2]
        stickers = []
        
        # Divide face into 3x3 grid
        cell_h, cell_w = h // 3, w // 3
        
        for i in range(3):
            for j in range(3):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                sticker = face_image[y1:y2, x1:x2]
                stickers.append(sticker)
        
        return stickers
    
    def get_dominant_color(self, sticker_image: np.ndarray) -> Tuple[int, int, int]:
        """
        Get dominant color from a sticker image.
        Returns BGR color tuple.
        """
        # Reshape to 1D array of pixels
        pixels = sticker_image.reshape(-1, 3)
        
        # Calculate mean color
        mean_color = np.mean(pixels, axis=0)
        
        return tuple(map(int, mean_color))
    
    def visualize_detection(self, img: np.ndarray, faces: List[np.ndarray]) -> np.ndarray:
        """Visualize detected faces on the image."""
        vis_img = img.copy()
        # Add visualization code here
        return vis_img
