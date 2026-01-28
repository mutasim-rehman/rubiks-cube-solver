"""
Test script for cube state representation
"""

from cube_state import CubeState


def test_solved_state():
    """Test that solved state is correctly identified"""
    cube = CubeState()
    assert cube.is_solved(), "Solved cube should be identified as solved"
    print("✓ Solved state test passed")


def test_kociemba_conversion():
    """Test conversion to kociemba format"""
    cube = CubeState()
    kociemba_str = cube.to_kociemba_string()
    
    # Format: 54 chars, no spaces; 6 faces of 9 each (U,R,F,D,L,B)
    assert len(kociemba_str) == 54, "Kociemba string must have 54 characters"
    faces = [kociemba_str[i*9:(i+1)*9] for i in range(6)]
    assert all(len(f) == 9 for f in faces), "Each face should have 9 characters"
    
    # For solved cube, all faces should be uniform
    assert all(len(set(f)) == 1 for f in faces), "Solved cube faces should be uniform"
    
    print("✓ Kociemba conversion test passed")


def test_face_manipulation():
    """Test face get/set operations"""
    cube = CubeState()
    
    # Get a face
    up_face = cube.get_face(CubeState.UP)
    assert len(up_face) == 3, "Face should be 3x3"
    assert len(up_face[0]) == 3, "Face rows should have 3 elements"
    
    # Modify a face
    new_face = [['R']*3 for _ in range(3)]
    cube.set_face(CubeState.UP, new_face)
    assert cube.get_face(CubeState.UP) == new_face, "Face should be updated"
    
    print("✓ Face manipulation test passed")


if __name__ == '__main__':
    print("Testing Cube State...")
    print("-" * 40)
    
    test_solved_state()
    test_kociemba_conversion()
    test_face_manipulation()
    
    print("-" * 40)
    print("All tests passed!")
