from .shanten_calc import calc_all
from .agari import get_tile14_and_key, get_hand_waits, get_agari_data


def convert_t14_to_full(tiles: list[int]):
    return [tiles.count(i) for i in range(34)]


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

        if get_agari_data(key) is None:
            return False

        tehai[i] -= 1

    return True
