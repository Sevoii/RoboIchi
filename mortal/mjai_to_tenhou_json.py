import json

CONVERSIONS = {
    # manzu
    "1m": 11, "2m": 12, "3m": 13, "4m": 14, "5m": 15, "6m": 16, "7m": 17, "8m": 18, "9m": 19,

    # pinzu
    "1p": 21, "2p": 22, "3p": 23, "4p": 24, "5p": 25, "6p": 26, "7p": 27, "8p": 28, "9p": 29,

    # souzu
    "1s": 31, "2s": 32, "3s": 33, "4s": 34, "5s": 35, "6s": 36, "7s": 37, "8s": 38, "9s": 39,

    # honors
    "E": 41, "S": 42, "W": 43, "N": 44, "P": 45, "F": 46, "C": 47,

    # red fives
    "5mr": 51, "5pr": 52, "5sr": 53,

    # unknown
    "?": -1
}


def tile_to_tenhou(tile):
    return CONVERSIONS[tile]


class RoundData:
    def __init__(self, start_event):
        self.round = ["E", "S", "W"].index(start_event["bakaze"]) * 4 + start_event["kyoku"] - 1
        self.honba = start_event["honba"]
        self.sticks = start_event["kyotaku"]

        self.dora = [tile_to_tenhou(start_event["dora_marker"])]
        self.ura_dora = []

        self.scores = start_event["scores"]
        self.deltas = []

        self.haipais = [[tile_to_tenhou(tile) for tile in hand] for hand in start_event["tehais"]]
        self.draws = [[], [], [], []]
        self.discards = [[], [], [], []]

        self.last_event = start_event
        self.pon_calls = [[], [], [], []]

    def dump(self):
        return [
            [self.round, self.honba, self.sticks],
            self.scores,
            self.dora,
            self.ura_dora,
            self.haipais[0],
            self.draws[0],
            self.discards[0],
            self.haipais[1],
            self.draws[1],
            self.discards[1],
            self.haipais[2],
            self.draws[2],
            self.discards[2],
            self.haipais[3],
            self.draws[3],
            self.discards[3],
            ["不明"]
        ]

    def process_event(self, event):
        if event["type"] == "dora":
            self.dora.append(tile_to_tenhou(event["dora_marker"]))
        elif event["type"] == "tsumo":
            self.draws[event["actor"]].append(tile_to_tenhou(event["pai"]))
        elif event["type"] == "dahai":
            if event["tsumogiri"]:
                self.discards[event["actor"]].append(60)
            else:
                self.discards[event["actor"]].append(tile_to_tenhou(event["pai"]))
        elif event["type"] == "chi":
            chi_meld = ["c", str(tile_to_tenhou(event["pai"]))] + [str(tile_to_tenhou(tile)) for
                                                                   tile in event["consumed"]]
            self.draws[event["actor"]].append("".join(chi_meld))
        elif event["type"] == "pon":
            relative_pos = (event["target"] - event["actor"]) % 4
            pon_meld = [str(tile_to_tenhou(tile)) for tile in event["consumed"]]
            pon_meld.insert(3 - relative_pos, f"p{tile_to_tenhou(event['pai'])}")
            self.draws[event["actor"]].append("".join(pon_meld))

            self.pon_calls[event["actor"]].append(event)
        elif event["type"] == "ankan":
            kan_meld = [str(tile_to_tenhou(tile)) for tile in event["consumed"]]
            kan_meld.insert(3, "a")
            self.discards[event["actor"]].append("".join(kan_meld))
        elif event["type"] == "kakan":
            found_call = [i for i in self.pon_calls[event["actor"]] if i["pai"][:2] == event["pai"][:2]][0]
            relative_pos = (found_call["target"] - found_call["actor"]) % 4
            kan_meld = [str(tile_to_tenhou(tile)) for tile in event["consumed"]]
            kan_meld.insert(3 - relative_pos, f"k{tile_to_tenhou(event['pai'])}")
            self.discards[event["actor"]].append("".join(kan_meld))
        elif event["type"] == "daiminkan":
            relative_pos = (event["target"] - event["actor"]) % 4

            kan_meld = [str(tile_to_tenhou(tile)) for tile in event["consumed"]]
            if relative_pos == 1:
                kan_meld.insert(3, "m")
            else:
                kan_meld.insert(3 - relative_pos, "m")
            self.draws[event["actor"]].append("".join(kan_meld))
        elif event["type"] == "reach":
            # do nothing doesn't matter that much
            pass
        elif event["type"] == "reach_accepted":
            assert self.last_event["actor"] == event["actor"]
            self.discards[self.last_event["actor"]].append(f'r{self.discards[self.last_event["actor"]].pop()}')
        elif event["type"] == "ryukyoku":
            # do nothing
            pass
        elif event["type"] == "hora":
            # maybe add some winning stuff
            self.ura_dora = [tile_to_tenhou(tile) for tile in event["ura_markers"]]
        else:
            raise RuntimeError(f"No Event Found: {event['type']}")

        self.last_event = event


def convert_mjai_log(events):
    basic_log = {
        "title": ["", ""],
        "name": ["P0", "P1", "P2", "P3"],
        "rule": {"aka": 1},
        "log": []
    }

    round_data = None
    for ev in events:
        if ev["type"] == "start_game" or ev["type"] == "end_game":
            pass
        elif ev["type"] == "start_kyoku":
            round_data = RoundData(ev)
        elif ev["type"] == "end_kyoku":
            basic_log["log"].append(round_data.dump())
            round_data = None
        else:
            round_data.process_event(ev)

    return basic_log


def main():
    with open("test_mjai_log.json") as f:
        data = json.load(f)

    print(json.dumps(convert_mjai_log(data), ensure_ascii=False))


if __name__ == "__main__":
    main()
