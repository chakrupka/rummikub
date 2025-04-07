from collections import Counter, defaultdict
from random import shuffle
import time
from termcolor import colored, cprint


class Tile:
    def __init__(self, color, number, is_joker=False):
        self.color = color
        self.number = number
        self.is_joker = is_joker
        self.code = f"{color[0]}{number}" if self.color != "white" else "j"

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
        shuffle(all_tiles)
        for _ in range(14):
            for player in players:
                tile = all_tiles.pop()
                player.add_to_hand(tile)
                self.unused_all.remove(tile)


class PlayHelper:
    def __init__(self, player, board):
        self.player = player
        self.board = board
        self.tile_dict = defaultdict(list)
        self.tile_counts = defaultdict(int)
        self.all_tiles = set()
        self.board_tiles = set()
        self._build_dict()

    def _build_dict(self):
        for tile in self.player.hand:
            self.tile_dict[tile.code].append(tile)
            self.tile_counts[tile.code] += 1
            self.all_tiles.add(tile)

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
                                self.tile_dict["j"].append(tile)
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
                                self.tile_dict["j"].append(tile)
                                self.tile_counts["j"] += 1
                                replacable = True
                                break

                    if not replacable:
                        self.tile_dict[tile.code].append(tile)
                        self.tile_counts[tile.code] += 1
                else:
                    self.tile_dict[tile.code].append(tile)
                    self.tile_counts[tile.code] += 1

                self.all_tiles.add(tile)
                self.board_tiles.add(tile)

    def turn(self):
        best_play = []
        max_tiles_played = 0
        start_time = time.time()
        last_print_time = start_time
        steps = 0
        memo = {}

        def backtrack(tiles, tile_sets, counts):
            nonlocal best_play, max_tiles_played, steps, memo, last_print_time

            tiles_key = tuple(sorted(tile.code for tile in tiles))
            if tiles_key in memo:
                return

            current_board_tiles = []
            tiles_in_play = []
            for tile_set in tile_sets:
                for tile in tile_set:
                    if tile in self.board_tiles:
                        current_board_tiles.append(tile)
                    tiles_in_play.append(tile)

            result = 0
            if len(current_board_tiles) == len(self.board_tiles):
                if len(tiles_in_play) > max_tiles_played:
                    best_play = [tile_set for tile_set in tile_sets]
                    max_tiles_played = len(tiles_in_play)
                    result = len(tiles_in_play)
                    memo[tiles_key] = result

            if len(tiles_in_play) + len(tiles) <= max_tiles_played:
                return

            for tile in tiles:
                if time.time() - last_print_time >= 5.0:
                    print(
                        f"Time elapsed: {time.time() - start_time:.0f}, steps: {steps}"
                    )
                    last_print_time = time.time()
                if tile.color != "white":
                    if tile.number <= 11:
                        run = [tile]
                        next_num = tile.number + 1
                        joker_info = []
                        next_code = f"{tile.color[0]}{next_num}"
                        temp_tiles = tiles.copy()
                        temp_tiles.remove(tile)
                        counts_temp = counts.copy()
                        counts_temp[tile.code] -= 1

                        while counts_temp[next_code] or counts_temp["j"]:
                            steps += 1
                            tile_index = -1
                            if counts_temp[next_code]:
                                if (
                                    counts_temp[next_code] == 1
                                    and len(self.tile_dict[next_code]) == 2
                                ):
                                    if self.tile_dict[next_code][0] in temp_tiles:
                                        tile_index = 0
                                run.append(self.tile_dict[next_code][tile_index])
                                temp_tiles.remove(self.tile_dict[next_code][tile_index])
                                counts_temp[next_code] -= 1
                            else:
                                if (
                                    counts_temp["j"] == 1
                                    and len(self.tile_dict["j"]) == 2
                                ):
                                    if self.tile_dict["j"][0] in temp_tiles:
                                        tile_index = 0
                                run.append(self.tile_dict["j"][tile_index])
                                temp_tiles.remove(self.tile_dict["j"][tile_index])
                                joker_info.append([tile.color, next_num])
                                counts_temp["j"] -= 1

                            if len(run) >= 3:
                                backtrack(
                                    temp_tiles,
                                    tile_sets
                                    + [
                                        TileSet(
                                            run,
                                            "run",
                                            joker_info if joker_info else None,
                                        )
                                    ],
                                    counts_temp,
                                )

                            next_num += 1
                            next_code = f"{tile.color[0]}{next_num}"

                    group = [tile]
                    joker_info = []
                    temp_tiles = tiles.copy()
                    temp_tiles.remove(tile)
                    counts_temp = counts.copy()
                    counts_temp[tile.code] -= 1

                    for color in ["red", "yellow", "cyan", "black"]:
                        steps += 1
                        next_code = f"{color[0]}{tile.number}"
                        if next_code != tile.code and (
                            counts_temp[next_code] or counts_temp["j"]
                        ):
                            tile_index = -1
                            if counts_temp[next_code]:
                                if (
                                    counts_temp[next_code] == 1
                                    and len(self.tile_dict[next_code]) == 2
                                ):
                                    if self.tile_dict[next_code][0] in temp_tiles:
                                        tile_index = 0
                                group.append(self.tile_dict[next_code][tile_index])
                                temp_tiles.remove(self.tile_dict[next_code][tile_index])
                                counts_temp[next_code] -= 1
                            else:
                                if (
                                    counts_temp["j"] == 1
                                    and len(self.tile_dict["j"]) == 2
                                ):
                                    if self.tile_dict["j"][0] in temp_tiles:
                                        tile_index = 0
                                group.append(self.tile_dict["j"][tile_index])
                                temp_tiles.remove(self.tile_dict["j"][tile_index])
                                joker_info.append([color, tile.number])
                                counts_temp["j"] -= 1

                            if len(group) >= 3:
                                backtrack(
                                    temp_tiles,
                                    tile_sets
                                    + [
                                        TileSet(
                                            group,
                                            "group",
                                            joker_info if joker_info else None,
                                        )
                                    ],
                                    counts_temp,
                                )
                steps += 1

        backtrack(self.all_tiles, [], self.tile_counts)
        print(f"Took {time.time() - start_time:.4f} seconds")

        for tile_set in best_play:
            for tile in tile_set:
                if tile.is_joker:
                    color, number = tile_set.joker_info.pop()
                    tile.color = color
                    tile.number = number
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
            print(f"Player {index + 1}:", end=" ")
            for tile in sorted(player.hand, key=lambda tile: (tile.color, tile.number)):
                print(tile, end="")
            print()

        print("\nBoard:", end=" ")
        for tile_set in self.board.sets:
            print(f"{tile_set}|", end="")

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
        best_play = play_helper.turn()

        if best_play:
            print("best_play:", best_play)
            cprint(f"\nPLAYS", attrs=["bold"], color="green", end=" ")
            self.board.sets = best_play
            for tile_set in best_play:
                for tile in tile_set:
                    if tile in player.hand:
                        print(f"{tile}", end="")
                        player.remove_from_hand(tile)
            print("\n")
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
        # for i in range(8, 12):
        #     self.players[0].hand.add(Tile("red", i))
        #     if i == 9:
        #         self.players[0].hand.add(Tile("cyan", i))
        #         self.players[0].hand.add(Tile("yellow", i))
        cprint(f"> BEGIN GAME", attrs=["bold", "underline"])
        self.display_game()


game = Game(4)
s = input("Take turn?")
while s == "":
    game.take_turn()
    s = input("Take turn?")
