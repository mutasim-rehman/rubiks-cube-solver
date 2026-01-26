# Rubik's Cube Solver Robot

A Rubik's Cube solving robot using computer vision with machine learning–assisted color classification and algorithmic solving.

## Features

- **Computer Vision**: Detects and extracts cube faces from images/video
- **ML Color Classification**: Machine learning model to accurately classify cube colors
- **Optimal Solver**: Finds the solving path with the least number of movements
- **Cube State Representation**: Efficient data structure to represent cube state

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from cube_solver import CubeSolver

solver = CubeSolver()
# Provide path to image or use webcam
solution = solver.solve_from_image('cube_image.jpg')
print(f"Solution: {solution}")
```

### Using Webcam

```python
from cube_solver import CubeSolver

solver = CubeSolver()
solution = solver.solve_from_webcam()
```

The webcam mode features:
- **Full 2D Cube Net Diagram**: Shows the complete unfolded cube with all 6 faces visible
  - Displays spatial relationships between faces (which faces are adjacent)
  - Numbered faces (1-6) matching standard cube net diagrams
  - Helps users understand which direction to rotate the cube
- **Rotation Hints**: Orange arrows show rotation direction from current to next face
- **Visual Status**: 
  - Green border = Current face to capture
  - Orange border = Next face in sequence
  - Gray = Remaining faces
  - Dimmed colors = Already captured faces
- **Alignment Box Overlay**: Green alignment box in camera feed matches the 2D net diagram
- **3x3 Grid Guide**: The alignment box shows a 3x3 grid matching the cube face structure
- **Corner Markers**: L-shaped corner markers for precise alignment
- **Alignment Detection**: Real-time feedback on alignment quality
- **Guided Sequence**: Logical rotation sequence (Blue → Red → Green → Orange → Yellow → White)
- **Real-time Instructions**: Step-by-step guidance for each face

## Project Structure

```
rubiks-cube-solver/
├── cube_vision.py          # Computer vision for face detection
├── color_classifier.py     # ML-based color classification
├── cube_state.py           # Cube state representation
├── cube_visualizer.py      # 2D net visualization and UI guides
├── cube_solver.py          # Solving algorithm
├── main.py                 # Main application
└── requirements.txt        # Dependencies
```

## How It Works

1. **Face Detection**:** The computer vision module detects the cube faces from the input image
2. **Color Classification**: ML model classifies each sticker color (R, G, B, Y, O, W)
3. **State Representation**: Colors are converted to a cube state string
4. **Solving**: Algorithm finds the optimal solution path
5. **Output**: Returns the sequence of moves to solve the cube

## Requirements

- Python 3.8+
- Webcam or images of Rubik's cube
- Good lighting conditions for accurate color detection
