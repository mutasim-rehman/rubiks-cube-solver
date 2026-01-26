# Quick Start Guide

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Method 1: Webcam (Recommended for first-time use)

```bash
python main.py --webcam
```

This will:
1. Open your webcam and show a **full 2D cube net diagram** (like the unfolded cube)
2. The 2D net shows all 6 faces and their spatial relationships:
   ```
       [3] Up (White)
   [5] [1] [2] [6]
   Left Front Right Back
       [4] Down (Yellow)
   ```
3. Guide you through a logical sequence:
   - **Step 1**: Start with **Blue** face (Back) - shown as face #6
   - **Step 2**: Rotate to show **Red** face (Right) - shown as face #2
   - **Step 3**: Rotate to show **Green** face (Front) - shown as face #1
   - **Step 4**: Rotate to show **Orange** face (Left) - shown as face #5
   - **Step 5**: Move up to show **Yellow** face (Down) - shown as face #4
   - **Step 6**: Move up again to show **White** face (Up) - shown as face #3
4. **Use the 2D net to see rotation direction**: The diagram shows which faces are adjacent, so you know which way to rotate
5. Press **SPACE** to capture each face
6. The 2D net highlights the current face (green) and next face (orange) with rotation arrows
7. Display the solution with optimal move count

**Controls:**
- **SPACE**: Capture current face
- **ESC**: Skip current face
- **Q**: Quit capture process

**Alignment Feature:**
- A green alignment box appears in the camera feed
- The box matches the 2D net diagram shown in the guide window
- Align your cube face with the green box (it has a 3x3 grid like the diagram)
- Corner markers help you position the cube accurately
- Alignment quality is shown in real-time (green = good, orange = needs adjustment)
- The alignment box helps ensure accurate color detection

### Method 2: Image File

```bash
python main.py --image path/to/cube_image.jpg
```

**Note:** The current face detection is simplified. For best results:
- Ensure good lighting
- Cube faces should be clearly visible
- Consider manually cropping faces if automatic detection fails

### Method 3: Manual Input (For Testing)

```python
from cube_solver import CubeSolver

solver = CubeSolver()

# Define cube state: 6 faces, each 3x3
faces = [
    # Up face (White center)
    [['W', 'W', 'W'],
     ['W', 'W', 'W'],
     ['W', 'W', 'W']],
    # Right face (Red center)
    [['R', 'R', 'R'],
     ['R', 'R', 'R'],
     ['R', 'R', 'R']],
    # ... (add all 6 faces)
]

solution = solver.solve_from_manual_input(faces)
print(f"Solution: {solution}")
```

## Understanding the Solution

The solution uses standard Rubik's cube notation:
- **U, R, F, D, L, B**: Rotate face 90° clockwise (Up, Right, Front, Down, Left, Back)
- **U', R', F', D', L', B'**: Rotate face 90° counter-clockwise
- **U2, R2, F2, D2, L2, B2**: Rotate face 180°

Example: `U R' F2 D` means:
1. Rotate Up face clockwise
2. Rotate Right face counter-clockwise
3. Rotate Front face 180°
4. Rotate Down face clockwise

## Tips for Best Results

1. **Lighting**: Use even, bright lighting to avoid shadows
2. **Background**: Use a contrasting background (not the same color as cube)
3. **Distance**: Keep cube at appropriate distance from camera
4. **Focus**: Ensure cube is in focus
5. **Color Calibration**: If colors are misclassified, you may need to adjust the color thresholds in `color_classifier.py`

## Troubleshooting

**Problem**: "Detected X faces, expected 6"
- **Solution**: Ensure all 6 faces are visible, or use webcam mode to capture faces one at a time

**Problem**: Colors are misclassified
- **Solution**: Improve lighting, or manually adjust color thresholds in `color_classifier.py`

**Problem**: "Error solving cube"
- **Solution**: Check that the cube state is valid (each face has exactly 9 stickers, colors are correct)

## Next Steps

- Improve face detection algorithm for better automatic detection
- Add color calibration tool
- Add visualization of cube state
- Add step-by-step solution animation
