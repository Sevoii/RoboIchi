# Rewrite of TenhouDecoder from ApplySci
#
# Source:
#  * https://github.com/ApplySci/tenhou-log/blob/master/TenhouDecoder.py
import urllib.parse as urllib_parse
from typing import TextIO
import xml.etree.ElementTree as XMLElementTree
import bz2


class JsonSerializable:
    PRIMITIVES = (bool, str, int, float, type(None))

    def serialize(self, *args, **kwargs):
        serialization = {}
        for (k, v) in self.__dict__.items():
            if k.startswith("_"):
                continue
            elif isinstance(v, JsonSerializable):
                serialization[k] = v.serialize(*args, **kwargs)
            else:
                serialization[k] = JsonSerializable._serialize(v, *args, **kwargs)

        return serialization

    @staticmethod
    def _serialize(obj, *args, **kwargs):
        if isinstance(obj, JsonSerializable.PRIMITIVES):
            return obj
        elif isinstance(obj, (list, tuple)):
            return JsonSerializable._serialize_iter(obj, *args, **kwargs)
        else:
            raise Exception(f"Serialization not supported for: {type(obj)}")

    @staticmethod
    def _serialize_primitive(obj: PRIMITIVES, *_, **__):
        return obj

    @staticmethod
    def _serialize_iter(obj: list, *args, **kwargs):
        return [i.serialize(*args, **kwargs) if isinstance(i, JsonSerializable)
                else JsonSerializable._serialize(i, *args, **kwargs) for i in obj]


class Tile(JsonSerializable):
    _TILES = """
        1m 2m 3m 4m 5m 6m 7m 8m 9m
        1p 2p 3p 4p 5p 6p 7p 8p 9p
        1s 2s 3s 4s 5s 6s 7s 8s 9s
        ew sw ww nw
        wd gd rd
    """.split()

    def __init__(self, i):
        if isinstance(i, str):
            i = int(i)

        self.i = i
        self.tile = i >> 2
        self.tile_num = i & 0x3

    def __repr__(self):
        return self.serialize(readable=True)

    def serialize(self, *args, **kwargs):
        if kwargs.get("readable"):
            return Tile._TILES[self.tile] + str(self.tile_num)
        else:
            return self.i

    def __eq__(self, other):
        return isinstance(other, Tile) and other.i == self.i

    def __lt__(self, other):
        return isinstance(other, Tile) and self.tile < other.tile

    def is_aka(self):
        return (self.tile == 4 or self.tile == 13 or self.tile == 22) and self.tile_num == 0

    def get_t37_idx(self):
        return self.tile + self.is_aka() + (self.tile > 4) + (self.tile > 13) + (self.tile > 22)


class Player(JsonSerializable):
    def __init__(self, name: str, rank: str, sex: str, rate: int, connected: bool):
        self.name = name
        self.rank = rank
        self.sex = sex
        self.rate = rate
        self.connected = connected


class RoundNo(JsonSerializable):
    ROUNDS = ["E1", "E2", "E3", "E4", "S1", "S2", "S3", "S4", "W1", "W2", "W3", "W4"]

    def __init__(self, round_no: int, honba: int):
        self.round_no = round_no
        self.honba = honba

    def serialize(self, *args, **kwargs):
        if kwargs.get("readable"):
            if self.honba == 0:
                return f"{RoundNo.ROUNDS[self.round_no]}"
            else:
                return f"{RoundNo.ROUNDS[self.round_no]}-{self.honba}"
        else:
            return self.round_no


class Round(JsonSerializable):
    def __init__(self, oya: int, starting_hands: list, round_no: int, honba: int, rii_sticks: int):
        self.oya = oya  # Round dealer
        self.starting_hands = starting_hands  # List of hands

        self.round_no = RoundNo(round_no, honba)
        self.honba_count = honba
        self.rii_sticks = rii_sticks

        # Who won the round
        self.agari: list[Agari] = []

        self.events: list[Event] = []

        # Did round go to exhaustive draw
        self.ryuukyoku = False  # Can also be a string, if it's special (idk)
        self.ryuukyoku_players = []

        # Riichi
        self.riichi_players = []  # Which player(s) rii
        self.riichi_turns = []  # What turns rii happened on

        self.turns = [0, 0, 0, 0]  # Final turn for each player
        self.score_changes = []  # Score changes, divided by 100


