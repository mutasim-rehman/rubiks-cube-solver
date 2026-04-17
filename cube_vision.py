"""
Computer Vision Module for Cube Face Detection
Detects and extracts cube faces from images or webcam feed.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from PIL import Image
from face_alignment_model import FaceAlignmentModel

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    # Optional dependency; standard formats still work without this.
    pass


class CubeFaceDetector:
    """
    Detects Rubik's cube faces from images.
    Uses contour detection to find square regions.
    """
    
    def __init__(self):
        self.face_size = 3  # 3x3 grid
        self.alignment_model = FaceAlignmentModel()
        self.alignment_model_loaded = self.alignment_model.load()
        
    def detect_faces(self, image_path: str) -> List[np.ndarray]:
        """
        Detect all 6 cube faces from an image.
        Returns list of 6 face images (3x3 grid regions).
        """
        img = self._load_image(image_path)
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

    def detect_cube_face_region(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the most likely cube face region in the frame using contour analysis.
        Returns (x, y, w, h) of the bounding box, or None if no confident detection.
        Works best when the cube face is roughly square and clearly visible.
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 120)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        min_area = (min(w, h) * 0.15) ** 2
        max_area = w * h * 0.7
        center_x, center_y = w // 2, h // 2

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            if len(approx) != 4:
                continue
            x, y, cw, ch = cv2.boundingRect(approx)
            aspect = max(cw, ch) / max(1, min(cw, ch))
            if aspect > 1.5:
                continue
            rect_area = cw * ch
            extent = area / max(1, rect_area)
            if extent < 0.6:
                continue
            cx, cy = x + cw // 2, y + ch // 2
            dist_from_center = np.sqrt((cx - center_x) ** 2 + (cy - center_y) ** 2)
            diag = np.sqrt(w * w + h * h)
            score = 1.0 - (dist_from_center / diag) * 0.5 + (extent - 0.6) * 0.5
            candidates.append((score, x, y, cw, ch))

        if not candidates:
            return None
        candidates.sort(key=lambda c: -c[0])
        _, x, y, cw, ch = candidates[0]
        pad = 2
        x = max(0, x - pad)
        y = max(0, y - pad)
        cw = min(w - x, cw + 2 * pad)
        ch = min(h - y, ch + 2 * pad)
        return (x, y, cw, ch)

    def extract_three_faces_from_top_view(self, image_path: str) -> Dict[str, np.ndarray]:
        """
        Extract top, left-side, and right-side faces from a standard "top-view" cube photo.
        Returns a dict with keys: 'top', 'left', 'right'.

        Assumes the cube is roughly centered and captured similar to:
            - top face as a diamond near upper-middle
            - two side faces below-left and below-right
        """
        img = self._load_image(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        return self.extract_three_faces_from_top_view_frame(img)

    def extract_three_faces_from_top_view_frame(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        """Frame-based version of extract_three_faces_from_top_view."""
        top_quad, left_quad, right_quad = self._get_top_view_quads_from_image(img)

        return {
            "top": self._warp_quad_to_square(img, top_quad),
            "left": self._warp_quad_to_square(img, left_quad),
            "right": self._warp_quad_to_square(img, right_quad),
        }

    def create_top_view_debug_overlay(self, image_path: str) -> np.ndarray:
        """
        Create a debug image showing inferred face regions and 3x3 sticker grid lines.
        """
        img = self._load_image(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        return self.create_top_view_debug_overlay_from_frame(img)

    def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image with OpenCV first, then Pillow fallback (supports HEIC with pillow-heif).
        Returns BGR ndarray or None.
        """
        img = cv2.imread(image_path)
        if img is not None:
            return img
        try:
            pil_img = Image.open(image_path)
            rgb = np.array(pil_img.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        except Exception:
            return None

    def create_top_view_debug_overlay_from_frame(self, img: np.ndarray) -> np.ndarray:
        """
        Frame-based debug overlay for top-view face inference.
        Draws:
        - face boundary polygons
        - projected 3x3 grid divisions
        - face labels (TOP/LEFT/RIGHT)
        """
        overlay = img.copy()
        top_quad, left_quad, right_quad = self._get_top_view_quads_from_image(img)

        faces = [
            ("TOP", top_quad, (255, 255, 255)),
            ("LEFT", left_quad, (0, 255, 0)),
            ("RIGHT", right_quad, (255, 0, 0)),
        ]

        for name, quad, color in faces:
            q = quad.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(overlay, [q], True, color, 3)
            self._draw_projected_grid(overlay, quad, color)
            cx, cy = np.mean(quad, axis=0).astype(int)
            cv2.putText(
                overlay,
                name,
                (int(cx) - 22, int(cy)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        # Blend with original for easier viewing
        return cv2.addWeighted(img, 0.72, overlay, 0.28, 0)

    def _get_top_view_quads(self, width: int, height: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get top, left, right quads for a top-view cube image.
        Point order in each quad: TL, TR, BR, BL.
        """
        wf = float(width)
        hf = float(height)
        top_quad = np.array([
            [0.50 * wf, 0.13 * hf],
            [0.68 * wf, 0.32 * hf],
            [0.50 * wf, 0.50 * hf],
            [0.32 * wf, 0.32 * hf],
        ], dtype=np.float32)
        left_quad = np.array([
            [0.18 * wf, 0.58 * hf],
            [0.50 * wf, 0.50 * hf],
            [0.50 * wf, 0.80 * hf],
            [0.20 * wf, 0.90 * hf],
        ], dtype=np.float32)
        right_quad = np.array([
            [0.50 * wf, 0.50 * hf],
            [0.82 * wf, 0.58 * hf],
            [0.80 * wf, 0.90 * hf],
            [0.50 * wf, 0.80 * hf],
        ], dtype=np.float32)
        return top_quad, left_quad, right_quad

    def _get_top_view_quads_from_image(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict quads from trained alignment model when available.
        Falls back to default hardcoded quads.
        """
        if self.alignment_model_loaded and self.alignment_model.is_trained():
            try:
                pred = self.alignment_model.predict_quads(img)
                return pred["top"], pred["left"], pred["right"]
            except Exception:
                pass
        return self._get_top_view_quads(img.shape[1], img.shape[0])

    def get_default_top_view_quads(self, width: int, height: int) -> Dict[str, np.ndarray]:
        """Public helper returning default top-view quads as dict."""
        top_quad, left_quad, right_quad = self._get_top_view_quads(width, height)
        return {"top": top_quad, "left": left_quad, "right": right_quad}

    def _draw_projected_grid(self, img: np.ndarray, quad: np.ndarray, color: Tuple[int, int, int]) -> None:
        """Draw projected 3x3 grid lines inside a quadrilateral."""
        # Quad order: TL, TR, BR, BL
        tl, tr, br, bl = quad

        # Vertical internal lines (1/3 and 2/3)
        for t in (1.0 / 3.0, 2.0 / 3.0):
            top_pt = (1 - t) * tl + t * tr
            bottom_pt = (1 - t) * bl + t * br
            cv2.line(
                img,
                (int(top_pt[0]), int(top_pt[1])),
                (int(bottom_pt[0]), int(bottom_pt[1])),
                color,
                2
            )

        # Horizontal internal lines (1/3 and 2/3)
        for t in (1.0 / 3.0, 2.0 / 3.0):
            left_pt = (1 - t) * tl + t * bl
            right_pt = (1 - t) * tr + t * br
            cv2.line(
                img,
                (int(left_pt[0]), int(left_pt[1])),
                (int(right_pt[0]), int(right_pt[1])),
                color,
                2
            )

    def _warp_quad_to_square(self, img: np.ndarray, quad: np.ndarray, out_size: int = 300) -> np.ndarray:
        """Perspective-warp a quadrilateral region into a square image."""
        destination = np.array([
            [0, 0],
            [out_size - 1, 0],
            [out_size - 1, out_size - 1],
            [0, out_size - 1],
        ], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(quad, destination)
        warped = cv2.warpPerspective(img, matrix, (out_size, out_size))
        return warped
