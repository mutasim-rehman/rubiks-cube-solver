# Java Project Analysis: 3x3x3-Rubiks-Cube-Solver

## Repository Overview
**Source**: [thatc0der/3x3x3-Rubiks-Cube-Solver](https://github.com/thatc0der/3x3x3-Rubiks-Cube-Solver)

## Key Findings

### 1. Capture Sequence
**Order**: TOP → LEFT → FRONT → RIGHT → BACK → BOTTOM
- This matches standard cube solving conventions
- Our implementation now follows this order: U → L → F → R → B → D

### 2. Cube State Representation

The Java project displays the cube in a flat 2D format:
```
     OYG          <- TOP face (3 rows)
     WYO
     YWG
 YBB RRR WWW OOB  <- LEFT, FRONT, RIGHT, BACK (middle row, 4 columns)
 GBR BRB YGR YOR
 RBW BGO BOY OGG
     RWW          <- BOTTOM face (3 rows)
     OWG
     YYG
```

**Layout Structure**:
- **Top 3 rows** = TOP face (White/Up)
- **Left 3 columns** (middle section) = LEFT face (Orange)
- **Middle-left 3 columns** = FRONT face (Green)
- **Middle-right 3 columns** = RIGHT face (Red)
- **Far right 3 columns** = BACK face (Blue)
- **Bottom 3 rows** = BOTTOM face (Yellow/Down)

### 3. Color Representation
- Uses single letters: O=Orange, Y=Yellow, W=White, G=Green, R=Red, B=Blue
- Matches our color codes: O, Y, W, G, R, B

### 4. Solving Algorithm
- **Custom algorithm** developed by the author
- **Average solution**: ~25 moves
- **Goal**: < 28 moves every time
- **Note**: Different from Kociemba (which we use) - Kociemba finds optimal solutions but may be slower

### 5. Image Processing
- Uses **OpenCV** (same as our implementation)
- Took ~1 month to get working
- Can be improved for better detection
- **Key requirement**: Good lighting, avoid lighting changes between pictures

### 6. User Interface
- Simple camera window
- **SPACE** to capture face
- **X** to quit
- Shows cube state in console after capture
- Displays solution in standard notation

### 7. Solution Output Format
Example output:
```
Your solution :) 
R2 U' R B2 U' R2 U' B R2 U' L U R2 U' D L D B D B' D' L2 F2 L F2 R' D2 R 
Number of moves: 28
```

## Improvements for Our Python Implementation

### Already Implemented ✅
1. ✅ 2D net visualization (matches their flat representation)
2. ✅ Real-time color preview
3. ✅ Alignment boxes for better capture
4. ✅ Guided sequence matching their order
5. ✅ Kociemba solver (optimal solutions)

### Potential Enhancements 🔄

1. **Cube State Display**
   - Add console output showing the cube state in their format
   - Display both scrambled and solved states

2. **Solution Formatting**
   - Show move count prominently
   - Display solution in same format as Java project

3. **Image Processing Improvements**
   - Better color calibration based on lighting
   - Improved edge detection for cube faces
   - Automatic face extraction from video

4. **Error Handling**
   - Better validation of cube state
   - Clear error messages if colors are misclassified

5. **User Experience**
   - Add option to re-capture a face if colors look wrong
   - Show confidence scores for color detection
   - Allow manual color correction

## Key Differences

| Feature | Java Project | Our Python Project |
|---------|-------------|-------------------|
| Solver | Custom (~25 moves) | Kociemba (optimal) |
| UI | Simple camera window | 3 windows (Guide, Camera, Preview) |
| Visualization | Console text | 2D net with colors |
| Color Preview | After capture | Real-time during capture |
| Alignment | Manual | Guided with alignment box |

## Recommendations

1. **Keep our enhanced UI** - The 2D net visualization and real-time preview are improvements
2. **Add console output** - Show cube state in the Java project's format for compatibility
3. **Improve color detection** - Their note about lighting suggests we should add color calibration
4. **Add validation** - Check cube state validity before solving (ensure all 6 colors appear exactly 9 times)
