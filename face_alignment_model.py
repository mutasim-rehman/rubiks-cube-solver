"""
Alignment model for predicting top-view cube face quads from annotated images.
"""

import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass


FACE_ORDER = ["top", "left", "right"]
MODEL_FILE = "face_alignment_model.pkl"


def load_image_any(path: Path) -> Optional[np.ndarray]:
    """Load image (BGR ndarray), with HEIC fallback."""
    img = cv2.imread(str(path))
    if img is not None:
        return img
    try:
        pil_img = Image.open(path)
        rgb = np.array(pil_img.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def extract_features(img: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """
    Build compact, lighting-tolerant features for alignment regression.
    Features = grayscale + Canny edges, concatenated.
    """
    w, h = size
    resized = cv2.resize(img, (w, h))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    feat = np.concatenate([gray.reshape(-1), edges.reshape(-1)]).astype(np.float32) / 255.0
    return feat


class FaceAlignmentModel:
    def __init__(self, model_path: str = MODEL_FILE, feature_size: Tuple[int, int] = (64, 64)) -> None:
        self.model_path = model_path
        self.feature_size = feature_size
        self.regressor: Optional[Pipeline] = None

    def is_trained(self) -> bool:
        return self.regressor is not None

    def load(self) -> bool:
        if not os.path.exists(self.model_path):
            return False
        try:
            with open(self.model_path, "rb") as f:
                payload = pickle.load(f)
            self.feature_size = tuple(payload["feature_size"])
            self.regressor = payload["regressor"]
            return True
        except Exception:
            return False

    def save(self) -> None:
        if self.regressor is None:
            raise ValueError("No trained regressor to save.")
        payload = {
            "feature_size": self.feature_size,
            "regressor": self.regressor,
        }
        with open(self.model_path, "wb") as f:
            pickle.dump(payload, f)

    def train_from_annotations(
        self,
        images_dir: str,
        annotations_dir: Optional[str] = None,
        min_samples: int = 5,
    ) -> Dict[str, float]:
        images_path = Path(images_dir)
        ann_path = Path(annotations_dir) if annotations_dir else (images_path / "annotations")
        if not images_path.exists():
            raise FileNotFoundError(f"Images directory not found: {images_path}")
        if not ann_path.exists():
            # Fallback: allow annotation dir as sibling of images_dir.
            sibling_ann = images_path.parent / "annotations"
            if sibling_ann.exists():
                ann_path = sibling_ann
            else:
                ann_path.mkdir(parents=True, exist_ok=True)
                raise FileNotFoundError(
                    f"Annotations directory not found. Created empty directory: {ann_path}\n"
                    "Add annotation JSON files (or run annotate_cube_faces.py) and train again."
                )

        X: List[np.ndarray] = []
        y: List[np.ndarray] = []
        sample_count = 0

        for ann_file in sorted(ann_path.glob("*.json")):
            with open(ann_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            image_file = data.get("image_file")
            if not image_file:
                continue
            img = load_image_any(images_path / image_file)
            if img is None:
                continue

            faces = data.get("faces", {})
            if any(face not in faces or len(faces[face]) != 4 for face in FACE_ORDER):
                continue

            h, w = img.shape[:2]
            target = []
            for face in FACE_ORDER:
                for x, yv in faces[face]:
                    target.append(float(x) / max(1.0, float(w)))
                    target.append(float(yv) / max(1.0, float(h)))

            X.append(extract_features(img, self.feature_size))
            y.append(np.array(target, dtype=np.float32))
            sample_count += 1

        if sample_count < min_samples:
            raise ValueError(f"Need at least {min_samples} annotated images, found {sample_count}")

        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y, dtype=np.float32)

        # Linear baseline works surprisingly well for normalized keypoint regression.
        self.regressor = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", MultiOutputRegressor(Ridge(alpha=1.0))),
        ])
        self.regressor.fit(X_arr, y_arr)

        preds = self.regressor.predict(X_arr)
        rmse = float(np.sqrt(np.mean((preds - y_arr) ** 2)))
        return {"samples": float(sample_count), "train_rmse_norm": rmse}

    def evaluate_annotations(
        self,
        images_dir: str,
        annotations_dir: Optional[str] = None,
        overlays_dir: Optional[str] = None,
    ) -> Dict[str, object]:
        """
        Evaluate trained model against annotations and optionally save overlays.
        Returns aggregate metrics and per-image errors.
        """
        if self.regressor is None:
            raise ValueError("Alignment model is not loaded/trained.")

        images_path = Path(images_dir)
        ann_path = Path(annotations_dir) if annotations_dir else (images_path / "annotations")
        if not images_path.exists():
            raise FileNotFoundError(f"Images directory not found: {images_path}")
        if not ann_path.exists():
            raise FileNotFoundError(f"Annotations directory not found: {ann_path}")

        out_path = Path(overlays_dir) if overlays_dir else None
        if out_path is not None:
            out_path.mkdir(parents=True, exist_ok=True)

        per_image = []
        pixel_errors = []

        for ann_file in sorted(ann_path.glob("*.json")):
            with open(ann_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            image_file = data.get("image_file")
            if not image_file:
                continue

            img = load_image_any(images_path / image_file)
            if img is None:
                continue

            faces = data.get("faces", {})
            if any(face not in faces or len(faces[face]) != 4 for face in FACE_ORDER):
                continue

            gt = {face: np.array(faces[face], dtype=np.float32) for face in FACE_ORDER}
            pred = self.predict_quads(img)

            # Mean point error in pixels over 12 points
            dists = []
            for face in FACE_ORDER:
                for i in range(4):
                    d = np.linalg.norm(pred[face][i] - gt[face][i])
                    dists.append(float(d))
            mean_px = float(np.mean(dists))
            pixel_errors.append(mean_px)
            per_image.append({"image_file": image_file, "mean_point_error_px": mean_px})

            if out_path is not None:
                vis = self._create_eval_overlay(img, gt, pred, image_file, mean_px)
                stem = Path(image_file).stem
                cv2.imwrite(str(out_path / f"{stem}_eval.png"), vis)

        if not per_image:
            raise ValueError("No valid annotated samples found for evaluation.")

        per_image_sorted = sorted(per_image, key=lambda x: x["mean_point_error_px"], reverse=True)
        return {
            "samples": len(per_image_sorted),
            "mean_error_px": float(np.mean(pixel_errors)),
            "median_error_px": float(np.median(pixel_errors)),
            "max_error_px": float(np.max(pixel_errors)),
            "per_image": per_image_sorted,
        }

    def _create_eval_overlay(
        self,
        img: np.ndarray,
        gt: Dict[str, np.ndarray],
        pred: Dict[str, np.ndarray],
        image_file: str,
        mean_px: float,
    ) -> np.ndarray:
        colors = {
            "top": (255, 255, 255),
            "left": (0, 255, 0),
            "right": (255, 0, 0),
        }
        canvas = img.copy()

        # GT = solid thick, prediction = thin + markers
        for face in FACE_ORDER:
            c = colors[face]
            gt_q = gt[face].astype(np.int32).reshape((-1, 1, 2))
            pred_q = pred[face].astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(canvas, [gt_q], True, c, 3)
            cv2.polylines(canvas, [pred_q], True, c, 1)
            for p in pred[face]:
                cv2.circle(canvas, (int(p[0]), int(p[1])), 3, c, -1)

        header_h = 70
        panel = np.zeros((header_h, canvas.shape[1], 3), dtype=np.uint8)
        panel[:] = (34, 34, 34)
        cv2.putText(panel, f"{image_file}", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(
            panel,
            f"Mean point error: {mean_px:.2f}px | GT=thick, Pred=thin+points",
            (10, 54),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (210, 210, 210),
            1,
        )
        return np.vstack((panel, canvas))

    def predict_quads(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        if self.regressor is None:
            raise ValueError("Alignment model is not loaded/trained.")

        feat = extract_features(img, self.feature_size).reshape(1, -1)
        pred = self.regressor.predict(feat)[0]
        h, w = img.shape[:2]

        out: Dict[str, np.ndarray] = {}
        k = 0
        for face in FACE_ORDER:
            pts = []
            for _ in range(4):
                x_norm = float(np.clip(pred[k], 0.0, 1.0))
                y_norm = float(np.clip(pred[k + 1], 0.0, 1.0))
                pts.append([x_norm * w, y_norm * h])
                k += 2
            out[face] = np.array(pts, dtype=np.float32)
        return out
