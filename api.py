"""
Hexgate API — Cube solver backend for web frontend.
Accepts face images, classifies colors, solves, returns solution.
"""
import base64
import io
import json
import numpy as np
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS

from cube_solver import CubeSolver

app = Flask(__name__)
CORS(app)

solver = CubeSolver()

# Face order for capture: U, L, F, R, B, D (matches webcam flow)


@app.route('/', methods=['GET'])
def index():
    """Root route for health checks and API discovery."""
    return jsonify({
        'name': 'Hexgate API',
        'status': 'ok',
        'endpoints': {
            'health': '/api/health',
            'classify': '/api/classify (POST)',
            'solve': '/api/solve (POST)',
        },
    })
FACE_ORDER = ['U', 'L', 'F', 'R', 'B', 'D']
FACE_ORDER_MAP = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}


def base64_to_image(b64: str) -> np.ndarray:
    """Decode base64 string to OpenCV BGR image."""
    data = base64.b64decode(b64.split(',')[1] if ',' in b64 else b64)
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Hexgate API'})


@app.route('/api/classify', methods=['POST'])
def classify_face():
    """
    Classify a single face image.
    Returns 3x3 grid of color codes (R, G, B, Y, O, W).
    """
    body = request.get_json()
    if not body or 'image' not in body:
        return jsonify({'error': 'Missing image'}), 400
    try:
        img = base64_to_image(body['image'])
        if img is None:
            return jsonify({'error': 'Invalid image'}), 400
        face_colors = solver.color_classifier.classify_face(img)
        return jsonify({'face': face_colors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/solve', methods=['POST'])
def solve():
    """
    Solve cube from 6 face images.
    Body: { "faces": [ { "face": "U", "image": "base64..." }, ... ] }
    Returns: { "solution": "U R F2 ...", "steps": ["U", "R", "F2", ...], "cubeState": "..." }
    """
    body = request.get_json()
    if not body or 'faces' not in body:
        return jsonify({'error': 'Missing faces array'}), 400

    faces_data = body['faces']
    if len(faces_data) != 6:
        return jsonify({'error': 'Exactly 6 faces required'}), 400

    # Build cube_faces in order U, R, F, D, L, B
    cube_faces = [None] * 6
    for item in faces_data:
        face_code = item.get('face', '').upper()
        if face_code not in FACE_ORDER_MAP:
            return jsonify({'error': f'Invalid face code: {face_code}'}), 400
        try:
            img = base64_to_image(item['image'])
            if img is None:
                return jsonify({'error': f'Invalid image for face {face_code}'}), 400
            face_colors = solver.color_classifier.classify_face(img)
            idx = FACE_ORDER_MAP[face_code]
            cube_faces[idx] = face_colors
        except Exception as e:
            return jsonify({'error': f'Failed to classify {face_code}: {str(e)}'}), 500

    if any(f is None for f in cube_faces):
        return jsonify({'error': 'Missing face data'}), 400

    try:
        solution = solver.solve_from_manual_input(cube_faces)
        if solution is None:
            return jsonify({
                'error': 'Could not solve. Check cube state (orientation, colors).',
                'cubeState': solver.cube_state.to_flat_string() if solver.cube_state else None
            }), 400

        steps = solution.split() if solution else []
        return jsonify({
            'solution': solution,
            'steps': steps,
            'moveCount': len(steps),
            'cubeState': solver.cube_state.to_flat_string()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
