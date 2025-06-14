# Python port of Equim's Rust port of tomohxx's C++ implementation of Shanten Number Calculator
#
# Source:
# * <https://github.com/Equim-chan/Mortal/blob/main/libriichi/src/algo/shanten.rs>
# * <https://github.com/tomohxx/shanten-number-calculator/>

import gzip
import pickle


def _read_table(file_loc: str) -> list[list[int]]:
    """
    Reads a GZipped Table and parses it
    :param file_loc: Location of the GZipped table
    :return: Table
    """
    ret = []
    entry = [0 for _ in range(10)]

    with gzip.open(file_loc, "rb") as f:
        for i, b in enumerate(f.read()):
            entry[(i * 2) % 10] = b & 0b1111
            entry[(i * 2) % 10 + 1] = (b >> 4) & 0b1111

            if (i + 1) % 5 == 0:
                ret.append(entry.copy())

    return ret


# _JIHAI_TABLE = _read_table("data/shanten_jihai.bin.gz")  # Length: 78032
# _SUHAI_TABLE = _read_table("data/shanten_suhai.bin.gz")  # Length: 1940777

# with open(__file__ + "/../data/jihai_table.pkl", "rb") as f:
#     _JIHAI_TABLE = pickle.load(f)
with open(__file__ + "/../data/suhai_table.pkl", "rb") as f:
    _SUHAI_TABLE = pickle.load(f)


def _add_suhai(lhs: list[int], index: int, m: int):
    """
    Adds Suhai (Non Honor Tiles) to be calc'd for shanten
    Modifies lhs in place
    :param lhs: ???
    :param index: Tile Hash (?)
    :param m: ???
    :return: N/A
    """
    tab = _SUHAI_TABLE[index]

    for j in range(5 + m, 4, -1):
        sht = min(lhs[j] + tab[0], lhs[0] + tab[j])
        for k in range(5, j):
            sht = min(sht, lhs[k] + tab[j - k], lhs[j - k] + tab[k])
        lhs[j] = sht

    for j in range(m, -1, -1):
        sht = lhs[j] + tab[0]
        for k in range(0, j):
            sht = min(sht, lhs[k] + tab[j - k])
        lhs[j] = sht


def _add_jihai(lhs: list[int], index: int, m: int):
    """
    Adds Jihai (Honor Tiles) to be calc'd for shanten
    Modifies lhs in place
    :param lhs: ???
    :param index: Tile Hash (?)
    :param m: ???
    :return: N/A
    """
    tab = _SUHAI_TABLE[index]

    j = m + 5
    sht = min(lhs[j] + tab[0], lhs[0] + tab[j])
    for k in range(5, j):
        sht = min(sht, lhs[k] + tab[j - k], lhs[j - k] + tab[k])
    lhs[j] = sht


def _sum_tiles(tiles: list[int]) -> int:
    """
    Converts tiles to base 5 as a hash (of sorts)
    :param tiles: Tiles given
    :return: Hash
    """
    acc = 0
    for x in tiles:
        acc = acc * 5 + x
    return acc


def calc_normal(tiles: list[int], len_div3: int):
    """
    Calculates the shanten assuming we're going for a normal hand
    :param tiles: Full Array of tiles
    :param len_div3: ???
    :return: Shanten to make a normal hand
    """
    ret = _SUHAI_TABLE[_sum_tiles(tiles[0:9])].copy()
    _add_suhai(ret, _sum_tiles(tiles[9:18]), len_div3)
    _add_suhai(ret, _sum_tiles(tiles[18:27]), len_div3)
    _add_jihai(ret, _sum_tiles(tiles[27:]), len_div3)

    return ret[5 + len_div3] - 1


def calc_chiitoi(tiles: list[int]):
    """
    Calculates the shanten assuming we're going for chiitoi
    :param tiles: Full Array of tiles
    :return: Shanten to make a chiitoi hand
    """
    pairs = 0
    kinds = 0
    for i in tiles:
        if i == 0:
            continue

        pairs += (i >= 2)
        kinds += 1

    return 7 - pairs + max(7 - kinds, 0) - 1


def calc_kokushi(tiles: list[int]):
    """
    Calculates the shanten assuming we're going for kokushi
    :param tiles: Full Array of tiles
    :return: Shanten to make a kokushi hand
    """
    pairs = 0
    kinds = 0
    for i in [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]:
        if tiles[i] == 0:
            continue

        pairs += tiles[i] >= 2
        kinds += 1

    return 14 - kinds - (pairs > 0) - 1


def calc_all(tiles: list[int], len_div3: int = None):
    """
    Calculates the shanten of the hand no matter what we're going for
    :param tiles: Full Array of tiles
    :param len_div3: ???
    :return: Hand Shanten
    """
    if len_div3 is None:
        len_div3 = len(tiles) // 3

    shanten = calc_normal(tiles, len_div3)

    if len_div3 >= 4:
        if shanten > 0:
            shanten = min(shanten, calc_chiitoi(tiles))
        if shanten > 0:
            shanten = min(shanten, calc_kokushi(tiles))

    return shanten
