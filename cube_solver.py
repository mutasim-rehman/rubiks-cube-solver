"""
Cube Solver Module
Finds optimal solution path using solving algorithms.
"""

import kociemba
from cube_state import CubeState
from cube_vision import CubeFaceDetector
from color_classifier import ColorClassifier
from typing import List, Optional
import cv2
import numpy as np


class CubeSolver:
    """
    Main cube solver that integrates vision, classification, and solving.
    """
    
    # Face order for input: Up, Right, Front, Down, Left, Back
    FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B']
    
    def __init__(self):
        self.face_detector = CubeFaceDetector()
        self.color_classifier = ColorClassifier()
        self.cube_state = None
    
    def solve_from_image(self, image_path: str) -> Optional[str]:
        """
        Solve cube from an image file.
        Returns solution string in standard notation.
        """
        # Detect faces
        face_images = self.face_detector.detect_faces(image_path)
        
        if len(face_images) != 6:
            print(f"Warning: Detected {len(face_images)} faces, expected 6")
            print("Please ensure all 6 faces are visible in the image")
            return None
        
        # Classify colors for each face
        cube_faces = []
        for face_img in face_images:
            face_colors = self.color_classifier.classify_face(face_img)
            cube_faces.append(face_colors)
        
        # Create cube state
        self.cube_state = CubeState(cube_faces)
        
        # Solve
        return self._solve()
    
    def solve_from_manual_input(self, faces: List[List[List[str]]]) -> Optional[str]:
        """
        Solve cube from manually provided face colors.
        faces: List of 6 faces, each is 3x3 array of color codes
        """
        self.cube_state = CubeState(faces)
        return self._solve()
    
    def solve_from_webcam(self) -> Optional[str]:
        """
        Solve cube using webcam feed.
        User will be prompted to show each face.
        """
        cap = cv2.VideoCapture(0)
        cube_faces = []
        
        print("Webcam mode: Show each face of the cube")
        print("Face order: Up, Right, Front, Down, Left, Back")
        print("Press SPACE to capture, ESC to skip face")
        
        face_names = ['Up (White center)', 'Right (Red center)', 'Front (Green center)',
                     'Down (Yellow center)', 'Left (Orange center)', 'Back (Blue center)']
        
        for i, face_name in enumerate(face_names):
            print(f"\nShowing: {face_name}")
            print("Position the cube face in the camera view...")
            
            captured = False
            while not captured:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Display frame
                display_frame = frame.copy()
                cv2.putText(display_frame, f"Face {i+1}/6: {face_name}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(display_frame, "SPACE: Capture | ESC: Skip", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Cube Solver - Capture Faces', display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):  # Space to capture
                    # Classify this face
                    face_colors = self.color_classifier.classify_face(frame)
                    cube_faces.append(face_colors)
                    print(f"Captured face {i+1}")
                    captured = True
                elif key == 27:  # ESC to skip
                    print(f"Skipped face {i+1}")
                    # Use placeholder colors
                    cube_faces.append([['W']*3 for _ in range(3)])
                    captured = True
        
        cap.release()
        cv2.destroyAllWindows()
        
        if len(cube_faces) == 6:
            self.cube_state = CubeState(cube_faces)
            return self._solve()
        else:
            print("Error: Not all faces captured")
            return None
    
    def _solve(self) -> Optional[str]:
        """
        Solve the cube using kociemba algorithm.
        Returns solution string.
        """
        if self.cube_state is None:
            return None
        
        try:
            # Convert to kociemba format
            kociemba_string = self.cube_state.to_kociemba_string()
            
            # Solve using kociemba (optimal solver)
            solution = kociemba.solve(kociemba_string)
            
            return solution
        except Exception as e:
            print(f"Error solving cube: {e}")
            print("Make sure the cube state is valid")
            return None
    
    def format_solution(self, solution: str) -> str:
        """
        Format solution string for better readability.
        """
        if solution is None:
            return "No solution found"
        
        moves = solution.split()
        formatted = []
        
        for move in moves:
            if len(move) == 1:
                formatted.append(f"{move} (90° clockwise)")
            elif move.endswith("'"):
                formatted.append(f"{move[0]}' (90° counter-clockwise)")
            elif move.endswith("2"):
                formatted.append(f"{move} (180°)")
            else:
                formatted.append(move)
        
        return "\n".join(formatted)
    
    def get_solution_steps(self, solution: str) -> List[str]:
        """Get solution as a list of individual moves."""
        if solution is None:
            return []
        return solution.split()
    
    def get_move_count(self, solution: str) -> int:
        """Get total number of moves in solution."""
        if solution is None:
            return 0
        return len(solution.split())
