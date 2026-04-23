#!/usr/bin/env python3
"""
Rubik's Cube Face Grid Drawer
Usage: python test_lines.py <image_path>

Interactive tool to draw a 3-face grid over a Rubik's cube photo.
Click to place the 4 corner points of each visible face, then the
script draws the 4x4 grid lines for color-cell sampling.

Controls:
  - Follow on-screen prompts to click cube corners
  - R  : reset current face
  - Z  : undo last point
  - S  : save result as <image>_lines.png
  - Q  : quit
"""

import sys
import cv2
import numpy as np
from pathlib import Path


# ── Config ────────────────────────────────────────────────────────────────────

FACE_CONFIGS = [
    {"name": "TOP face",   "color": (0, 255, 255),   "hint": "Click 4 corners: top-left → top-right → bottom-right → bottom-left"},
    {"name": "LEFT face",  "color": (255, 180, 0),   "hint": "Click 4 corners: top-left → top-right → bottom-right → bottom-left"},
    {"name": "RIGHT face", "color": (0, 200, 255),   "hint": "Click 4 corners: top-left → top-right → bottom-right → bottom-left"},
]

GRID_N       = 3          # 3×3 cube → 4 lines each direction
LINE_THICK   = 2
CORNER_R     = 6
SAMPLE_R     = 8          # radius of sample-dot drawn at cell center
FONT         = cv2.FONT_HERSHEY_SIMPLEX


# ── Geometry helpers ──────────────────────────────────────────────────────────

def lerp(p0, p1, t):
    """Linear interpolation between two (x,y) points."""
    return (
        p0[0] + (p1[0] - p0[0]) * t,
        p0[1] + (p1[1] - p0[1]) * t,
    )


def grid_lines(corners):
    """
    Given 4 corners [TL, TR, BR, BL] (each a float (x,y)),
    return the parametric line segments for an N×N grid.
    Returns list of ((x1,y1),(x2,y2)) pairs (integer pixel coords).
    """
    TL, TR, BR, BL = corners
    lines = []
    steps = GRID_N + 1   # number of lines = N+1

    # Lines parallel to the top/bottom edges
    for i in range(steps):
        t = i / GRID_N
        p_left  = lerp(TL, BL, t)
        p_right = lerp(TR, BR, t)
        lines.append((
            (int(round(p_left[0])),  int(round(p_left[1]))),
            (int(round(p_right[0])), int(round(p_right[1]))),
        ))

    # Lines parallel to the left/right edges
    for j in range(steps):
        t = j / GRID_N
        p_top    = lerp(TL, TR, t)
        p_bottom = lerp(BL, BR, t)
        lines.append((
            (int(round(p_top[0])),    int(round(p_top[1]))),
            (int(round(p_bottom[0])), int(round(p_bottom[1]))),
        ))

    return lines


def cell_centers(corners):
    """Return the center point of each cell in the N×N grid."""
    TL, TR, BR, BL = corners
    centers = []
    for row in range(GRID_N):
        for col in range(GRID_N):
            t_row = (row + 0.5) / GRID_N
            t_col = (col + 0.5) / GRID_N
            left   = lerp(TL, BL, t_row)
            right  = lerp(TR, BR, t_row)
            center = lerp(left, right, t_col)
            centers.append((int(round(center[0])), int(round(center[1]))))
    return centers


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_face(canvas, corners, color):
    """Draw the grid lines and cell-center dots for one face."""
    for p1, p2 in grid_lines(corners):
        cv2.line(canvas, p1, p2, color, LINE_THICK, cv2.LINE_AA)
    for cx, cy in cell_centers(corners):
        cv2.circle(canvas, (cx, cy), SAMPLE_R, color, 2, cv2.LINE_AA)
        cv2.circle(canvas, (cx, cy), 2, color, -1)


def draw_corners(canvas, pts, color):
    """Draw the clicked corner dots."""
    for i, (x, y) in enumerate(pts):
        cv2.circle(canvas, (x, y), CORNER_R, color, -1, cv2.LINE_AA)
        cv2.putText(canvas, str(i + 1), (x + 8, y - 8),
                    FONT, 0.55, color, 2, cv2.LINE_AA)


def overlay_status(canvas, face_idx, pts, faces_done):
    """Write instructions onto the canvas."""
    h, w = canvas.shape[:2]
    cfg = FACE_CONFIGS[face_idx]

    # Semi-transparent banner at top
    banner = canvas.copy()
    cv2.rectangle(banner, (0, 0), (w, 60), (30, 30, 30), -1)
    cv2.addWeighted(banner, 0.65, canvas, 0.35, 0, canvas)

    cv2.putText(canvas,
                f"Face {face_idx + 1}/3 — {cfg['name']}  ({len(pts)}/4 corners)",
                (10, 22), FONT, 0.65, cfg["color"], 2, cv2.LINE_AA)
    cv2.putText(canvas,
                cfg["hint"] + "   |  Z=undo  R=reset face  S=save  Q=quit",
                (10, 48), FONT, 0.42, (200, 200, 200), 1, cv2.LINE_AA)

    # Show completed faces count
    if faces_done:
        cv2.putText(canvas,
                    f"Completed faces: {faces_done}",
                    (w - 220, 22), FONT, 0.55, (100, 255, 100), 1, cv2.LINE_AA)


