import gzip
import sqlite3
import torch
import numpy as np
from torch.utils.data import IterableDataset


class LazyLoadDatabase:
    def __init__(self, db_loc, table, page_size=500):
        self.db_loc = db_loc
        self.table = table

        self.page_size = page_size
        with sqlite3.connect(db_loc) as con:
            cur = con.cursor()
            cur.execute("SELECT MAX(ROWID) FROM haipai")
            self.db_size = next(cur)[0]

        self.conn = None

    def __iter__(self, initial_offset=0, skip=1):
        cur = self.conn.cursor()
        for offset in range(0, self.db_size // skip, self.page_size):
            cur.execute(
                f"SELECT * FROM {self.table} WHERE (ROWID + {initial_offset}) % {skip} = 0 LIMIT {self.page_size} OFFSET {offset * skip}")
            for item in cur:
                yield item

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_loc)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            self.conn = None


def decompress_arr(data):
    return np.frombuffer(gzip.decompress(data), dtype=np.float32)


class DatabaseDataset(IterableDataset):
    def __init__(self, db_loc: str, ver=0):
        self.db = LazyLoadDatabase(db_loc, "haipai", page_size=10000)
        self.ver = ver

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
                yield self.handle_item(item)

    def handle_item(self, item):
        match self.ver:
            case 0:
                return DatabaseDataset.handle_item_ver0(item)
            case _:
                raise NotImplementedError(f"Version {self.ver} is not implemented yet")

    @staticmethod
    def handle_item_ver0(item):
        data = decompress_arr(item[1])
        arr = np.zeros((3, 37), dtype=np.float32)

        # Manual Rescaling
        arr[0, 0] = data[0] / 3
        arr[0, 1:3] = data[1:3] * 0.1
        arr[0, 3] = data[3] / 3
        arr[0, 4:8] = data[4:8] * 0.1

        arr[1, int(data[8])] = 0.1

        np.add.at(arr[2], data[9:22].astype(dtype=np.int64), 0.1)

        return arr, data[22]
