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

## Project Structure

```
rubiks-cube-solver/
├── cube_vision.py          # Computer vision for face detection
├── color_classifier.py     # ML-based color classification
├── cube_state.py           # Cube state representation
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
