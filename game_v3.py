import pulp as pl
import itertools
import collections
import random
from termcolor import colored, cprint

COLORS = ["B", "R", "O", "K"]
NUMBERS = range(1, 14)
TILES = [(c, n) for c in COLORS for n in NUMBERS] + ["J"]
SETS = set()


def add_to_sets(tileset):
    set_to_add = tuple(sorted(tileset, key=str))
    SETS.add(set_to_add)


for c in COLORS:
    for n in NUMBERS:
        for run_len in range(3, 6):
            if n + run_len <= 14:
                add_to_sets([(c, n) for n in range(n, n + run_len)])
for n in NUMBERS:
    for group_len in range(3, 5):
        for group in itertools.combinations(COLORS, group_len):
            add_to_sets([(c, n) for c in group])


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


def optimal_play(board_tiles, rack_tiles):
    global SETS, TILES

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

    table_vec = counter_to_vector(board_tiles)
    rack_vec = counter_to_vector(rack_tiles)

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

    tiles_in_sets = collections.Counter()
    for j, var in x.items():
        copies = int(round(var.value()))
        if copies:
            set_tup = idx2set[j]
            for _ in range(copies):
                tiles_in_sets.update(set_tup)

    best_play = []
    for j, var in x.items():
        copies = int(round(var.value()))
        if copies:
            best_play.extend([idx2set[j] for _ in range(copies)])

    played_tiles = []
    for i, var in y.items():
        copies = int(round((var.value)()))
        if copies:
            played_tiles.extend([idx2tile[i] for _ in range(copies)])

    return best_play, played_tiles


def color_tile(tile):
    tile_str = f"[{tile[1]}]" if tile != "J" else "[J]"
    char_to_color = {"B": "cyan", "R": "red", "O": "yellow", "K": "black"}
    if tile == "J":
        return colored(tile_str, "white")
    return colored(tile_str, char_to_color[tile[0]])


class Game:
    def __init__(self, num_players):
        self.board_tiles = collections.Counter()
        self.board_sets = []
        self.unturned_tiles = []
        self.num_players = num_players
        self.player_hands = {
            i: collections.Counter() for i in range(1, num_players + 1)
        }
        self.player_turn = 1
        self.setup_game()

    def setup_game(self):
        global TILES
        usable_tiles = TILES * 2
        random.shuffle(usable_tiles)
        print(usable_tiles.count("J"))

        for _ in range(14):
            for i in range(1, self.num_players + 1):
                self.player_hands[i][usable_tiles.pop()] += 1

        self.unturned_tiles = usable_tiles

        cprint(f"> BEGIN GAME", attrs=["bold", "underline"])
        self.display_game()

    def take_turn(self):
        cprint(f"\n> PLAYER {self.player_turn}", attrs=["bold", "underline"])
        best_play, played_tiles = optimal_play(
            self.board_tiles, self.player_hands[self.player_turn]
        )
        if best_play:
            cprint(f"\nPLAYS", attrs=["bold"], color="green", end=" ")
            self.board_sets = best_play
            for tile in played_tiles:
                cprint(color_tile(tile), end="")
                self.board_tiles[tile] += 1
                self.player_hands[self.player_turn][tile] -= 1
                if not self.player_hands[self.player_turn][tile]:
                    del self.player_hands[self.player_turn][tile]
            print("\n")
        else:
            drawn_tile = self.unturned_tiles.pop()
            self.player_hands[self.player_turn][drawn_tile] += 1
            cprint(f"\nDRAWS", attrs=["bold"], color="red", end=" ")
            print(f"{color_tile(drawn_tile)}\n")

        self.player_turn = (
            self.player_turn + 1 if self.player_turn < self.num_players else 1
        )
        self.display_game()

    def display_game(self):
        for id, hand in self.player_hands.items():
            print(f"Player {id}:", end=" ")
            sorted_hand = sorted([tile for tile in hand.keys() if tile != "J"])
            sorted_hand.extend(["J"] * hand["J"])
            for tile in sorted_hand:
                tile_str = color_tile(tile)
                print(f"{tile_str:<10}", end="")
            print()

        print("\nBoard:", end=" ")
        for set_tup in self.board_sets:
            for tile in set_tup:
                cprint(color_tile(tile), end="")
            print(" | ", end="")

        print("\n\nPool:", end=" ")
        sorted_pool = sorted([tile for tile in self.unturned_tiles if tile != "J"])
        sorted_pool.extend(["J"] * self.unturned_tiles.count("J"))
        for tile in sorted_pool:
            cprint(color_tile(tile), end="")
        print("\n")


game = Game(4)
s = input("Take turn?")
while s == "":
    game.take_turn()
    s = input("Take turn?")
