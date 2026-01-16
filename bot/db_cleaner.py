import sqlite3

IN_DB = "../db/2021.db"
OUT_DB = "../db/games_clean.db"


with sqlite3.connect(IN_DB) as conn:
    cur = conn.cursor()
    rows = cur.execute("SELECT log_content FROM logs WHERE NOT is_tonpusen AND NOT is_hirosima AND NOT was_error ORDER BY RANDOM()").fetchall()

with sqlite3.connect(OUT_DB) as conn:
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_content TEXT NOT NULL
    )
    """)

    cur.executemany("INSERT INTO logs (log_content) VALUES (?)", rows)
