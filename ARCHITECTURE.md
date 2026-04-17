# Rubik's Cube Solver — Technical Architecture

This document describes the technical architecture of the Rubik's Cube solving robot, including data flow, component interactions, and UML diagrams.

---

## 1. System Overview

The system is organized in **three layers**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: COMPUTER VISION                                                     │
│  cube_vision.py │ color_classifier.py │ cube_visualizer.py                   │
│  Face detection │ Color classification (KNN/ML) │ 2D net guides & overlays  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: SOLVING ALGORITHM                                                  │
│  cube_state.py │ cube_moves.py │ cube_solver.py │ constraint_solver.py        │
│  State repr.   │ Move permutations │ kociemba integration │ 5-face variant   │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: HARDWARE EXECUTION                                                 │
│  robot.ino │ run_solution.ino                                                │
│  ESP32 + 6× NEMA 17 steppers (A4988) │ Solution embedded or Serial trigger   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Data flow:** `CV → Solver → Solution string → Hardware`

---

## 2. High-Level Component Diagram

```mermaid
graph TB
    subgraph "Entry Points"
        main[main.py]
        api[api.py - Flask]
        collect[collect_training_data.py]
    end

    subgraph "Layer 1: Computer Vision"
        detector[CubeFaceDetector]
        classifier[ColorClassifier]
        visualizer[CubeVisualizer]
    end

    subgraph "Layer 2: Solving"
        solver[CubeSolver]
        state[CubeState]
        moves[cube_moves]
        kociemba[kociemba lib]
        constraint[constraint_solver]
    end

    subgraph "Layer 3: Hardware"
        robot[robot.ino]
        run_sol[run_solution.ino]
    end

    main --> solver
    api --> solver
    collect --> classifier
    collect --> visualizer

    solver --> detector
    solver --> classifier
    solver --> visualizer
    solver --> state
    solver --> kociemba
    solver --> constraint
    state --> moves
    constraint --> moves

    solver -->|"write_solution_to_robot_ino"| run_sol
```

---

## 3. Class Diagram (Core Python Modules)

```mermaid
classDiagram
    class CubeState {
        +UP, RIGHT, FRONT, DOWN, LEFT, BACK: int
        +faces: List~List~List~str~~
        +get_face(face_idx)
        +set_face(face_idx, face)
        +to_kociemba_string() str
        +from_kociemba_string(s) CubeState
        +apply_sequence(moves) CubeState
        +validate() Tuple~bool, str~
        +is_solved() bool
        +to_flat_string() str
    }

    class CubeFaceDetector {
        +face_size: int
        +detect_faces(image_path) List~ndarray~
        +detect_faces_from_frame(frame) List~ndarray~
        -_extract_faces(img) List~ndarray~
        -_divide_into_regions(img) List~ndarray~
        +extract_stickers(face_image) List~ndarray~
        +get_dominant_color(sticker_image) Tuple
    }

    class ColorClassifier {
        +CUBE_COLORS: Dict
        +MODEL_FILE: str
        -scaler: StandardScaler
        -knn: KNeighborsClassifier
        +load_model()
        +save_model()
        +train_model(data_dir)
        +classify_color(sticker_image) str
        +classify_face(face_image) List~List~str~~
        -_extract_features(image) ndarray
        -_get_dominant_color(image) Tuple
        -_classify_by_distance(bgr, hsv) str
    }

    class CubeVisualizer {
        +cell_size: int
        +create_2d_net(...) ndarray
        +create_capture_guide(...) ndarray
        +create_alignment_overlay(frame, face_code) ndarray
        +create_color_preview(...) ndarray
        +detect_alignment_quality(frame, face_code) Tuple
        +visualize_cube_state(cube_state) ndarray
    }

    class CubeSolver {
        -face_detector: CubeFaceDetector
        -color_classifier: ColorClassifier
        -visualizer: CubeVisualizer
        -cube_state: CubeState
        +solve_from_image(path, constrained) str
        +solve_from_webcam(constrained) str
        +solve_from_manual_input(faces, constrained) str
        -_solve(constrained) str
        +display_cube_state()
        +display_solution(solution)
        +format_solution(solution) str
    }

    CubeSolver --> CubeFaceDetector : uses
    CubeSolver --> ColorClassifier : uses
    CubeSolver --> CubeVisualizer : uses
    CubeSolver --> CubeState : creates/manages
    CubeState --> cube_moves : apply_sequence
```

---

