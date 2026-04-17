"""
Cube Solution Simulation
Shows each move being applied step by step and verifies the final solution.
"""

# Force matplotlib to use non-GUI backend before any imports.
# (sklearn/scikit-image can pull in matplotlib; GUI backends conflict with OpenCV on Windows)
import matplotlib
matplotlib.use('Agg')

import json
import sys
import time
from cube_solver import CubeSolver
from cube_state import CubeState
from cube_visualizer import CubeVisualizer
import cv2


def print_cube_state(cube_state: CubeState, title: str = ""):
    """Print cube state in a formatted way."""
    if title:
        print(f"\n{'='*60}")
        print(f"{title}")
        print('='*60)
    print(cube_state.to_flat_string())


def simulate_solution(cube_state: CubeState, solution: str, interactive: bool = True, delay: float = 1.0):
    """
    Simulate applying a solution move by move.
    
    Args:
        cube_state: Initial cube state
        solution: Solution string (e.g., "R U R' U'")
        interactive: If True, wait for user input between moves. If False, auto-play with delay.
        delay: Delay in seconds between moves when not interactive
    """
    if not solution or solution.strip() == "":
        print("\nCube is already solved! No moves needed.")
        print_cube_state(cube_state, "Initial State (Solved)")
        return cube_state
    
    moves = solution.split()
    current_state = cube_state
    
    print("\n" + "="*60)
    print("SOLUTION SIMULATION")
    print("="*60)
    print(f"Total moves: {len(moves)}")
    print(f"Solution: {solution}")
    print("="*60)
    
    # Show initial state
    print_cube_state(current_state, "INITIAL STATE")
    
    if interactive:
        print("\nPress ENTER to apply next move, or 'a' + ENTER to auto-play remaining moves")
        print("Press 'q' + ENTER to quit")
    
    # Apply each move
    for i, move in enumerate(moves, 1):
        print(f"\n{'='*60}")
        print(f"MOVE {i}/{len(moves)}: {move}")
        print('='*60)
        
        # Show state before move
        print_cube_state(current_state, f"Before {move}")
        
        # Apply the move
        try:
            # Apply single move
            new_state = current_state.apply_sequence(move)
            current_state = new_state
            
            # Show state after move
            print_cube_state(current_state, f"After {move}")
            
            # Check if solved after this move
            if current_state.is_solved():
                print("\n🎉 CUBE IS SOLVED! 🎉")
                break
            
        except Exception as e:
            print(f"\n❌ ERROR applying move {move}: {e}")
            return current_state
        
        # Interactive mode: wait for user input
        if interactive:
            user_input = input("\nPress ENTER for next move, 'a' for auto-play, 'q' to quit: ").strip().lower()
            if user_input == 'q':
                print("\nSimulation stopped by user.")
                break
            elif user_input == 'a':
                print("\nAuto-playing remaining moves...")
                interactive = False
        else:
            # Auto-play mode: wait for delay
            time.sleep(delay)
    
    # Final verification
    print("\n" + "="*60)
    print("FINAL VERIFICATION")
    print("="*60)
    print_cube_state(current_state, "Final State")
    
    is_solved = current_state.is_solved()
    if is_solved:
        print("\n✅ VERIFICATION: Cube is SOLVED!")
    else:
        print("\n❌ VERIFICATION: Cube is NOT solved!")
        print("This indicates an issue with the solution or move application.")
    
    return current_state


