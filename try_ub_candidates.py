"""Try candidate R,L,F,D sequences to find ones equal to U and B (kociemba)."""
from cube_moves import apply_sequence_kociemba

SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
target_u = apply_sequence_kociemba(SOLVED, "U")
target_b = apply_sequence_kociemba(SOLVED, "B")

# Candidates: common short conjugates (6-10 moves)
candidates = [
    "F R D R' D' F'",
    "R D F D' F' R'",
    "L F R F' R' L'",
    "F L R L' R' F'",
    "D R F R' F' D'",
    "R F D F' D' R'",
    "F D R D' R' F'",
    "R D' F D F' R'",
    "D F R F' R' D'",
    "L D F D' F' L'",
    "F R D' R' D F'",
    "R F D F' R' D'",
    "D R F' R' F D'",
    "F D R' D' R F'",
    "R D F' D' F R'",
    "L R F R' L' F'",
    "F R L R' L' F'",
    "R L F L' R' F'",
    "D F L F' L' D'",
    "F D L D' L' F'",
    "R F L F' L' R'",
    "L D R D' R' L'",
    "D L F L' F' D'",
    "L F D F' D' L'",
    "F L D L' D' F'",
    "R L D L' D' R'",
    "D R L R' L' D'",
    "L R D R' D' L'",
    "R D L D' L' R'",
    "D L R L' R' D'",
]

print("Testing U equivalents...")
for seq in candidates:
    got = apply_sequence_kociemba(SOLVED, seq)
    if got == target_u:
        print("  U =", seq)
        break
else:
    print("  No U found in candidates")

print("Testing B equivalents...")
for seq in candidates:
    got = apply_sequence_kociemba(SOLVED, seq)
    if got == target_b:
        print("  B =", seq)
        break
else:
    print("  No B found in candidates")