## 4. Data Flow: Solve from Image

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Solver as CubeSolver
    participant Detector as CubeFaceDetector
    participant Classifier as ColorClassifier
    participant State as CubeState
    participant Kociemba as kociemba
    participant Ino as run_solution.ino

    Main->>Solver: solve_from_image(path)
    Solver->>Detector: detect_faces(image_path)
    Detector-->>Solver: List[6 face images]

    loop For each face
        Solver->>Classifier: classify_face(face_img)
        Classifier-->>Solver: 3×3 color grid
    end

    Solver->>State: CubeState(cube_faces)
    Solver->>State: to_kociemba_string()
    State-->>Solver: 54-char string

    alt constrained (--no-u)
        Solver->>Solver: solve_without_u(kociemba_string)
    else standard
        Solver->>Kociemba: solve(kociemba_string)
        Kociemba-->>Solver: "U R F2 ..."
    end

    Solver-->>Main: solution string
    Main->>Main: write_solution_to_robot_ino(solution)
    Main->>Ino: Replace SOLUTION_PLACEHOLDER
```

---

## 5. Data Flow: Solve from Webcam

```mermaid
sequenceDiagram
    participant User
    participant Solver as CubeSolver
    participant Classifier as ColorClassifier
    participant Visualizer as CubeVisualizer
    participant State as CubeState

    User->>Solver: solve_from_webcam()
    Solver->>Solver: cv2.VideoCapture(0)

    loop Until 6 faces captured
        User->>Solver: SPACE (capture) / W,G,R,B,O,Y (select face)
        Solver->>Solver: Extract ROI from frame center
        Solver->>Classifier: classify_face(roi)
        Classifier-->>Solver: 3×3 colors
        Solver->>Visualizer: create_alignment_overlay()
        Solver->>Visualizer: create_capture_guide()
        Solver->>Visualizer: create_color_preview()
        Solver-->>User: Display windows (Camera, Guide, Preview)
    end

    User->>Solver: ENTER (finish)
    Solver->>State: CubeState(cube_faces)
    Solver->>Solver: _solve()
    Solver-->>User: solution string
```

---

## 6. Cube State Representation

### Face Order (Internal & Kociemba)

| Index | Face | Color | Kociemba |
|-------|------|-------|----------|
| 0 | Up | White (W) | U |
| 1 | Right | Blue (B) | R |
| 2 | Front | Red (R) | F |
| 3 | Down | Yellow (Y) | D |
| 4 | Left | Green (G) | L |
| 5 | Back | Orange (O) | B |

### Kociemba String Format (54 chars)

```
UUUUUUUUU RRRRRRRRR FFFFFFFFF DDDDDDDDD LLLLLLLLL BBBBBBBBB
  0-8        9-17      18-26      27-35      36-44      45-53
```

### Move Notation

| Notation | Meaning |
|----------|---------|
| `U` | Up face, 90° clockwise |
| `U'` | Up face, 90° counter-clockwise |
| `U2` | Up face, 180° |
| Same for R, F, D, L, B | |

---

## 7. Constraint Solver (5-Face / No-U Mode)

When the robot has no motor on the Up face, the constraint solver rewrites U moves into equivalent L,R,F,B,D sequences.

```mermaid
flowchart LR
    subgraph Input
        K[Kociemba solution]
    end

    subgraph Rewrite
        T[Tokenize]
        M{U/U'/U2?}
        Macro[Replace with precomputed macro]
        Pass[Pass through]
    end

    subgraph Simplify
        Merge[Merge adjacent same-face moves]
        Cancel[Cancel X + X' or X2 + X2]
    end

    subgraph Output
        Out[L,R,F,B,D only solution]
    end

    K --> T
    T --> M
    M -->|Yes| Macro
    M -->|No| Pass
    Macro --> Merge
    Pass --> Merge
    Merge --> Cancel
    Cancel --> Out
```

**Macro discovery:** BFS from solved state using only L,R,F,B,D moves. Target states: `U`, `U'`, `U2` applied to solved cube. Precomputed macros can be loaded from `precomputed_u_macros_5faces.json`.

---

## 8. Move Permutations (cube_moves.py)

Facelet indices follow kociemba: U(0-8), R(9-17), F(18-26), D(27-35), L(36-44), B(45-53).

```mermaid
flowchart TB
    subgraph Permutation Logic
        P[54-element permutation array]
        A[Apply: new[i] = old[perm[i]]]
    end

    subgraph Move Table
        U["U, U', U2"]
        D["D, D', D2"]
        R["R, R', R2"]
        L["L, L', L2"]
        F["F, F', F2"]
        B["B, B', B2"]
    end

    subgraph Functions
        apply["apply_sequence(cubestring, moves)"]
        kociemba_apply["apply_sequence_kociemba() - uses pykociemba"]
    end

    U --> P
    D --> P
    R --> P
    L --> P
    F --> P
    B --> P
    P --> A
    A --> apply
```

`apply_sequence_kociemba` uses the kociemba library's `FaceCube`/`CubieCube` for exact convention matching with the solver output.

---

## 9. Hardware Architecture (ESP32)

