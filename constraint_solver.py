"""
Constraint Cube Solver: solutions using only L, R, F, B, D (no U moves).

Motivation:
- Robot has 5 motors on faces: Left, Right, Front, Back, Down.
- Up (U) face has no motor, so we must avoid any U / U' / U2 turns.
- R and D are fixed physical axes (we never "reinterpret" faces).

Approach:
- Use kociemba to get an optimal full solution (may contain U moves).
- Replace each U / U' / U2 move with an equivalent sequence of L,R,F,B,D
  moves that has exactly the same effect on the cube state.
- Simplify the final move sequence by merging/canceling consecutive
  turns on the same face.

This file mirrors the design of cube_solver_constrained.py but is specific
to the 5-motor setup (L,R,F,B,D) and only rewrites U moves.

Typical usage:
    from constraint_solver import solve_without_u

    solution_5faces = solve_without_u(kociemba_54_char_string)
    # => string of moves using only L/R/F/B/D faces.

Implementation details:
- We rely on kociemba's own move application (via cube_moves.apply_sequence_kociemba)
  so our state representation matches the solver exactly.
- The equivalence for U is found via BFS the first time this module is used,
  unless a precomputed JSON with macros is available.
"""

import json
import kociemba
import os
from collections import deque
from pathlib import Path
from typing import List, Dict, Optional

from cube_moves import apply_sequence_kociemba


# Kociemba solved-state string (URFDLB order, 9 stickers each).
SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


# Only these faces exist as motors on the robot.
# We allow quarter (X), half (X2) and inverse (X') turns.
ALLOWED_MOVES: List[str] = [
    "R", "R'", "R2",
    "L", "L'", "L2",
    "F", "F'", "F2",
    "B", "B'", "B2",
    "D", "D'", "D2",
]


# Precomputed L,R,F,B,D equivalents for U (kociemba convention).
# When present, this avoids doing BFS at runtime.
# Format: {"U": [...], "U'": [...], "U2": [...]}
_PRECOMPUTED_U_MACROS: Optional[Dict[str, List[str]]] = None


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
    BFS from SOLVED using only allowed moves.
    Return the shortest sequence that reaches target_state,
    or None if not found within max_depth.
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


def set_u_macros(macros: Dict[str, List[str]]) -> None:
    """
    Inject precomputed U macros so BFS is skipped.
    Expected keys: "U", "U'", "U2".
    """
    global _PRECOMPUTED_U_MACROS
    _PRECOMPUTED_U_MACROS = dict(macros)


def load_u_macros_from_file(path: str) -> bool:
    """
    Load U macros from a JSON file.
    Returns True if loaded successfully, False otherwise.

    JSON format example:
    {
        "U": ["R", "F", "R'", ...],
        "U'": [...],
        "U2": [...]
    }
    """
    global _PRECOMPUTED_U_MACROS
    p = Path(path)
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        _PRECOMPUTED_U_MACROS = {k: list(v) for k, v in data.items()}
        return True
    except Exception:
        return False


def _build_u_macros(max_depth: int = 10) -> Dict[str, List[str]]:
    """
    Precompute macros for U, U', U2 as sequences of L,R,F,B,D.
    Uses BFS from the solved state; may take noticeable time on first run.
    """
    target_u = apply_sequence_kociemba(SOLVED, "U")

    seq_u = _bfs_find_equivalent(target_u, ALLOWED_MOVES, max_depth=max_depth)

    if seq_u is None:
        raise RuntimeError(
            f"Could not find L,R,F,B,D equivalent for U within depth {max_depth}. "
            "You may need to increase max_depth or provide precomputed macros "
            "via set_u_macros() or load_u_macros_from_file()."
        )

    seq_u_inv = _invert_sequence(seq_u)
    seq_u2 = seq_u + seq_u

    return {
        "U": seq_u,
        "U'": seq_u_inv,
        "U2": seq_u2,
    }


# Cache for U macros at module load (None = not yet computed).
_U_MACROS: Optional[Dict[str, List[str]]] = None


def _get_u_macros() -> Dict[str, List[str]]:
    """
    Return a dict with entries for U, U', U2 as lists of L,R,F,B,D moves.
    Loads from JSON or computes via BFS on first use.
    """
    global _U_MACROS, _PRECOMPUTED_U_MACROS

    if _U_MACROS is not None:
        return _U_MACROS

    # If user injected macros programmatically, use them.
    if _PRECOMPUTED_U_MACROS is not None:
        _U_MACROS = _PRECOMPUTED_U_MACROS
        return _U_MACROS

    # Try loading from same directory as this module.
    module_dir = os.path.dirname(os.path.abspath(__file__))
    default_macros_path = os.path.join(module_dir, "precomputed_u_macros_5faces.json")
    if load_u_macros_from_file(default_macros_path):
        _U_MACROS = _PRECOMPUTED_U_MACROS
        return _U_MACROS

    # Fall back to BFS search at runtime.
    _U_MACROS = _build_u_macros()
    return _U_MACROS


def _merge_two_moves(face: str, a: str, b: str) -> Optional[str]:
    """
    Combine two consecutive moves on the same face into one or cancel.
    Returns one move string or None (cancel).
    face is one of R, L, F, B, D.
    """

    def power(m: str) -> int:
        if len(m) == 1:
            return 1
        if m.endswith("'"):
            return 3
        # X2
        return 2

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
    """One pass: merge adjacent same-face moves. Returns a new list."""
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

        if face_a in "RLFBD" and face_a == face_b:
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
    """
    Repeatedly merge adjacent same-face moves until stable.
    Works for faces R, L, F, B, D.
    """
    prev = moves
    while True:
        next_list = _simplify_once(prev)
        if next_list == prev:
            return next_list
        prev = next_list


def rewrite_solution_without_u(solution: str) -> List[str]:
    """
    Rewrite a full solution (e.g. from kociemba) to use only
    L, R, F, B, D faces. Every U / U' / U2 move is replaced by
    its precomputed macro.
    """
    macros = _get_u_macros()
    tokens = solution.split()
    result: List[str] = []

    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # Normalize notation exactly as keys are stored.
        key = t
        if key in macros:
            result.extend(macros[key])
        else:
            result.append(t)

    return result


def solve_without_u(kociemba_string: str) -> str:
    """
    Solve the cube and return a solution that uses only L, R, F, B, D moves.

    - Input is a 54-character kociemba string (URFDLB order).
    - Uses kociemba for the full solution.
    - Rewrites U / U' / U2 to L,R,F,B,D macros.
    - Simplifies the final sequence (cancels and merges adjacent same-face moves).
    """
    kociemba_string = kociemba_string.replace(" ", "")
    if len(kociemba_string) != 54:
        raise ValueError("kociemba_string must be 54 characters")

    if kociemba_string == SOLVED:
        return ""

    full_solution = kociemba.solve(kociemba_string)
    no_u_list = rewrite_solution_without_u(full_solution)
    simplified = simplify_moves(no_u_list)
    return " ".join(simplified)


def get_move_count(solution: str) -> int:
    """Return the number of moves in a solution string (space-separated)."""
    if not solution or not solution.strip():
        return 0
    return len(solution.split())


__all__ = [
    "SOLVED",
    "solve_without_u",
    "rewrite_solution_without_u",
    "simplify_moves",
    "get_move_count",
    "set_u_macros",
    "load_u_macros_from_file",
]

