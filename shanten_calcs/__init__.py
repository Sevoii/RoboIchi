from .shanten_calc import calc_all


def convert_t14_to_full(tiles: list[int]):
    return [tiles.count(i) for i in range(34)]