```mermaid
flowchart TB
    subgraph ESP32
        Serial[Serial Monitor]
        Loop[loop]
        Process[processCommand]
        MoveFace[moveFace]
    end

    subgraph Motors
        M0[U - STEP:13 DIR:14 EN:33]
        M1[D - STEP:26 DIR:25 EN:27]
        M2[L - STEP:32 DIR:15 EN:19]
        M3[R - STEP:23 DIR:22 EN:18]
        M4[F - STEP:4  DIR:2  EN:5]
        M5[B - STEP:12 DIR:21 EN:17]
    end

    subgraph A4988
        A0[A4988]
        A1[A4988]
        A2[A4988]
        A3[A4988]
        A4[A4988]
        A5[A4988]
    end

    subgraph NEMA17
        N0[NEMA 17]
        N1[NEMA 17]
        N2[NEMA 17]
        N3[NEMA 17]
        N4[NEMA 17]
        N5[NEMA 17]
    end

    Serial --> Loop
    Loop --> Process
    Process --> MoveFace
    MoveFace --> M0
    MoveFace --> M1
    MoveFace --> M2
    MoveFace --> M3
    MoveFace --> M4
    MoveFace --> M5

    M0 --> A0 --> N0
    M1 --> A1 --> N1
    M2 --> A2 --> N2
    M3 --> A3 --> N3
    M4 --> A4 --> N4
    M5 --> A5 --> N5
```

### robot.ino vs run_solution.ino

| Sketch | Purpose | Trigger |
|--------|---------|---------|
| `robot.ino` | Test: paste algorithm in Serial Monitor | Enter |
| `run_solution.ino` | Production: solution embedded by Python | SPACE + Enter |

### Speed Profiles

- **Side faces (L,R,F,B):** `SIDE_START_DELAY = 800`, `SIDE_TARGET_DELAY = 100`, `SIDE_RAMP = 200`
- **U/D faces:** `UD_START_DELAY = 800`, `UD_TARGET_DELAY = 200`, `UD_RAMP = 250`
- **Physical direction:** F and L motors have reversed wiring; `physicalClockwise` is inverted in `run_solution.ino`

---

## 10. API / Web Frontend

```mermaid
sequenceDiagram
    participant Browser
    participant Frontend as frontend/index.html
    participant API as api.py (Flask)
    participant Solver as CubeSolver

    Browser->>Frontend: Load
    Frontend->>API: GET /api/health

    loop Capture 6 faces
        Browser->>Frontend: User captures face
        Frontend->>API: POST /api/classify { image: base64 }
        API->>Solver: color_classifier.classify_face(img)
        API-->>Frontend: { face: [[...]] }
    end

    Frontend->>API: POST /api/solve { faces: [...] }
    API->>Solver: solve_from_manual_input(faces)
    Solver-->>API: solution
    API-->>Frontend: { solution, steps, cubeState }
```

---

## 11. Training Pipeline (Color Classifier)

```mermaid
flowchart LR
    subgraph Collect
        collect[collect_training_data.py]
        webcam[Webcam]
        labels[R,G,B,Y,O,W]
    end

    subgraph Train
        train["ColorClassifier.train_model('training_data')"]
        knn[KNeighborsClassifier]
        scaler[StandardScaler]
    end

    subgraph Features
        bgr[BGR]
        hsv[HSV]
        lab[LAB]
        vec[9-dim feature vector]
    end

    webcam --> collect
    labels --> collect
    collect --> training_data
    training_data --> train
    train --> knn
    train --> scaler
    bgr --> vec
    hsv --> vec
    lab --> vec
    vec --> knn
    knn --> color_model.pkl
```

---

## 12. File Dependency Graph

```mermaid
graph TD
    main[main.py]
    api[api.py]
    collect[collect_training_data.py]

    main --> cube_solver
    api --> cube_solver

    cube_solver[cube_solver.py] --> cube_vision
    cube_solver --> color_classifier
    cube_solver --> cube_visualizer
    cube_solver --> cube_state
    cube_solver --> constraint_solver

    cube_state[cube_state.py] --> cube_moves
    constraint_solver[constraint_solver.py] --> cube_moves
    constraint_solver --> kociemba

    cube_solver --> kociemba[kociemba]

    collect --> color_classifier
    collect --> cube_visualizer

    cube_moves[cube_moves.py] --> kociemba
```

---

## 13. Key Dependencies

| Package | Purpose |
|---------|---------|
| `opencv-python` | Image I/O, face detection, visualization |
| `numpy` | Array operations |
| `scikit-learn` | KMeans, KNN, StandardScaler |
| `kociemba` | Optimal cube solver (two-phase algorithm) |
| `flask` / `flask-cors` | REST API for web frontend |

---

## 14. Glossary

| Term | Definition |
|------|------------|
| **Face** | One of 6 cube sides (U, R, F, D, L, B) |
| **Facelet** | Single sticker; 9 per face, 54 total |
| **Kociemba string** | 54-char representation in URFDLB order |
| **Macro** | Sequence of moves equivalent to a single U/U'/U2 |
| **ROI** | Region of interest (center crop for webcam capture) |
| **2D net** | Unfolded cube layout for capture guidance |