class ChiiMeld(JsonSerializable):
    def __init__(self, data: int):
        self.relative_player = data & 0x3
        self.call_type = "chi"
        t0, t1, t2 = (data >> 3) & 0x3, (data >> 5) & 0x3, (data >> 7) & 0x3
        base_and_called = data >> 10
        self.chii_type = data % 3  # Ex 456 -> 0: 4 chii, 1: 5 chii, 2: 6 chii
        base = base_and_called // 3
        base = (base // 7) * 9 + base % 7
        self.tiles = (Tile(t0 + 4 * (base + 0)), Tile(t1 + 4 * (base + 1)), Tile(t2 + 4 * (base + 2)))


class PonMeld(JsonSerializable):
    def __init__(self, data: int):
        self.relative_player = data & 0x3

        t4 = (data >> 5) & 0x3
        t0, t1, t2 = ((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2))[t4]
        base_and_called = data >> 9
        self.calling_player = base_and_called % 3  # Who called the pon/kan
        base = base_and_called // 3

        if data & 0x8:
            self.call_type = "pon"
            self.tiles = (Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base))
        else:
            # Added Kan
            self.call_type = "shouminkan"
            self.tiles = (Tile(t0 + 4 * base), Tile(t1 + 4 * base), Tile(t2 + 4 * base), Tile(t4 + 4 * base))


class KanMeld(JsonSerializable):
    def __init__(self, data: int):
        self.relative_player = data & 0x3

        base_and_called = data >> 8
        # relative_player = 0 if referring to ourselves
        if self.relative_player:
            self.calling_player = base_and_called % 4
            self.call_type = "daiminkan"
        else:
            self.calling_player = self.relative_player
            self.call_type = "ankan"

        base = base_and_called // 4
        self.tiles = (Tile(4 * base), Tile(1 + 4 * base), Tile(2 + 4 * base), Tile(3 + 4 * base))


# Is this just Pei? Seems like it
class NukiMeld(JsonSerializable):
    def __init__(self, data: int):
        self.from_player = data & 0x3
        self.call_type = "nuki"
        self.tiles = (Tile(data >> 0),)


class Event(JsonSerializable):
    def __init__(self, event_name):
        self.event_name = event_name


class CallTileEvent(Event):
    def __init__(self, player: int, call_data: int):
        super().__init__("call")
        self.player = player
        if call_data & 0x4:
            self.meld = ChiiMeld(call_data)
        elif call_data & 0x18:
            self.meld = PonMeld(call_data)
        elif call_data & 0x20:
            self.meld = NukiMeld(call_data)
        else:
            self.meld = KanMeld(call_data)


class DoraIndicatorEvent(Event):
    def __init__(self, tile: Tile):
        super().__init__("dora")
        self.tile = tile


class DrawTileEvent(Event):
    def __init__(self, player: int, tile: Tile):
        super().__init__("draw_tile")
        self.player = player
        self.tile = tile


class DiscardTileEvent(Event):
    def __init__(self, player: int, tile: Tile):
        super().__init__("discard_tile")
        self.player = player
        self.tile = tile


class RiichiEvent(Event):
    def __init__(self, player):
        super().__init__("riichi")
        self.player = player


class RonEvent(Event):
    def __init__(self, winning_players: list[int], from_player: int):
        super().__init__("ron")
        self.winning_players = winning_players
        self.from_player = from_player


class TsumoEvent(Event):
    def __init__(self, player: int):
        super().__init__("tsumo")
        self.player = player


class RyuuyokuEvent(Event):
    def __init__(self, rk_type):
        super().__init__("ryuuyoku")
        self.rk_type = "s" if isinstance(rk_type, bool) else rk_type