def visualize_simulation(cube_state: CubeState, solution: str, interactive: bool = True, delay: float = 1.0):
    """
    Visualize the simulation with OpenCV windows showing the cube state.
    
    Args:
        cube_state: Initial cube state
        solution: Solution string
        interactive: If True, wait for key press between moves
        delay: Delay in seconds when not interactive
    """
    if not solution or solution.strip() == "":
        print("\nCube is already solved! No moves needed.")
        visualizer = CubeVisualizer()
        img = visualizer.visualize_cube_state(cube_state)
        cv2.imshow("Cube State (Solved)", img)
        print("\nPress any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return
    
    moves = solution.split()
    current_state = cube_state
    visualizer = CubeVisualizer()
    
    print("\n" + "="*60)
    print("VISUAL SOLUTION SIMULATION")
    print("="*60)
    print(f"Total moves: {len(moves)}")
    print(f"Solution: {solution}")
    print("="*60)
    print("\nControls:")
    print("  SPACE or ENTER: Next move")
    print("  'a': Auto-play remaining moves")
    print("  'q' or ESC: Quit")
    print("="*60)
    
    # Show initial state
    img = visualizer.visualize_cube_state(current_state)
    cv2.imshow("Cube Solver Simulation", img)
    print("\nInitial state displayed. Press SPACE to start...")
    
    # Wait for start
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord(' ') or key == 13:  # Space or Enter
            break
        elif key == ord('q') or key == 27:  # Q or ESC
            cv2.destroyAllWindows()
            return
    
    # Apply each move
    for i, move in enumerate(moves, 1):
        print(f"\nMove {i}/{len(moves)}: {move}")
        
        # Apply the move
        try:
            new_state = current_state.apply_sequence(move)
            current_state = new_state
            
            # Update visualization
            img = visualizer.visualize_cube_state(current_state)
            
            # Add move info to image
            info_text = f"Move {i}/{len(moves)}: {move}"
            cv2.putText(img, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            if current_state.is_solved():
                solved_text = "SOLVED!"
                cv2.putText(img, solved_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                print("\n🎉 CUBE IS SOLVED! 🎉")
            
            cv2.imshow("Cube Solver Simulation", img)
            
        except Exception as e:
            print(f"\n❌ ERROR applying move {move}: {e}")
            cv2.destroyAllWindows()
            return current_state
        
        # Check if solved
        if current_state.is_solved():
            print("\nPress any key to close...")
            cv2.waitKey(0)
            break
        
        # Interactive mode: wait for key press
        if interactive:
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q') or key == 27:  # Q or ESC
                print("\nSimulation stopped by user.")
                break
            elif key == ord('a'):  # Auto-play
                print("\nAuto-playing remaining moves...")
                interactive = False
        else:
            # Auto-play mode: wait for delay
            time.sleep(delay)
            # Still check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("\nSimulation stopped by user.")
                break
    
    # Final verification
    print("\n" + "="*60)
    print("FINAL VERIFICATION")
    print("="*60)
    print_cube_state(current_state, "Final State")
    
    is_solved = current_state.is_solved()
    if is_solved:
        print("\n✅ VERIFICATION: Cube is SOLVED!")
    else:
        print("\n❌ VERIFICATION: Cube is NOT solved!")
        print("This indicates an issue with the solution or move application.")
    
    print("\nPress any key to close visualization...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return current_state


def create_test_scrambled_cube():
    """Create a simple test scrambled cube for testing."""
    # Start with solved cube and apply a simple scramble
    solved = CubeState()
    # Apply a simple scramble: R U R' U'
    scrambled = solved.apply_sequence("R U R' U'")
    return scrambled


def main():
    """Main function to run the simulation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Simulate Rubik\'s Cube Solution - Step through each move and verify the solution',
        epilog='''
Examples:
  # Test with a scrambled cube (quick test)
  python simulate_solution.py --test --visual
  
  # Manual input with visual simulation
  python simulate_solution.py --visual
  
  # Use webcam to capture cube, then simulate
  python simulate_solution.py --webcam --visual
  
  # If webcam windows don't appear (Windows): use web frontend, save API result to solution.json, then:
  python simulate_solution.py --from-json solution.json --visual
  
  # Auto-play moves (non-interactive)
  python simulate_solution.py --test --auto --delay 0.5
  
  # Text-only simulation (no OpenCV)
  python simulate_solution.py --test
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--image', type=str, help='Path to cube image')
    parser.add_argument('--webcam', action='store_true', help='Use webcam to capture faces')
    parser.add_argument('--from-json', type=str, metavar='FILE', help='Load solution + cubeState from JSON (e.g. from web API). Use when --webcam windows do not appear.')
    parser.add_argument('--visual', action='store_true', help='Show visual simulation with OpenCV')
    parser.add_argument('--auto', action='store_true', help='Auto-play moves (non-interactive)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between moves in seconds (default: 1.0)')
    parser.add_argument('--test', action='store_true', help='Use a test scrambled cube for quick testing')
    
    args = parser.parse_args()
    
    solver = CubeSolver()
    cube_state = None
    solution = None
    
    # Get cube state
    if args.from_json:
        with open(args.from_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        solution = data.get('solution', '')
        cube_state_str = data.get('cubeState')
        if not cube_state_str:
            print("Error: JSON must contain 'cubeState' (from API response)")
            return
        cube_state = CubeState.from_flat_string(cube_state_str)
        solver.cube_state = cube_state
        print(f"Loaded from {args.from_json}")
    elif args.test:
        print("Using test scrambled cube...")
        cube_state = create_test_scrambled_cube()
        solution = solver.solve_from_manual_input(cube_state.faces)
    elif args.webcam:
        print("Starting webcam mode...")
        solution = solver.solve_from_webcam()
        if solver.cube_state:
            cube_state = solver.cube_state
    elif args.image:
        print(f"Processing image: {args.image}")
        solution = solver.solve_from_image(args.image)
        if solver.cube_state:
            cube_state = solver.cube_state
    else:
        # Manual input mode
        print("="*60)
        print("MANUAL CUBE INPUT")
        print("="*60)
        print("Enter cube state manually.")
        print("Face order: Up, Right, Front, Down, Left, Back")
        print("Colors: R=Red, G=Green, B=Blue, Y=Yellow, O=Orange, W=White")
        print("\nFor each face, enter 3 rows of 3 colors each.")
        print("Example for a solved white face: WWW WWW WWW")
        print("="*60)
        
        faces = []
        face_names = ['Up (White)', 'Right (Blue)', 'Front (Red)', 
                     'Down (Yellow)', 'Left (Green)', 'Back (Orange)']
        
        for i, face_name in enumerate(face_names):
            print(f"\nEnter {face_name} face (3 rows, 3 colors each):")
            face = []
            for row in range(3):
                while True:
                    row_input = input(f"  Row {row+1}: ").strip().upper()
                    if len(row_input) == 3 and all(c in 'RGBYOW' for c in row_input):
                        face.append(list(row_input))
                        break
                    else:
                        print("    Invalid input. Enter exactly 3 colors (R, G, B, Y, O, W)")
            faces.append(face)
        
        cube_state = CubeState(faces)
        solution = solver.solve_from_manual_input(faces)
    
    if cube_state is None:
        print("\nError: Could not get cube state.")
        return
    
    if solution is None:
        print("\nError: Could not get solution.")
        return
    
    # Display initial cube state
    print("\n" + "="*60)
    print("INITIAL CUBE STATE")
    print("="*60)
    solver.display_cube_state()
    
    # Display solution
    print("\n" + "="*60)
    print("SOLUTION")
    print("="*60)
    print(f"Solution: {solution}")
    print(f"Number of moves: {solver.get_move_count(solution)}")
    
    # Run simulation
    if args.visual:
        visualize_simulation(cube_state, solution, 
                           interactive=not args.auto, 
                           delay=args.delay)
    else:
        simulate_solution(cube_state, solution, 
                         interactive=not args.auto, 
                         delay=args.delay)


if __name__ == '__main__':
    main()