# ── Main application ──────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_lines.py <image_path>")
        sys.exit(1)

    img_path = Path(sys.argv[1])
    if not img_path.exists():
        print(f"Error: file not found: {img_path}")
        sys.exit(1)

    original = cv2.imread(str(img_path))
    if original is None:
        print(f"Error: cannot read image: {img_path}")
        sys.exit(1)

    # Resize large images for comfortable display (keep aspect ratio)
    max_dim = 1000
    h, w = original.shape[:2]
    scale = min(max_dim / w, max_dim / h, 1.0)
    if scale < 1.0:
        original = cv2.resize(original, (int(w * scale), int(h * scale)),
                              interpolation=cv2.INTER_AREA)

    # State
    face_idx   = 0          # which face we are currently marking
    current_pts = []        # corner points for current face (up to 4)
    finished_faces = []     # list of (corners, color) for completed faces

    win = "Rubik's Cube Line Tool"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, original.shape[1], original.shape[0])

    def mouse_cb(event, x, y, flags, _param):
        nonlocal current_pts
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(current_pts) < 4:
                current_pts.append((x, y))

    cv2.setMouseCallback(win, mouse_cb)

    saved = False

    while True:
        canvas = original.copy()

        # Draw all completed faces
        for corners, color in finished_faces:
            draw_face(canvas, corners, color)
            draw_corners(canvas, corners, color)

        # Draw in-progress corners
        if face_idx < len(FACE_CONFIGS):
            color = FACE_CONFIGS[face_idx]["color"]
            draw_corners(canvas, current_pts, color)

            # Preview grid as soon as 4 corners are placed
            if len(current_pts) == 4:
                draw_face(canvas, current_pts, color)

            overlay_status(canvas, face_idx, current_pts, len(finished_faces))

        elif not saved:
            # All 3 faces done — prompt to save
            h2, w2 = canvas.shape[:2]
            cv2.putText(canvas,
                        "All faces done!  Press S to save, Q to quit.",
                        (10, h2 - 20), FONT, 0.7, (100, 255, 100), 2, cv2.LINE_AA)

        cv2.imshow(win, canvas)
        key = cv2.waitKey(20) & 0xFF

        # ── Key handling ──────────────────────────────────────────────────────

        if key == ord('q') or key == 27:          # Q / Esc → quit
            break

        elif key == ord('z') and current_pts:     # Z → undo last point
            current_pts.pop()

        elif key == ord('r'):                      # R → reset current face
            current_pts = []

        elif key == ord('s'):                      # S → save
            # Build final output (all finished + current if complete)
            out = original.copy()
            all_faces = list(finished_faces)
            if face_idx < len(FACE_CONFIGS) and len(current_pts) == 4:
                all_faces.append((current_pts, FACE_CONFIGS[face_idx]["color"]))

            for corners, color in all_faces:
                draw_face(out, corners, color)
                draw_corners(out, corners, color)

            out_path = img_path.parent / (img_path.stem + "_lines.png")
            cv2.imwrite(str(out_path), out)
            print(f"Saved → {out_path}")
            saved = True

            # Also print sample-center pixel coordinates for each face
            print("\nCell-center pixel coordinates (for color sampling):")
            for i, (corners, _) in enumerate(all_faces):
                print(f"  Face {i + 1} ({FACE_CONFIGS[i]['name']}):")
                for row in range(GRID_N):
                    row_pts = []
                    for col in range(GRID_N):
                        cx, cy = cell_centers(corners)[row * GRID_N + col]
                        row_pts.append(f"({cx},{cy})")
                    print("    " + "  ".join(row_pts))

        # Auto-advance: if 4 corners placed and user clicks a 4th point,
        # treat it as "confirm this face"
        if face_idx < len(FACE_CONFIGS) and len(current_pts) == 4:
            # Wait for one more key press or click to confirm
            # (the grid preview is already shown; user presses Enter or Space)
            if key in (13, 32):          # Enter or Space → confirm face
                finished_faces.append(
                    (list(current_pts), FACE_CONFIGS[face_idx]["color"])
                )
                current_pts = []
                face_idx += 1
                if face_idx >= len(FACE_CONFIGS):
                    print("All 3 faces marked. Press S to save.")

    cv2.destroyAllWindows()

    if not saved and finished_faces:
        print("Tip: run again and press S to save your markings.")


if __name__ == "__main__":
    main()