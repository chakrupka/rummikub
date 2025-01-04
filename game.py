from collections import defaultdict
from random import shuffle
from termcolor import colored
from itertools import chain


class Tile:
    def __init__(self, color, number, is_joker=False):
        self.color = color
        self.number = number
        self.is_joker = is_joker

    def __str__(self):
        if self.color:
            return colored(f"[{self.number}]", self.color)
        else:
            return colored("[J]", "white")


class Set:
    def __init__(self, tiles):
        self.tiles = sorted(tiles, key=lambda tile: tile.number)
        self.size = len(tiles)

    def add_tiles(self, tiles):
        self.tiles.extend(tiles).sort(key=lambda tile: tile.number)
        self.size = len(self.tiles)


class Player:
    def __init__(self, id):
        self.id = id
        self.hand_numbers = defaultdict(set)
        self.hand_colors = defaultdict(set)

    def add_to_hand(self, tile):
        self.hand_numbers[tile.number].add(tile)
        self.hand_colors[tile.color].add(tile)

    def remove_from_hand(self, tile):
        self.hand_numbers[tile.number].remove(tile)
        self.hand_colors[tile.color].remove(tile)


class Game:
    def __init__(self, num_players, starting_player=1):
        self.unused_tiles_numbers = defaultdict(set)
        self.unused_tiles_colors = defaultdict(set)
        self.played_tiles_numbers = defaultdict(set)
        self.played_tiles_colors = defaultdict(set)
        self.sets = []
        self.num_players = num_players
        self.players = {i: Player(i) for i in range(1, num_players + 1)}
        self.turn = starting_player

        self._setup_game()

    def _generate_tiles(self):
        for _ in range(2):
            for number in range(1, 14):
                for color in ["light_red", "light_yellow", "light_cyan", "black"]:
                    tile = Tile(color, number)
                    self.unused_tiles_numbers[number].add(tile)
                    self.unused_tiles_colors[color].add(tile)

        for _ in range(2):
            joker = Tile(None, None, True)
            self.unused_tiles_numbers[-1].add(joker)
            self.unused_tiles_colors["white"].add(joker)

    def _setup_game(self):
        self._generate_tiles()
        tiles_list = list(chain.from_iterable(self.unused_tiles_numbers.values()))
        shuffle(tiles_list)

        for _ in range(14):
            for i in range(1, self.num_players + 1):
                tile = tiles_list.pop()
                self.players[i].add_to_hand(tile)
                if tile.is_joker:
                    self.unused_tiles_numbers[-1].remove(tile)
                    self.unused_tiles_colors["white"].remove(tile)
                else:
                    self.unused_tiles_numbers[tile.number].remove(tile)
                    self.unused_tiles_colors[tile.color].remove(tile)

    def take_turn(self):
        pass

    def display_game(self):
        for id, player in self.players.items():
            print(f"Player {id}:", end="")
            hand = list(chain.from_iterable(player.hand_numbers.values()))
            for tile in hand:
                print(f" {tile}", end="")
            print()

        print("Board:")
        for set in self.sets:
            print(set)

        print("Pool:", end="")
        pool_tiles = list(chain.from_iterable(self.unused_tiles_numbers.values()))
        for tile in pool_tiles:
            print(f" {tile}", end="")


game = Game(4)
game.display_game()
