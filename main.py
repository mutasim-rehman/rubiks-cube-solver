"""
Main Application for Rubik's Cube Solver
"""

import sys
import argparse
from cube_solver import CubeSolver


def main():
    parser = argparse.ArgumentParser(description='Rubik\'s Cube Solver')
    parser.add_argument('--image', type=str, help='Path to cube image')
    parser.add_argument('--webcam', action='store_true', help='Use webcam to capture faces')
    parser.add_argument('--format', action='store_true', help='Format solution output')
    
    args = parser.parse_args()
    
    solver = CubeSolver()
    
    if args.webcam:
        print("Starting webcam mode...")
        solution = solver.solve_from_webcam()
    elif args.image:
        print(f"Processing image: {args.image}")
        solution = solver.solve_from_image(args.image)
    else:
        print("Please provide --image <path> or --webcam")
        print("\nExample usage:")
        print("  python main.py --image cube.jpg")
        print("  python main.py --webcam")
        return
    
    if solution:
        # Display cube state (matching Java project format)
        solver.display_cube_state()
        
        # Display solution
        solver.display_solution(solution, show_solved_state=True)
        
        if args.format:
            print("\nFormatted solution:")
            print(solver.format_solution(solution))
        
        print("\nMove notation:")
        print("  U = Up face, 90° clockwise")
        print("  U' = Up face, 90° counter-clockwise")
        print("  U2 = Up face, 180°")
        print("  (Same for R, F, D, L, B)")
        print("\nNote: Hold the cube in the orientation shown above when applying the solution")
    else:
        print("\nFailed to solve cube. Please check:")
        print("  1. All 6 faces are clearly visible")
        print("  2. Lighting is adequate")
        print("  3. Colors are distinguishable")


if __name__ == '__main__':
    main()
