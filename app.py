from flask import Flask, request
from flask_cors import CORS
import collections
from game_v3 import optimal_play


app = Flask(__name__)
CORS(app)


@app.route("/", methods=("GET", "POST"))
def api():
    if request.method == "GET":
        return "<p>Rummikub Optimal Play Solver</p>"

    data = request.get_json()
    board_sets = collections.Counter(format_request(board=data["board"]))
    rack_tiles = collections.Counter(format_request(rack=data["rack"]))

    best_play, played_tiles = optimal_play(board_sets, rack_tiles)

    if not played_tiles:
        return {"best_play": [], "from_rack": []}

    formatted_sets, formatted_tiles = format_response(best_play, played_tiles)
    return {"best_play": formatted_sets, "from_rack": formatted_tiles}


def format_request(board=None, rack=None):
    if board:
        tile_sets = []
        for tile_set in board:
            formatted_set = [
                ("J") if num == "J" else (color, int(num)) for color, num in tile_set
            ]
            tile_sets.append(tuple(formatted_set))
        return tile_sets

    if rack:
        return [("J") if num == "J" else (color, int(num)) for color, num in rack]


def format_response(play, tiles):
    formatted_play = []
    for set_tup in play:
        set_array = []
        for tile in set_tup:
            if tile == "J":
                set_array.append(["K", "J"])
            else:
                set_array.append([tile[0], f"{tile[1]}"])
        formatted_play.append(set_array)

    formatted_tiles = []
    for tile in tiles:
        if tile == "J":
            formatted_tiles.append(["K", "J"])
        else:
            formatted_tiles.append([tile[0], f"{tile[1]}"])

    return formatted_play, formatted_tiles
