"""
Interactive annotator for cube face quads in top-view photos.

Usage:
  py annotate_cube_faces.py --images-dir training_data/CubeStates

Controls:
  - Left click near a point and drag to move it
  - 1 / 2 / 3 : set active face (top / left / right)
  - TAB       : cycle active face
  - N         : next image (auto-saves current)
  - P         : previous image (auto-saves current)
  - R         : reset current image to defaults
  - S         : save current annotation
  - Q / ESC   : save and quit
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass

from cube_vision import CubeFaceDetector


FACE_ORDER = ["top", "left", "right"]
FACE_COLORS = {
    "top": (255, 255, 255),   # white
    "left": (0, 255, 0),      # green
    "right": (255, 0, 0),     # blue
}
CORNER_NAMES = ["TL", "TR", "BR", "BL"]
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".heic", ".heif"}


def load_image_any(path: Path) -> Optional[np.ndarray]:
    """Load image with OpenCV first; fallback to Pillow for formats like HEIC."""
    img = cv2.imread(str(path))
    if img is not None:
        return img

    try:
        pil_img = Image.open(path)
        rgb = np.array(pil_img.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


class CubeFaceAnnotator:
    def __init__(self, images_dir: Path, annotations_dir: Optional[Path] = None) -> None:
        self.images_dir = images_dir
        self.annotations_dir = annotations_dir or (images_dir / "annotations")
        self.annotations_dir.mkdir(parents=True, exist_ok=True)

        self.detector = CubeFaceDetector()
        self.image_paths = self._collect_images()
        if not self.image_paths:
            raise ValueError(f"No images found in {images_dir}")

        self.index = 0
        self.current_image: Optional[np.ndarray] = None
        self.current_points: Dict[str, np.ndarray] = {}
        self.current_grid_splits: Dict[str, Dict[str, List[float]]] = {}
        self.current_manual_lines: Dict[str, List[List[List[float]]]] = {}
        self.active_face = "top"
        self.dragging: Optional[Tuple[str, int]] = None
        self.dragging_line: Optional[Tuple[str, str, int]] = None  # (face, axis, idx)
        self.pending_manual_line_start: Optional[Tuple[str, np.ndarray]] = None

    def _collect_images(self) -> List[Path]:
        paths = []
        for p in sorted(self.images_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                paths.append(p)
        return paths

    def _annotation_path_for(self, image_path: Path) -> Path:
        return self.annotations_dir / f"{image_path.stem}.json"

    def _default_points(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        h, w = img.shape[:2]
        return self.detector.get_default_top_view_quads(w, h)

    def _load_annotation(self, image_path: Path, img: np.ndarray) -> Dict[str, np.ndarray]:
        ann_path = self._annotation_path_for(image_path)
        if not ann_path.exists():
            return self._default_points(img)

        try:
            with open(ann_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            faces = data.get("faces", {})
            points: Dict[str, np.ndarray] = {}
            for face in FACE_ORDER:
                raw = faces.get(face)
                if not raw or len(raw) != 4:
                    return self._default_points(img)
                points[face] = np.array(raw, dtype=np.float32)
            self.current_grid_splits = self._parse_grid_splits(data.get("grid_splits", {}))
            self.current_manual_lines = self._parse_manual_lines(data.get("manual_inner_lines", {}))
            return points
        except Exception:
            return self._default_points(img)

    def _save_annotation(self) -> None:
        image_path = self.image_paths[self.index]
        if self.current_image is None:
            return

        h, w = self.current_image.shape[:2]
        payload = {
            "image_file": image_path.name,
            "image_path": str(image_path.as_posix()),
            "image_size": {"width": int(w), "height": int(h)},
            "point_order": CORNER_NAMES,  # TL, TR, BR, BL
            "faces": {
                face: [[float(x), float(y)] for x, y in self.current_points[face]]
                for face in FACE_ORDER
            },
            "grid_splits": self.current_grid_splits,
            "manual_inner_lines": self.current_manual_lines,
        }
        ann_path = self._annotation_path_for(image_path)
        with open(ann_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Saved annotation: {ann_path}")

    def _load_current(self) -> bool:
        image_path = self.image_paths[self.index]
        img = load_image_any(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return False

        self.current_grid_splits = self._default_grid_splits()
        self.current_manual_lines = self._default_manual_lines()
        self.current_image = img
        self.current_points = self._load_annotation(image_path, img)
        self._sync_shared_corners_from("top", 2)
        self.active_face = "top"
        self.dragging = None
        self.dragging_line = None
        self.pending_manual_line_start = None
        print(f"\nImage {self.index + 1}/{len(self.image_paths)}: {image_path.name}")
        return True

    def _default_grid_splits(self) -> Dict[str, Dict[str, List[float]]]:
        return {
            face: {"u": [1.0 / 3.0, 2.0 / 3.0], "v": [1.0 / 3.0, 2.0 / 3.0]}
            for face in FACE_ORDER
        }

    def _default_manual_lines(self) -> Dict[str, List[List[List[float]]]]:
        return {face: [] for face in FACE_ORDER}

    def _parse_grid_splits(self, raw: Dict[str, Dict[str, List[float]]]) -> Dict[str, Dict[str, List[float]]]:
        splits = self._default_grid_splits()
        for face in FACE_ORDER:
            if face not in raw:
                continue
            face_raw = raw.get(face, {})
            u = face_raw.get("u", splits[face]["u"])
            v = face_raw.get("v", splits[face]["v"])
            if isinstance(u, list) and len(u) == 2:
                splits[face]["u"] = [float(max(0.05, min(0.95, u[0]))), float(max(0.05, min(0.95, u[1])))]
            if isinstance(v, list) and len(v) == 2:
                splits[face]["v"] = [float(max(0.05, min(0.95, v[0]))), float(max(0.05, min(0.95, v[1])))]
            splits[face]["u"].sort()
            splits[face]["v"].sort()
        return splits

    def _parse_manual_lines(self, raw: Dict[str, List[List[List[float]]]]) -> Dict[str, List[List[List[float]]]]:
        lines = self._default_manual_lines()
        for face in FACE_ORDER:
            face_lines = raw.get(face, [])
            if not isinstance(face_lines, list):
                continue
            parsed_face_lines: List[List[List[float]]] = []
            for line in face_lines:
                if not isinstance(line, list) or len(line) != 2:
                    continue
                p1, p2 = line
                if not isinstance(p1, list) or len(p1) != 2 or not isinstance(p2, list) or len(p2) != 2:
                    continue
                parsed_face_lines.append([
                    [float(p1[0]), float(p1[1])],
                    [float(p2[0]), float(p2[1])],
                ])
            lines[face] = parsed_face_lines
        return lines

    def _draw_projected_grid(
        self,
        canvas: np.ndarray,
        quad: np.ndarray,
        color: Tuple[int, int, int],
        face: str,
    ) -> None:
        tl, tr, br, bl = quad
        u_splits = self.current_grid_splits[face]["u"]
        v_splits = self.current_grid_splits[face]["v"]
        for t in u_splits:
            top_pt = (1 - t) * tl + t * tr
            bottom_pt = (1 - t) * bl + t * br
            cv2.line(
                canvas,
                (int(top_pt[0]), int(top_pt[1])),
                (int(bottom_pt[0]), int(bottom_pt[1])),
                color,
                2,
            )
        for t in v_splits:
            left_pt = (1 - t) * tl + t * bl
            right_pt = (1 - t) * tr + t * br
            cv2.line(
                canvas,
                (int(left_pt[0]), int(left_pt[1])),
                (int(right_pt[0]), int(right_pt[1])),
                color,
                2,
            )

    def _render(self) -> np.ndarray:
        assert self.current_image is not None
        canvas = self.current_image.copy()

        for face in FACE_ORDER:
            quad = self.current_points[face]
            color = FACE_COLORS[face]
            cv2.polylines(canvas, [quad.astype(np.int32).reshape((-1, 1, 2))], True, color, 2)
            self._draw_projected_grid(canvas, quad, color, face)
            cx, cy = np.mean(quad, axis=0).astype(int)
            label = face.upper()
            if face == self.active_face:
                label += " *"
            cv2.putText(canvas, label, (int(cx) - 22, int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

            for i, pt in enumerate(quad):
                px, py = int(pt[0]), int(pt[1])
                radius = 8 if face == self.active_face else 6
                cv2.circle(canvas, (px, py), radius, color, -1)
                cv2.circle(canvas, (px, py), radius + 2, (30, 30, 30), 1)
                if face == self.active_face:
                    cv2.putText(
                        canvas,
                        CORNER_NAMES[i],
                        (px + 8, py - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        color,
                        1,
                    )
            for line in self.current_manual_lines.get(face, []):
                if len(line) != 2:
                    continue
                p1, p2 = line
                cv2.line(
                    canvas,
                    (int(p1[0]), int(p1[1])),
                    (int(p2[0]), int(p2[1])),
                    color,
                    2,
                    cv2.LINE_AA,
                )

        if self.pending_manual_line_start is not None:
            pending_face, p = self.pending_manual_line_start
            if pending_face in FACE_COLORS:
                cv2.circle(canvas, (int(p[0]), int(p[1])), 8, FACE_COLORS[pending_face], 2)
                cv2.putText(
                    canvas,
                    f"{pending_face.upper()} line start",
                    (int(p[0]) + 10, int(p[1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    FACE_COLORS[pending_face],
                    1,
                )

        info_h = 112
        panel = np.zeros((info_h, canvas.shape[1], 3), dtype=np.uint8)
        panel[:] = (34, 34, 34)
        image_name = self.image_paths[self.index].name
        cv2.putText(panel, f"{self.index + 1}/{len(self.image_paths)}  {image_name}", (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(panel, f"Active face: {self.active_face.upper()}  (1=TOP, 2=LEFT, 3=RIGHT, TAB=cycle)",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 230, 240), 1)
        cv2.putText(panel, "Drag points/lines with mouse | S=save | R=reset | N/P=next/prev | Q=quit",
                    (10, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (220, 230, 240), 1)
        cv2.putText(panel, "Double-click point A then B to draw inner line on active face | C clears active face lines", (10, 101),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (190, 190, 190), 1)
        return np.vstack((panel, canvas))

    def _clamp_point(self, x: int, y: int) -> Tuple[float, float]:
        assert self.current_image is not None
        h, w = self.current_image.shape[:2]
        return float(max(0, min(w - 1, x))), float(max(0, min(h - 1, y)))

    def _pick_nearest_corner(self, x: int, y: int, threshold: float = 20.0) -> Optional[Tuple[str, int]]:
        best = None
        best_d = float("inf")
        for face in FACE_ORDER:
            pts = self.current_points[face]
            for i, pt in enumerate(pts):
                d = np.linalg.norm(np.array([x, y], dtype=np.float32) - pt)
                if d < best_d:
                    best_d = d
                    best = (face, i)
        if best is not None and best_d <= threshold:
            return best
        return None

    def _pick_nearest_line(self, x: int, y: int, threshold: float = 14.0) -> Optional[Tuple[str, str, int]]:
        """
        Pick nearest internal line in active face.
        Returns (face, axis, index) where axis is 'u' or 'v'.
        """
        face = self.active_face
        quad = self.current_points[face]
        tl, tr, br, bl = quad
        p = np.array([x, y], dtype=np.float32)

        candidates: List[Tuple[float, str, int]] = []
        for axis in ("u", "v"):
            splits = self.current_grid_splits[face][axis]
            for idx, t in enumerate(splits):
                if axis == "u":
                    a = (1 - t) * tl + t * tr
                    b = (1 - t) * bl + t * br
                else:
                    a = (1 - t) * tl + t * bl
                    b = (1 - t) * tr + t * br
                d = self._point_to_segment_distance(p, a, b)
                candidates.append((d, axis, idx))

        if not candidates:
            return None
        candidates.sort(key=lambda c: c[0])
        d, axis, idx = candidates[0]
        if d <= threshold:
            return face, axis, idx
        return None

    @staticmethod
    def _point_to_segment_distance(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
        ab = b - a
        denom = np.dot(ab, ab)
        if denom <= 1e-8:
            return float(np.linalg.norm(p - a))
        t = np.dot(p - a, ab) / denom
        t = max(0.0, min(1.0, t))
        proj = a + t * ab
        return float(np.linalg.norm(p - proj))

    def _projection_ratio(self, p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
        ab = b - a
        denom = np.dot(ab, ab)
        if denom <= 1e-8:
            return 0.5
        t = np.dot(p - a, ab) / denom
        return float(max(0.02, min(0.98, t)))

    def _set_line_position_from_point(self, face: str, axis: str, idx: int, x: int, y: int) -> None:
        p = np.array([x, y], dtype=np.float32)
        quad = self.current_points[face]
        tl, tr, br, bl = quad
        if axis == "u":
            t1 = self._projection_ratio(p, tl, tr)
            t2 = self._projection_ratio(p, bl, br)
            t = 0.5 * (t1 + t2)
        else:
            t1 = self._projection_ratio(p, tl, bl)
            t2 = self._projection_ratio(p, tr, br)
            t = 0.5 * (t1 + t2)
        arr = self.current_grid_splits[face][axis]
        arr[idx] = max(0.05, min(0.95, t))
        arr.sort()

    def _sync_shared_corners_from(self, source_face: str, source_idx: int) -> None:
        """
        Enforce shared-corner constraints:
        - top south <-> left top-right <-> right top-left
        - top west  <-> left top-left
        - top east  <-> right top-right
        """
        links = {
            ("top", 2): [("left", 1), ("right", 0)],
            ("left", 1): [("top", 2), ("right", 0)],
            ("right", 0): [("top", 2), ("left", 1)],
            ("top", 3): [("left", 0)],
            ("left", 0): [("top", 3)],
            ("top", 1): [("right", 1)],
            ("right", 1): [("top", 1)],
            ("right", 3): [("left", 2)],
            ("left", 2): [("right", 3)],
        }
        src_key = (source_face, source_idx)
        src_point = self.current_points[source_face][source_idx].copy()
        for dst_face, dst_idx in links.get(src_key, []):
            self.current_points[dst_face][dst_idx] = src_point.copy()

    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param: object) -> None:
        if self.current_image is None:
            return
        panel_h = 112
        if y < panel_h:
            return
        img_y = y - panel_h

        if event == cv2.EVENT_LBUTTONDOWN:
            picked = self._pick_nearest_corner(x, img_y)
            if picked is not None:
                self.dragging = picked
                self.dragging_line = None
            else:
                picked_line = self._pick_nearest_line(x, img_y)
                if picked_line is not None:
                    self.dragging_line = picked_line
                    self.dragging = None
                    return
                # If no nearby corner, move nearest corner in active face.
                pts = self.current_points[self.active_face]
                dists = [np.linalg.norm(np.array([x, img_y], dtype=np.float32) - p) for p in pts]
                idx = int(np.argmin(dists))
                picked = (self.active_face, idx)
                self.dragging = picked
                self.dragging_line = None

        elif event == cv2.EVENT_LBUTTONDBLCLK:
            nx, ny = self._clamp_point(x, img_y)
            point = np.array([nx, ny], dtype=np.float32)
            if self.pending_manual_line_start is None:
                self.pending_manual_line_start = (self.active_face, point)
                return
            start_face, start_pt = self.pending_manual_line_start
            if start_face != self.active_face:
                self.pending_manual_line_start = (self.active_face, point)
                return
            self.current_manual_lines[self.active_face].append([
                [float(start_pt[0]), float(start_pt[1])],
                [float(point[0]), float(point[1])],
            ])
            self.pending_manual_line_start = None

        elif event == cv2.EVENT_MOUSEMOVE and self.dragging is not None:
            face, idx = self.dragging
            nx, ny = self._clamp_point(x, img_y)
            self.current_points[face][idx] = np.array([nx, ny], dtype=np.float32)
            self._sync_shared_corners_from(face, idx)

        elif event == cv2.EVENT_MOUSEMOVE and self.dragging_line is not None:
            face, axis, idx = self.dragging_line
            nx, ny = self._clamp_point(x, img_y)
            self._set_line_position_from_point(face, axis, idx, int(nx), int(ny))

        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = None
            self.dragging_line = None

    def run(self) -> None:
        if not self._load_current():
            return

        window = "Cube Face Quad Annotator"
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window, self._mouse_callback)

        while True:
            frame = self._render()
            cv2.imshow(window, frame)
            key = cv2.waitKey(20) & 0xFF

            if key in (ord("q"), 27):  # q / esc
                self._save_annotation()
                break
            if key == ord("s"):
                self._save_annotation()
            elif key == ord("r"):
                if self.current_image is not None:
                    self.current_points = self._default_points(self.current_image)
                    self.current_grid_splits = self._default_grid_splits()
                    self.current_manual_lines = self._default_manual_lines()
                    self._sync_shared_corners_from("top", 2)
                    self.pending_manual_line_start = None
                    print("Reset to defaults.")
            elif key in (ord("c"), ord("C")):
                self.current_manual_lines[self.active_face] = []
                self.pending_manual_line_start = None
                print(f"Cleared manual inner lines for {self.active_face.upper()}.")
            elif key in (ord("1"), ord("2"), ord("3")):
                self.active_face = FACE_ORDER[int(chr(key)) - 1]
            elif key == 9:  # TAB
                idx = (FACE_ORDER.index(self.active_face) + 1) % len(FACE_ORDER)
                self.active_face = FACE_ORDER[idx]
            elif key in (ord("n"), ord("N")):
                self._save_annotation()
                self.index = (self.index + 1) % len(self.image_paths)
                self._load_current()
            elif key in (ord("p"), ord("P")):
                self._save_annotation()
                self.index = (self.index - 1) % len(self.image_paths)
                self._load_current()

        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate cube face quads for top-view photos")
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("training_data") / "CubeStates",
        help="Directory containing cube-state photos",
    )
    parser.add_argument(
        "--annotations-dir",
        type=Path,
        default=None,
        help="Directory to write annotation JSON files (default: <images-dir>/annotations)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    images_dir: Path = args.images_dir
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    annotator = CubeFaceAnnotator(images_dir=images_dir, annotations_dir=args.annotations_dir)
    annotator.run()


if __name__ == "__main__":
    main()
