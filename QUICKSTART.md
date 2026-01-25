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
1. Open your webcam
2. Prompt you to show each face of the cube (one at a time)
3. Press SPACE to capture each face
4. Display the solution with optimal move count

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
