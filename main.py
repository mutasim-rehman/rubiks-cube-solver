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
        print("\n" + "="*50)
        print("SOLUTION FOUND!")
        print("="*50)
        
        move_count = solver.get_move_count(solution)
        print(f"\nTotal moves: {move_count}")
        print(f"\nSolution sequence:")
        
        if args.format:
            print(solver.format_solution(solution))
        else:
            print(solution)
        
        print("\nMove notation:")
        print("  U = Up face, 90° clockwise")
        print("  U' = Up face, 90° counter-clockwise")
        print("  U2 = Up face, 180°")
        print("  (Same for R, F, D, L, B)")
    else:
        print("\nFailed to solve cube. Please check:")
        print("  1. All 6 faces are clearly visible")
        print("  2. Lighting is adequate")
        print("  3. Colors are distinguishable")


if __name__ == '__main__':
    main()
