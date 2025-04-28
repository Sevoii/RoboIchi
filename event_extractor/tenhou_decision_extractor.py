import shanten_calcs
from tenhou_game_state import GameState, PlayerState
import tenhou_decoder


class ActionSpace:
    def __init__(self):
        self.allowed_tiles_discard = [0 for _ in range(37)]
        self.allowed_riichi = 0
        self.allowed_chii_types = [0 for _ in range(3)]
        self.allowed_pon = 0
        self.allowed_kan = 0
        self.allowed_win = 0
        self.allowed_draw = 0

    def dump(self):
        # Mortal Bindings
        # 0-36 discard or kan choice
        # 37 can riichi
        # 38-40 can chii types
        # 41 pon
        # 42 kan
        # 43 agari
        # 44 draw
        # 45 pass

        return (self.allowed_tiles_discard + [self.allowed_riichi] + self.allowed_chii_types +
                [self.allowed_pon,
                 self.allowed_kan,
                 self.allowed_win,
                 self.allowed_draw,
                 int(any((self.allowed_riichi, any(self.allowed_chii_types), self.allowed_pon, self.allowed_kan,
                          self.allowed_win, self.allowed_draw)))])


def get_rii_tiles(tiles: list[int], return_early=False):
    if sum(tiles) != 14:
        return False

    discard_tiles = []

    for i in range(34):
        if not tiles[i]: continue

        tiles[i] -= 1
        shanten = shanten_calcs.calc_all(tiles)
        tiles[i] += 1

        if shanten <= 0:
            discard_tiles.append(i)
            if return_early:
                return True

    return discard_tiles


def can_hand_win(player: PlayerState):
    # todo
    return False


def extract_events(game_data: GameState):
    game_data.next_round()
    while game_data.current_round is not None:
        while (ev := game_data.get_next_event()):
            if isinstance(ev, tenhou_decoder.DrawTileEvent):
                # POV player makes decision on calls: abortive draw, kan, tsumo, riichi
                game_data.process_event()
                curr_player = game_data.current_round.players[ev.player]

                action_space = ActionSpace()
                flag = False

                action_space.allowed_draw = (not game_data.current_round.did_someone_call() and
                                             game_data.current_round.tiles_left >= 66 and sum(
                            map(lambda t: (t % 9 == 0 or t % 9 == 8) or t >= 7,
                                curr_player.closed_hand)) >= 9)

                t34 = shanten_calcs.convert_t14_to_full([i.tile for i in curr_player.closed_hand])
                if curr_player.is_rii:
                    action_space.allowed_kan = shanten_calcs.check_ankan_after_riichi(t34, ev.tile.tile)
                else:
                    # todo
                    pass
                action_space.allowed_win = can_hand_win(curr_player)
                action_space.allowed_riichi = get_rii_tiles(t34, True)

                if flag:
                    match type(game_data.get_next_event()):
                        case tenhou_decoder.RiichiEvent:
                            assert action_space.allowed_riichi
                            correct_decision = 37
                        case tenhou_decoder.TsumoEvent:
                            assert action_space.allowed_win
                            correct_decision = 43
                        case tenhou_decoder.CallTileEvent:
                            assert action_space.allowed_kan
                            correct_decision = 42
                        case tenhou_decoder.RyuuyokuEvent:
                            correct_decision = 44 if action_space.allowed_draw else 45
                        case _:
                            correct_decision = 45

                    yield game_data.dump_compressed(ev.player), action_space, correct_decision
            elif isinstance(ev, tenhou_decoder.DiscardTileEvent):
                # Pre Discard: POV player makes decision on what to discard
                # Post Discard: Other players make decision on calling tiles (ron, pon/kan, chii)
                pass
            elif isinstance(ev, tenhou_decoder.CallTileEvent):
                # Kan which tile
                # If kan type is shouminkan, check chankans
                # If kan type is ankan, check kokushi
                pass
            else:
                game_data.process_event()

        game_data.next_round()
