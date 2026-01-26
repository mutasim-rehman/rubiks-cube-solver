"""
Cube Solver Module
Finds optimal solution path using solving algorithms.
"""

import kociemba
from cube_state import CubeState
from cube_vision import CubeFaceDetector
from color_classifier import ColorClassifier
from cube_visualizer import CubeVisualizer
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
        self.visualizer = CubeVisualizer()
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
        Solve cube using webcam feed with guided sequence.
        User follows a logical sequence: Blue -> Red -> Green -> Orange -> Yellow -> White
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return None
        
        # Guided sequence matching Java project: TOP, LEFT, FRONT, RIGHT, BACK, BOTTOM
        # Sequence: Up (White/TOP) -> Left (Orange) -> Front (Green) -> Right (Red) -> Back (Blue) -> Down (Yellow/BOTTOM)
        # Maps to: U, L, F, R, B, D
        capture_sequence = [
            {
                'face_code': 'U',
                'face_name': 'Up (White) - TOP',
                'instruction': 'Step 1: Show the WHITE face (TOP)\nHold cube with white face up',
                'action': 'Show white top face'
            },
            {
                'face_code': 'L',
                'face_name': 'Left (Orange)',
                'instruction': 'Step 2: Show the ORANGE face (LEFT)\nRotate cube to show left side',
                'action': 'Show orange left face'
            },
            {
                'face_code': 'F',
                'face_name': 'Front (Green)',
                'instruction': 'Step 3: Show the GREEN face (FRONT)\nRotate cube to show front side',
                'action': 'Show green front face'
            },
            {
                'face_code': 'R',
                'face_name': 'Right (Red)',
                'instruction': 'Step 4: Show the RED face (RIGHT)\nRotate cube to show right side',
                'action': 'Show red right face'
            },
            {
                'face_code': 'B',
                'face_name': 'Back (Blue)',
                'instruction': 'Step 5: Show the BLUE face (BACK)\nRotate cube to show back side',
                'action': 'Show blue back face'
            },
            {
                'face_code': 'D',
                'face_name': 'Down (Yellow) - BOTTOM',
                'instruction': 'Step 6: Show the YELLOW face (BOTTOM)\nFlip cube to show bottom',
                'action': 'Show yellow bottom face'
            }
        ]
        
        # Map to internal face order: U, R, F, D, L, B
        face_order_map = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}
        cube_faces = [None] * 6  # Pre-allocate for correct order
        captured_face_codes = []
        
        print("\n" + "="*60)
        print("RUBIK'S CUBE SOLVER - GUIDED CAPTURE")
        print("="*60)
        print("\nFollow the sequence to capture all 6 faces")
        print("Press SPACE to capture, ESC to skip face, Q to quit")
        print("="*60 + "\n")
        
        # Create guide windows
        cv2.namedWindow('Cube Guide', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Color Preview', cv2.WINDOW_NORMAL)
        
        for step, face_info in enumerate(capture_sequence, 1):
            face_code = face_info['face_code']
            face_name = face_info['face_name']
            instruction = face_info['instruction']
            
            print(f"\nStep {step}/6: {face_name}")
            print(f"Action: {face_info['action']}")
            print("Position the cube face in the camera view...")
            
            # Determine next face for rotation hints
            next_face_code = None
            if step < len(capture_sequence):
                next_face_code = capture_sequence[step]['face_code']
            
            # Create guide image with full 2D net
            guide_image = self.visualizer.create_capture_guide(
                current_face=face_code,
                step=step,
                total_steps=6,
                instruction=instruction,
                captured_faces=captured_face_codes,
                next_face=next_face_code
            )
            
            # Store captured face colors for preview
            captured_face_colors = {}
            for cf in captured_face_codes:
                if cube_faces[face_order_map[cf]] is not None:
                    captured_face_colors[cf] = cube_faces[face_order_map[cf]]
            
            # Initialize color preview window with empty state
            try:
                empty_colors = [['W']*3 for _ in range(3)]  # Placeholder
                initial_preview = self.visualizer.create_color_preview(
                    current_face=face_code,
                    detected_colors=empty_colors,
                    captured_faces=captured_face_colors,
                    step=step,
                    total_steps=6
                )
                cv2.imshow('Color Preview', initial_preview)
            except Exception as e:
                print(f"Warning: Could not initialize color preview: {e}")
            
            captured = False
            frame_count = 0
            while not captured:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read from webcam")
                    break
                
                # Resize frame for display
                display_frame = cv2.resize(frame, (640, 480))
                
                # Extract the alignment region (ROI) for both preview and capture
                h, w = frame.shape[:2]
                box_size = min(w, h) * 0.4
                center_x, center_y = w // 2, h // 2
                box_half = int(box_size // 2)
                
                roi = frame[
                    max(0, center_y - box_half):min(h, center_y + box_half),
                    max(0, center_x - box_half):min(w, center_x + box_half)
                ]
                
                # Create alignment overlay (matches the 2D net diagram box)
                display_frame = self.visualizer.create_alignment_overlay(display_frame, face_code)
                
                # Add overlay text on camera feed
                cv2.putText(display_frame, f"Step {step}/6: {face_name}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, "SPACE: Capture | ESC: Skip | Q: Quit", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Check alignment quality (use display_frame for consistency)
                is_aligned, confidence = self.visualizer.detect_alignment_quality(display_frame, face_code)
                
                # Show alignment feedback
                if is_aligned:
                    alignment_text = f"Alignment: Good ({int(confidence * 100)}%)"
                    color = (0, 255, 0)  # Green
                else:
                    alignment_text = f"Alignment: Adjust ({int(confidence * 100)}%)"
                    color = (0, 165, 255)  # Orange
                
                cv2.putText(display_frame, alignment_text, 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Real-time color detection (update every 2 frames for better responsiveness)
                frame_count += 1
                should_update_preview = (frame_count % 2 == 0)  # Update every 2 frames
                
                if should_update_preview:
                    detected_colors = None
                    try:
                        if roi.size > 0 and roi.shape[0] > 10 and roi.shape[1] > 10:
                            # Classify current face in real-time from ROI
                            detected_colors = self.color_classifier.classify_face(roi)
                    except Exception as e:
                        # If detection fails, use placeholder
                        detected_colors = None
                        if frame_count % 60 == 0:  # Only print occasionally
                            print(f"Color detection warning: {e}")
                    
                    # Always show preview, even if detection failed
                    try:
                        if detected_colors is None:
                            # Use placeholder colors
                            detected_colors = [['W']*3 for _ in range(3)]
                        
                        # Create color preview
                        color_preview = self.visualizer.create_color_preview(
                            current_face=face_code,
                            detected_colors=detected_colors,
                            captured_faces=captured_face_colors,
                            step=step,
                            total_steps=6
                        )
                        
                        # Show color preview window
                        cv2.imshow('Color Preview', color_preview)
                    except Exception as e:
                        # Last resort - show basic preview
                        if frame_count % 60 == 0:
                            print(f"Preview display error: {e}")
                
                # Show windows
                cv2.imshow('Cube Guide', guide_image)
                cv2.imshow('Camera Feed', display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):  # Space to capture
                    # Classify this face using the ROI
                    if roi.size > 0 and roi.shape[0] > 10 and roi.shape[1] > 10:
                        face_colors = self.color_classifier.classify_face(roi)
                        # Store in correct position
                        face_idx = face_order_map[face_code]
                        cube_faces[face_idx] = face_colors
                        captured_face_codes.append(face_code)
                        print(f"✓ Captured {face_name}")
                        captured = True
                    else:
                        print("Error: Could not capture face (invalid region)")
                elif key == ord('q') or key == ord('Q'):  # Q to quit
                    print("\nCapture cancelled by user")
                    cap.release()
                    cv2.destroyAllWindows()
                    return None
                elif key == 27:  # ESC to skip
                    print(f"⚠ Skipped {face_name} (using placeholder)")
                    # Use placeholder colors
                    face_idx = face_order_map[face_code]
                    cube_faces[face_idx] = [['W']*3 for _ in range(3)]
                    captured_face_codes.append(face_code)
                    captured = True
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Check if all faces captured
        if all(face is not None for face in cube_faces):
            self.cube_state = CubeState(cube_faces)
            print("\n" + "="*60)
            print("All faces captured! Solving cube...")
            print("="*60)
            return self._solve()
        else:
            print("\nError: Not all faces captured")
            return None
    
    def _solve(self) -> Optional[str]:
        """
        Solve the cube using kociemba algorithm.
        Returns solution string.
        """
        if self.cube_state is None:
            return None
        
        # Validate cube state before solving
        is_valid, error_msg = self.cube_state.validate()
        if not is_valid:
            print(f"Invalid cube state: {error_msg}")
            print("Please check that each color appears exactly 9 times")
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
    
    def display_cube_state(self):
        """
        Display cube state in flat 2D format (matching Java project output).
        """
        if self.cube_state is None:
            print("No cube state available")
            return
        
        print("\nYour cube:")
        print(self.cube_state.to_flat_string())
    
    def display_solution(self, solution: str, show_solved_state: bool = True):
        """
        Display solution in format matching Java project.
        """
        if solution is None:
            print("No solution found")
            return
        
        move_count = self.get_move_count(solution)
        
        print("\nCalculating...")
        if show_solved_state:
            # Show solved state
            solved_cube = CubeState()  # Creates solved state
            print(solved_cube.to_flat_string())
        
        print(f"\nYour solution :)")
        print(solution)
        print(f"Number of moves: {move_count}")
    
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
