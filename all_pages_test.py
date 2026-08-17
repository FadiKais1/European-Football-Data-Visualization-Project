"""Smoke test: every view runs without raising, under several filter states.

The Home page is exercised through `streamlit_app.py` rather than directly,
because it uses `st.page_link`, which needs the navigation registry that the
entry script sets up. Running it standalone would fail for that reason alone,
which would be a test artefact rather than a real defect.
"""
from streamlit.testing.v1 import AppTest
import sys

VIEWS = [
    ("streamlit_app.py", "Home (via navigation)"),
    ("views/story.py", "Story"),
    ("views/home_advantage.py", "Home Advantage"),
    ("views/explorer.py", "Evolution"),
    ("views/attacking.py", "Attacking"),
    ("views/team_deep_dive.py", "Team Deep-Dive"),
    ("views/referees.py", "Referees"),
    ("views/league_profiles.py", "League Profiles"),
    ("views/linked.py", "Linked Views"),
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
        at = AppTest.from_file(path, default_timeout=300).run()
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

# Every step of the guided story must render its own content. Steps are
# asserted by heading text rather than by absence of an exception, since a
# step that silently renders nothing would otherwise pass.
STORY_STEPS = {
    0: "Home teams win more",
    1: "That advantage weakened",
    2: "The crowd went missing",
    3: "What the referees did",
    4: "Players and officials",
    5: "It happened everywhere",
}
for i, expected in STORY_STEPS.items():
    at = AppTest.from_file("views/story.py", default_timeout=300).run()
    at.session_state["story_step"] = i
    at = at.run()
    text = " ".join(m.value for m in at.markdown if isinstance(m.value, str))
    if at.exception:
        fails += 1
        print(f"FAIL  Story [step {i + 1}]")
        for e in at.exception:
            print("      ", e.value)
    elif expected not in text:
        fails += 1
        print(f"FAIL  Story [step {i + 1}] — heading not rendered")
    else:
        print(f"OK    Story [step {i + 1}]")

# The final step uses st.page_link, so it needs the navigation registry.
at = AppTest.from_file("streamlit_app.py", default_timeout=300).run()
at.session_state["story_step"] = 6
at = at.run()
at.switch_page("views/story.py")
at = at.run()
if at.exception:
    fails += 1
    print("FAIL  Story [step 7]")
    for e in at.exception:
        print("      ", e.value)
else:
    print("OK    Story [step 7]")

print("\nFAILURES:", fails)
sys.exit(fails)
