"""
Cube State Representation
Represents a Rubik's cube state and provides utilities for state manipulation.
"""

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
        Convert cube state to kociemba format string.
        Format: UUUUUUUUU RRRRRRRRR FFFFFFFFF DDDDDDDDD LLLLLLLLL BBBBBBBBB
        """
        kociemba_faces = []
        face_order = [self.UP, self.RIGHT, self.FRONT, self.DOWN, self.LEFT, self.BACK]
        
        for face_idx in face_order:
            face = self.faces[face_idx]
            face_str = ''
            for row in face:
                for color in row:
                    # Convert color to kociemba format
                    kociemba_color = self.COLOR_MAP.get(color, color)
                    face_str += kociemba_color
            kociemba_faces.append(face_str)
        
        return ' '.join(kociemba_faces)
    
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
    
    def __str__(self):
        """String representation of cube state."""
        return self.to_kociemba_string()
