"""
Verification script: scramble -> solve -> apply solution => solved.
Uses kociemba's own move application so conventions match.
"""

import kociemba
from cube_moves import apply_sequence_kociemba

SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def main():
    cases = [
        "R",
        "R U R' U'",
        "F2",
        "R U R' U' R U R' U'",
        "R2 U2 F2",
        "L U2 D' R F2 B",
    ]
    print("Verifying solver (scramble -> solve -> apply solution => solved)\n")
    all_ok = True
    for scramble in cases:
        try:
            scrambled = apply_sequence_kociemba(SOLVED, scramble)
            solution = kociemba.solve(scrambled)
            after = apply_sequence_kociemba(scrambled, solution)
            ok = after == SOLVED
            status = "OK" if ok else "FAIL"
            print(f"  Scramble: {scramble}")
            print(f"  Solution: {solution}")
            print(f"  => {status}")
            if not ok:
                print(f"     Expected solved, got: {after[:30]}...")
                all_ok = False
        except Exception as e:
            print(f"  Scramble: {scramble} => ERROR: {e}")
            all_ok = False
        print()
    print("=" * 50)
    print("All checks passed." if all_ok else "Some checks FAILED.")
    return all_ok


if __name__ == "__main__":
    main()
