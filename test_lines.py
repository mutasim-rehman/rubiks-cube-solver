#!/usr/bin/env python3
import sys
import cv2
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans

# ── Configuration ────────────────────────────────────────────────────────────

COLOR_RANGES = {
    # Broadened ranges to account for shadows and different lighting
    "red":    [((0, 70, 50), (12, 255, 255)), ((160, 70, 50), (180, 255, 255))],
    "orange": [((10, 70, 50), (28, 255, 255))],
    "yellow": [((25, 60, 50), (48, 255, 255))],
    "green":  [((40, 60, 40), (95, 255, 255))],
    "blue":   [((95, 60, 40), (145, 255, 255))],
    "white":  [((0, 0, 100), (180, 80, 255))] # Lowered V from 140 to 100
}

# LOWERED from 500 to 100 to catch smaller images/tiles
MIN_TILE_AREA = 100

# Flood fill tolerance (LAB Euclidean distance)
FLOOD_TOL = 20
ALPHA = 0.5  # Opacity of the region highlights (0.0 to 1.0)


# ── Detection Logic ──────────────────────────────────────────────────────────

def get_refined_tiles(img):
    h, w = img.shape[:2]
    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Optional: Brightness normalization (CLAHE)
    # This helps if the image is unevenly lit
    lab_planes = list(cv2.split(img_lab))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab_planes[0] = clahe.apply(lab_planes[0].astype(np.uint8))
    img_norm = cv2.merge(lab_planes)
    img_norm = cv2.cvtColor(img_norm, cv2.COLOR_LAB2BGR)

    seed_mask = np.zeros((h, w), dtype=np.uint8)
    for color_name, ranges in COLOR_RANGES.items():
        for (low, high) in ranges:
            m = cv2.inRange(hsv, np.array(low), np.array(high))
            seed_mask = cv2.bitwise_or(seed_mask, m)

    # DEBUG: Save this to see what colors are being picked up
    cv2.imwrite("debug_mask.png", seed_mask)
    print("  [debug] Check 'debug_mask.png' to see detected color regions.")

    # Clean the mask
    kernel = np.ones((3, 3), np.uint8)
    seed_mask = cv2.morphologyEx(seed_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(seed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tiles = []
    processed_mask = np.zeros((h, w), dtype=np.uint8)

    for cnt in contours:
        # Use the lowered MIN_TILE_AREA
        if cv2.contourArea(cnt) < MIN_TILE_AREA: continue

        M = cv2.moments(cnt)
        if M["m00"] == 0: continue
        cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])

        if processed_mask[cy, cx] > 0: continue

        flood_mask = np.zeros((h + 2, w + 2), np.uint8)
        # Use the normalized image for flood fill to be more consistent
        cv2.floodFill(
            img_norm, flood_mask, (cx, cy), 0,
            loDiff=(FLOOD_TOL,) * 3, upDiff=(FLOOD_TOL,) * 3,
            flags=cv2.FLOODFILL_MASK_ONLY
        )

        actual_mask = flood_mask[1:-1, 1:-1]
        processed_mask = cv2.bitwise_or(processed_mask, actual_mask)

        tile_cnts, _ = cv2.findContours(actual_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if tile_cnts:
            best_cnt = max(tile_cnts, key=cv2.contourArea)
            M = cv2.moments(best_cnt)
            if M["m00"] > 0:
                tx, ty = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                tiles.append({"contour": best_cnt, "center": (tx, ty)})

    return tiles

def group_faces(tiles):
    """Clusters detected tiles into 3 faces based on spatial centers."""
    if len(tiles) < 9:
        raise RuntimeError(f"Only found {len(tiles)} tiles. Need at least 9.")

    centers = np.array([t["center"] for t in tiles], dtype=np.float32)
    num_clusters = min(3, len(tiles) // 3)

    kmeans = KMeans(n_clusters=num_clusters, n_init=10).fit(centers)

    faces = []
    for i in range(num_clusters):
        face_tiles = [tiles[j] for j in range(len(tiles)) if kmeans.labels_[j] == i]
        # Sort by area/proximity to keep the most 'grid-like' 9 if needed
        faces.append(face_tiles)
    return faces


# ── Main ─────────────────────────────────────────────────────────────────────

def process_image(img_path):
    img = cv2.imread(str(img_path))
    if img is None: raise FileNotFoundError(f"Image {img_path} not found.")

    canvas = img.copy()
    overlay = np.zeros_like(img)

    print("[1/3] Growing regions from tile seeds...")
    tiles = get_refined_tiles(img)

    print("[2/3] Clustering regions into faces...")
    try:
        faces = group_faces(tiles)
    except Exception as e:
        print(f"Error: {e}")
        return

    print("[3/3] Drawing grids and highlights...")
    face_colors = [(0, 255, 255), (255, 0, 255), (255, 255, 0)]  # Cyan, Magenta, Yellow

    for i, face in enumerate(faces):
        color = face_colors[i % 3]

        # Draw each region highlight
        for tile in face:
            cv2.drawContours(overlay, [tile["contour"]], -1, color, -1)
            cv2.circle(canvas, tile["center"], 4, (0, 0, 0), -1)

        # Fit a grid boundary to the group of tiles
        if len(face) >= 4:
            pts = np.array([t["center"] for t in face], dtype=np.float32)
            rect = cv2.minAreaRect(pts)
            box = cv2.boxPoints(rect)
            # FIX: Use .astype(np.int32) instead of the removed np.int0
            box = box.astype(np.int32)
            cv2.polylines(canvas, [box], True, color, 3, cv2.LINE_AA)

    # Apply transparency
    # Result = img * (1 - alpha) + overlay * alpha
    result = cv2.addWeighted(overlay, ALPHA, canvas, 1, 0)

    out_path = img_path.parent / (img_path.stem + "_detected.png")
    cv2.imwrite(str(out_path), result)
    print(f"Success! Output saved to: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_lines.py <image_path>")
    else:
        process_image(Path(sys.argv[1]))