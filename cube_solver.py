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
        Solve cube using webcam feed with guided interactive capture.
        User can select any face to capture by clicking on it.
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return None
        
        # Face information
        capture_sequence = {
            'U': {'name': 'Up (White) - TOP', 'instruction': 'Show the WHITE face (TOP)', 'action': 'Show white top face'},
            'L': {'name': 'Left (Orange)', 'instruction': 'Show the ORANGE face (LEFT)', 'action': 'Show orange left face'},
            'F': {'name': 'Front (Green)', 'instruction': 'Show the GREEN face (FRONT)', 'action': 'Show green front face'},
            'R': {'name': 'Right (Red)', 'instruction': 'Show the RED face (RIGHT)', 'action': 'Show red right face'},
            'B': {'name': 'Back (Blue)', 'instruction': 'Show the BLUE face (BACK)', 'action': 'Show blue back face'},
            'D': {'name': 'Down (Yellow) - BOTTOM', 'instruction': 'Show the YELLOW face (BOTTOM)', 'action': 'Show yellow bottom face'}
        }
        
        # Map to internal face order: U, R, F, D, L, B
        face_order_map = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}
        
        # Shared state for callback
        state = {
            'current_face_code': 'U',  # Start with Up face
            'captured_face_codes': [],
            'cube_faces': [None] * 6
        }
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Calculate offsets used in create_capture_guide
                cell_w = self.visualizer.cell_size
                cell_h = self.visualizer.cell_size
                grid_w = cell_w * 3
                grid_h = cell_h * 3
                
                # Canvas dims from create_2d_net
                canvas_w = int(grid_w * 4 + cell_w * 3)
                
                # Guide dims from create_capture_guide
                guide_w = max(canvas_w, 700)
                
                net_y = 100
                net_x = (guide_w - canvas_w) // 2
                
                face = self.visualizer.get_face_at_point(x, y, offset_x=net_x, offset_y=net_y)
                if face:
                    state['current_face_code'] = face
                    print(f"Selected face: {face}")

        print("\n" + "="*60)
        print("RUBIK'S CUBE SOLVER - INTERACTIVE CAPTURE")
        print("="*60)
        print("\nInstructions:")
        print("1. Click on any face in the 'Cube Guide' window to select it")
        print("2. Press SPACE to capture the selected face")
        print("3. Press ENTER when all faces are captured to solve")
        print("4. Press Q to quit")
        print("="*60 + "\n")
        
        # Create windows
        cv2.namedWindow('Cube Guide', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Color Preview', cv2.WINDOW_NORMAL)
        
        # Set mouse callback
        cv2.setMouseCallback('Cube Guide', mouse_callback)
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read from webcam")
                break
            
            # Get current face info
            face_code = state['current_face_code']
            face_info = capture_sequence[face_code]
            face_name = face_info['name']
            instruction = face_info['instruction']
            
            # 1. Update Guide Window
            # Create guide image with full 2D net
            guide_image = self.visualizer.create_capture_guide(
                current_face=face_code,
                step=len(state['captured_face_codes']),  # This is just for display, might be confusing if jumping around
                total_steps=6,
                instruction=instruction + "\n(Click faces to switch)",
                captured_faces=state['captured_face_codes'],
                next_face=None # No strict sequence anymore
            )
            cv2.imshow('Cube Guide', guide_image)
            
            # 2. Update Camera Feed
            display_frame = cv2.resize(frame, (640, 480))
            h, w = frame.shape[:2]
            box_size = min(w, h) * 0.4
            center_x, center_y = w // 2, h // 2
            box_half = int(box_size // 2)
            
            # Extract ROI
            roi = frame[
                max(0, center_y - box_half):min(h, center_y + box_half),
                max(0, center_x - box_half):min(w, center_x + box_half)
            ]
            
            # Overlays
            display_frame = self.visualizer.create_alignment_overlay(display_frame, face_code)
            cv2.putText(display_frame, f"Target: {face_name}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display_frame, "SPACE: Capture | ENTER: Solve | Q: Quit", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Alignment check
            is_aligned, confidence = self.visualizer.detect_alignment_quality(display_frame, face_code)
            if is_aligned:
                alignment_text = f"Alignment: Good ({int(confidence * 100)}%)"
                color = (0, 255, 0)
            else:
                alignment_text = f"Alignment: Adjust ({int(confidence * 100)}%)"
                color = (0, 165, 255)
            cv2.putText(display_frame, alignment_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            cv2.imshow('Camera Feed', display_frame)
            
            # 3. Update Color Preview
            frame_count += 1
            if frame_count % 2 == 0:
                detected_colors = None
                try:
                    if roi.size > 0 and roi.shape[0] > 10 and roi.shape[1] > 10:
                        detected_colors = self.color_classifier.classify_face(roi)
                except Exception:
                    pass
                
                if detected_colors is None:
                    detected_colors = [['W']*3 for _ in range(3)]
                
                # Build current faces dict for preview
                current_faces_dict = {}
                for fc in state['captured_face_codes']:
                     # Find which index this face maps to
                    idx = face_order_map[fc]
                    if state['cube_faces'][idx] is not None:
                        current_faces_dict[fc] = state['cube_faces'][idx]

                try:
                    color_preview = self.visualizer.create_color_preview(
                        current_face=face_code,
                        detected_colors=detected_colors,
                        captured_faces=current_faces_dict,
                        step=len(state['captured_face_codes']),
                        total_steps=6
                    )
                    cv2.imshow('Color Preview', color_preview)
                except Exception as e:
                    if frame_count % 60 == 0:
                        print(f"Preview error: {e}")

            # Input Handling
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                print("\nCapture cancelled by user")
                cap.release()
                cv2.destroyAllWindows()
                return None
                
            elif key == ord(' '):  # SPACE to capture
                if roi.size > 0 and roi.shape[0] > 10 and roi.shape[1] > 10:
                    face_colors = self.color_classifier.classify_face(roi)
                    face_idx = face_order_map[face_code]
                    state['cube_faces'][face_idx] = face_colors
                    
                    if face_code not in state['captured_face_codes']:
                        state['captured_face_codes'].append(face_code)
                    
                    print(f"✓ Captured {face_name}")
                    
                    # Auto-advance logic (optional, but helpful)
                    # Find next uncaptured face in sequence U, L, F, R, B, D
                    ordered_faces = ['U', 'L', 'F', 'R', 'B', 'D'] # Guided order
                    try:
                        curr_idx = ordered_faces.index(face_code)
                        # Look for next uncaptured
                        found_next = False
                        for i in range(1, 6):
                            next_f = ordered_faces[(curr_idx + i) % 6]
                            if next_f not in state['captured_face_codes']:
                                state['current_face_code'] = next_f
                                found_next = True
                                break
                        if not found_next:
                             print("All faces captured! Press ENTER to solve.")
                    except ValueError:
                        pass
                else:
                    print("Error: Invalid capture region")
                    
            elif key == 13:  # ENTER key to solve
                # Check if all faces present
                missing_faces = []
                for f_code, idx in face_order_map.items():
                    if state['cube_faces'][idx] is None:
                        missing_faces.append(f_code)
                
                if not missing_faces:
                    print("\nAll faces captured. Solving...")
                    break
                else:
                    print(f"Cannot solve yet. Missing faces: {', '.join(missing_faces)}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        if all(face is not None for face in state['cube_faces']):
            self.cube_state = CubeState(state['cube_faces'])
            return self._solve()
        
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
