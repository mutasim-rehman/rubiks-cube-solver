# Alignment Guide

## Overview

The cube solver now includes an alignment system that helps you position each cube face accurately. The alignment box in the camera feed matches the 2D net diagram pattern, making it easy to align your cube.

## How It Works

### 1. 2D Net Diagram
The guide window shows a 2D net of the cube with the following layout:
```
    [3] Up (White)
[5] [1] [2] [6]
Left Front Right Back
    [4] Down (Yellow)
```

### 2. Alignment Box
When capturing a face, you'll see:
- **Green alignment box** in the center of the camera feed
- **3x3 grid lines** inside the box (matching the cube face structure)
- **Corner markers** (L-shaped) at each corner for precise positioning
- **Face label** above the box showing which face to capture

### 3. Alignment Process

1. **Position the cube** so the face you're capturing is visible
2. **Align the cube face** with the green box:
   - The cube face should fill most of the green box
   - Use the corner markers to align the cube corners
   - The 3x3 grid should roughly match your cube's stickers
3. **Check alignment feedback**:
   - Green "Alignment: Good" = ready to capture
   - Orange "Alignment: Adjust" = move cube closer/further or adjust angle
4. **Press SPACE** when alignment is good

## Tips for Best Alignment

1. **Distance**: Hold the cube about 30-50cm from the camera
2. **Angle**: Keep the face perpendicular to the camera (not tilted)
3. **Lighting**: Ensure even lighting on the cube face
4. **Fill the box**: The cube face should fill 30-90% of the alignment box
5. **Steady**: Hold the cube steady when pressing SPACE

## Visual Features

- **Semi-transparent overlay**: The alignment box has a subtle green overlay to help you see the cube through it
- **Grid lines**: The 3x3 grid helps you align the cube's sticker pattern
- **Corner markers**: L-shaped markers at corners for precise edge alignment
- **Real-time feedback**: Alignment quality updates as you move the cube

## Troubleshooting

**Problem**: Alignment always shows "Adjust"
- **Solution**: Move the cube closer or further from the camera
- **Solution**: Ensure the face is square to the camera (not tilted)
- **Solution**: Check lighting - shadows can affect detection

**Problem**: Cube face doesn't fit in the box
- **Solution**: Move further from the camera
- **Solution**: The box size is optimized for most cube sizes

**Problem**: Colors are misclassified despite good alignment
- **Solution**: Improve lighting conditions
- **Solution**: Ensure the cube face is well-lit and colors are clear
- **Solution**: Try capturing again with better lighting
