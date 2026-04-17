# Rubik's Cube Solver Robot

A Rubik's Cube solving robot using computer vision, an optimal solving algorithm, and hardware execution on an ESP32 with stepper motors.

## Architecture (three layers)

The project is organized in three layers:

1. **Computer vision (CV)** — Captures cube state from camera or images: face detection, color classification, and cube state representation.
2. **Solving algorithm** — Takes the cube state and computes an optimal (or constrained) solution sequence in standard notation (e.g. U, D', F2, R, L').
3. **Hardware** — Runs the solution on the physical robot: ESP32 + 6 NEMA 17 stepper motors driven by 6 A4988 drivers; solution is flashed or streamed to the ESP and executed on trigger (e.g. Serial: SPACE + ENTER).

Data flows **CV → solver → solution string → hardware**.

## Features

- **Computer Vision**: Detects and extracts cube faces from images/video
- **ML Color Classification**: Machine learning model to accurately classify cube colors
- **Optimal Solver**: Finds the solving path with the least number of movements
- **Cube State Representation**: Efficient data structure to represent cube state
- **Hardware layer**: ESP32 firmware to run solution on 6-axis stepper rig (NEMA 17 + A4988)

## Installation

```bash
pip install -r requirements.txt
```

### First-time setup: Color classifier

A pre-trained model (`color_model.pkl`) is included — you can run the solver immediately. To retrain from the included training data:

```bash
python -c "from color_classifier import ColorClassifier; c = ColorClassifier(); c.train_model('training_data'); c.save_model()"
```

To collect your own training data, run `python collect_training_data.py`.

### Train alignment model (annotated top-view images)

If you annotated face geometry in `training_data/CubeStates/annotations`, train the
alignment model (quads only) with:

```bash
py train_face_alignment_model.py --images-dir training_data/CubeStates
```

This writes `face_alignment_model.pkl`. When present, `cube_vision.py` uses it for
top/left/right face region alignment in two-image mode. Color detection still uses
the existing `color_model.pkl`.

Evaluate alignment quality and save overlay comparisons:

```bash
py train_face_alignment_model.py --images-dir training_data/CubeStates --evaluate
```

Evaluate an existing model without retraining:

```bash
py train_face_alignment_model.py --images-dir training_data/CubeStates --evaluate-only
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

## Hardware (layer 3)

- **MCU**: ESP32  
- **Drives**: 6× NEMA 17 stepper motors, each driven by an A4988 driver  
- **Pin layout**: Each motor uses 3 pins — **STEP**, **DIR**, **ENABLE** (order in code below).

| Face | Index | STEP | DIR | ENABLE |
|------|--------|------|-----|--------|
| U    | 0      | 13   | 14  | 33     |
| D    | 1      | 26   | 25  | 27     |
| L    | 2      | 32   | 15  | 19     |
| R    | 3      | 23   | 22  | 18     |
| F    | 4      | 4    | 2   | 5      |
| B    | 5      | 12   | 21  | 17     |

```c
// steps, dir, enable
const int motors[6][3] = {
  {13, 14, 33}, // 0: U
  {26, 25, 27}, // 1: D
  {32, 15, 19}, // 2: L
  {23, 22, 18}, // 3: R
  {4, 2, 5},    // 4: F
  {12, 21, 17}  // 5: B
};
```

Step counts and speed profiles (delays, ramp) are calibrated per motor and must not be changed without re-calibration. They are defined in `robot.ino` and mirrored in `run_solution.ino`.

- **robot.ino** — Test sketch: paste an algorithm in Serial Monitor and press Enter to run it.  
- **run_solution.ino** — Production sketch: solution is written here by the Python solver; flash to ESP32, then press **SPACE** and **ENTER** in Serial Monitor to execute the stored algorithm.

## Project Structure

```
rubiks-cube-solver/
├── training_data/         # Pre-collected sticker images (R,G,B,Y,O,W) for KNN training
├── cube_vision.py          # CV: face detection
├── color_classifier.py     # CV: ML color classification
├── cube_state.py           # State representation
├── cube_visualizer.py      # 2D net visualization and UI guides
├── cube_solver.py          # Layer 2: solving algorithm (+ writes solution to run_solution.ino)
├── main.py                 # Main application
├── robot.ino               # Hardware: test sketch (paste algorithm, run)
├── run_solution.ino        # Hardware: run solver-written solution (SPACE+ENTER)
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
