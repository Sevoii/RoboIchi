from riichienv import RiichiEnv, Action, GameRule
import riichi


class MortalAgent:
    def __init__(self, engine, player_id: int):
        self.player_id = player_id
        self.model = riichi.mjai.Bot(engine, player_id)

    def act(self, obs) -> Action:
        resp = None
        for event in obs.new_events():
            resp = self.model.react(event)

        action = obs.select_action_from_mjai(resp)
        assert action is not None, "Mortal must return a legal action"
        return action


def main():
    from mortal.model import load_model

    env = RiichiEnv(game_mode="4p-red-half", rule=GameRule.default_tenhou())
    agents = {pid: MortalAgent(pid, load_model) for pid in range(4)}
    obs_dict = env.reset()
    while not env.done():
        actions = {pid: agents[pid].act(obs) for pid, obs in obs_dict.items()}
        obs_dict = env.step(actions)

    print(env.scores(), env.ranks())


if __name__ == "__main__":
    main()