class Agari(JsonSerializable):
    # There is more data but this was not needed for my usecase, so this is just here for posterity sake
    def __init__(self, win_type: str, winning_player: int, points: int, from_player: int):
        self.win_type = win_type
        self.winning_player = winning_player
        self.points = points
        self.from_player = from_player


class GameData(JsonSerializable):
    PLAYERS = ["n0", "n1", "n2", "n3"]
    HANDS = ["hai0", "hai1", "hai2", "hai3"]

    def __init__(self, log: str | TextIO):
        self.game_type = ""
        self.lobby = ""
        self.players: list[Player] = []
        self.rounds: list[Round] = []
        self.results: list[tuple[int, float]] = []  # Tuple of (final_score / 100, uma)

        self.decode(log)

    def reset(self):
        self.game_type = ""
        self.lobby = ""
        self.players = []
        self.rounds = []
        self.results = []

    def tag_GO(self, _, data):
        # The <GO lobby=""/> attribute was introduced at some point between
        # 2010 and 2012:
        self.game_type = data["type"]
        self.lobby = data.get("lobby")

    def tag_UN(self, _, data):
        if "dan" in data:
            names = [urllib_parse.unquote(data[name]) for name in GameData.PLAYERS if data[name]]
            ranks = GameData.decode_list(data["dan"])
            sexes = GameData.decode_list(data["sx"], dtype=str)
            rates = GameData.decode_list(data["rate"], dtype=float)
            for (name, rank, sex, rate) in zip(names, ranks, sexes, rates):
                self.players.append(Player(name, rank, sex, rate, False))
        else:
            for (player, name) in zip(self.players, GameData.PLAYERS):
                if name in data:
                    player.connected = True

    def tag_BYE(self, _, data):
        self.players[int(data["who"])].connected = False

    def tag_INIT(self, _, data):
        round_no, honba, rii_sticks, d0, d1, dora = GameData.decode_list(data["seed"])

        new_round = Round(
            int(data["oya"]),
            [GameData.decode_list(data[hand], Tile) for hand in GameData.HANDS if hand in data and data[hand]],
            round_no,
            honba,
            rii_sticks
        )

        self._finish_round()
        self.rounds.append(new_round)
        new_round.events.append(DoraIndicatorEvent(Tile(dora)))

    def tag_N(self, _, data):
        current_round = self.rounds[-1]

        calling_player = int(data["who"])
        current_round.events.append(CallTileEvent(calling_player, int(data["m"])))
        current_round.turns[calling_player] += 1

    def tag_TAIKYOKU(self, _, data):
        pass

    def tag_DORA(self, _, data):
        current_round = self.rounds[-1]

        current_round.events.append(DoraIndicatorEvent(Tile(int(data["hai"]))))

    def tag_RYUUKYOKU(self, _, data):
        current_round = self.rounds[-1]
        current_round.ryuukyoku = True

        deltas = data['sc'].split(',')
        current_round.score_changes = [int(deltas[x]) for x in range(1, 8, 2)]

        if 'owari' in data:
            temp = [[int, float][i % 2](j) for i, j in enumerate(data['owari'].split(","))]
            self.results = list(zip(temp[::2], temp[1::2]))

        # For special ryuukyoku types, set to string ID rather than boolean
        if 'type' in data:
            current_round.ryuukyoku = data['type']
        if current_round.ryuukyoku is True or current_round.ryuukyoku == "nm":
            tenpai = current_round.ryuukyoku_tenpai = []
            for index, attr_name in enumerate(GameData.HANDS):
                if attr_name in data:
                    tenpai.append(index)

    def tag_AGARI(self, _, data):
        current_round = self.rounds[-1]

        # agari = Agari()
        # self.round.agari.append(agari)
        agari_type = "RON" if data["fromWho"] != data["who"] else "TSUMO"
        agari_player = int(data["who"])
        agari_fu, agari_points, limit = GameData.decode_list(data["ten"])
        agari_from = int(data["fromWho"]) if agari_type == "RON" else None

        current_round.agari.append(Agari(agari_type, agari_player, agari_points, agari_from))

        deltas = data['sc'].split(',')
        current_round.score_changes = [int(deltas[x]) for x in range(1, 8, 2)]

        if 'owari' in data:
            temp = [[int, float][i % 2](j) for i, j in enumerate(data['owari'].split(","))]
            self.results = list(zip(temp[::2], temp[1::2]))

    def tag_REACH(self, _, data):
        # Note: This event is fired AFTER you discard
        if 'ten' in data:
            current_round = self.rounds[-1]
            player = int(data['who'])
            current_round.riichi_players.append(player)
            current_round.riichi_turns.append(current_round.turns[player])

            # Player decision to rii always comes after
            current_round.events.insert(-1, RiichiEvent(player))

    def default(self, tag, _):
        if tag[0] in "DEFG":
            current_round = self.rounds[-1]
            current_round.events.append(DiscardTileEvent(ord(tag[0]) - ord("D"), Tile(tag[1:])))
        elif tag[0] in "TUVW":
            current_round = self.rounds[-1]

            player = ord(tag[0]) - ord("T")
            current_round.events.append(DrawTileEvent(player, Tile(tag[1:])))
            current_round.turns[player] += 1

    @staticmethod
    def decode_list(thislist, dtype: type = int):
        return tuple(dtype(i) for i in thislist.split(","))

    def decode(self, log: str | TextIO):
        try:
            events = XMLElementTree.parse(log).getroot()
        except OSError:
            events = XMLElementTree.fromstring(log)

        tags = {key[4:]: getattr(GameData, key) for key in GameData.__dict__ if key.startswith("tag_")}

        self.reset()
        for event in events:
            tags.get(event.tag, GameData.default)(self, event.tag, event.attrib)

        self._finish_round()

    def _finish_round(self):
        if not self.rounds:
            return

        current_round = self.rounds[-1]

        if current_round.ryuukyoku:
            current_round.events.append(RyuuyokuEvent(current_round.ryuukyoku))
        elif current_round.agari[0].win_type == "RON":  # Ron
            current_round.events.append(
                RonEvent([i.winning_player for i in current_round.agari], current_round.agari[0].from_player))
        else:  # Tsumo
            current_round.events.append(TsumoEvent(current_round.agari[0].winning_player))


