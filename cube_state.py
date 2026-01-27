"""
Cube State Representation
Represents a Rubik's cube state and provides utilities for state manipulation.
"""

from typing import Tuple


class CubeState:
    """
    Represents a Rubik's cube state.
    Face order: Up, Right, Front, Down, Left, Back
    Color mapping: U=W(White), R=R(Red), F=G(Green), D=Y(Yellow), L=O(Orange), B=B(Blue)
    """
    
    # Face indices
    UP = 0
    RIGHT = 1
    FRONT = 2
    DOWN = 3
    LEFT = 4
    BACK = 5
    
    # Color mapping for kociemba
    # U=Up, R=Right, F=Front, D=Down, L=Left, B=Back
    COLOR_MAP = {
        'W': 'U',  # White -> Up
        'R': 'R',  # Red -> Right
        'G': 'F',  # Green -> Front
        'Y': 'D',  # Yellow -> Down
        'O': 'L',  # Orange -> Left
        'B': 'B',  # Blue -> Back
    }
    
    def __init__(self, faces=None):
        """
        Initialize cube state.
        faces: List of 6 faces, each face is a 3x3 array of colors
        """
        if faces is None:
            # Solved state
            self.faces = [
                [['W']*3 for _ in range(3)],  # Up (White)
                [['R']*3 for _ in range(3)],  # Right (Red)
                [['G']*3 for _ in range(3)],  # Front (Green)
                [['Y']*3 for _ in range(3)],  # Down (Yellow)
                [['O']*3 for _ in range(3)],  # Left (Orange)
                [['B']*3 for _ in range(3)],  # Back (Blue)
            ]
        else:
            self.faces = faces
    
    def get_face(self, face_idx):
        """Get a specific face."""
        return self.faces[face_idx]
    
    def set_face(self, face_idx, face):
        """Set a specific face."""
        self.faces[face_idx] = face
    
    def to_kociemba_string(self):
        """
        Convert cube state to kociemba format string expected by the
        `kociemba` Python library.
        
        The library expects a single 54‑character string (no spaces) where
        the facelets are ordered as:
            UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
        and the faces are in the order: Up, Right, Front, Down, Left, Back.
        """
        kociemba_faces = []
        face_order = [self.UP, self.RIGHT, self.FRONT, self.DOWN, self.LEFT, self.BACK]
        
        for face_idx in face_order:
            face = self.faces[face_idx]
            face_str = ''
            for row in face:
                for color in row:
                    # Convert internal color code to kociemba facelet letter
                    kociemba_color = self.COLOR_MAP.get(color, color)
                    face_str += kociemba_color
            kociemba_faces.append(face_str)
        
        # Concatenate without spaces – kociemba expects length 54
        return ''.join(kociemba_faces)
    
    def from_face_colors(self, face_colors):
        """
        Create cube state from detected face colors.
        face_colors: List of 6 faces, each is a 3x3 array of color codes
        """
        self.faces = face_colors
        return self
    
    def is_solved(self):
        """Check if cube is in solved state."""
        for face in self.faces:
            center_color = face[1][1]
            for row in face:
                for color in row:
                    if color != center_color:
                        return False
        return True
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate cube state.
        Returns (is_valid, error_message)
        A valid cube must have exactly 9 of each color.
        """
        color_counts = {'R': 0, 'G': 0, 'B': 0, 'Y': 0, 'O': 0, 'W': 0}
        
        for face in self.faces:
            for row in face:
                for color in row:
                    if color in color_counts:
                        color_counts[color] += 1
                    else:
                        return False, f"Invalid color detected: {color}"
        
        # Check each color appears exactly 9 times
        for color, count in color_counts.items():
            if count != 9:
                return False, f"Color {color} appears {count} times, expected 9"
        
        return True, "Valid cube state"
    
    def to_flat_string(self) -> str:
        """
        Convert cube state to flat 2D string representation (matching Java project format).
        Format:
            [TOP 3 rows]
        [LEFT] [FRONT] [RIGHT] [BACK] (middle row)
            [BOTTOM 3 rows]
        """
        # Face order: U, R, F, D, L, B
        # For display: U (top), L, F, R, B (middle), D (bottom)
        top = self.faces[self.UP]
        left = self.faces[self.LEFT]
        front = self.faces[self.FRONT]
        right = self.faces[self.RIGHT]
        back = self.faces[self.BACK]
        bottom = self.faces[self.DOWN]
        
        lines = []
        
        # Top face (3 rows)
        for row in top:
            lines.append("     " + "".join(row))
        
        # Middle row: Left, Front, Right, Back
        for i in range(3):
            left_row = "".join(left[i])
            front_row = "".join(front[i])
            right_row = "".join(right[i])
            back_row = "".join(back[i])
            lines.append(f" {left_row} {front_row} {right_row} {back_row}")
        
        # Bottom face (3 rows)
        for row in bottom:
            lines.append("     " + "".join(row))
        
        return "\n".join(lines)
    
    def __str__(self):
        """String representation of cube state."""
        return self.to_kociemba_string()
