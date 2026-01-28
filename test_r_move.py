from cube_moves import apply_sequence

s = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
s1 = apply_sequence(s, "R")
s2 = apply_sequence(s1, "R'")
print("R then R' == solved:", s2 == s)
print("After R:", s1)
print("After R then R':", s2)
