"""
Constrained Cube Solver: solutions using only R, L, F, D.

For a robot with motors only on Right, Left, Front, and Down:
- U (up) and B (back) are passive; their pieces are moved indirectly.
- Every full solution (from e.g. kociemba) is rewritten so that each U/B move
  is replaced by an equivalent sequence of R, L, F, D moves.

Usage:
  solution = solve_constrained(kociemba_54_char_string)
  # Returns a move sequence using only R, L', R2, L, F, F', F2, D, D', D2.

To avoid slow BFS on first run, generate precomputed macros once:
  python find_ub_macros.py   # may take 10–30 min; creates precomputed_ub_macros.json
Then place precomputed_ub_macros.json in the same directory as this file (or call
load_u_b_macros_from_file(path) before solving).
"""

import json
import kociemba
import os
from collections import deque
from pathlib import Path
from typing import List, Dict, Optional, Any

# Use kociemba's move application so state representation matches exactly.
from cube_moves import apply_sequence_kociemba


SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

# Only these moves can be executed by the robot.
ALLOWED_MOVES = [
    "R", "R'", "R2",
    "L", "L'", "L2",
    "F", "F'", "F2",
    "D", "D'", "D2",
]

# Precomputed R,L,F,D equivalents for U and B (kociemba convention).
# Computed once via BFS; allows skipping slow BFS at runtime.
# Format: {"U": ["R","F",...], "U'": [...], "U2": [...], "B": [...], "B'": [...], "B2": [...]}
_PRECOMPUTED_MACROS: Optional[Dict[str, List[str]]] = None


def _invert_move(m: str) -> str:
    """Inverse of a single move: R <-> R', X2 stays X2."""
    if len(m) == 1:
        return m + "'"
    if m.endswith("'"):
        return m[0]
    if m.endswith("2"):
        return m
    return m


def _invert_sequence(seq: List[str]) -> List[str]:
    """Reverse the sequence and invert each move."""
    return [_invert_move(m) for m in reversed(seq)]


def _bfs_find_equivalent(
    target_state: str,
    allowed: List[str],
    max_depth: int = 10,
) -> Optional[List[str]]:
    """
    BFS from SOLVED using only allowed moves. Return shortest sequence
    that reaches target_state, or None if not found within max_depth.
    """
    if target_state == SOLVED:
        return []
    seen = {SOLVED}
    queue: deque = deque([(SOLVED, [])])
    while queue:
        state, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for move in allowed:
            new_state = apply_sequence_kociemba(state, move)
            if new_state in seen:
                continue
            seen.add(new_state)
            new_path = path + [move]
            if new_state == target_state:
                return new_path
            queue.append((new_state, new_path))
    return None


def set_u_b_macros(macros: Dict[str, List[str]]) -> None:
    """Inject precomputed U/B macros so BFS is skipped. Keys: U, U', U2, B, B', B2."""
    global _PRECOMPUTED_MACROS
    _PRECOMPUTED_MACROS = dict(macros)


def load_u_b_macros_from_file(path: str) -> bool:
    """Load macros from a JSON file. Returns True if loaded, False if file missing/invalid."""
    global _PRECOMPUTED_MACROS
    p = Path(path)
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        _PRECOMPUTED_MACROS = {k: list(v) for k, v in data.items()}
        return True
    except Exception:
        return False


def _build_u_b_macros(max_depth: int = 10) -> Dict[str, List[str]]:
    """
    Precompute macros: for each of U, U', U2, B, B', B2, store a list of
    moves (only R,L,F,D) that have the same effect. Uses BFS (can be slow).
    """
    target_u = apply_sequence_kociemba(SOLVED, "U")
    target_b = apply_sequence_kociemba(SOLVED, "B")

    seq_u = _bfs_find_equivalent(target_u, ALLOWED_MOVES, max_depth=max_depth)
    seq_b = _bfs_find_equivalent(target_b, ALLOWED_MOVES, max_depth=max_depth)

    if seq_u is None:
        raise RuntimeError(
            f"Could not find R,L,F,D equivalent for U within depth {max_depth}. "
            "Run find_ub_macros.py and pass macros via set_u_b_macros() or load_u_b_macros_from_file()."
        )
    if seq_b is None:
        raise RuntimeError(
            f"Could not find R,L,F,D equivalent for B within depth {max_depth}. "
            "Run find_ub_macros.py and pass macros via set_u_b_macros() or load_u_b_macros_from_file()."
        )

    seq_u_inv = _invert_sequence(seq_u)
    seq_u2 = seq_u + seq_u
    seq_b_inv = _invert_sequence(seq_b)
    seq_b2 = seq_b + seq_b

    return {
        "U": seq_u,
        "U'": seq_u_inv,
        "U2": seq_u2,
        "B": seq_b,
        "B'": seq_b_inv,
        "B2": seq_b2,
    }


