import bz2
import mjlog2json
import riichi
import json
import os
import sqlite3

db_loc = "../db/2021.db"

with sqlite3.connect(db_loc) as conn:
    cur = conn.cursor()
    data = [mjlog2json.convert_xml_to_mjai(bz2.decompress(i[0]).decode()) for i in cur.execute("SELECT log_content FROM logs WHERE NOT is_tonpusen AND NOT is_hirosima LIMIT 5")]

loader = riichi.dataset.GameplayLoader(3, oracle=False)
data = loader.load_json_log_batch(data)