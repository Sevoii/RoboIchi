import os
import sqlite3
import json

rii_loc = os.path.abspath(__file__ + "/../../db/rii.db")

def encode_winning(tiles):
    a = 0
    for t in tiles:
        a += 2 ** t
    return a

with sqlite3.connect(rii_loc) as conn:
    cur_read = conn.cursor()
    cur_write = conn.cursor()

    cur_read.execute("CREATE TABLE IF NOT EXISTS riichi1(log_id INT, num_discards INT, tile INT, winning_tiles INT)")

    for i in cur_read.execute("SELECT log_id, num_discards, tile, winning_tiles FROM riichi"):
        cur_write.execute("INSERT INTO riichi1 VALUES (?, ?, ?, ?)",
                          (i[0], i[1], i[2], encode_winning(json.loads(i[3]))))

