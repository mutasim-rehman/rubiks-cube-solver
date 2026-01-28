"""
Move permutations for the Rubik's cube.
Facelet order (kociemba): U(0-8), R(9-17), F(18-26), D(27-35), L(36-44), B(45-53).
Per-face layout: row-major [0,1,2; 3,4,5; 6,7,8].
Permutation p: after move, facelet at i receives color from facelet p[i] (new[i] = old[p[i]]).
"""

def _build_u_cw():
    p = list(range(54))
    # U face 90 CW
    f = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    for i in range(9):
        p[i] = f[i]
    # Cycle F top -> R top -> B top -> L top -> F top
    # F 18,19,20; R 9,10,11; B 45,46,47; L 36,37,38
    p[9], p[10], p[11] = 18, 19, 20
    p[45], p[46], p[47] = 9, 10, 11
    p[36], p[37], p[38] = 45, 46, 47
    p[18], p[19], p[20] = 36, 37, 38
    return p


def _build_d_cw():
    p = list(range(54))
    # D face 90 CW
    f = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    for i in range(9):
        p[27 + i] = 27 + f[i]
    # Cycle F bottom -> L bottom -> B bottom -> R bottom -> F bottom
    # F 24,25,26; L 42,43,44; B 51,52,53; R 15,16,17
    p[42], p[43], p[44] = 24, 25, 26
    p[51], p[52], p[53] = 42, 43, 44
    p[15], p[16], p[17] = 51, 52, 53
    p[24], p[25], p[26] = 15, 16, 17
    return p


def _build_r_cw():
    p = list(range(54))
    # R face 90 CW
    f = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    for i in range(9):
        p[9 + i] = 9 + f[i]
    # Cycle U col2 -> F col2 -> D col2 -> B col0 (reversed) -> U col2
    # U 2,5,8; F 20,23,26; D 29,32,35; B 45,48,51 (col 0, reverse when D<->B)
    p[20], p[23], p[26] = 2, 5, 8
    p[29], p[32], p[35] = 20, 23, 26
    p[45], p[48], p[51] = 35, 32, 29  # D->B reversed
    p[2], p[5], p[8] = 51, 48, 45     # B->U reversed
    return p


def _build_l_cw():
    p = list(range(54))
    # L face 90 CW
    f = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    for i in range(9):
        p[36 + i] = 36 + f[i]
    # Cycle U col0 -> B col2 (reversed) -> D col0 -> F col0 -> U col0
    # U 0,3,6; B 47,50,53; D 27,30,33; F 18,21,24
    p[47], p[50], p[53] = 0, 3, 6     # U->B reversed
    p[27], p[30], p[33] = 53, 50, 47  # B->D reversed
    p[18], p[21], p[24] = 27, 30, 33
    p[0], p[3], p[6] = 24, 21, 18
    return p


def _build_f_cw():
    p = list(range(54))
    # F face 90 CW
    f = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    for i in range(9):
        p[18 + i] = 18 + f[i]
    # Cycle U row2 -> R col0 -> D row0 -> L col2 -> U row2
    # U 6,7,8; R 9,12,15; D 27,28,29; L 38,41,44
    p[9], p[12], p[15] = 6, 7, 8
    p[27], p[28], p[29] = 9, 12, 15
    p[38], p[41], p[44] = 27, 28, 29
    p[6], p[7], p[8] = 44, 41, 38    # L col2 reversed when going to U
    return p


def _build_b_cw():
    p = list(range(54))
    # B face 90 CW
    f = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    for i in range(9):
        p[45 + i] = 45 + f[i]
    # Cycle U row0 -> L col0 -> D row2 -> R col2 -> U row0
    # U 0,1,2; L 36,39,42; D 33,34,35; R 11,14,17
    p[36], p[39], p[42] = 0, 1, 2
    p[33], p[34], p[35] = 36, 39, 42
    p[11], p[14], p[17] = 33, 34, 35
    p[0], p[1], p[2] = 17, 14, 11   # R col2 reversed when going to U
    return p


def _apply_perm(s, perm):
    """Apply permutation to 54-char string. new[i] = old[perm[i]]."""
    return ''.join(s[perm[i]] for i in range(54))


def _invert_perm(perm):
    inv = [0] * 54
    for i in range(54):
        inv[perm[i]] = i
    return inv


def _compose(perm_a, perm_b):
    """Compose: first apply b, then a. result[i] = b[a[i]] for 'from' convention."""
    return [perm_b[perm_a[i]] for i in range(54)]


# Build move table
_MOVES = {}

def _add(name, perm):
    _MOVES[name] = perm


_add('U', _build_u_cw())
_add('U\'', _invert_perm(_build_u_cw()))
_add('U2', _compose(_build_u_cw(), _build_u_cw()))

_add('D', _build_d_cw())
_add('D\'', _invert_perm(_build_d_cw()))
_add('D2', _compose(_build_d_cw(), _build_d_cw()))

_add('R', _build_r_cw())
_add('R\'', _invert_perm(_build_r_cw()))
_add('R2', _compose(_build_r_cw(), _build_r_cw()))

_add('L', _build_l_cw())
_add('L\'', _invert_perm(_build_l_cw()))
_add('L2', _compose(_build_l_cw(), _build_l_cw()))

_add('F', _build_f_cw())
_add('F\'', _invert_perm(_build_f_cw()))
_add('F2', _compose(_build_f_cw(), _build_f_cw()))

_add('B', _build_b_cw())
_add('B\'', _invert_perm(_build_b_cw()))
_add('B2', _compose(_build_b_cw(), _build_b_cw()))


def apply_sequence(cubestring, moves):
    """Apply a sequence of moves (e.g. \"R U R' U'\") to a 54-char kociemba cubestring. Returns new string."""
    s = cubestring
    for m in moves.split():
        key = m
        if m.endswith("'"):
            key = m[0] + "'"  # normalize "R'" 
        if key not in _MOVES:
            raise ValueError(f"Unknown move: {m}")
        s = _apply_perm(s, _MOVES[key])
    return s


def get_move_perm(name):
    """Get permutation for a single move (e.g. 'U', \"R'\", 'F2')."""
    if name.endswith("'"):
        key = name[0] + "'"
    else:
        key = name
    return _MOVES.get(key)


def apply_sequence_kociemba(cubestring: str, moves: str) -> str:
    """
    Apply a move sequence using kociemba's cubie-level moves.
    Use this when applying kociemba's solution so conventions match exactly.
    """
    import os
    import sys
    import kociemba
    kociemba_dir = os.path.dirname(os.path.abspath(kociemba.__file__))
    if kociemba_dir not in sys.path:
        sys.path.insert(0, kociemba_dir)
    from pykociemba.facecube import FaceCube
    from pykociemba.cubiecube import CubieCube, moveCube

    ax = "URFDLB"
    cc = FaceCube(cubestring.replace(" ", "")).toCubieCube()
    for tok in moves.split():
        tok = tok.strip()
        if not tok:
            continue
        face = tok[0]
        if face not in ax:
            raise ValueError(f"Unknown face in move: {tok}")
        axis = ax.index(face)
        if len(tok) == 1:
            power = 1
        elif tok.endswith("2"):
            power = 2
        else:
            power = 3  # R' or R'
        for _ in range(power):
            cc.multiply(moveCube[axis])
    return cc.toFaceCube().to_String()
