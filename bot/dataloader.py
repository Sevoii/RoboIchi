import sqlite3
import torch
from torch.utils.data import IterableDataset
import riichi
import mjlog2json
import bz2


class LazyLoadDatabase:
    def __init__(self, db_loc, table):
        self.db_loc = db_loc
        self.table = table

        self.conn = None

    def __iter__(self, initial_offset=0, skip=1):
        cur = self.conn.cursor()
        cur.execute(
            f"""
            SELECT log_content
            FROM {self.table}
            WHERE (id + ?) % ? = 0
            """,
            (initial_offset, skip),
        )

        for i in cur:
            yield i[0]

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_loc)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            self.conn = None


class DatabaseDataset(IterableDataset):
    def __init__(self, db_loc: str, table_name="logs", page_size=1000):
        self.db = LazyLoadDatabase(db_loc, table_name)
        self.loader = riichi.dataset.GameplayLoader(3, oracle=False)

    def __iter__(self):
        with self.db as db:
            worker_info = torch.utils.data.get_worker_info()
            if worker_info is None:
                num_workers = 1
                initial_offset = 0
            else:
                num_workers = worker_info.num_workers
                initial_offset = worker_info.id

            for item in db.__iter__(initial_offset=initial_offset, skip=num_workers):
                # TODO - figure out if we just want to put bz2 decompression into convert xml code
                #      - or just figure out if we just compress in tbh idk
                gameplay = self.loader.load_json_log(mjlog2json.convert_xml_to_mjai(bz2.decompress(item).decode()))
                for i in gameplay:
                    for j in zip(i.take_obs(), i.take_actions(), i.take_masks()):
                        yield j


def test():
    dataset = DatabaseDataset("../db/games_clean.db")

    k = 0
    for i in dataset:
        print(i)
        k += 1
        if k >= 100:
            break


if __name__ == "__main__":
    test()
