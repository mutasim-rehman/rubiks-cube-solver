"""
Preview saved cube-face annotations.

Usage:
  py preview_cube_annotations.py --images-dir training_data/CubeStates
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass


FACE_ORDER = ["top", "left", "right"]
FACE_COLORS = {
    "top": (255, 255, 255),
    "left": (0, 255, 0),
    "right": (255, 0, 0),
}
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".heic", ".heif"}


def load_image_any(path: Path):
    img = cv2.imread(str(path))
    if img is not None:
        return img
    try:
        pil_img = Image.open(path)
        rgb = np.array(pil_img.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def draw_projected_grid(canvas: np.ndarray, quad: np.ndarray, color, splits=None):
    tl, tr, br, bl = quad
    if not splits:
        splits = {"u": [1.0 / 3.0, 2.0 / 3.0], "v": [1.0 / 3.0, 2.0 / 3.0]}
    for t in splits.get("u", [1.0 / 3.0, 2.0 / 3.0]):
        top_pt = (1 - t) * tl + t * tr
        bottom_pt = (1 - t) * bl + t * br
        cv2.line(canvas, tuple(top_pt.astype(int)), tuple(bottom_pt.astype(int)), color, 2)
    for t in splits.get("v", [1.0 / 3.0, 2.0 / 3.0]):
        left_pt = (1 - t) * tl + t * bl
        right_pt = (1 - t) * tr + t * br
        cv2.line(canvas, tuple(left_pt.astype(int)), tuple(right_pt.astype(int)), color, 2)


def parse_args():
    parser = argparse.ArgumentParser(description="Preview cube quad annotations")
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("training_data") / "CubeStates",
        help="Directory containing source images",
    )
    parser.add_argument(
        "--annotations-dir",
        type=Path,
        default=None,
        help="Directory with JSON annotations (default: <images-dir>/annotations)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    images_dir: Path = args.images_dir
    annotations_dir: Path = args.annotations_dir or (images_dir / "annotations")

    if not images_dir.exists() or not annotations_dir.exists():
        print("Images or annotations directory not found.")
        return

    annotation_files = sorted([p for p in annotations_dir.iterdir() if p.suffix.lower() == ".json"])
    if not annotation_files:
        print("No annotation files found.")
        return

    idx = 0
    window = "Cube Annotation Preview"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    while True:
        ann_path = annotation_files[idx]
        with open(ann_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        image_file = data.get("image_file", "")
        image_path = images_dir / image_file
        img = load_image_any(image_path)
        if img is None:
            canvas = np.zeros((500, 900, 3), dtype=np.uint8)
            cv2.putText(canvas, f"Could not load {image_file}", (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        else:
            canvas = img.copy()
            grid_splits = data.get("grid_splits", {})
            for face in FACE_ORDER:
                quad = np.array(data["faces"][face], dtype=np.float32)
                color = FACE_COLORS[face]
                cv2.polylines(canvas, [quad.astype(np.int32).reshape((-1, 1, 2))], True, color, 2)
                draw_projected_grid(canvas, quad, color, grid_splits.get(face))
                cx, cy = np.mean(quad, axis=0).astype(int)
                cv2.putText(canvas, face.upper(), (int(cx) - 20, int(cy)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            panel = np.zeros((76, canvas.shape[1], 3), dtype=np.uint8)
            panel[:] = (35, 35, 35)
            cv2.putText(panel, f"{idx + 1}/{len(annotation_files)}  {image_file}", (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(panel, "N/P: next/prev   Q or ESC: quit", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (210, 210, 210), 1)
            canvas = np.vstack((panel, canvas))

        cv2.imshow(window, canvas)
        key = cv2.waitKey(0) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord("n"), ord("N")):
            idx = (idx + 1) % len(annotation_files)
        elif key in (ord("p"), ord("P")):
            idx = (idx - 1) % len(annotation_files)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
