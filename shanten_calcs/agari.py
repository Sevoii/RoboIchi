# Python port of Equim's Rust port of EndlessCheng's Go port of 山岡忠夫's Java
# implementation of his agari algorithm.
#
# Source:
# * Rust: <https://github.com/Equim-chan/Mortal/blob/main/libriichi/src/algo/agari.rs>
# * Go: <https://github.com/EndlessCheng/mahjong-helper/blob/master/util/agari.go>
# * Java: <http://hp.vector.co.jp/authors/VA046927/mjscore/AgariIndex.java>
# * Algorithm: <http://hp.vector.co.jp/authors/VA046927/mjscore/mjalgorism.html>

import gzip
import struct


# TL Note: Agari means Win
class AgariData:
    """
    A class used to deserialize data from the agari table
    """

    def __init__(self, flags):
        self.pair_idx = (flags >> 6) & 0b1111

        # Triplet
        self.kotsu_count = flags & 0b111
        self.kotsu_idxs = [((flags >> (10 + i * 4)) & 0b1111) for i in range(self.kotsu_count)]

        # Sequence
        self.shuntsu_count = (flags >> 3) & 0b111
        self.shuntsu_idxs = [((flags >> (10 + i * 4)) & 0b1111) for i in
                             range(self.kotsu_count, self.kotsu_count + self.shuntsu_count)]

        self.has_chitoi = ((flags >> 26) & 1) == 1
        self.has_chuuren = ((flags >> 27) & 1) == 1
        self.has_ittsuu = ((flags >> 28) & 1) == 1
        self.has_ryanpeikou = ((flags >> 29) & 1) == 1
        self.has_ipeikou = ((flags >> 30) & 1) == 1

    def __repr__(self):
        return (f"AgariData(pair_idx={self.pair_idx}, kotsu_idxs={self.kotsu_idxs}, "
                f"shuntsu_idxs={self.shuntsu_idxs}, has_chitoi={self.has_chitoi}, "
                f"has_chuuren={self.has_chuuren}, has_ittsuu={self.has_ittsuu}, "
                f"has_ryanpeikou={self.has_ryanpeikou}, has_ipeikou={self.has_ipeikou})")


def load_table_from_gzip(file_loc: str = "data/agari.bin.gz", table_size: int = 9362) -> dict[int, list[AgariData]]:
    """
    Load the Agari Table from a GZIP file
    The file used in the repository was taken from:
    https://github.com/Equim-chan/Mortal/blob/main/libriichi/src/algo/data/agari.bin.gz

    :param file_loc: Location of the GZipped Table
    :param table_size: Size of the actual table
    :return: Table populated with values
    """
    table = {}
    with gzip.open(file_loc, "rb") as f:
        for _ in range(table_size):
            key = struct.unpack('<I', f.read(4))[0]  # Little-endian u32
            v_size = struct.unpack('<B', f.read(1))[0]  # u8
            value = [AgariData(struct.unpack('<I', f.read(4))[0]) for _ in range(v_size)]
            table[key] = value
    return table


def get_tile14_and_key(tiles: list[int]) -> tuple[list[int], int]:
    """
    Converts an array of tiles to a format supported by the Agari Table, returns the key for the agari table as well
    :param tiles: An array of length 34 representing the number of each tile in one's hand
        0-8: Man Tiles
        9-17: Pin Tiles
        18-26: Sou Tiles
        27-30: Wind Tiles
        31-33: Dragon Tiles
    This should (?)
    :return: Array that points to each tile in the hand, key to be used in the agari table
    """
    tile14 = [0 for _ in range(14)]
    tile14_idx = 0
    key = 0

    bit_idx = -1
    prev_in_hand = False

    # First 27 tiles (3 suits of 9 tiles)
    for kind in range(3):  # 0 to 2
        for num in range(9):  # 0 to 8
            i = kind * 9 + num
            c = tiles[i]

            if c > 0:
                prev_in_hand = True
                tile14[tile14_idx] = i
                tile14_idx += 1
                bit_idx += 1

                if c == 2:
                    key |= 0b11 << bit_idx
                    bit_idx += 2
                elif c == 3:
                    key |= 0b1111 << bit_idx
                    bit_idx += 4
                elif c == 4:
                    key |= 0b11_1111 << bit_idx
                    bit_idx += 6
                # if c == 1: do nothing
            elif prev_in_hand:
                prev_in_hand = False
                key |= 0b1 << bit_idx
                bit_idx += 1

        if prev_in_hand:
            prev_in_hand = False
            key |= 0b1 << bit_idx
            bit_idx += 1

    for tile_id in range(27, 34):
        c = tiles[tile_id]
        if c > 0:
            tile14[tile14_idx] = tile_id
            tile14_idx += 1
            bit_idx += 1

            if c == 2:
                key |= 0b11 << bit_idx
                bit_idx += 2
            elif c == 3:
                key |= 0b1111 << bit_idx
                bit_idx += 4
            elif c == 4:
                key |= 0b11_1111 << bit_idx
                bit_idx += 6

            key |= 0b1 << bit_idx
            bit_idx += 1

    return tile14, key


def get_hand_waits(tehai: list[int]):
    tehai = tehai[:]

    waits = []

    for i in range(34):
        if tehai[i] >= 4:
            continue

        tehai[i] += 1

        t14, key = get_tile14_and_key(tehai)
        if key in AGARI_TABLE:
            waits.append(i)

        tehai[i] -= 1

    return waits


def check_ankan_after_riichi(tehai: list[int], tile_id: int, strict: bool) -> bool:
    if tehai[tile_id] != 4:
        return False
    elif tile_id >= 27:  # Honor Tile can always ankan
        return True

    tehai = tehai[:]  # Copying the list

    tehai[tile_id] -= 1
    waits = get_hand_waits(tehai)

    tehai[tile_id] = 0

    for i in waits:
        tehai[i] += 1
        t14, key = get_tile14_and_key(tehai)

        if key not in AGARI_TABLE:
            return False

        tehai[i] -= 1

    return True


AGARI_TABLE: dict[int, list['AgariData']] = load_table_from_gzip()
