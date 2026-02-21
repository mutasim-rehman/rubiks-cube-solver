"""
Cube Visualization Module
Creates 2D net visualization of the cube for user guidance.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class CubeVisualizer:
    """
    Visualizes cube state and provides 2D net guide for face capture.
    """
    
    # Color mapping for visualization (BGR for OpenCV)
    COLOR_BGR = {
        'R': (0, 0, 255),      # Red
        'G': (0, 255, 0),      # Green
        'B': (255, 0, 0),      # Blue
        'Y': (0, 255, 255),    # Yellow
        'O': (0, 165, 255),    # Orange
        'W': (255, 255, 255),  # White
    }
    
    # Face labels
    FACE_LABELS = {
        'U': 'Up (White)',
        'R': 'Right (Blue)',
        'F': 'Front (Red)',
        'D': 'Down (Yellow)',
        'L': 'Left (Green)',
        'B': 'Back (Orange)',
    }
    
    def __init__(self, cell_size: int = 60):
        self.cell_size = cell_size
        self.face_size = 3  # 3x3 grid
    
    def create_2d_net(self, highlighted_face: Optional[str] = None, 
                      captured_faces: List[str] = None,
                      show_rotation_hints: bool = True,
                      next_face: Optional[str] = None,
                      face_colors: Optional[Dict[str, List[List[str]]]] = None) -> np.ndarray:
        """
        Create a 2D net visualization matching the Java project layout.
        
        Layout (standard cube net):
                [U] Up/White (TOP)
        [L] [F] [R] [B]
        Left Front Right Back (Middle)
                [D] Down/Yellow (BOTTOM)
        
        This matches the Java project representation where:
        - Top 3 rows = TOP face (White/Up)
        - Left 3 columns = LEFT face (Green)
        - Middle-left 3 columns = FRONT face (Red)
        - Middle-right 3 columns = RIGHT face (Blue)
        - Far right 3 columns = BACK face (Orange)
        - Bottom 3 rows = BOTTOM face (Yellow/Down)
        """
        if captured_faces is None:
            captured_faces = []
        
        # Calculate dimensions
        cell_w = self.cell_size
        cell_h = self.cell_size
        grid_w = cell_w * 3  # 3x3 grid per face
        grid_h = cell_h * 3
        
        # Create canvas (4 faces wide, 3 faces tall)
        canvas_w = grid_w * 4 + cell_w * 3  # 4 grids + padding
        canvas_h = grid_h * 3 + cell_h * 3  # 3 grids + padding
        canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
        canvas[:] = (50, 46, 58)  # Soft dark background
        
        # Face positions in the net (x, y positions in grid units)
        # Format: (face_code, x_offset, y_offset, label, number)
        # Layout matching Java project: TOP, LEFT, FRONT, RIGHT, BACK, BOTTOM
        face_positions = [
            ('U', 1, 0, 'Up (White) - TOP', '1'),      # Top: White/Up
            ('L', 0, 1, 'Left (Green)', '2'),          # Middle left: Green/Left
            ('F', 1, 1, 'Front (Red)', '3'),           # Middle center-left: Red/Front
            ('R', 2, 1, 'Right (Blue)', '4'),         # Middle center-right: Blue/Right
            ('B', 3, 1, 'Back (Orange)', '5'),         # Middle right: Orange/Back
            ('D', 1, 2, 'Down (Yellow) - BOTTOM', '6'), # Bottom: Yellow/Down
        ]
        
        for face_code, x_off, y_off, label, number in face_positions:
            x_start = x_off * grid_w + cell_w * 1.5
            y_start = y_off * grid_h + cell_h * 1.5
            
            # Determine if this face should be highlighted
            is_highlighted = (highlighted_face == face_code)
            is_captured = (face_code in captured_faces)
            is_next = (next_face == face_code)
            
            # Get actual colors for this face if available
            actual_colors = None
            if face_colors and face_code in face_colors:
                actual_colors = face_colors[face_code]
            
            # Draw face grid
            self._draw_face_grid(canvas, int(x_start), int(y_start), face_code, 
                               is_highlighted, is_captured, label, number, is_next,
                               actual_colors=actual_colors)
        
        # Draw rotation arrows if showing hints and we have current/next face
        if show_rotation_hints and highlighted_face and next_face:
            self._draw_rotation_arrows(canvas, face_positions, grid_w, grid_h, 
                                     cell_w, cell_h, highlighted_face, next_face)
        
        return canvas
    
    def _draw_face_grid(self, canvas: np.ndarray, x_start: int, y_start: int,
                       face_code: str, is_highlighted: bool, is_captured: bool,
                       label: str, number: str = '', is_next: bool = False,
                       actual_colors: Optional[List[List[str]]] = None):
        """Draw a 3x3 face grid on the canvas."""
        cell_w = self.cell_size
        cell_h = self.cell_size
        
        # Get face color (default)
        color_map = {'U': 'W', 'R': 'R', 'F': 'G', 'D': 'Y', 'L': 'O', 'B': 'B'}
        face_color_code = color_map.get(face_code, 'W')
        face_color = self.COLOR_BGR[face_color_code]
        
        # Draw 3x3 grid
        for i in range(3):
            for j in range(3):
                x = x_start + j * cell_w
                y = y_start + i * cell_h
                
                # Determine cell color
                if actual_colors and i < len(actual_colors) and j < len(actual_colors[i]):
                    # Use actual detected color
                    detected_color_code = actual_colors[i][j]
                    cell_color = self.COLOR_BGR.get(detected_color_code, (80, 80, 80))
                    # Make it slightly brighter if it's the current face being captured
                    if is_highlighted:
                        cell_color = tuple(min(255, int(c * 1.1)) for c in cell_color)
                elif is_captured:
                    # Captured faces: show in color but dimmed
                    cell_color = tuple(int(c * 0.6) for c in face_color)
                    cell_color = (max(0, min(255, cell_color[0])), 
                                 max(0, min(255, cell_color[1])), 
                                 max(0, min(255, cell_color[2])))
                elif is_highlighted:
                    # Highlighted face: bright color with border
                    cell_color = face_color
                elif is_next:
                    # Next face: slightly brighter than others
                    cell_color = (120, 120, 120)
                else:
                    # Other faces: gray
                    cell_color = (80, 80, 80)
                
                # Draw cell
                cv2.rectangle(canvas, (x, y), (x + cell_w - 2, y + cell_h - 2),
                            cell_color, -1)
                
                # Draw border
                if is_highlighted:
                    border_color = (0, 255, 0)  # Green for current
                    border_thickness = 4
                elif is_next:
                    border_color = (0, 200, 255)  # Orange for next
                    border_thickness = 3
                else:
                    border_color = (100, 100, 100)
                    border_thickness = 1
                cv2.rectangle(canvas, (x, y), (x + cell_w - 2, y + cell_h - 2),
                            border_color, border_thickness)
        
        # Draw number in center cell (like the diagram)
        if number:
            center_x = x_start + cell_w * 1.5
            center_y = y_start + cell_h * 1.5
            # Make number more visible if we have actual colors
            if actual_colors:
                number_color = (0, 0, 0)  # Black for better contrast
            else:
                number_color = (255, 255, 255) if is_highlighted else (150, 150, 150)
            font_scale = 1.2
            thickness = 2
            (text_w, text_h), _ = cv2.getTextSize(number, cv2.FONT_HERSHEY_SIMPLEX,
                                                 font_scale, thickness)
            text_x = int(center_x - text_w // 2)
            text_y = int(center_y + text_h // 2)
            cv2.putText(canvas, number, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, number_color, thickness)
        
        # Draw label
        label_y = y_start - 10
        if label_y < 0:
            label_y = y_start + cell_h * 3 + 20
        
        font_scale = 0.5
        thickness = 1
        if is_highlighted:
            text_color = (0, 255, 0)  # Green
        elif is_next:
            text_color = (0, 200, 255)  # Orange
        else:
            text_color = (200, 200, 200)
        
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                             font_scale, thickness)
        text_x = x_start + (cell_w * 3 - text_w) // 2
        cv2.putText(canvas, label, (text_x, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)
    
    def _draw_rotation_arrows(self, canvas: np.ndarray, face_positions: List,
                             grid_w: int, grid_h: int, cell_w: int, cell_h: int,
                             current_face: str, next_face: str):
        """Draw arrows showing rotation direction from current to next face."""
        # Find positions of current and next faces
        current_pos = None
        next_pos = None
        
        for face_code, x_off, y_off, label, number in face_positions:
            if face_code == current_face:
                current_pos = (x_off, y_off)
            if face_code == next_face:
                next_pos = (x_off, y_off)
        
        if not current_pos or not next_pos:
            return
        
        # Calculate center points of faces
        current_x = int(current_pos[0] * grid_w + cell_w * 1.5 + grid_w // 2)
        current_y = int(current_pos[1] * grid_h + cell_h * 1.5 + grid_h // 2)
        next_x = int(next_pos[0] * grid_w + cell_w * 1.5 + grid_w // 2)
        next_y = int(next_pos[1] * grid_h + cell_h * 1.5 + grid_h // 2)
        
        # Draw arrow from current to next
        arrow_color = (0, 200, 255)  # Orange
        thickness = 3
        tip_length = 0.3
        
        # Calculate arrow direction
        dx = next_x - current_x
        dy = next_y - current_y
        length = np.sqrt(dx*dx + dy*dy)
        
        if length > 20:  # Only draw if faces are far enough apart
            # Normalize
            dx /= length
            dy /= length
            
            # Start point (edge of current face)
            start_x = int(current_x + dx * grid_w * 0.45)
            start_y = int(current_y + dy * grid_h * 0.45)
            
            # End point (edge of next face)
            end_x = int(next_x - dx * grid_w * 0.45)
            end_y = int(next_y - dy * grid_h * 0.45)
            
            # Draw arrow line
            cv2.arrowedLine(canvas, (start_x, start_y), (end_x, end_y),
                          arrow_color, thickness, tipLength=tip_length)
            
            # Add rotation instruction text
            mid_x = (start_x + end_x) // 2
            mid_y = (start_y + end_y) // 2
            
            # Determine rotation direction
            rotation_text = self._get_rotation_instruction(current_face, next_face)
            if rotation_text:
                font_scale = 0.5
                thickness_text = 1
                (text_w, text_h), _ = cv2.getTextSize(rotation_text, 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness_text)
                text_x = mid_x - text_w // 2
                text_y = mid_y - 10
                
                # Draw text background
                cv2.rectangle(canvas, 
                             (text_x - 5, text_y - text_h - 5),
                             (text_x + text_w + 5, text_y + 5),
                             (0, 0, 0), -1)
                
                cv2.putText(canvas, rotation_text, (text_x, text_y),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, arrow_color, thickness_text)
    
    def _get_rotation_instruction(self, current: str, next_face: str) -> str:
        """Get human-readable rotation instruction."""
        # Spatial relationships in the 2D net
        relationships = {
            'F': {'R': 'Rotate Right', 'L': 'Rotate Left', 'U': 'Rotate Up', 'D': 'Rotate Down'},
            'R': {'B': 'Rotate Right', 'F': 'Rotate Left', 'U': 'Rotate Up', 'D': 'Rotate Down'},
            'B': {'L': 'Rotate Right', 'R': 'Rotate Left', 'U': 'Rotate Up', 'D': 'Rotate Down'},
            'L': {'F': 'Rotate Right', 'B': 'Rotate Left', 'U': 'Rotate Up', 'D': 'Rotate Down'},
            'U': {'F': 'Rotate Down', 'B': 'Rotate Down', 'R': 'Rotate Right', 'L': 'Rotate Left'},
            'D': {'F': 'Rotate Up', 'B': 'Rotate Up', 'R': 'Rotate Right', 'L': 'Rotate Left'},
        }
        
        return relationships.get(current, {}).get(next_face, '')
    
    def create_capture_guide(self, current_face: str, step: int, total_steps: int,
                            instruction: str, captured_faces: List[str] = None,
                            next_face: Optional[str] = None,
                            face_colors: Optional[Dict[str, List[List[str]]]] = None) -> np.ndarray:
        """
        Create a guide image showing the full 2D net with current face highlighted.
        This helps users understand spatial relationships and rotation directions.
        """
        if captured_faces is None:
            captured_faces = []
        
        # Create 2D net with all faces visible
        net_image = self.create_2d_net(
            highlighted_face=current_face,
            captured_faces=captured_faces,
            show_rotation_hints=True,
            next_face=next_face,
            face_colors=face_colors
        )
        
        # Add instruction text at the top
        guide_h = net_image.shape[0] + 120
        guide_w = max(net_image.shape[1], 700)
        guide = np.zeros((guide_h, guide_w, 3), dtype=np.uint8)
        guide[:] = (58, 52, 68)  # Soft dark purple
        
        # Place net in center
        net_y = 100
        net_x = (guide_w - net_image.shape[1]) // 2
        guide[net_y:net_y + net_image.shape[0], net_x:net_x + net_image.shape[1]] = net_image
        
        # Add header text
        header_text = f"Step {step}/{total_steps}: {instruction}"
        cv2.putText(guide, header_text, (20, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add instruction text
        lines = instruction.split('\n')
        for i, line in enumerate(lines):
            cv2.putText(guide, line, (20, 50 + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Add legend
        legend_y = net_y + net_image.shape[0] + 10
        cv2.putText(guide, "Green = Current | Orange = Next | Gray = Remaining", 
                   (20, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(guide, "Use the 2D net to see which direction to rotate the cube", 
                   (20, legend_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return guide
    
    def create_alignment_overlay(self, frame: np.ndarray, face_code: str) -> np.ndarray:
        """
        Create an alignment overlay on the camera frame.
        Shows a box matching the 2D net diagram for the user to align the cube face.
        """
        overlay = frame.copy()
        h, w = overlay.shape[:2]
        
        # Calculate alignment box size (square, fits in frame)
        box_size = min(w, h) * 0.4  # 40% of smaller dimension
        center_x, center_y = w // 2, h // 2
        
        # Draw outer alignment box (thick border)
        box_half = int(box_size // 2)
        top_left = (center_x - box_half, center_y - box_half)
        bottom_right = (center_x + box_half, center_y + box_half)
        
        # Draw semi-transparent background
        overlay_alpha = overlay.copy()
        cv2.rectangle(overlay_alpha, top_left, bottom_right, (0, 255, 0), -1)
        cv2.addWeighted(overlay_alpha, 0.1, overlay, 0.9, 0, overlay)
        
        # Draw main alignment box (thick green border)
        cv2.rectangle(overlay, top_left, bottom_right, (0, 255, 0), 3)
        
        # Draw 3x3 grid inside the box (like the diagram)
        cell_size = int(box_size / 3)
        for i in range(1, 3):
            # Vertical lines
            x = center_x - box_half + i * cell_size
            cv2.line(overlay, (x, center_y - box_half), 
                    (x, center_y + box_half), (0, 255, 0), 2)
            # Horizontal lines
            y = center_y - box_half + i * cell_size
            cv2.line(overlay, (center_x - box_half, y), 
                    (center_x + box_half, y), (0, 255, 0), 2)
        
        # Draw corner markers for better alignment (L-shaped)
        corner_size = 25
        # Top-left corner
        tl_x, tl_y = center_x - box_half, center_y - box_half
        cv2.line(overlay, (tl_x, tl_y), (tl_x + corner_size, tl_y), (0, 255, 0), 3)
        cv2.line(overlay, (tl_x, tl_y), (tl_x, tl_y + corner_size), (0, 255, 0), 3)
        # Top-right corner
        tr_x, tr_y = center_x + box_half, center_y - box_half
        cv2.line(overlay, (tr_x, tr_y), (tr_x - corner_size, tr_y), (0, 255, 0), 3)
        cv2.line(overlay, (tr_x, tr_y), (tr_x, tr_y + corner_size), (0, 255, 0), 3)
        # Bottom-left corner
        bl_x, bl_y = center_x - box_half, center_y + box_half
        cv2.line(overlay, (bl_x, bl_y), (bl_x + corner_size, bl_y), (0, 255, 0), 3)
        cv2.line(overlay, (bl_x, bl_y), (bl_x, bl_y - corner_size), (0, 255, 0), 3)
        # Bottom-right corner
        br_x, br_y = center_x + box_half, center_y + box_half
        cv2.line(overlay, (br_x, br_y), (br_x - corner_size, br_y), (0, 255, 0), 3)
        cv2.line(overlay, (br_x, br_y), (br_x, br_y - corner_size), (0, 255, 0), 3)
        
        # Add face label
        face_labels = {
            'B': 'Back (Orange)',
            'R': 'Right (Blue)',
            'F': 'Front (Red)',
            'L': 'Left (Green)',
            'D': 'Down (Yellow)',
            'U': 'Up (White)'
        }
        label_text = face_labels.get(face_code, face_code)
        (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        text_x = center_x - text_w // 2
        text_y = center_y - box_half - 15
        
        # Draw text background
        cv2.rectangle(overlay, 
                     (text_x - 5, text_y - text_h - 5),
                     (text_x + text_w + 5, text_y + 5),
                     (0, 0, 0), -1)
        
        cv2.putText(overlay, label_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add instruction text at bottom
        instruction_text = "Align cube face with the green box above"
        (inst_w, inst_h), _ = cv2.getTextSize(instruction_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        inst_x = (w - inst_w) // 2
        inst_y = h - 30
        
        cv2.putText(overlay, instruction_text, (inst_x, inst_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return overlay
    
    def detect_alignment_quality(self, frame: np.ndarray, face_code: str) -> Tuple[bool, float]:
        """
        Detect how well the cube face is aligned with the alignment box.
        Returns (is_aligned, confidence_score)
        """
        h, w = frame.shape[:2]
        box_size = min(w, h) * 0.4
        center_x, center_y = w // 2, h // 2
        box_half = int(box_size // 2)
        
        # Extract the alignment region
        roi = frame[center_y - box_half:center_y + box_half,
                    center_x - box_half:center_x + box_half]
        
        if roi.size == 0:
            return False, 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Look for square-like patterns (cube face should have clear edges)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return False, 0.0
        
        # Find the largest contour (likely the cube face)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Check if it's roughly square
        peri = cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
        
        # Calculate alignment score
        roi_area = box_size * box_size
        area_ratio = area / roi_area if roi_area > 0 else 0
        
        # Good alignment: large area, roughly square shape
        is_square_like = len(approx) >= 4
        has_good_size = 0.3 < area_ratio < 0.9  # Face should fill 30-90% of box
        
        is_aligned = is_square_like and has_good_size
        confidence = min(area_ratio * 1.2, 1.0) if is_aligned else area_ratio * 0.5
        
        return is_aligned, confidence
    
    def visualize_cube_state(self, cube_state) -> np.ndarray:
        """
        Visualize the current cube state as a 2D net.
        """
        # Get face colors from cube state
        face_codes = ['U', 'R', 'F', 'D', 'L', 'B']
        face_colors_dict = {}
        
        for i, face_code in enumerate(face_codes):
            face = cube_state.get_face(i)
            face_colors_dict[face_code] = face
        
        canvas = self.create_2d_net(face_colors=face_colors_dict)
        return canvas
    
    def create_color_preview(self, current_face: str, detected_colors: List[List[str]],
                           captured_faces: Dict[str, List[List[str]]],
                           step: int, total_steps: int) -> np.ndarray:
        """
        Create a real-time color preview window showing detected colors in the 2D net.
        This updates as the camera processes frames.
        """
        # Combine captured faces with current face being detected
        all_face_colors = captured_faces.copy()
        all_face_colors[current_face] = detected_colors
        
        # Create 2D net with actual colors
        net_image = self.create_2d_net(
            highlighted_face=current_face,
            captured_faces=list(captured_faces.keys()),
            show_rotation_hints=False,
            face_colors=all_face_colors
        )
        
        # Add header
        preview_h = net_image.shape[0] + 80
        preview_w = max(net_image.shape[1], 600)
        preview = np.zeros((preview_h, preview_w, 3), dtype=np.uint8)
        preview[:] = (58, 52, 68)  # Soft dark purple (matches guide)
        
        # Place net in center
        net_y = 60
        net_x = (preview_w - net_image.shape[1]) // 2
        preview[net_y:net_y + net_image.shape[0], net_x:net_x + net_image.shape[1]] = net_image
        
        # Add title
        title = "Real-Time Color Detection Preview"
        cv2.putText(preview, title, (20, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add status
        status_text = f"Step {step}/{total_steps}: Detecting colors for {current_face} face"
        cv2.putText(preview, status_text, (20, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Add legend at bottom
        legend_y = net_y + net_image.shape[0] + 15
        cv2.putText(preview, "Colors update in real-time as camera detects them", 
                   (20, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        cv2.putText(preview, "Green border = Current face | Dimmed = Captured faces", 
                   (20, legend_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        return preview