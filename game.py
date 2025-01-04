import random
import termcolor


class Tile:
    def __init__(self, color, number, is_joker=False):
        self.color = color
        self.number = number
        self.is_joker = is_joker

    def __str__(self):
        if self.color:
            return termcolor.colored(f"[{self.number}]", self.color)
        else:
            return termcolor.colored("[J]", "white")


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
        self.hand = set()

    def add_to_hand(self, tile):
        self.hand.add(tile)

    def remove_from_hand(self, tile):
        self.hand.remove(tile)


class Game:
    def __init__(self, num_players):
        self.tiles = set()
        self.unused_tiles = None
        self.played_tiles = set()
        self.sets = []
        self.num_players = num_players
        self.players = {i: Player(i) for i in range(1, num_players + 1)}

        self._setup_game()

    def _generate_tiles(self):
        for _ in range(2):
            for number in range(1, 14):
                for color in ["light_red", "light_yellow", "light_cyan", "black"]:
                    self.tiles.add(Tile(color, number))

        self.tiles.update([Tile(None, None, True) for _ in range(2)])

    def _setup_game(self):
        self._generate_tiles()
        tiles_list = list(self.tiles)
        random.shuffle(tiles_list)

        for _ in range(14):
            for i in range(1, self.num_players + 1):
                tile = tiles_list.pop()
                self.players[i].add_to_hand(tile)

        self.unused_tiles = set(tiles_list)

    def display_game(self):
        for id, player in self.players.items():
            print(f"Player {id}:", end="")
            for tile in player.hand:
                print(f" {tile}", end="")
            print()

        print("Board:")
        for set in self.sets:
            print(set)

        print("Pool:", end="")
        for tile in self.unused_tiles:
            print(f" {tile}", end="")


game = Game(4)
game.display_game()
