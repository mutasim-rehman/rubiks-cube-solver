"""
Simulation: verify that the constrained solver (R, L, F, D only) actually solves the cube.

Flow for each test case:
  1. Start from solved cube.
  2. Apply a scramble (may include U, B).
  3. Get constrained solution (only R, L, F, D).
  4. Apply that solution to the scrambled state.
  5. Check that the result is the solved cube.

Also prints full (kociemba) solution length vs constrained solution length.

If precomputed_ub_macros.json exists in the project directory, it is loaded
so the solver does not need to run BFS (which can be slow).
"""

import os
import kociemba
from cube_moves import apply_sequence_kociemba
from cube_solver_constrained import (
    SOLVED,
    solve_constrained,
    load_u_b_macros_from_file,
    rewrite_solution_to_rlfd,
    simplify_moves,
    get_move_count,
)

# Load precomputed U/B macros if available (avoids slow BFS)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_precomputed_path = os.path.join(_script_dir, "precomputed_ub_macros.json")
if load_u_b_macros_from_file(_precomputed_path):
    pass  # macros loaded


def run_simulation():
    test_cases = [
        "R",
        "R U R' U'",
        "F2",
        "U",
        "B",
        "U2",
        "B2",
        "R U R' U' R U R' U'",
        "R2 U2 F2",
        "L U2 D' R F2 B",
        "U B U' B'",
        "F R U R' U' F'",
    ]

    print("=" * 70)
    print("CONSTRAINED SOLVER SIMULATION (R, L, F, D only)")
    print("=" * 70)
    print("Each row: scramble -> constrained solution -> apply -> solved?")
    print()

    all_ok = True
    for scramble in test_cases:
        try:
            scrambled = apply_sequence_kociemba(SOLVED, scramble)
            full_solution = kociemba.solve(scrambled)
            constrained_solution = solve_constrained(scrambled)
            after = apply_sequence_kociemba(scrambled, constrained_solution)
            ok = after == SOLVED
            all_ok = all_ok and ok
            status = "OK" if ok else "FAIL"
            n_full = get_move_count(full_solution)
            n_const = get_move_count(constrained_solution)
            print(f"  Scramble: {scramble}")
            print(f"  Full (kociemba) solution [{n_full} moves]: {full_solution}")
            print(f"  Constrained (R,L,F,D) solution [{n_const} moves]: {constrained_solution}")
            print(f"  After applying constrained solution => {status}")
            if not ok:
                print(f"     Expected SOLVED, got state (first 30 chars): {after[:30]}...")
            print()
        except Exception as e:
            print(f"  Scramble: {scramble} => ERROR: {e}")
            all_ok = False
            print()

    print("=" * 70)
    print("All checks passed." if all_ok else "Some checks FAILED.")
    return all_ok


def main():
    success = run_simulation()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
