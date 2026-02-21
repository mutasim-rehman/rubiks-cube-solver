"""
Example usage of the Rubik's Cube Solver
"""

from cube_solver import CubeSolver
from cube_state import CubeState


def example_manual_input():
    """Example: Solve cube from manually specified colors"""
    print("Example: Manual Input")
    print("-" * 50)
    
    solver = CubeSolver()
    
    # Example: Create a scrambled cube state
    # Format: 6 faces, each is 3x3 array of color codes
    # Colors: R=Red, G=Green, B=Blue, Y=Yellow, O=Orange, W=White
    # Face mapping: Red=Front, Green=Left, Blue=Right, Orange=Back, White=Up, Yellow=Down
    faces = [
        # Up (White center) - scrambled
        [['W', 'W', 'W'],
         ['W', 'W', 'W'],
         ['W', 'W', 'W']],
        # Right (Blue center)
        [['B', 'B', 'B'],
         ['B', 'B', 'B'],
         ['B', 'B', 'B']],
        # Front (Red center)
        [['R', 'R', 'R'],
         ['R', 'R', 'R'],
         ['R', 'R', 'R']],
        # Down (Yellow center)
        [['Y', 'Y', 'Y'],
         ['Y', 'Y', 'Y'],
         ['Y', 'Y', 'Y']],
        # Left (Green center)
        [['G', 'G', 'G'],
         ['G', 'G', 'G'],
         ['G', 'G', 'G']],
        # Back (Orange center)
        [['O', 'O', 'O'],
         ['O', 'O', 'O'],
         ['O', 'O', 'O']],
    ]
    
    # Note: This is a solved cube, so solution will be empty
    # For a scrambled cube, modify the faces array above
    
    solution = solver.solve_from_manual_input(faces)
    
    if solution:
        print(f"Solution: {solution}")
        print(f"Move count: {solver.get_move_count(solution)}")
    else:
        print("No solution needed (cube is solved) or error occurred")


def example_with_image():
    """Example: Solve cube from image file"""
    print("\nExample: Image Input")
    print("-" * 50)
    
    solver = CubeSolver()
    
    # Replace with path to your cube image
    image_path = "cube_image.jpg"
    
    try:
        solution = solver.solve_from_image(image_path)
        
        if solution:
            print(f"Solution: {solution}")
            print(f"Formatted solution:")
            print(solver.format_solution(solution))
        else:
            print("Could not solve cube from image")
    except FileNotFoundError:
        print(f"Image file not found: {image_path}")
        print("Please provide a valid image path")


if __name__ == '__main__':
    print("Rubik's Cube Solver - Examples")
    print("=" * 50)
    
    # Run examples
    example_manual_input()
    # example_with_image()  # Uncomment when you have an image
    
    print("\n" + "=" * 50)
    print("For webcam usage, run: python main.py --webcam")
    print("For image usage, run: python main.py --image <path>")
