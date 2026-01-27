"""
Data Collection Script for Rubik's Cube Color Classifier
Allows users to capture cube faces and manually label sticker colors
to build a training dataset for the ML model.
"""

import cv2
import numpy as np
import os
import time
from cube_visualizer import CubeVisualizer
from color_classifier import ColorClassifier

class DataCollector:
    def __init__(self, output_dir="training_data"):
        self.output_dir = output_dir
        self.visualizer = CubeVisualizer()
        self.classifier = ColorClassifier()
        self.colors = ['R', 'G', 'B', 'Y', 'O', 'W']
        self.color_names = {
            'R': 'Red',
            'G': 'Green',



            'B': 'Blue',
            'Y': 'Yellow',
            'O': 'Orange',
            'W': 'White'
        }
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories for each color."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        for color in self.colors:
            path = os.path.join(self.output_dir, color)
            if not os.path.exists(path):
                os.makedirs(path)
                
    def save_sticker(self, sticker_img, color_code):
        """Save a sticker image to the appropriate directory."""
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}.png"
        path = os.path.join(self.output_dir, color_code, filename)
        cv2.imwrite(path, sticker_img)
        print(f"Saved {self.color_names[color_code]} sticker to {path}")

    def extract_stickers(self, face_img):
        """Extract 9 individual stickers from the face image."""
        h, w = face_img.shape[:2]
        cell_h, cell_w = h // 3, w // 3
        stickers = []
        
        for i in range(3):
            for j in range(3):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w
                sticker = face_img[y1:y2, x1:x2]
                stickers.append(sticker)
        return stickers

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return

        print("\n" + "="*60)
        print("RUBIK'S CUBE DATA COLLECTOR")
        print("="*60)
        print("1. Align cube face in the green box")
        print("2. Press SPACE to capture")
        print("3. Label each sticker by pressing: R, G, B, Y, O, W")
        print("   (Press ESC to discard capture)")
        print("4. Press Q to quit and train model")
        print("="*60 + "\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize for consistent display
            display_frame = cv2.resize(frame, (640, 480))
            
            # Draw alignment overlay (using 'F' as a generic face code)
            display_frame = self.visualizer.create_alignment_overlay(display_frame, 'F')
            
            # Add instructions
            cv2.putText(display_frame, "SPACE: Capture | Q: Quit & Train", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow('Data Collector', display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                # Capture and process
                self.process_capture(frame)

        cap.release()
        cv2.destroyAllWindows()
        
        # Trigger training
        self.train_model()
        
    def train_model(self):
        """Train the model with collected data."""
        print("\n" + "="*60)
        print("TRAINING MODEL")
        print("="*60)
        
        # Check if we have data
        has_data = False
        for color in self.colors:
            path = os.path.join(self.output_dir, color)
            if os.path.exists(path) and len(os.listdir(path)) > 0:
                has_data = True
                break
        
        if not has_data:
            print("No training data found. Skipping training.")
            return
            
        print("Training model with collected data...")
        try:
            self.classifier.train_model(self.output_dir)
            print("\nTraining complete! The model has been saved.")
            print("You can now run 'python main.py --webcam' to use the improved classifier.")
        except Exception as e:
            print(f"Error during training: {e}")

    def process_capture(self, frame):
        """Handle the capture and labeling process."""
        # Extract ROI (same logic as cube_solver.py)
        h, w = frame.shape[:2]
        box_size = min(w, h) * 0.4
        center_x, center_y = w // 2, h // 2
        box_half = int(box_size // 2)
        
        roi = frame[
            max(0, center_y - box_half):min(h, center_y + box_half),
            max(0, center_x - box_half):min(w, center_x + box_half)
        ]

        if roi.size == 0:
            print("Error: Invalid ROI")
            return

        stickers = self.extract_stickers(roi)
        
        # Create a window for labeling
        cv2.namedWindow('Label Sticker', cv2.WINDOW_NORMAL)
        
        print("\nStarting labeling sequence (9 stickers)...")
        print("Top-Left -> Top-Right, then next row...")
        
        for i, sticker in enumerate(stickers):
            labeled = False
            while not labeled:
                # Show the sticker being labeled
                display_sticker = cv2.resize(sticker, (300, 300))
                
                # Create a composite image with instructions
                info_h, info_w = 150, 300
                info_img = np.zeros((info_h, info_w, 3), dtype=np.uint8)
                
                cv2.putText(info_img, f"Sticker {i+1}/9", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(info_img, "Press: R G B Y O W", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                cv2.putText(info_img, "ESC: Discard Face", (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 1)
                
                # Stack sticker and info vertically
                combined = np.vstack([display_sticker, info_img])
                
                cv2.imshow('Label Sticker', combined)
                
                key = cv2.waitKey(0) & 0xFF
                
                if key == 27:  # ESC
                    print("Capture discarded.")
                    cv2.destroyWindow('Label Sticker')
                    return
                
                # Map keys to colors
                key_char = chr(key).upper()
                if key_char in self.colors:
                    self.save_sticker(sticker, key_char)
                    labeled = True
                else:
                    print(f"Invalid key '{key_char}'. Use R, G, B, Y, O, W.")
        
        cv2.destroyWindow('Label Sticker')
        print("Face capture complete!")

if __name__ == "__main__":
    collector = DataCollector()
    collector.run()
