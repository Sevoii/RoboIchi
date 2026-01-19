import sqlite3

# IN_DB = "../db/2021.db"
IN_DB = "../db/all_games.db"
# OUT_DB = "../db/games_clean.db"
OUT_DB = "../db/all_games_clean.db"


with sqlite3.connect(IN_DB) as conn:
    cur = conn.cursor()
    # rows = cur.execute("SELECT log_content FROM logs WHERE NOT is_tonpusen AND NOT is_hirosima AND NOT was_error ORDER BY RANDOM()").fetchall()
    rows = cur.execute("SELECT id,log FROM logs WHERE num_players=4 AND NOT is_tonpu AND NOT was_error AND is_processed").fetchall()

with sqlite3.connect(OUT_DB) as conn:
    cur = conn.cursor()

    # cur.execute("""
    # CREATE TABLE IF NOT EXISTS logs (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     log_content TEXT NOT NULL
    # )
    # """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id TEXT,
        log_content BLOB NOT NULL
    )
    """)

    # cur.executemany("INSERT INTO logs (log_content) VALUES (?)", rows)
    cur.executemany("INSERT INTO logs (log_id, log_content) VALUES (?, ?)", rows)
