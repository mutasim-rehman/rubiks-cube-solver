"""
Cube Solver Module
Finds optimal solution path using solving algorithms.
"""

import kociemba
import os
from cube_state import CubeState
from cube_vision import CubeFaceDetector
from color_classifier import ColorClassifier
from cube_visualizer import CubeVisualizer
from typing import List, Optional, Dict
import cv2
import numpy as np
from constraint_solver import solve_without_u

# Default path for the ESP32 solution runner .ino (updated when solver runs)
DEFAULT_RUN_SOLUTION_INO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_solution.ino")


def write_solution_to_robot_ino(solution: str, ino_path: Optional[str] = None) -> bool:
    """
    Write the solution algorithm string into run_solution.ino so it can be
    flashed to the ESP32 and executed (e.g. trigger with SPACE+ENTER in Serial Monitor).
    solution: e.g. "U D' F2 R L' F R2 D' L2 ..."
    ino_path: path to run_solution.ino; defaults to run_solution.ino next to this module.
    Returns True if the file was written successfully.
    """
    path = ino_path or DEFAULT_RUN_SOLUTION_INO
    if not os.path.isfile(path):
        print(f"Warning: run_solution.ino not found at {path}; skipping write.")
        return False
    # Escape for C string: backslash and double-quote
    escaped = (solution or "").replace("\\", "\\\\").replace('"', '\\"')
    placeholder = 'SOLUTION_PLACEHOLDER'
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if placeholder not in content:
            print(f"Warning: {path} does not contain {placeholder}; skipping write.")
            return False
        content = content.replace(f'"{placeholder}"', f'"{escaped}"', 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Solution written to {path}")
        return True
    except OSError as e:
        print(f"Error writing solution to {path}: {e}")
        return False


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
    
    def solve_from_image(self, image_path: str, constrained: bool = False) -> Optional[str]:
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
        
        # Solve (optionally with constrained 5-face solver)
        return self._solve(constrained=constrained)
    
    def solve_from_manual_input(self, faces: List[List[List[str]]], constrained: bool = False) -> Optional[str]:
        """
        Solve cube from manually provided face colors.
        faces: List of 6 faces, each is 3x3 array of color codes
        """
        self.cube_state = CubeState(faces)
        return self._solve(constrained=constrained)
    
    def solve_from_webcam(self, constrained: bool = False) -> Optional[str]:
        """
        Solve cube using webcam feed with interactive capture.
        Allows user to select faces to capture in any order and confirm when done.
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return None
        
        # Face definitions with navigation info and orientation guides
        faces_info = {
            'U': {
                'name': 'Up (White)', 
                'next': 'L',
                'guide': 'Rotate so GREEN face is at BOTTOM',
                'center': 'W'
            },
            'L': {
                'name': 'Left (Orange)', 
                'next': 'F',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'O'
            },
            'F': {
                'name': 'Front (Green)', 
                'next': 'R',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'G'
            },
            'R': {
                'name': 'Right (Red)', 
                'next': 'B',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'R'
            },
            'B': {
                'name': 'Back (Blue)', 
                'next': 'D',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'B'
            },
            'D': {
                'name': 'Down (Yellow)', 
                'next': 'U',
                'guide': 'Rotate so GREEN face is at TOP',
                'center': 'Y'
            }
        }
        
        # Map to internal face order: U, R, F, D, L, B
        face_order_map = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}
        
        # Navigation key mapping
        nav_keys = {
            ord('w'): 'U', ord('W'): 'U',
            ord('o'): 'L', ord('O'): 'L',
            ord('g'): 'F', ord('G'): 'F',
            ord('r'): 'R', ord('R'): 'R',
            ord('b'): 'B', ord('B'): 'B',
            ord('y'): 'D', ord('Y'): 'D'
        }
        
        cube_faces = [None] * 6
        captured_face_codes = []  # List to track captured faces
        current_face = 'U'  # Start with Up/White
        
        print("\n" + "="*60)
        print("RUBIK'S CUBE SOLVER - INTERACTIVE CAPTURE")
        print("="*60)
        print("Controls:")
        print(" SPACE: Capture current face")
        print(" W/O/G/R/B/Y: Select White/Orange/Green/Red/Blue/Yellow face")
        print(" ENTER or E: Finish and Solve (requires all 6 faces)")
        print(" Q: Quit")
        print("="*60 + "\n")
        
        # Create windows
        cv2.namedWindow('Cube Guide', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Color Preview', cv2.WINDOW_NORMAL)
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read from webcam")
                break
                
            frame_count += 1
            
            # --- Handle Input ---
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == ord('Q'):
                print("Quit requested.")
                cap.release()
                cv2.destroyAllWindows()
                return None
                
            elif key in nav_keys:
                current_face = nav_keys[key]
                print(f"Switched to {faces_info[current_face]['name']}")
                
            elif key == 13 or key == ord('e') or key == ord('E'):  # Enter or E
                if len(captured_face_codes) == 6:
                    print("Finishing capture...")
                    break
                elif len(captured_face_codes) > 6: # Should not happen with unique list logic, but just in case
                     break
                else:
                    # Provide feedback on what's missing
                    missing = []
                    for code in ['U', 'L', 'F', 'R', 'B', 'D']:
                        if code not in captured_face_codes:
                            missing.append(faces_info[code]['name'])
                    print(f"Cannot solve yet! Missing: {', '.join(missing)}")
            
            # --- ROI Extraction ---
            # We use the full frame for detection
            h, w = frame.shape[:2]
            box_size = min(w, h) * 0.4
            center_x, center_y = w // 2, h // 2
            box_half = int(box_size // 2)
            
            roi = frame[
                max(0, center_y - box_half):min(h, center_y + box_half),
                max(0, center_x - box_half):min(w, center_x + box_half)
            ]
            
            # --- Capture Action ---
            if key == ord(' '):
                if roi.size > 0 and roi.shape[0] > 10 and roi.shape[1] > 10:
                    try:
                        face_colors = self.color_classifier.classify_face(roi)
                        
                        # Check center color match
                        center_color = face_colors[1][1]
                        expected_center = faces_info[current_face]['center']
                        if center_color != expected_center:
                            print(f"Warning: Expected center {expected_center}, got {center_color}")
                            # We allow it for now but warn, as lighting might be tricky
                        
                        face_idx = face_order_map[current_face]
                        cube_faces[face_idx] = face_colors
                        
                        if current_face not in captured_face_codes:
                            captured_face_codes.append(current_face)
                        
                        print(f"✓ Captured {faces_info[current_face]['name']}")
                        
                        # Auto-advance to next face if not all captured
                        if len(captured_face_codes) < 6:
                            current_face = faces_info[current_face]['next']
                    except Exception as e:
                        print(f"Capture failed: {e}")
                else:
                    print("Error: Invalid capture region")

            # --- Visualization ---
            
            # 1. Camera Feed with Overlay
            display_frame = cv2.resize(frame, (640, 480))
            display_frame = self.visualizer.create_alignment_overlay(display_frame, current_face)
            
            # Status Text on Camera Feed
            cv2.putText(display_frame, f"Target: {faces_info[current_face]['name']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Orientation Guide
            guide_text = faces_info[current_face]['guide']
            cv2.putText(display_frame, guide_text, 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            status_color = (0, 255, 0) if len(captured_face_codes) == 6 else (0, 165, 255)
            cv2.putText(display_frame, f"Captured: {len(captured_face_codes)}/6", 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                       
            if len(captured_face_codes) == 6:
                 cv2.putText(display_frame, "Press ENTER or E to Solve", 
                       (10, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                 cv2.putText(display_frame, "SPACE: Capture | W/O/G/R/B/Y: Select Face", 
                       (10, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                 cv2.putText(display_frame, "ENTER/E: Finish", 
                       (10, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Alignment Quality Feedback
            is_aligned, confidence = self.visualizer.detect_alignment_quality(display_frame, current_face)
            if is_aligned:
                cv2.putText(display_frame, "Aligned", (530, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # 2. Color Preview
            if frame_count % 4 == 0: # Update preview occasionally
                try:
                    detected_colors = [['W']*3 for _ in range(3)]
                    if roi.size > 0 and roi.shape[0] > 10:
                        detected_colors = self.color_classifier.classify_face(roi)
                    
                    captured_dict = {}
                    for code in captured_face_codes:
                        captured_dict[code] = cube_faces[face_order_map[code]]
                        
                    preview_img = self.visualizer.create_color_preview(
                        current_face=current_face,
                        detected_colors=detected_colors,
                        captured_faces=captured_dict,
                        step=len(captured_face_codes) + 1, 
                        total_steps=6
                    )
                    cv2.imshow('Color Preview', preview_img)
                except Exception:
                    pass

            # 3. Guide Image
            next_face = faces_info[current_face]['next']
            guide_img = self.visualizer.create_capture_guide(
                current_face=current_face,
                step=len(captured_face_codes) + 1,
                total_steps=6,
                instruction=f"{faces_info[current_face]['name']}\n{faces_info[current_face]['guide']}",
                captured_faces=captured_face_codes,
                next_face=next_face
            )
            cv2.imshow('Cube Guide', guide_img)
            
            cv2.imshow('Camera Feed', display_frame)

        cap.release()
        cv2.destroyAllWindows()
        
        # Check if we have all faces (double check) and solve
        if all(face is not None for face in cube_faces):
            self.cube_state = CubeState(cube_faces)
            print("\n" + "="*60)
            print("All faces captured! Solving cube...")
            print("="*60)
            return self._solve(constrained=constrained)
        else:
            print("\nError: Not all faces captured properly.")
            return None
    
    def _solve(self, constrained: bool = False) -> Optional[str]:
        """
        Solve the cube using kociemba algorithm.
        Returns solution string.
        """
        if self.cube_state is None:
            return None
        
        # If our internal representation is already a solved cube,
        # we can skip calling the solver and just return an empty solution.
        # This also avoids confusing "solutions" for an already solved cube.
        try:
            if self.cube_state.is_solved():
                print("Cube is already solved. No moves needed.")
                return ""
        except Exception:
            # If for some reason is_solved fails, fall back to normal flow.
            pass
        
        # Validate cube state before solving
        is_valid, error_msg = self.cube_state.validate()
        if not is_valid:
            print(f"Invalid cube state: {error_msg}")
            print("Please check that each color appears exactly 9 times")
            return None
        
        try:
            # Convert to kociemba format
            kociemba_string = self.cube_state.to_kociemba_string()
            print(f"Cube string: {kociemba_string}")
            
            if constrained:
                # Use constrained solver that avoids U moves and only uses L,R,F,B,D.
                solution = solve_without_u(kociemba_string)
            else:
                # Solve using kociemba (optimal solver)
                solution = kociemba.solve(kociemba_string)
            
            return solution
        except ValueError as e:
            err = str(e)
            print(f"Error solving cube: {err}")
            if "invalid" in err.lower() or "Error" in err:
                print("The cube state is invalid or impossible. This often happens when:")
                print("  • Face orientations are wrong (especially Back face—ensure it's not rotated 90° or 180°)")
                print("  • Colors are misclassified (e.g. lighting) or a face is misidentified")
                print("  • Each face was captured in the correct orientation (see capture guide)")
            return None
        except Exception as e:
            print(f"Error solving cube: {e}")
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