# Cache macros at module load (None = not yet computed).
_U_B_MACROS: Optional[Dict[str, List[str]]] = None


def _get_macros() -> Dict[str, List[str]]:
    global _U_B_MACROS, _PRECOMPUTED_MACROS
    if _U_B_MACROS is not None:
        return _U_B_MACROS
    if _PRECOMPUTED_MACROS is not None:
        _U_B_MACROS = _PRECOMPUTED_MACROS
        return _U_B_MACROS
    # Try loading from same directory as this module
    _module_dir = os.path.dirname(os.path.abspath(__file__))
    _default_macros_path = os.path.join(_module_dir, "precomputed_ub_macros.json")
    if load_u_b_macros_from_file(_default_macros_path):
        _U_B_MACROS = _PRECOMPUTED_MACROS
        return _U_B_MACROS
    _U_B_MACROS = _build_u_b_macros()
    return _U_B_MACROS


def _merge_two_moves(face: str, a: str, b: str) -> Optional[str]:
    """
    Combine two consecutive moves on the same face into one or cancel.
    Returns one move string or None (cancel). face is one of R,L,F,D.
    """
    def power(m: str) -> int:
        if len(m) == 1:
            return 1
        if m.endswith("'"):
            return 3
        return 2  # X2

    pa = power(a)
    pb = power(b)
    total = (pa + pb) % 4
    if total == 0:
        return None
    if total == 1:
        return face
    if total == 2:
        return face + "2"
    return face + "'"


def _simplify_once(moves: List[str]) -> List[str]:
    """One pass: merge adjacent same-face moves. Returns new list."""
    if len(moves) <= 1:
        return list(moves)
    out: List[str] = []
    i = 0
    while i < len(moves):
        if i + 1 >= len(moves):
            out.append(moves[i])
            i += 1
            continue
        a, b = moves[i], moves[i + 1]
        face_a = a[0]
        face_b = b[0]
        if face_a in "RLFD" and face_a == face_b:
            merged = _merge_two_moves(face_a, a, b)
            if merged is None:
                i += 2
                continue
            out.append(merged)
            i += 2
            continue
        out.append(a)
        i += 1
    return out


def simplify_moves(moves: List[str]) -> List[str]:
    """Repeatedly merge adjacent same-face moves until stable."""
    prev = moves
    while True:
        next_list = _simplify_once(prev)
        if next_list == prev:
            return next_list
        prev = next_list


def rewrite_solution_to_rlfd(solution: str) -> List[str]:
    """
    Rewrite a full solution (e.g. from kociemba) to use only R, L, F, D.
    Every U and B move is replaced by its precomputed macro.
    """
    macros = _get_macros()
    tokens = solution.split()
    result: List[str] = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # Normalize "R'" style
        if t.endswith("'"):
            key = t[0] + "'"
        else:
            key = t
        if key in macros:
            result.extend(macros[key])
        else:
            result.append(t)
    return result


def solve_constrained(kociemba_string: str) -> str:
    """
    Solve the cube and return a solution that uses only R, L, F, D moves.
    - Uses kociemba for the full solution.
    - Rewrites U/B to R,L,F,D macros.
    - Simplifies the final sequence (cancels and merges adjacent same-face moves).
    """
    kociemba_string = kociemba_string.replace(" ", "")
    if len(kociemba_string) != 54:
        raise ValueError("kociemba_string must be 54 characters")

    if kociemba_string == SOLVED:
        return ""

    full_solution = kociemba.solve(kociemba_string)
    rlfd_list = rewrite_solution_to_rlfd(full_solution)
    simplified = simplify_moves(rlfd_list)
    return " ".join(simplified)


def get_move_count(solution: str) -> int:
    """Number of moves in a solution string."""
    if not solution or not solution.strip():
        return 0
    return len(solution.split())
