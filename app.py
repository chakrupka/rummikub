from flask import Flask, request
from solver import optimal_play
from flask_cors import CORS
import collections

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET", "POST"])
def api():
    if request.method == "GET":
        return "<p>Rummikub Optimal Play Solver</p>"
    data = request.get_json()
    board_tiles = collections.Counter(tiles_to_tuples(data["board"]))
    rack_tiles = collections.Counter(tiles_to_tuples(data["rack"]))

    best_play, played_tiles = optimal_play(board_tiles, rack_tiles)
    if not played_tiles:
        return {"best_play": [], "from_rack": []}
    formatted_sets, formatted_tiles = format_response(best_play, played_tiles)
    return {"best_play": formatted_sets, "from_rack": formatted_tiles}


def tiles_to_tuples(tiles):
    out = []
    for color, num in tiles:
        if num == 0:
            out.append("J")
        else:
            out.append((color, num))
    return out


def format_response(play, tiles):
    formatted_play = []
    for set_tup in play:
        set_array = []
        for tile in set_tup:
            if tile != "J":
                set_array.append([tile[0], tile[1]])
            else:
                set_array.append(["J", 0])
        formatted_play.append(set_array)

    formatted_tiles = []
    for tile in tiles:
        if tile != "J":
            formatted_tiles.append([tile[0], tile[1]])
        else:
            formatted_tiles.append(["J", 0])

    return formatted_play, formatted_tiles
