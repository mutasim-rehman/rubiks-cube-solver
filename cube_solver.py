"""
Cube Solver Module
Finds optimal solution path using solving algorithms.
"""

import kociemba
import copy
import os
from cube_state import CubeState
from cube_vision import CubeFaceDetector
from color_classifier import ColorClassifier
from cube_visualizer import CubeVisualizer
from typing import List, Optional, Dict, Tuple, Set, FrozenSet
import cv2
import numpy as np
from dataclasses import dataclass, field

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


@dataclass(frozen=True)
class EdgePiece:
    name: str
    colors: FrozenSet[str]


@dataclass(frozen=True)
class CornerPiece:
    name: str
    colors: FrozenSet[str]


@dataclass
class DownEdgeSlot:
    pos: Tuple[int, int]
    side_color: str
    candidates: List[EdgePiece] = field(default_factory=list)
    assigned: Optional[EdgePiece] = None


@dataclass
class DownCornerSlot:
    pos: Tuple[int, int]
    side_colors: FrozenSet[str]
    candidates: List[CornerPiece] = field(default_factory=list)
    assigned: Optional[CornerPiece] = None


class CubeSolver:
    """
    Main cube solver that integrates vision, classification, and solving.
    """

    # Face order for input: Up, Right, Front, Down, Left, Back
    FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B']

    EDGE_PIECES = [
        EdgePiece("WR", frozenset(("W", "R"))),
        EdgePiece("WB", frozenset(("W", "B"))),
        EdgePiece("WO", frozenset(("W", "O"))),
        EdgePiece("WG", frozenset(("W", "G"))),
        EdgePiece("YR", frozenset(("Y", "R"))),
        EdgePiece("YB", frozenset(("Y", "B"))),
        EdgePiece("YO", frozenset(("Y", "O"))),
        EdgePiece("YG", frozenset(("Y", "G"))),
        EdgePiece("RB", frozenset(("R", "B"))),
        EdgePiece("BO", frozenset(("B", "O"))),
        EdgePiece("OG", frozenset(("O", "G"))),
        EdgePiece("GR", frozenset(("G", "R"))),
    ]
    CORNER_PIECES = [
        CornerPiece("WRB", frozenset(("W", "R", "B"))),
        CornerPiece("WBO", frozenset(("W", "B", "O"))),
        CornerPiece("WOG", frozenset(("W", "O", "G"))),
        CornerPiece("WGR", frozenset(("W", "G", "R"))),
        CornerPiece("YRB", frozenset(("Y", "R", "B"))),
        CornerPiece("YBO", frozenset(("Y", "B", "O"))),
        CornerPiece("YOG", frozenset(("Y", "O", "G"))),
        CornerPiece("YGR", frozenset(("Y", "G", "R"))),
    ]

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
        - Image 1: White(top), Green(left), Red(right)   -> U/F/R
        - Image 2: White(top), Orange(left), Blue(right) -> U/L/B
        We infer the unseen Down (Yellow) face via deterministic edge/corner constraints.
        """
        self._show_two_image_deduction_preview(image_one_path, image_two_path)

        try:
            img1_faces = self.face_detector.extract_three_faces_and_splits_from_top_view(image_one_path)
            img2_faces = self.face_detector.extract_three_faces_and_splits_from_top_view(image_two_path)
        except Exception as exc:
            print(f"Failed to read or extract faces from images: {exc}")
            return None

        # CubeState order: U, R, F, D, L, B
        cube_faces = [None] * 6

        # Image 1 mapping: U/F/R
        cube_faces[0] = self.color_classifier.classify_face(
            img1_faces["top"]["image"],
            u_splits=img1_faces["top"]["u_splits"],
            v_splits=img1_faces["top"]["v_splits"],
        )  # U
        cube_faces[2] = self.color_classifier.classify_face(
            img1_faces["left"]["image"],
            u_splits=img1_faces["left"]["u_splits"],
            v_splits=img1_faces["left"]["v_splits"],
        )  # F
        cube_faces[1] = self.color_classifier.classify_face(
            img1_faces["right"]["image"],
            u_splits=img1_faces["right"]["u_splits"],
            v_splits=img1_faces["right"]["v_splits"],
        )  # R
        # Image 2 mapping: U/L/B
        cube_faces_img2_u = self.color_classifier.classify_face(
            img2_faces["top"]["image"],
            u_splits=img2_faces["top"]["u_splits"],
            v_splits=img2_faces["top"]["v_splits"],
        )  # U (again)
        cube_faces[4] = self.color_classifier.classify_face(
            img2_faces["left"]["image"],
            u_splits=img2_faces["left"]["u_splits"],
            v_splits=img2_faces["left"]["v_splits"],
        )  # L
        cube_faces[5] = self.color_classifier.classify_face(
            img2_faces["right"]["image"],
            u_splits=img2_faces["right"]["u_splits"],
            v_splits=img2_faces["right"]["v_splits"],
        )  # B

        # Merge U from both shots (prefer image 1, but average conflicts by center lock + vote)
        cube_faces[0] = self._merge_face_predictions(cube_faces[0], cube_faces_img2_u)

        # Lock expected centers for known 5 faces.
        cube_faces[0][1][1] = 'W'
        cube_faces[1][1][1] = 'R'
        cube_faces[2][1][1] = 'G'
        cube_faces[4][1][1] = 'O'
        cube_faces[5][1][1] = 'B'

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

        # Infer / use Down face from the live visual editor state.
        solved = self._solve_with_inferred_down(self.cube_state.faces, constrained=constrained)
        if solved is not None:
            return solved

        print("\nCould not solve from the current visual state.")
        print("Adjust stickers in the visual confirmation window and retry.")
        return None

    def _merge_face_predictions(self, face_a: List[List[str]], face_b: List[List[str]]) -> List[List[str]]:
        """Merge two 3x3 face predictions by simple per-cell voting."""
        merged = [['W'] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                merged[i][j] = face_a[i][j] if face_a[i][j] == face_b[i][j] else face_a[i][j]
        return merged

    def _solve_with_inferred_down(self, partial_faces: List[List[List[str]]], constrained: bool = False) -> Optional[str]:
        """
        Given U,R,F,L,B known and D unknown, infer Down face deterministically by
        assigning legal edge/corner pieces to each Down slot.
        """
        if partial_faces and partial_faces[3] is not None:
            down = partial_faces[3]
            has_unknown = any(
                down[r][c] == '?'
                for r in range(3)
                for c in range(3)
                if (r, c) != (1, 1)
            )
            if not has_unknown:
                candidate_faces = [copy.deepcopy(face) for face in partial_faces]
                solution = self._try_solve_candidate(candidate_faces, constrained=constrained)
                if solution is not None:
                    self.cube_state = CubeState(candidate_faces)
                    return solution

        inferred_down = self._infer_down_face_deterministic(partial_faces)
        if inferred_down is None:
            return None

        unresolved = [
            (r, c)
            for r in range(3)
            for c in range(3)
            if (r, c) != (1, 1) and inferred_down[r][c] == '?'
        ]
        if unresolved:
            slots_txt = ", ".join([f"({r},{c})" for r, c in unresolved])
            print(f"Deterministic inference left ambiguous Down slots: {slots_txt}")
            return None

        candidate_faces = [copy.deepcopy(face) for face in partial_faces]
        candidate_faces[3] = inferred_down
        solution = self._try_solve_candidate(candidate_faces, constrained=constrained)
        if solution is None:
            print("Deterministic Down inference produced an invalid cube state.")
            return None

        self.cube_state = CubeState(candidate_faces)
        print("Inferred Down face deterministically from edge/corner piece constraints.")
        return solution

    def _infer_down_face_with_options(
        self,
        partial_faces: List[List[List[str]]]
    ) -> Tuple[Optional[List[List[str]]], Dict[Tuple[int, int], List[str]]]:
        """
        Infer Down face and also expose per-slot candidate colors for unresolved slots.
        """
        if not partial_faces or len(partial_faces) != 6:
            return None, {}
        if any(partial_faces[idx] is None for idx in [0, 1, 2, 4, 5]):
            return None, {}

        down = copy.deepcopy(partial_faces[3]) if partial_faces[3] is not None else [['?'] * 3 for _ in range(3)]
        if len(down) != 3 or any(len(row) != 3 for row in down):
            down = [['?'] * 3 for _ in range(3)]
        down[1][1] = 'Y'

        used_edges = self._collect_used_non_down_edges(partial_faces)
        used_corners = self._collect_used_non_down_corners(partial_faces)
        remaining_edges = [p for p in self.EDGE_PIECES if p.name not in used_edges]
        remaining_corners = [p for p in self.CORNER_PIECES if p.name not in used_corners]

        edge_slots = self._build_down_edge_slots(partial_faces, down, remaining_edges)
        corner_slots = self._build_down_corner_slots(partial_faces, down, remaining_corners)
        if any(len(slot.candidates) == 0 for slot in edge_slots + corner_slots):
            return None, {}

        changed = True
        while changed:
            changed = False
            for slot in edge_slots:
                if slot.assigned is None and len(slot.candidates) == 1:
                    slot.assigned = slot.candidates[0]
                    changed = True
            for slot in corner_slots:
                if slot.assigned is None and len(slot.candidates) == 1:
                    slot.assigned = slot.candidates[0]
                    changed = True

            changed |= self._prune_assigned_edge_candidates(edge_slots)
            changed |= self._prune_assigned_corner_candidates(corner_slots)
            changed |= self._assign_unique_edge_candidates(edge_slots)
            changed |= self._assign_unique_corner_candidates(corner_slots)

        options: Dict[Tuple[int, int], List[str]] = {}
        for slot in edge_slots:
            if slot.assigned is not None:
                down[slot.pos[0]][slot.pos[1]] = self._edge_down_color(slot.assigned, slot.side_color)
            else:
                colors = sorted({self._edge_down_color(p, slot.side_color) for p in slot.candidates})
                options[slot.pos] = colors
        for slot in corner_slots:
            if slot.assigned is not None:
                down[slot.pos[0]][slot.pos[1]] = self._corner_down_color(slot.assigned, slot.side_colors)
            else:
                colors = sorted({self._corner_down_color(p, slot.side_colors) for p in slot.candidates})
                options[slot.pos] = colors
        return down, options

    def _infer_down_face_deterministic(self, partial_faces: List[List[List[str]]]) -> Optional[List[List[str]]]:
        down, options = self._infer_down_face_with_options(partial_faces)
        if down is None:
            print("No legal deterministic candidates for at least one Down slot.")
            return None
        if options:
            for pos in options:
                down[pos[0]][pos[1]] = '?'
        return down

    def _collect_used_non_down_edges(self, faces: List[List[List[str]]]) -> Set[str]:
        f = faces
        pairs = [
            (f[0][2][1], f[2][0][1]),  # UF
            (f[0][1][2], f[1][0][1]),  # UR
            (f[0][0][1], f[5][0][1]),  # UB
            (f[0][1][0], f[4][0][1]),  # UL
            (f[2][1][2], f[1][1][0]),  # FR
            (f[2][1][0], f[4][1][2]),  # FL
            (f[5][1][0], f[1][1][2]),  # BR
            (f[5][1][2], f[4][1][0]),  # BL
        ]
        return self._match_edge_piece_names(pairs)

    def _collect_used_non_down_corners(self, faces: List[List[List[str]]]) -> Set[str]:
        f = faces
        triples = [
            (f[0][2][2], f[2][0][2], f[1][0][0]),  # UFR
            (f[0][2][0], f[2][0][0], f[4][0][2]),  # UFL
            (f[0][0][0], f[4][0][0], f[5][0][2]),  # ULB
            (f[0][0][2], f[1][0][2], f[5][0][0]),  # URB
        ]
        return self._match_corner_piece_names(triples)

    def _match_edge_piece_names(self, color_pairs: List[Tuple[str, str]]) -> Set[str]:
        matched: Set[str] = set()
        for a, b in color_pairs:
            colors = frozenset((a, b))
            if '?' in colors:
                continue
            piece = next((p for p in self.EDGE_PIECES if p.colors == colors), None)
            if piece is not None:
                matched.add(piece.name)
        return matched

    def _match_corner_piece_names(self, color_triples: List[Tuple[str, str, str]]) -> Set[str]:
        matched: Set[str] = set()
        for a, b, c in color_triples:
            colors = frozenset((a, b, c))
            if '?' in colors:
                continue
            piece = next((p for p in self.CORNER_PIECES if p.colors == colors), None)
            if piece is not None:
                matched.add(piece.name)
        return matched

    def _build_down_edge_slots(
        self,
        faces: List[List[List[str]]],
        down: List[List[str]],
        remaining_edges: List[EdgePiece],
    ) -> List[DownEdgeSlot]:
        f = faces
        slot_specs = [
            ((0, 1), f[2][2][1]),  # DF
            ((1, 2), f[1][2][1]),  # DR
            ((2, 1), f[5][2][1]),  # DB
            ((1, 0), f[4][2][1]),  # DL
        ]
        slots: List[DownEdgeSlot] = []
        for (r, c), side_col in slot_specs:
            observed = down[r][c]
            candidates: List[EdgePiece] = []
            for piece in remaining_edges:
                if side_col not in piece.colors:
                    continue
                other = self._edge_down_color(piece, side_col)
                if observed != '?' and observed != other:
                    continue
                candidates.append(piece)
            slots.append(DownEdgeSlot(pos=(r, c), side_color=side_col, candidates=candidates))
        return slots

    def _build_down_corner_slots(
        self,
        faces: List[List[List[str]]],
        down: List[List[str]],
        remaining_corners: List[CornerPiece],
    ) -> List[DownCornerSlot]:
        f = faces
        slot_specs = [
            ((0, 0), frozenset((f[2][2][0], f[4][2][2]))),  # DFL
            ((0, 2), frozenset((f[2][2][2], f[1][2][0]))),  # DFR
            ((2, 2), frozenset((f[5][2][0], f[1][2][2]))),  # DBR
            ((2, 0), frozenset((f[5][2][2], f[4][2][0]))),  # DBL
        ]
        slots: List[DownCornerSlot] = []
        for (r, c), side_cols in slot_specs:
            observed = down[r][c]
            candidates: List[CornerPiece] = []
            for piece in remaining_corners:
                if not side_cols.issubset(piece.colors):
                    continue
                other = self._corner_down_color(piece, side_cols)
                if observed != '?' and observed != other:
                    continue
                candidates.append(piece)
            slots.append(DownCornerSlot(pos=(r, c), side_colors=side_cols, candidates=candidates))
        return slots

    def _edge_down_color(self, piece: EdgePiece, side_color: str) -> str:
        return next(iter(piece.colors - {side_color}))

    def _corner_down_color(self, piece: CornerPiece, side_colors: FrozenSet[str]) -> str:
        return next(iter(piece.colors - side_colors))

    def _prune_assigned_edge_candidates(self, slots: List[DownEdgeSlot]) -> bool:
        changed = False
        assigned = {s.assigned.name for s in slots if s.assigned is not None}
        for slot in slots:
            if slot.assigned is not None:
                slot.candidates = [slot.assigned]
                continue
            old_len = len(slot.candidates)
            slot.candidates = [c for c in slot.candidates if c.name not in assigned]
            changed |= len(slot.candidates) != old_len
        return changed

    def _prune_assigned_corner_candidates(self, slots: List[DownCornerSlot]) -> bool:
        changed = False
        assigned = {s.assigned.name for s in slots if s.assigned is not None}
        for slot in slots:
            if slot.assigned is not None:
                slot.candidates = [slot.assigned]
                continue
            old_len = len(slot.candidates)
            slot.candidates = [c for c in slot.candidates if c.name not in assigned]
            changed |= len(slot.candidates) != old_len
        return changed

    def _assign_unique_edge_candidates(self, slots: List[DownEdgeSlot]) -> bool:
        changed = False
        unresolved = [s for s in slots if s.assigned is None]
        counts: Dict[str, int] = {}
        for slot in unresolved:
            for cand in slot.candidates:
                counts[cand.name] = counts.get(cand.name, 0) + 1
        for slot in unresolved:
            uniques = [c for c in slot.candidates if counts.get(c.name, 0) == 1]
            if len(uniques) == 1:
                slot.assigned = uniques[0]
                changed = True
        return changed

    def _assign_unique_corner_candidates(self, slots: List[DownCornerSlot]) -> bool:
        changed = False
        unresolved = [s for s in slots if s.assigned is None]
        counts: Dict[str, int] = {}
        for slot in unresolved:
            for cand in slot.candidates:
                counts[cand.name] = counts.get(cand.name, 0) + 1
        for slot in unresolved:
            uniques = [c for c in slot.candidates if counts.get(c.name, 0) == 1]
            if len(uniques) == 1:
                slot.assigned = uniques[0]
                changed = True
        return changed

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

    def _prompt_manual_down_face(self, prefilled: Optional[List[List[str]]] = None) -> Optional[List[List[str]]]:
        """
        Manual fallback for Down face input.
        Enter 3 rows of 3 chars each using R,G,B,Y,O,W (center forced to Y).
        If prefilled is provided, known deterministic slots are shown and preserved.
        """
        rows: List[List[str]] = copy.deepcopy(prefilled) if prefilled is not None else [['?'] * 3 for _ in range(3)]
        if len(rows) != 3 or any(len(row) != 3 for row in rows):
            rows = [['?'] * 3 for _ in range(3)]
        valid = {'R', 'G', 'B', 'Y', 'O', 'W'}
        for r in range(3):
            existing = ''.join(rows[r]).replace('?', '_')
            raw = input(
                f"Down face row {r + 1} (3 chars, e.g. YRG; current {existing}; or 'q' to cancel): "
            ).strip().upper()
            if raw == 'Q':
                return None
            if raw == "":
                raw = ''.join(rows[r])
            if len(raw) != 3 or any((ch not in valid and ch != '?') for ch in raw):
                print("Invalid row format.")
                return None
            for c, ch in enumerate(raw):
                if ch != '?':
                    rows[r][c] = ch
        if any(rows[r][c] == '?' for r in range(3) for c in range(3) if (r, c) != (1, 1)):
            print("Incomplete Down face: unresolved slots remain.")
            return None
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
        Two-image mode behavior:
          - Click U/R/F/L/B stickers to cycle detected colors.
          - Down face is inferred in real-time from piece constraints.
          - If deterministic inference leaves ambiguous Down slots, click those Down
            stickers to choose from valid candidate colors (visual, no terminal typing).
        Controls:
          - Y or Enter: confirm and continue solving
          - N or Esc or Q: reject and cancel
        """
        if self.cube_state is None:
            return False

        try:
            working_faces = copy.deepcopy(self.cube_state.faces)
            tmp_state = CubeState(working_faces)
            net = self.visualizer.visualize_cube_state(tmp_state)
        except Exception as exc:
            print(f"Failed to render cube preview: {exc}")
            fallback = input("Confirm cube state anyway? (y/n): ").strip().lower()
            return fallback in ("y", "yes")

        panel_h = 130
        panel_w = max(700, net.shape[1])
        face_to_idx = {c: i for i, c in enumerate(self.FACE_ORDER)}
        editable_faces = {'U', 'R', 'F', 'L', 'B'}
        cycle = self.visualizer.STICKER_COLOR_CYCLE

        ui = {
            'faces': working_faces,
            'manual_down': {},
            'down_options': {},
            'display_faces': working_faces,
            'dirty': True,
            'net_x_off': 0,
            'net_y_off': panel_h,
            'net_h': net.shape[0],
            'net_w': net.shape[1],
            'picker': None,
        }

        def get_net_cell_bounds(face_code: str, row: int, col: int) -> Optional[Tuple[int, int, int, int]]:
            """Return (x1,y1,x2,y2) bounds in net-local coordinates for one sticker cell."""
            cell = int(self.visualizer.cell_size)
            grid = cell * 3
            face_pos = {
                'U': (1, 0),
                'L': (0, 1),
                'F': (1, 1),
                'R': (2, 1),
                'B': (3, 1),
                'D': (1, 2),
            }
            pos = face_pos.get(face_code)
            if pos is None:
                return None
            x_off, y_off = pos
            x_start = int(x_off * grid + cell * 1.5)
            y_start = int(y_off * grid + cell * 1.5)
            x1 = x_start + col * cell
            y1 = y_start + row * cell
            x2 = x1 + cell - 2
            y2 = y1 + cell - 2
            return (x1, y1, x2, y2)

        def apply_picker_color(face_code: str, row: int, col: int, selected: str) -> None:
            """Apply selected color from picker to editable faces or inferred Down slots."""
            if face_code in editable_faces:
                fidx = face_to_idx[face_code]
                ui['faces'][fidx][row][col] = selected
                # User changed observed faces; old manual down choices may no longer fit.
                ui['manual_down'].clear()
                ui['dirty'] = True
                return
            if face_code == 'D':
                pos = (row, col)
                options = ui['down_options'].get(pos, [])
                if selected in options:
                    ui['manual_down'][pos] = selected
                    ui['dirty'] = True

        def open_picker(face_code: str, row: int, col: int, options: List[str], current: str) -> None:
            ui['picker'] = {
                'face': face_code,
                'row': row,
                'col': col,
                'options': list(options),
                'current': current,
                'rects': [],
            }
            ui['dirty'] = True

        def rebuild_composed() -> np.ndarray:
            # Build a temporary partial state and infer down in real-time.
            partial_faces = copy.deepcopy(ui['faces'])
            if partial_faces[3] is None:
                partial_faces[3] = [['?'] * 3 for _ in range(3)]
            partial_faces[3][1][1] = 'Y'
            for (r, c), v in ui['manual_down'].items():
                if (r, c) != (1, 1):
                    partial_faces[3][r][c] = v

            inferred_down, down_options = self._infer_down_face_with_options(partial_faces)
            if inferred_down is None:
                inferred_down = copy.deepcopy(partial_faces[3])
                down_options = {}
            ui['down_options'] = down_options

            display_faces = copy.deepcopy(ui['faces'])
            display_faces[3] = inferred_down
            ui['display_faces'] = display_faces

            unresolved = len(ui['down_options'])
            st = CubeState(display_faces)
            n = self.visualizer.visualize_cube_state(st)
            ui['net_h'] = n.shape[0]
            ui['net_w'] = n.shape[1]
            pw = max(700, n.shape[1])
            panel_local = np.zeros((panel_h, pw, 3), dtype=np.uint8)
            panel_local[:] = (42, 42, 42)
            cv2.putText(
                panel_local,
                "Predicted Cube State",
                (20, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (255, 255, 255),
                2
            )
            cv2.putText(
                panel_local,
                "Click a sticker once, then choose color from popup (center locked)",
                (20, 62),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (200, 235, 255),
                1
            )
            cv2.putText(
                panel_local,
                "Down face infers live; click ambiguous Down slots for options",
                (20, 92),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 210, 255),
                1
            )
            status = "Down resolved" if unresolved == 0 else f"Down unresolved slots: {unresolved}"
            status_color = (120, 255, 160) if unresolved == 0 else (80, 190, 255)
            cv2.putText(
                panel_local,
                f"{status} | Y or ENTER: solve | N/ESC/Q: cancel",
                (20, 118),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                status_color,
                1
            )
            if pw > n.shape[1]:
                padded_net = np.zeros((n.shape[0], pw, 3), dtype=np.uint8)
                padded_net[:] = (35, 35, 35)
                x_off = (pw - n.shape[1]) // 2
                padded_net[:, x_off:x_off + n.shape[1]] = n
                ui['net_x_off'] = x_off
                composed_local = np.vstack((panel_local, padded_net))
            else:
                ui['net_x_off'] = 0
                composed_local = np.vstack((panel_local, n))

            picker = ui.get('picker')
            if picker:
                bounds = get_net_cell_bounds(picker['face'], picker['row'], picker['col'])
                if bounds is None:
                    ui['picker'] = None
                    return composed_local

                cx1, cy1, cx2, cy2 = bounds
                cell_w = max(1, cx2 - cx1 + 1)
                chip_w = max(30, int(cell_w * 0.6))
                chip_h = max(24, int(cell_w * 0.55))
                chip_gap = 8
                options = picker.get('options', [])
                if not options:
                    ui['picker'] = None
                    return composed_local

                total_w = len(options) * chip_w + max(0, len(options) - 1) * chip_gap
                anchor_x = ui['net_x_off'] + (cx1 + cx2) // 2
                x0 = anchor_x - total_w // 2
                max_x0 = max(0, composed_local.shape[1] - total_w - 1)
                x0 = max(0, min(x0, max_x0))
                y0 = ui['net_y_off'] + cy1 - chip_h - 20
                if y0 < 6:
                    y0 = ui['net_y_off'] + cy2 + 14
                y1 = y0 + chip_h

                cv2.rectangle(
                    composed_local,
                    (x0 - 8, y0 - 34),
                    (x0 + total_w + 8, y1 + 8),
                    (28, 28, 28),
                    -1
                )
                cv2.rectangle(
                    composed_local,
                    (x0 - 8, y0 - 34),
                    (x0 + total_w + 8, y1 + 8),
                    (160, 160, 160),
                    1
                )
                cv2.putText(
                    composed_local,
                    "Pick color",
                    (x0 - 2, y0 - 12),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.52,
                    (235, 235, 235),
                    1
                )

                rects = []
                for idx, opt in enumerate(options):
                    rx1 = x0 + idx * (chip_w + chip_gap)
                    ry1 = y0
                    rx2 = rx1 + chip_w
                    ry2 = y1
                    fill = self.visualizer.COLOR_BGR.get(opt, (90, 90, 90))
                    cv2.rectangle(composed_local, (rx1, ry1), (rx2, ry2), fill, -1)
                    border = (255, 255, 255) if opt == picker.get('current') else (40, 40, 40)
                    cv2.rectangle(composed_local, (rx1, ry1), (rx2, ry2), border, 2)
                    cv2.putText(
                        composed_local,
                        opt,
                        (rx1 + max(6, chip_w // 4), ry1 + max(18, int(chip_h * 0.7))),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.62,
                        (0, 0, 0) if opt in ('W', 'Y') else (255, 255, 255),
                        2
                    )
                    rects.append((opt, rx1, ry1, rx2, ry2))
                picker['rects'] = rects
                ui['picker'] = picker

            return composed_local

        def on_mouse(event, x, y, _flags, _param):
            if event != cv2.EVENT_LBUTTONDOWN:
                return
            picker = ui.get('picker')
            if picker:
                for opt, rx1, ry1, rx2, ry2 in picker.get('rects', []):
                    if rx1 <= x <= rx2 and ry1 <= y <= ry2:
                        apply_picker_color(picker['face'], picker['row'], picker['col'], opt)
                        ui['picker'] = None
                        ui['dirty'] = True
                        return
                ui['picker'] = None

            nx = x - ui['net_x_off']
            ny = y - ui['net_y_off']
            if nx < 0 or ny < 0 or nx >= ui['net_w'] or ny >= ui['net_h']:
                ui['dirty'] = True
                return
            hit = self.visualizer.hit_test_net_cell(nx, ny)
            if not hit:
                ui['dirty'] = True
                return
            face_code, row, col = hit
            if row == 1 and col == 1:
                ui['dirty'] = True
                return
            if face_code in editable_faces:
                fidx = face_to_idx[face_code]
                current = ui['faces'][fidx][row][col]
                open_picker(face_code, row, col, list(cycle), current if current in cycle else cycle[0])
                return
            if face_code == 'D':
                pos = (row, col)
                options = ui['down_options'].get(pos, [])
                if not options:
                    ui['dirty'] = True
                    return
                current = ui['manual_down'].get(pos, ui['display_faces'][3][row][col])
                open_picker(face_code, row, col, list(options), current if current in options else options[0])

        window_name = "Confirm Cube State"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, on_mouse)

        while True:
            if ui['dirty']:
                composed = rebuild_composed()
                cv2.imshow(window_name, composed)
                ui['dirty'] = False
            key = cv2.waitKey(30) & 0xFF
            if key in (ord('y'), ord('Y'), 13):
                unresolved = len(ui['down_options'])
                if unresolved > 0:
                    print(f"Please resolve {unresolved} Down slot(s) by clicking them.")
                    continue
                self.cube_state = CubeState(copy.deepcopy(ui['display_faces']))
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
