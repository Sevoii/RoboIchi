from mortal.model import load_model as load_model_mortal
from mortal_policy.model import load_model as load_model_mortal_policy

import riichi

mortal_engine = load_model_mortal()
mortal_policy_engine = load_model_mortal_policy()

two_v_two_arena = riichi.arena.TwoVsTwo(disable_progress_bar=False, log_dir="./logs")
two_v_two_arena.py_vs_py(mortal_engine, mortal_policy_engine, (42, 42), 200)
