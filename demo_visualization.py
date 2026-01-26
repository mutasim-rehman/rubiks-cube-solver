"""
Demo script to showcase the 2D cube net visualization
"""

import cv2
from cube_visualizer import CubeVisualizer


def demo_2d_net():
    """Demonstrate the 2D net visualization"""
    visualizer = CubeVisualizer()
    
    print("Creating 2D cube net visualization...")
    print("This shows the cube layout and which face to capture next")
    
    # Show different states
    faces_to_capture = ['B', 'R', 'F', 'L', 'D', 'U']
    captured_faces = []
    
    for i, face_code in enumerate(faces_to_capture):
        print(f"\nStep {i+1}/6: Highlighting {face_code} face")
        
        # Create visualization
        net_image = visualizer.create_2d_net(
            highlighted_face=face_code,
            captured_faces=captured_faces
        )
        
        # Create guide
        guide_image = visualizer.create_capture_guide(
            current_face=face_code,
            step=i+1,
            total_steps=6,
            instruction=f"Show {face_code} face"
        )
        
        # Display
        cv2.imshow('2D Cube Net', net_image)
        cv2.imshow('Capture Guide', guide_image)
        
        print("Press any key to continue to next step...")
        cv2.waitKey(0)
        
        # Mark as captured
        captured_faces.append(face_code)
    
    # Show final state (all captured)
    print("\nAll faces captured!")
    final_net = visualizer.create_2d_net(captured_faces=captured_faces)
    cv2.imshow('Final State - All Faces Captured', final_net)
    
    print("Press any key to exit...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    print("="*60)
    print("2D Cube Net Visualization Demo")
    print("="*60)
    demo_2d_net()
    print("\nDemo complete!")
