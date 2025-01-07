from collections import defaultdict
from itertools import combinations
from random import shuffle
from termcolor import colored, cprint

colors = set(["red", "yellow", "cyan", "black"])


class Tile:
    def __init__(self, color, number, is_joker=False):
        self.color = color
        self.number = number
        self.is_joker = is_joker

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if not self.is_joker:
            return colored(f"[{self.number}]", self.color)
        else:
            return colored("[J]", "white")


class Set:
    def __init__(self, tiles):
        self.tiles = sorted(tiles, key=lambda tile: tile.number)
        self.size = len(tiles)

    def add_tiles(self, tiles):
        self.tiles.extend(tiles)
        self.tiles.sort(key=lambda tile: tile.number)
        self.size = len(self.tiles)

    def __str__(self):
        return " ".join(str(tile) for tile in self.tiles)


class Player:
    def __init__(self, id):
        self.id = id
        self.hand = set()
        self.has_played = False

    def add_to_hand(self, tile):
        self.hand.add(tile)

    def remove_from_hand(self, tile):
        self.hand.remove(tile)


class PlayHelper:
    def __init__(self, player):
        self.player = player

    def get_score(self, tiles):
        total = 0
        for tile in tiles:
            if not tile.is_joker:
                total += tile.number
            else:
                if len(tiles) > 0 and not any(t.is_joker for t in tiles):
                    total += tiles[0].number
                else:
                    total += 10
        return total

    def first_turn(self):
        tiles_list = list(self.player.hand)
        valid_sets = []

        for size in range(3, min(5, len(tiles_list) + 1)):
            for combo in combinations(tiles_list, size):
                if self.is_valid_play(list(combo)):
                    score = self.get_score(combo)
                    valid_sets.append((combo, score))

        best_play = None
        best_score = 0

        for i in range(1, len(valid_sets) + 1):
            for combo in combinations(valid_sets, i):
                total_score = sum(score for _, score in combo)
                if total_score >= 30:
                    used_tiles = set()
                    valid = True
                    sets = []
                    for set_tiles, _ in combo:
                        for tile in set_tiles:
                            if tile in used_tiles:
                                valid = False
                                break
                            used_tiles.add(tile)
                        if not valid:
                            break
                        sets.append(Set(set_tiles))

                    if valid and total_score > best_score:
                        best_score = total_score
                        best_play = sets

        return best_play if best_score >= 30 else None

    def is_valid_play(self, tiles):
        return self.is_run(tiles) or self.is_group(tiles)

    def is_run(self, tiles):
        if len(tiles) < 3:
            return False

        regular_tiles = [t for t in tiles if not t.is_joker]
        jokers = [t for t in tiles if t.is_joker]

        if len(regular_tiles) < 2:
            return False

        first_color = next(t.color for t in regular_tiles)
        if not all(t.color == first_color for t in regular_tiles):
            return False

        numbers = sorted(t.number for t in regular_tiles)
        if len(numbers) == len(tiles):
            return all(
                numbers[i] + 1 == numbers[i + 1] for i in range(len(numbers) - 1)
            )

        gaps = []
        for i in range(len(numbers) - 1):
            gap = numbers[i + 1] - numbers[i] - 1
            if gap > 0:
                gaps.append(gap)

        return sum(gaps) <= len(jokers)

    def is_group(self, tiles):
        if len(tiles) < 3 or len(tiles) > 4:
            return False

        regular_tiles = [t for t in tiles if not t.is_joker]

        first_number = next(t.number for t in regular_tiles)
        if not all(t.number == first_number for t in regular_tiles):
            return False

        colors = set(t.color for t in regular_tiles)
        return len(colors) == len(regular_tiles)


class Game:
    def __init__(self, num_players, starting_player=1):
        self.unused_tiles = set()
        self.played_tiles = set()
        self.sets = []
        self.num_players = num_players
        self.players = {i: Player(i) for i in range(1, num_players + 1)}
        self.player_turn = starting_player
        self.setup_game()

    def _generate_tiles(self):
        for _ in range(2):
            for number in range(1, 14):
                for color in colors:
                    self.unused_tiles.add(Tile(color, number))
        for _ in range(2):
            self.unused_tiles.add(Tile("white", -1, True))

    def take_turn(self):
        cprint(f"> PLAYER {self.player_turn} TURN", attrs=["bold", "underline"])
        player = self.players[self.player_turn]
        play_helper = PlayHelper(player)

        if not player.has_played:
            play = play_helper.first_turn()
            if play:
                for set_tiles in play:
                    self.sets.append(set_tiles)
                    for tile in set_tiles.tiles:
                        player.remove_from_hand(tile)
                player.has_played = True
            else:
                tiles_list = list(self.unused_tiles)
                shuffle(tiles_list)
                drawn_tile = tiles_list.pop()
                player.add_to_hand(drawn_tile)
                self.unused_tiles.remove(drawn_tile)

        self.player_turn += 1
        self.display_game()

    def display_game(self):
        for id, player in self.players.items():
            print(f"Player {id}:", end=" ")
            for tile in sorted(player.hand, key=lambda tile: (tile.color, tile.number)):
                print(tile, end=" ")
            print()

        print("\nBoard:", end=" ")
        for set_tiles in self.sets:
            print(set_tiles, end=" | ")

        print("\n\nPool:", end=" ")
        for tile in sorted(
            self.unused_tiles, key=lambda tile: (tile.color, tile.number)
        ):
            print(tile, end=" ")
        print("\n")

    def setup_game(self):
        self._generate_tiles()
        tiles_list = list(self.unused_tiles)
        shuffle(tiles_list)

        for _ in range(14):
            for i in range(1, self.num_players + 1):
                tile = tiles_list.pop()
                self.players[i].add_to_hand(tile)
                self.unused_tiles.remove(tile)

        cprint(f"> BEGIN GAME", attrs=["bold", "underline"])
        self.display_game()


game = Game(4)
game.take_turn()
