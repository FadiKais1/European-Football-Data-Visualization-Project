"""Smoke test: every view runs without raising, under several filter states."""
from streamlit.testing.v1 import AppTest
import sys

VIEWS = [
    ("views/home_advantage.py", "Home Advantage"),
    ("views/explorer.py", "Evolution"),
    ("views/attacking.py", "Attacking"),
    ("views/team_deep_dive.py", "Team Deep-Dive"),
    ("views/referees.py", "Referees"),
    ("views/league_profiles.py", "League Profiles"),
    ("views/about.py", "About"),
]

STATES = [
    ("defaults", {}),
    ("single league", {"flt_leagues": ["Serie A"]}),
    ("pre-COVID only", {"flt_seasons": ("2006/07", "2010/11")}),
    ("post-COVID only", {"flt_seasons": ("2022/23", "2025/26")}),
]

fails = 0
for path, name in VIEWS:
    for label, state in STATES:
        at = AppTest.from_file(path, default_timeout=240).run()
        for k, v in state.items():
            at.session_state[k] = v
        if state:
            at = at.run()
        if at.exception:
            fails += 1
            print(f"FAIL  {name} [{label}]")
            for e in at.exception:
                print("      ", e.value)
        else:
            print(f"OK    {name} [{label}]")

print("\nFAILURES:", fails)
sys.exit(fails)
