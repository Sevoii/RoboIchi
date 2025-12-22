from event_extractor import tenhou_decoder, tenhou_game_state
import shanten_calcs
import os
import sqlite3
import json
import time
import bz2


def extract_riis(game_data: tenhou_decoder.GameData):
    riis = []

    game_state = tenhou_game_state.GameState(game_data)
    game_state.next_round()

    while game_state.current_round is not None:
        while ev := game_state.get_next_event():
            game_state.process_event()

            if isinstance(ev, tenhou_decoder.RiichiEvent):
                discard_ev = game_state.get_next_event()

                if not isinstance(discard_ev, tenhou_decoder.DiscardTileEvent):
                    raise RuntimeError("Event after Riichi event is not discard event")

                game_state.process_event()
                player = game_state.current_round.players[discard_ev.player]

                winning_tiles = shanten_calcs.get_hand_waits(
                    shanten_calcs.convert_t14_to_full([i.tile for i in player.closed_hand]))

                if discard_ev.tile.is_aka():
                    # print("here")
                    riis.append([player._num_discards, discard_ev.tile.tile, winning_tiles])
                # riis.append([player._num_discards, discard_ev.tile.tile, winning_tiles])

        game_state.next_round()

    return riis


def main(games_loc: str, rii_loc: str = None):
    rii_loc = rii_loc or os.path.abspath(__file__ + "/../../db/rii.db")
    games_loc = os.path.abspath(games_loc).replace("'", "''")

    if not os.path.exists(rii_loc):
        with sqlite3.connect(rii_loc) as conn:
            cur_read = conn.cursor()

            cur_read.execute("CREATE TABLE indexed(log_id TEXT primary key)")
            cur_read.execute("CREATE TABLE riichi(log_id INT, num_discards INT, tile INT, winning_tiles STR)")

    # Sanitize String
    if not os.path.exists(games_loc):
        raise Exception("Game DB does not exist")

    if ";" in games_loc or "--" in games_loc:
        raise Exception("Invalid chars in db path")

    last_seen = time.time()

    with sqlite3.connect(rii_loc) as conn:
        cur_read = conn.cursor()
        cur_write = conn.cursor()

        # Good Luck All
        cur_read.execute(f"ATTACH DATABASE '{games_loc}' AS gamedb")
        cur_read.execute(
            "SELECT gamedb.logs.log_id, gamedb.logs.log_content FROM gamedb.logs LEFT JOIN indexed ON gamedb.logs.log_id = indexed.log_id WHERE indexed.log_id IS NULL AND NOT gamedb.logs.is_sanma AND NOT gamedb.logs.is_tonpuu")

        for i, (game_id, content) in enumerate(cur_read):
            if i % 500 == 0:
                print(f"Row: {i}, Time Taken: {time.time() - last_seen}")
                last_seen = time.time()
                conn.commit()

            cur_write.execute("INSERT INTO indexed VALUES(?)", (game_id,))
            row_id = cur_write.lastrowid

            decompressed = bz2.decompress(content).decode()
            for rii in extract_riis(tenhou_decoder.GameData(decompressed)):
                cur_write.execute("INSERT INTO riichi VALUES (?, ?, ?, ?)",
                                  (row_id, rii[0], rii[1], json.dumps(rii[2])))


if __name__ == "__main__":
    main(__file__ + "/../../db/2021.db", __file__ + "/../../db/akarii.db")
