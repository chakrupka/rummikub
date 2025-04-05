from collections import Counter, defaultdict
from random import shuffle
from termcolor import colored, cprint


class Tile:
    def __init__(self, color, number, is_joker=False):
        self.color = color
        self.number = number
        self.is_joker = is_joker
        self.code = f"{color[0]}{number}" if not is_joker else "j"

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if not self.is_joker:
            return colored(f"[{self.number}]", self.color)
        else:
            return colored("[J]", "white")


class TileSet:
    def __init__(self, tiles, type, joker_info=None):
        self.tiles = sorted(tiles, key=lambda tile: tile.number)
        self.type = type
        self.joker_info = joker_info

    def __iter__(self):
        return iter(self.tiles)

    def __str__(self):
        return "".join(str(tile) for tile in self.tiles)


class BoardController:
    def __init__(self):
        self.unused_all = set()
        self.sets = []
        self._generate_tiles()

    def _generate_tiles(self):
        for _ in range(2):
            for number in range(1, 14):
                for color in ["red", "yellow", "cyan", "black"]:
                    tile = Tile(color, number)
                    self.unused_all.add(tile)
            joker_tile = Tile("white", -1, True)
            self.unused_all.add(joker_tile)

    def allocate_tiles(self, players):
        all_tiles = list(self.unused_all)
        for _ in range(14):
            for player in players:
                tile = all_tiles.pop()
                player.add_to_hand(tile)
                self.unused_all.remove(tile)


class PlayHelper:
    def __init__(self, player, board):
        self.player = player
        self.board = board

        self.unused_dict = defaultdict(lambda: defaultdict(list))
        self.unused_jokers = []
        self.tile_counts = defaultdict(int)

        self._build_dict()
        self.valid_sets = self._gather_valid_sets()

    def _build_dict(self):
        for tile in self.player.hand:
            if tile.is_joker:
                self.unused_jokers.append(tile)
                self.tile_counts["j"] += 1
            else:
                self.unused_dict[tile.color][tile.number].append(tile)
                self.tile_counts[tile.code] += 1

        for tile_set in self.board.sets:
            for tile in tile_set:
                if tile.is_joker:
                    replacable = False
                    if tile_set.type == "run":
                        for p_tile in self.player.hand:
                            if (
                                p_tile.color == tile.color
                                and p_tile.number == tile.number
                            ):
                                self.unused_jokers.append(tile)
                                self.tile_counts["j"] += 1
                                replacable = True
                                break
                    else:
                        used_colors = set()
                        for set_tile in tile_set:
                            if not set_tile.is_joker:
                                used_colors.add(tile.color)

                        for p_tile in self.player.hand:
                            if (
                                p_tile.color not in used_colors
                                and p_tile.number == tile.number
                            ):
                                self.unused_jokers.append(tile)
                                self.tile_counts["j"] += 1
                                replacable = True
                                break

                    if not replacable:
                        self.unused_dict[tile.color][tile.number].append(tile)
                        self.tile_counts[tile.code] += 1
                else:
                    self.unused_dict[tile.color][tile.number].append(tile)
                    self.tile_counts[tile.code] += 1

    def _gather_valid_sets(self):
        valid_sets = []

        def find_runs(tile):
            runs = []
            run = [tile]
            jokers_used = 0
            joker_info = []
            next_num = tile.number + 1

            while self.unused_dict[tile.color][next_num] or jokers_used < len(
                self.unused_jokers
            ):
                if self.unused_dict[tile.color][next_num]:
                    run.append(self.unused_dict[tile.color][next_num][-1])
                else:
                    joker = self.unused_jokers[-1]
                    joker_info.append([tile.color, next_num])
                    run.append(joker)
                    jokers_used += 1

                if len(run) >= 3:
                    runs.append(
                        TileSet(run, "run", joker_info if jokers_used else None)
                    )

                next_num += 1

            return runs

        def find_groups(tile):
            groups = []
            group = [tile]
            jokers_used = 0
            joker_info = []
            colors = ["red", "yellow", "cyan", "black"]

            for color in colors:
                if color != tile.color and (
                    self.unused_dict[color][tile.number]
                    or jokers_used < len(self.unused_jokers)
                ):
                    if self.unused_dict[color][tile.number]:
                        group.append(self.unused_dict[color][tile.number][-1])
                    else:
                        joker = self.unused_jokers[-1]
                        joker_info.append([color, tile.number])
                        group.append(joker)
                        jokers_used += 1

                    if len(group) >= 3:
                        groups.append(
                            TileSet(group, "run", joker_info if jokers_used else None)
                        )

            return groups

        for color in ["red", "yellow", "cyan", "black"]:
            for number in list(self.unused_dict[color].keys()):
                for tile in self.unused_dict[color][number]:
                    if tile.number <= 11:
                        valid_sets.extend(find_runs(tile))
                    valid_sets.extend(find_groups(tile))

        return valid_sets

    def first_turn(self):
        print("\nValid set:", end=" ")
        for tile_set in self.valid_sets:
            print(f"{tile_set} | ", end="")

        best_play = []
        max_tiles_played = 0
        all_board_tiles = set(
            [tile for tile_set in self.board.sets for tile in tile_set]
        )
        counts = defaultdict(int)

        def backtrack(tile_sets, current_sets):
            nonlocal best_play, max_tiles_played, all_board_tiles, counts
            if not tile_sets:
                return

            current_board_tiles = set()
            tiles_in_play = set()
            for tile_set in current_sets:
                for tile in tile_sets:
                    if tile in all_board_tiles:
                        current_board_tiles.add(tile)
                    tiles_in_play.add(tile)

            if len(current_board_tiles) == len(all_board_tiles):
                if len(tiles_in_play) > max_tiles_played:
                    best_play = [tile_set for tile_set in current_sets]
                    max_tiles_played = len(tiles_in_play)

            for index, tile_set in enumerate(tile_sets):
                counts_prev = counts.copy()
                counts_temp = counts.copy()
                for tile_set in tile_sets:
                    duplicates = False
                    for tile in tile_set:
                        if counts_temp[tile.code] + 1 > self.tile_counts[tile.code]:
                            duplicates = True
                            break
                        counts_temp[tile.code] += 1
                    if not duplicates:
                        counts = counts_temp
                        backtrack(
                            tile_sets[min(0, index - 1) : index]
                            + tile_sets[index + 1 :],
                            current_sets + [tile_set],
                        )
                counts = counts_prev

            return

        backtrack(self.valid_sets, [])

        return best_play


