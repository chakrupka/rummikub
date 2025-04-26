import pulp as pl
import itertools
import collections


def optimal_play(board_tiles, rack_tiles):
    COLORS = ["B", "R", "O", "K"]
    NUMBERS = range(1, 14)
    TILES = [(c, n) for c in COLORS for n in NUMBERS] + ["J"]
    SETS = set()

    def add_to_sets(tileset):
        set_to_add = tuple(sorted(tileset, key=str))
        SETS.add(set_to_add)

    # Runs
    for c in COLORS:
        for n in NUMBERS:
            for run_len in range(3, 6):
                if n + run_len <= 14:
                    add_to_sets([(c, n) for n in range(n, n + run_len)])
    # Groups
    for n in NUMBERS:
        for group_len in range(3, 5):
            for group in itertools.combinations(COLORS, group_len):
                add_to_sets([(c, n) for c in group])

    # Jokers
    def inject_jokers(tileset, k):
        for indexes in itertools.combinations(range(len(tileset)), k):
            tileset_copy = list(tileset)
            for index in indexes:
                tileset_copy[index] = "J"
            if k == 2 and len(tileset) == 3 and len({tile[1] for tile in tileset}) == 1:
                continue
            add_to_sets(tuple(tileset_copy))

    for tileset in list(SETS):
        if "J" not in tileset:
            inject_jokers(tileset, 1)
            inject_jokers(tileset, 2)

    print("Board:", sorted(board_tiles, key=str))
    print("Rack:", sorted(rack_tiles, key=str))

    tile2idx = {tile: i for i, tile in enumerate(TILES)}
    idx2tile = {i: tile for tile, i in tile2idx.items()}

    SETS = sorted(list(SETS), key=str)
    set2idx = {s: j for j, s in enumerate(SETS)}
    idx2set = {j: s for s, j in set2idx.items()}

    S = collections.defaultdict(dict)
    for s, j in set2idx.items():
        for tile in s:
            i = tile2idx[tile]
            S[i][j] = S[i].get(j, 0) + 1

    def counter_to_vector(counter):
        v = [0] * 53
        for tile, copies in counter.items():
            v[tile2idx[tile]] = copies
        return v

    table_vec = counter_to_vector(collections.Counter(board_tiles))
    rack_vec = counter_to_vector(collections.Counter(rack_tiles))

    prob = pl.LpProblem(name="Rummikub_MaxTiles", sense=pl.LpMaximize)

    x = pl.LpVariable.dicts(
        name="x", indices=set2idx.values(), lowBound=0, upBound=2, cat="Integer"
    )
    y = pl.LpVariable.dicts(
        name="y", indices=tile2idx.values(), lowBound=0, upBound=2, cat="Integer"
    )

    prob += pl.lpSum(y[i] for i in y), "Maximize_tiles_played"

    for i in range(len(TILES)):
        lhs = pl.lpSum(S[i].get(j, 0) * x[j] for j in S[i])
        rhs = table_vec[i] + y[i]
        prob += (lhs == rhs), f"balance_{i}"
        prob += y[i] <= rack_vec[i], f"rack_{i}"

    w = collections.Counter()
    for j, set_tuple in idx2set.items():
        copies_possible = (
            min(board_tiles[tile] for tile in set_tuple)
            if all(tile in board_tiles for tile in set_tuple)
            else 0
        )
        w[j] = copies_possible

    z = pl.LpVariable.dicts(
        name="z", indices=set2idx.values(), lowBound=0, upBound=2, cat="Integer"
    )
    for j in set2idx.values():
        prob += z[j] <= x[j], f"link1_{j}"
        prob += z[j] <= w[j], f"link2_{j}"

    M = 40.0
    primary = pl.lpSum(y[i] for i in y)
    secondary = (1 / M) * pl.lpSum(z[j] for j in z)

    prob.sense = pl.LpMaximize
    prob.setObjective(primary + secondary)

    status = prob.solve(pl.PULP_CBC_CMD(msg=False))
    if status != pl.LpStatusOptimal:
        raise Exception("No optimal solution found")
    print("Primary objective value:", pl.value(prob.objective))

    tiles_in_sets = collections.Counter()
    for j, var in x.items():
        copies = int(round(var.value()))
        if copies:
            set_tup = idx2set[j]
            for _ in range(copies):
                tiles_in_sets.update(set_tup)

    best_play = []
    print("Best play:")
    for j, var in x.items():
        copies = int(round(var.value()))
        if copies:
            print(f"  {copies} × [{idx2set[j]}]")
            best_play.extend([idx2set[j] for _ in range(copies)])

    print("Tiles from rack:")
    played_tiles = []
    for i, var in y.items():
        copies = int(round((var.value)()))
        if copies:
            print(f"  {copies} × {idx2tile[i]}")
            played_tiles.extend([idx2tile[i] for _ in range(copies)])

    return best_play, played_tiles