def test(old_log, new_log):
    import json

    ROUND_NAMES_OLD = "東1,東2,東3,東4,南1,南2,南3,南4,西1,西2,西3,西4,北1,北2,北3,北4".split(",")
    ROUND_NAMES_NEW = "E1,E2,E3,E4,S1,S2,S3,S4,W1,W2,W3,W4,N1,N2,N3,N4".split(",")
    EVENT_NAMES = [("Dora", "dora"), ("Draw", "draw_tile"), ("Discard", "discard_tile"), ("Call", "call")]

    with open(old_log) as f:
        old = json.load(f)
    with open(new_log) as f:
        new = json.load(f)

    assert len(old["rounds"]) == len(new["rounds"])

    for i in range(len(old["rounds"])):
        old_round = old["rounds"][i]
        new_round = new["rounds"][i]

        assert old_round["hands"] == new_round["starting_hands"]
        assert old_round["dealer"] == new_round["oya"]
        assert ROUND_NAMES_OLD.index(old_round["round"][0]) == ROUND_NAMES_NEW.index(new_round["round_no"][:2])
        assert old_round["round"][1] == new_round["honba_count"]
        assert old_round["round"][2] == new_round["rii_sticks"]

        j = k = 0

        while j < len(old_round["events"]) and k < len(new_round["events"]):
            old_ev = old_round["events"][j]
            new_ev = new_round["events"][k]

            if new_ev["event_name"] == "riichi":
                k += 1
            else:
                # Need to check the event contents
                assert (old_ev["type"], new_ev["event_name"]) in EVENT_NAMES
                j += 1
                k += 1

        assert j == len(old_round["events"]) and k == len(new_round["events"])


def extract_bz2(hex_str: str):
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]

    compressed = bytes.fromhex(hex_str)
    decompressed = bz2.decompress(compressed).decode()

    return GameData(decompressed)


if __name__ == '__main__':
    # test("log.json", "log1.json")
    print(Tile(31 << 2).serialize(readable=True))