class Player:
    def __init__(self):
        self.hand = set()
        self.has_played = False

    def add_to_hand(self, tile):
        self.hand.add(tile)

    def remove_from_hand(self, tile):
        self.hand.remove(tile)


class Game:
    def __init__(self, num_players, starting_player=0):
        self.players = [Player() for _ in range(num_players)]
        self.player_turn = starting_player
        self.board = BoardController()
        self.setup_game()

    def display_game(self):
        for index, player in enumerate(self.players):
            print(f"Player {index}:", end=" ")
            for tile in sorted(player.hand, key=lambda tile: (tile.color, tile.number)):
                print(tile, end="")
            print()

        print("\nBoard:", end=" ")
        for tile_set in self.board.sets:
            print(f"{tile_set} | ", end="")

        print("\n\nPool:", end=" ")
        for tile in sorted(
            self.board.unused_all, key=lambda tile: (tile.color, tile.number)
        ):
            print(tile, end="")
        print("\n")

    def take_turn(self):
        cprint(f"\n> PLAYER {self.player_turn + 1}", attrs=["bold", "underline"])
        player = self.players[self.player_turn]
        play_helper = PlayHelper(player, self.board)
        if not player.has_played:
            play = play_helper.first_turn()

        if play:
            cprint(f"\nPLAYS", attrs=["bold"], color="green", end=" ")
            if not player.has_played:
                for tile_set in play:
                    self.board.sets.append(tile_set)
                    for tile in tile_set.tiles:
                        print(f"{tile}", end="")
                        player.remove_from_hand(tile)
                print("\n")
                player.has_played = True
        else:
            tiles_list = list(self.board.unused_all)
            shuffle(tiles_list)
            drawn_tile = tiles_list.pop()
            player.add_to_hand(drawn_tile)
            self.board.unused_all.remove(drawn_tile)
            cprint(f"\nDRAWS", attrs=["bold"], color="red", end=" ")
            print(f"{drawn_tile}\n")

        self.player_turn = self.player_turn + 1 if self.player_turn < 3 else 0
        self.display_game()

    def setup_game(self):
        self.board.allocate_tiles(self.players)
        cprint(f"> BEGIN GAME", attrs=["bold", "underline"])
        self.display_game()


game = Game(4)
s = input("Take turn?")
while s == "":
    game.take_turn()
    s = input("Take turn?")
