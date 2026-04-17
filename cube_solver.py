"""
Cube Solver Module
Finds optimal solution path using solving algorithms.
"""

import kociemba
import os
import itertools
from cube_state import CubeState
from cube_vision import CubeFaceDetector
from color_classifier import ColorClassifier
from cube_visualizer import CubeVisualizer
from typing import List, Optional, Dict
import cv2
import numpy as np

# Default path for the ESP32 solution runner .ino (updated when solver runs)
DEFAULT_RUN_SOLUTION_INO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_solution.ino")


def _draw_rounded_rect(img: np.ndarray, pt1: tuple, pt2: tuple, color: tuple, radius: int = 12, thickness: int = -1) -> None:
    """Draw a rounded rectangle. pt1=(x1,y1), pt2=(x2,y2)."""
    x1, y1 = min(pt1[0], pt2[0]), min(pt1[1], pt2[1])
    x2, y2 = max(pt1[0], pt2[0]), max(pt1[1], pt2[1])
    h, w = y2 - y1, x2 - x1
    r = min(radius, h // 2, w // 2)
    if r <= 0:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        return
    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, thickness)
    cv2.circle(img, (x1 + r, y1 + r), r, color, thickness)
    cv2.circle(img, (x2 - r, y1 + r), r, color, thickness)
    cv2.circle(img, (x1 + r, y2 - r), r, color, thickness)
    cv2.circle(img, (x2 - r, y2 - r), r, color, thickness)


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
        self.visualizer = CubeVisualizer(cell_size=52)
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
                'guide': 'Rotate so RED face is at BOTTOM',
                'center': 'W'
            },
            'L': {
                'name': 'Left (Green)', 
                'next': 'F',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'G'
            },
            'F': {
                'name': 'Front (Red)', 
                'next': 'R',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'R'
            },
            'R': {
                'name': 'Right (Blue)', 
                'next': 'B',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'B'
            },
            'B': {
                'name': 'Back (Orange)', 
                'next': 'D',
                'guide': 'Rotate so WHITE face is at TOP',
                'center': 'O'
            },
            'D': {
                'name': 'Down (Yellow)', 
                'next': 'U',
                'guide': 'Rotate so RED face is at TOP',
                'center': 'Y'
            }
        }
        
        # Map to internal face order: U, R, F, D, L, B
        face_order_map = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}
        
        # Navigation key mapping (by sticker color initial)
        nav_keys = {
            ord('w'): 'U', ord('W'): 'U',  # White -> Up
            ord('g'): 'L', ord('G'): 'L',  # Green -> Left
            ord('r'): 'F', ord('R'): 'F',  # Red -> Front
            ord('b'): 'R', ord('B'): 'R',  # Blue -> Right
            ord('o'): 'B', ord('O'): 'B',  # Orange -> Back
            ord('y'): 'D', ord('Y'): 'D',  # Yellow -> Down
        }
        
        cube_faces = [None] * 6
        captured_face_codes = []  # List to track captured faces
        current_face = 'U'  # Start with Up/White
        
        print("\n" + "="*60)
        print("RUBIK'S CUBE SOLVER - INTERACTIVE CAPTURE")
        print("="*60)
        print("Controls:")
        print(" SPACE: Capture current face")
        print(" W/G/R/B/O/Y: Select White/Green/Red/Blue/Orange/Yellow face")
        print(" ENTER or E: Finish and Solve (requires all 6 faces)")
        print(" Q: Quit")
        print("="*60 + "\n")
        
        # Single unified window
        cv2.namedWindow('Rubik\'s Cube Solver', cv2.WINDOW_NORMAL)
        
        frame_count = 0
        preview_img = None  # Cached; updated every 4 frames
        
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
            
            # 1. Camera Feed with Overlay (65% scale: 624x468)
            display_frame = cv2.resize(frame, (624, 468))
            display_frame = self.visualizer.create_alignment_overlay(display_frame, current_face)
            
            # Status Text on Camera Feed (scaled for 624x468)
            fh = display_frame.shape[0]
            fw = display_frame.shape[1]
            cv2.putText(display_frame, f"Target: {faces_info[current_face]['name']}", 
                       (12, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            guide_text = faces_info[current_face]['guide']
            cv2.putText(display_frame, guide_text, 
                       (12, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
            status_color = (0, 255, 0) if len(captured_face_codes) == 6 else (0, 165, 255)
            cv2.putText(display_frame, f"Captured: {len(captured_face_codes)}/6", 
                       (12, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
            if len(captured_face_codes) == 6:
                cv2.putText(display_frame, "Press ENTER to Solve!", 
                       (12, fh - 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, "SPACE: Capture | W/G/R/B/O/Y: Face | ENTER: Done", 
                       (12, fh - 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            is_aligned, _ = self.visualizer.detect_alignment_quality(display_frame, current_face)
            if is_aligned:
                cv2.putText(display_frame, "OK", (fw - 50, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # 2. Color Preview (update every 4 frames to save CPU)
            if frame_count % 4 == 0:
                detected_colors = [['W']*3 for _ in range(3)]
                if roi.size > 0 and roi.shape[0] > 10:
                    try:
                        detected_colors = self.color_classifier.classify_face(roi)
                    except Exception:
                        pass
                try:
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
                except Exception:
                    preview_img = np.zeros((200, 400, 3), dtype=np.uint8)
                    preview_img.fill(20)
            if preview_img is None:
                preview_img = np.zeros((200, 400, 3), dtype=np.uint8)
                preview_img.fill(20)

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

            # 4. Combine into single window: Camera (left) | Guide + Color Preview (right, stacked) @ 65% scale
            panel_h = 273
            total_h = panel_h * 2
            cam_w = int(display_frame.shape[1] * total_h / display_frame.shape[0])
            cam_resized = cv2.resize(display_frame, (cam_w, total_h))
            guide_resized = cv2.resize(guide_img, (cam_w, panel_h))
            preview_resized = cv2.resize(preview_img, (cam_w, panel_h))
            right_col = np.vstack((guide_resized, preview_resized))
            div_w = 6
            # Gradient divider (soft peach to mint, vertical)
            divider = np.zeros((total_h, div_w, 3), dtype=np.uint8)
            for i in range(total_h):
                t = i / max(1, total_h)
                divider[i, :] = (
                    int(255 * (1 - t) + 200 * t),
                    int(218 * (1 - t) + 235 * t),
                    int(230 * (1 - t) + 245 * t),
                )
            composite = np.hstack((cam_resized, divider, right_col))
            # Outer accent border (warm gradient frame)
            border_w = 3
            composite = cv2.copyMakeBorder(composite, border_w, border_w, border_w, border_w,
                                          cv2.BORDER_CONSTANT, value=(90, 120, 180))
            # Pill labels with shadow for depth
            labels = [
                (20, 32, "  Camera  ", (255, 235, 250), (180, 70, 120)),
                (cam_w + div_w + 20, 32, "  Guide  ", (235, 255, 240), (70, 160, 95)),
                (cam_w + div_w + 20, panel_h + 32, "  Colors  ", (250, 248, 255), (160, 110, 170)),
            ]
            for lx, ly, text, fill_bgr, txt_bgr in labels:
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)
                pad_x, pad_y = 10, 6
                rx1, ry1 = max(border_w + 2, lx - pad_x), max(border_w + 2, ly - th - pad_y)
                rx2, ry2 = min(composite.shape[1] - border_w - 2, lx + tw + pad_x), min(composite.shape[0] - border_w - 2, ly + pad_y)
                # Shadow (offset +1)
                _draw_rounded_rect(composite, (rx1 + 2, ry1 + 2), (rx2 + 2, ry2 + 2), (40, 40, 50), radius=8, thickness=-1)
                _draw_rounded_rect(composite, (rx1, ry1), (rx2, ry2), fill_bgr, radius=8, thickness=-1)
                cv2.putText(composite, text, (lx, ly), cv2.FONT_HERSHEY_DUPLEX, 0.5, txt_bgr, 1)
            # Header with gradient + progress dots
            header_h = 38
            header = np.zeros((header_h, composite.shape[1], 3), dtype=np.uint8)
            header[:, :] = (55, 48, 72)
            for x in range(header.shape[1]):
                t = x / header.shape[1]
                header[:, x] = (int(48 + 25 * (1 - t)), int(42 + 20 * t), int(72 + 15 * t))
            cv2.putText(header, "Rubik's Cube Solver", (header.shape[1] // 2 - 95, 26),
                       cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 250, 255), 1)
            # Progress dots: 6 faces, green = captured
            dot_y, dot_r = 19, 4
            dot_spacing = 22
            dot_start = header.shape[1] // 2 - (5 * dot_spacing) // 2
            for i, code in enumerate(['U', 'L', 'F', 'R', 'B', 'D']):
                cx = dot_start + i * dot_spacing
                filled = code in captured_face_codes
                cv2.circle(header, (cx, dot_y), dot_r + 1, (60, 60, 70), -1)
                cv2.circle(header, (cx, dot_y), dot_r, (80, 255, 120) if filled else (100, 100, 110), -1)
            composite = np.vstack((header, composite))
            cv2.imshow('Rubik\'s Cube Solver', composite)
            if frame_count == 1:
                try:
                    cv2.resizeWindow('Rubik\'s Cube Solver', 1040, 620)
                except cv2.error:
                    pass

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

    def solve_from_two_images(
        self,
        image_one_path: str,
        image_two_path: str,
        constrained: bool = False
    ) -> Optional[str]:
        """
        Solve from two top-view photos with a fixed robot-friendly setup:
        - Image 1: White(top), Red(left), Blue(right)   -> U/F/R
        - Image 2: White(top), Orange(left), Green(right) -> U/B/L
        We infer the unseen Down (Yellow) face by brute-forcing valid completions.
        """
        self._show_two_image_deduction_preview(image_one_path, image_two_path)

        try:
            img1_faces = self.face_detector.extract_three_faces_from_top_view(image_one_path)
            img2_faces = self.face_detector.extract_three_faces_from_top_view(image_two_path)
        except Exception as exc:
            print(f"Failed to read or extract faces from images: {exc}")
            return None

        # CubeState order: U, R, F, D, L, B
        cube_faces = [None] * 6

        # Image 1 mapping: U/F/R
        cube_faces[0] = self.color_classifier.classify_face(img1_faces["top"])    # U
        cube_faces[2] = self.color_classifier.classify_face(img1_faces["left"])   # F
        cube_faces[1] = self.color_classifier.classify_face(img1_faces["right"])  # R
        # Image 2 mapping: U/B/L
        cube_faces_img2_u = self.color_classifier.classify_face(img2_faces["top"])    # U (again)
        cube_faces[5] = self.color_classifier.classify_face(img2_faces["left"])       # B
        cube_faces[4] = self.color_classifier.classify_face(img2_faces["right"])      # L

        # Merge U from both shots (prefer image 1, but average conflicts by center lock + vote)
        cube_faces[0] = self._merge_face_predictions(cube_faces[0], cube_faces_img2_u)

        # Lock expected centers for known 5 faces.
        cube_faces[0][1][1] = 'W'
        cube_faces[1][1][1] = 'B'
        cube_faces[2][1][1] = 'R'
        cube_faces[4][1][1] = 'G'
        cube_faces[5][1][1] = 'O'

        # Build a partial state with unknown Down face for visual confirmation.
        partial_down = [['?'] * 3 for _ in range(3)]
        partial_down[1][1] = 'Y'
        cube_faces[3] = partial_down

        self.cube_state = CubeState(cube_faces)
        print("\nPredicted 5-face state from 2 images (Down/Yellow inferred next):")
        self.display_cube_state()
        if not self._confirm_cube_state_visual():
            print("Cancelled by user. Please retake photos and try again.")
            return None

        # Infer Down face by brute-forcing sticker permutations consistent with remaining counts.
        solved = self._solve_with_inferred_down(cube_faces, constrained=constrained)
        if solved is not None:
            return solved

        print("\nCould not infer a valid Down face from permutations.")
        print("Please enter Down face manually (Y center expected).")
        manual_down = self._prompt_manual_down_face()
        if manual_down is None:
            print("Manual entry cancelled.")
            return None
        cube_faces[3] = manual_down
        self.cube_state = CubeState(cube_faces)
        if not self._confirm_cube_state_visual():
            return None
        return self._solve(constrained=constrained)

    def _merge_face_predictions(self, face_a: List[List[str]], face_b: List[List[str]]) -> List[List[str]]:
        """Merge two 3x3 face predictions by simple per-cell voting."""
        merged = [['W'] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                merged[i][j] = face_a[i][j] if face_a[i][j] == face_b[i][j] else face_a[i][j]
        return merged

    def _solve_with_inferred_down(self, partial_faces: List[List[List[str]]], constrained: bool = False) -> Optional[str]:
        """
        Given U,R,F,L,B known and D unknown, brute-force D stickers from remaining color counts.
        Returns solution string when first valid cube is found; sets self.cube_state.
        """
        remaining_counts = self._remaining_color_counts_for_down(partial_faces)
        if remaining_counts is None:
            print("Known faces already violate color counts; cannot infer Down face.")
            return None

        if remaining_counts.get('Y', 0) < 1:
            print("Invalid remaining counts: Down center must be Yellow.")
            return None

        # Center fixed at Y.
        remaining_counts['Y'] -= 1
        if remaining_counts['Y'] < 0:
            return None

        non_center_multiset: List[str] = []
        for color in ['W', 'R', 'G', 'B', 'O', 'Y']:
            non_center_multiset.extend([color] * remaining_counts.get(color, 0))
        if len(non_center_multiset) != 8:
            print(f"Expected 8 remaining non-center stickers for Down face, got {len(non_center_multiset)}.")
            return None

        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]

        tested = 0
        unique_perms = set(itertools.permutations(non_center_multiset))
        for perm in unique_perms:
            down = [['Y'] * 3 for _ in range(3)]
            down[1][1] = 'Y'
            for (r, c), col in zip(positions, perm):
                down[r][c] = col

            candidate_faces = [face for face in partial_faces]
            candidate_faces[3] = down
            solution = self._try_solve_candidate(candidate_faces, constrained=constrained)
            tested += 1
            if solution is not None:
                self.cube_state = CubeState(candidate_faces)
                print(f"Inferred Down face after testing {tested} permutation(s).")
                return solution

            if tested % 5000 == 0:
                print(f"Inference progress: tested {tested} permutations...")

        print(f"Tried {tested} permutations, no solvable completion found.")
        return None

    def _remaining_color_counts_for_down(self, partial_faces: List[List[List[str]]]) -> Optional[Dict[str, int]]:
        counts = {'W': 0, 'R': 0, 'G': 0, 'B': 0, 'O': 0, 'Y': 0}
        for face_idx in [0, 1, 2, 4, 5]:  # U,R,F,L,B known
            face = partial_faces[face_idx]
            if face is None:
                return None
            for row in face:
                for color in row:
                    if color not in counts:
                        return None
                    counts[color] += 1
        remaining = {c: 9 - counts[c] for c in counts}
        if any(v < 0 for v in remaining.values()):
            return None
        return remaining

    def _try_solve_candidate(self, candidate_faces: List[List[List[str]]], constrained: bool = False) -> Optional[str]:
        candidate = CubeState(candidate_faces)
        is_valid, _ = candidate.validate()
        if not is_valid:
            return None
        try:
            k_str = candidate.to_kociemba_string()
            if constrained:
                from constraint_solver import solve_without_u
                return solve_without_u(k_str)
            return kociemba.solve(k_str)
        except Exception:
            return None

    def _prompt_manual_down_face(self) -> Optional[List[List[str]]]:
        """
        Manual fallback for Down face input.
        Enter 3 rows of 3 chars each using R,G,B,Y,O,W (center will be forced to Y).
        """
        rows: List[List[str]] = []
        valid = {'R', 'G', 'B', 'Y', 'O', 'W'}
        for r in range(3):
            raw = input(f"Down face row {r + 1} (3 chars, e.g. YRG; or 'q' to cancel): ").strip().upper()
            if raw == 'Q':
                return None
            if len(raw) != 3 or any(ch not in valid for ch in raw):
                print("Invalid row format.")
                return None
            rows.append(list(raw))
        rows[1][1] = 'Y'
        return rows

    def _show_two_image_deduction_preview(self, image_one_path: str, image_two_path: str) -> None:
        """
        Show a visual explanation of how the program inferred 3 faces per image.
        Displays highlighted face regions and projected 3x3 sticker grid lines.
        """
        try:
            img1_dbg = self.face_detector.create_top_view_debug_overlay(image_one_path)
            img2_dbg = self.face_detector.create_top_view_debug_overlay(image_two_path)
        except Exception as exc:
            print(f"Could not render image deduction preview: {exc}")
            return

        target_h = 460
        w1 = int(img1_dbg.shape[1] * target_h / max(1, img1_dbg.shape[0]))
        w2 = int(img2_dbg.shape[1] * target_h / max(1, img2_dbg.shape[0]))
        img1_resized = cv2.resize(img1_dbg, (w1, target_h))
        img2_resized = cv2.resize(img2_dbg, (w2, target_h))

        gap = np.zeros((target_h, 14, 3), dtype=np.uint8)
        gap[:] = (45, 45, 45)
        row = np.hstack((img1_resized, gap, img2_resized))

        header_h = 96
        header = np.zeros((header_h, row.shape[1], 3), dtype=np.uint8)
        header[:] = (36, 36, 36)
        cv2.putText(
            header,
            "Face Deduction Preview (2-Image Mode)",
            (18, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )
        cv2.putText(
            header,
            "White=Top face | Green=Left face | Blue=Right face | grid lines = sticker split",
            (18, 64),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            (210, 235, 255),
            1
        )
        cv2.putText(
            header,
            "Press any key to continue to color prediction and confirmation",
            (18, 86),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.54,
            (190, 190, 190),
            1
        )

        composed = np.vstack((header, row))
        window_name = "Two-Image Deduction"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, composed)
        cv2.waitKey(0)
        cv2.destroyWindow(window_name)

    def _confirm_cube_state_visual(self) -> bool:
        """
        Show a visual cube-state confirmation window.
        Controls:
          - Y or Enter: confirm and continue solving
          - N or Esc or Q: reject and cancel
        """
        if self.cube_state is None:
            return False

        try:
            net = self.visualizer.visualize_cube_state(self.cube_state)
        except Exception as exc:
            print(f"Failed to render cube preview: {exc}")
            fallback = input("Confirm cube state anyway? (y/n): ").strip().lower()
            return fallback in ("y", "yes")

        panel_h = 110
        panel_w = max(700, net.shape[1])
        panel = np.zeros((panel_h, panel_w, 3), dtype=np.uint8)
        panel[:] = (42, 42, 42)

        cv2.putText(
            panel,
            "Predicted Cube State",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )
        cv2.putText(
            panel,
            "Press Y or ENTER to solve | Press N / ESC / Q to cancel",
            (20, 78),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (190, 220, 255),
            1
        )

        if panel_w > net.shape[1]:
            padded_net = np.zeros((net.shape[0], panel_w, 3), dtype=np.uint8)
            padded_net[:] = (35, 35, 35)
            x_off = (panel_w - net.shape[1]) // 2
            padded_net[:, x_off:x_off + net.shape[1]] = net
            composed = np.vstack((panel, padded_net))
        else:
            composed = np.vstack((panel, net))

        window_name = "Confirm Cube State"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, composed)

        while True:
            key = cv2.waitKey(0) & 0xFF
            if key in (ord('y'), ord('Y'), 13):
                cv2.destroyWindow(window_name)
                return True
            if key in (ord('n'), ord('N'), 27, ord('q'), ord('Q')):
                cv2.destroyWindow(window_name)
                return False
    
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
                from constraint_solver import solve_without_u
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
