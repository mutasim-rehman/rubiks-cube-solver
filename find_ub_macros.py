"""One-off: find R,L,F,D sequences that equal U and B via BFS. Print and exit."""
from collections import deque
from cube_moves import apply_sequence_kociemba

SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
ALLOWED = ["R","R'","R2","L","L'","L2","F","F'","F2","D","D'","D2"]

INVERSE = {"R": "R'", "R'": "R", "R2": "R2", "L": "L'", "L'": "L", "L2": "L2",
           "F": "F'", "F'": "F", "F2": "F2", "D": "D'", "D'": "D", "D2": "D2"}


def bfs(target, max_d=10):
    seen = {SOLVED}
    queue = deque([(SOLVED, [])])
    while queue:
        state, path = queue.popleft()
        if len(path) >= max_d:
            continue
        for m in ALLOWED:
            new_s = apply_sequence_kociemba(state, m)
            if new_s in seen:
                continue
            seen.add(new_s)
            new_path = path + [m]
            if new_s == target:
                return new_path
            queue.append((new_s, new_path))
    return None


def bfs_bidirectional(target, max_depth_each=5):
    """Bidirectional BFS: forward from SOLVED, backward from target. Covers path length up to 2*max_depth_each."""
    if target == SOLVED:
        return []
    # Forward: state -> path from SOLVED to state
    forward_seen = {SOLVED: []}
    forward_queue = deque([(SOLVED, [])])
    # Backward: state -> path (as list of moves) from target to state (we apply inverse moves)
    backward_seen = {target: []}
    backward_queue = deque([(target, [])])

    def expand_forward():
        state, path = forward_queue.popleft()
        if len(path) >= max_depth_each:
            return None
        for m in ALLOWED:
            new_s = apply_sequence_kociemba(state, m)
            if new_s in forward_seen:
                continue
            fwd_path = path + [m]
            forward_seen[new_s] = fwd_path
            forward_queue.append((new_s, fwd_path))
            if new_s in backward_seen:
                back_path = backward_seen[new_s]
                return fwd_path + list(reversed(back_path))
        return None

    def expand_backward():
        state, path = backward_queue.popleft()
        if len(path) >= max_depth_each:
            return None
        for m in ALLOWED:
            inv_m = INVERSE[m]
            new_s = apply_sequence_kociemba(state, inv_m)
            if new_s in backward_seen:
                continue
            back_path = path + [m]
            backward_seen[new_s] = back_path
            backward_queue.append((new_s, back_path))
            if new_s in forward_seen:
                fwd_path = forward_seen[new_s]
                return fwd_path + list(reversed(back_path))
        return None

    while forward_queue or backward_queue:
        if forward_queue:
            r = expand_forward()
            if r is not None:
                return r
        if backward_queue:
            r = expand_backward()
            if r is not None:
                return r
    return None

if __name__ == "__main__":
    target_u = apply_sequence_kociemba(SOLVED, "U")
    target_b = apply_sequence_kociemba(SOLVED, "B")
    u, b = None, None

    print("Trying bidirectional BFS (depth 6 each side, total length up to 12)...")
    u = bfs_bidirectional(target_u, max_depth_each=6)
    if u:
        print("U =", " ".join(u), "(%d moves)" % len(u))
    else:
        print("U not found with bidirectional depth 6")
    b = bfs_bidirectional(target_b, max_depth_each=6)
    if b:
        print("B =", " ".join(b), "(%d moves)" % len(b))
    else:
        print("B not found with bidirectional depth 6")

    if not u or not b:
        print("Falling back to one-way BFS (depth 7; may take 10–20 min)...")
        for max_d in [7]:
            if u is None:
                print("Searching for U (max depth %d)..." % max_d)
                u = bfs(target_u, max_d=max_d)
                if u:
                    print("U =", " ".join(u), "(%d moves)" % len(u))
            if b is None:
                print("Searching for B (max depth %d)..." % max_d)
                b = bfs(target_b, max_d=max_d)
                if b:
                    print("B =", " ".join(b), "(%d moves)" % len(b))
            if u and b:
                break

    # Save to JSON for constrained solver
    if u and b:
        import json
        from cube_solver_constrained import _invert_sequence
        macros = {
            "U": u,
            "U'": _invert_sequence(u),
            "U2": u + u,
            "B": b,
            "B'": _invert_sequence(b),
            "B2": b + b,
        }
        out_path = "precomputed_ub_macros.json"
        with open(out_path, "w") as f:
            json.dump(macros, f, indent=2)
        print("Saved macros to", out_path)
    else:
        print("Could not find U and/or B equivalents. Run with longer timeout or higher depth.")
