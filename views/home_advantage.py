"""
Dashboard 1 — The Home Advantage Story.

The narrative page. It establishes that home advantage exists, shows it
weakening when stadiums emptied, and then identifies referee behaviour as
a mechanism that moved at the same time.
"""

from __future__ import annotations

import streamlit as st

from lib import charts as C
from lib import data as D
from lib import theme as T

D.sidebar_filters()

matches_all = D.load_matches()
matches = D.apply_filters(matches_all)

# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------

T.eyebrow("Dashboard 1 of 6 · Home advantage")
st.markdown("# Football's home advantage is partly made of noise")
T.lede(
    "Home teams have won far more often than away teams for as long as the "
    "game has been recorded, and the reasons offered are usually travel "
    "fatigue, familiarity with the pitch, and the crowd. Those explanations "
    "are hard to separate — until 2020, when COVID-19 emptied the stadiums "
    "and left everything else in place. This dashboard uses that period as a "
    "natural experiment across 36,197 matches in Europe's five biggest "
    "leagues."
)

if matches.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

crowd = matches.groupby("crowd_status", observed=True)
pre = matches[matches["crowd_status"] == T.CROWD_PRE]
emp = matches[matches["crowd_status"] == T.CROWD_EMPTY]
post = matches[matches["crowd_status"] == T.CROWD_POST]


def _hw(df):
    return float(df["is_home_win"].mean() * 100) if len(df) else float("nan")


def _gap(df):
    if not len(df):
        return float("nan")
    return float(df["away_yellows"].mean() - df["home_yellows"].mean())


T.eyebrow("Home wins, by crowd conditions")
T.stat_row([
    {"label": "Crowds present", "value": f"{_hw(pre):.1f}%", "tone": "amber",
     "note": f"{len(pre):,} matches to Mar 2020"},
    {"label": "Empty stadiums", "value": f"{_hw(emp):.1f}%", "tone": "steel",
     "note": f"{len(emp):,} matches"},
    {"label": "Crowds returned", "value": f"{_hw(post):.1f}%", "tone": "amber-light",
     "note": f"{len(post):,} matches since Jul 2021"},
    {"label": "Swing when empty",
     "value": f"{_hw(emp) - _hw(pre):+.1f}pp", "tone": "steel",
     "note": "percentage points vs crowds"},
])

st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 1. Does home advantage exist, and did it move?
# --------------------------------------------------------------------------

st.markdown("## 1. Twenty seasons of home advantage")

col_a, col_b = st.columns([3, 1])
with col_b:
    split = st.toggle(
        "Split by league", value=False,
        help="Check whether the pattern holds in all five leagues or is driven by one.",
    )

seasons = D.season_axis(matches)
by = ["season", "league_short"] if split else ["season"]
hw = D.home_win_rate(matches, by)

st.plotly_chart(
    C.home_win_timeline(hw, seasons, by_league=split),
    width="stretch",
)

if split:
    T.readout(
        "Every league moves in the same direction during the shaded window, which "
        "rules out a quirk of one competition's scheduling or officiating."
    )
else:
    T.readout(
        "The home win rate is stable for well over a decade, then drops sharply "
        "across the shaded empty-stadium seasons before recovering only partially. "
        "Toggle the league split to confirm the pattern is not driven by a single league."
    )

# --------------------------------------------------------------------------
# 2. The mechanism
# --------------------------------------------------------------------------

st.markdown("## 2. What the referees did")
T.lede(
    "If the crowd is what creates home advantage, its effect should show up in "
    "decisions the crowd can influence. Bookings are the clearest test: referees "
    "have consistently shown more yellow cards to away teams than home teams."
)

gap = D.card_gap(matches, ["season"])
st.plotly_chart(C.card_gap_timeline(gap, seasons), width="stretch")

gap_pre, gap_emp, gap_post = _gap(pre), _gap(emp), _gap(post)
T.readout(
    f"Away teams were booked {gap_pre:.2f} times more per match than home teams "
    f"while crowds were present — a bias that held for fourteen consecutive seasons. "
    f"In empty stadiums it fell to {gap_emp:.3f}, effectively zero, then returned to "
    f"{gap_post:.2f} once fans came back. A bias that disappears and reappears with "
    "the crowd is much harder to explain by chance than a one-off dip."
)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        C.crowd_bars(
            D.home_win_rate(matches, ["crowd_status"]),
            "home_win_pct",
            "Home wins under each crowd condition",
            "Home wins (% of matches)", suffix="%",
        ),
        width="stretch",
    )
with c2:
    st.plotly_chart(
        C.crowd_bars(
            D.card_gap(matches, ["crowd_status"]),
            "yellow_gap",
            "Booking bias under each crowd condition",
            "Away − home yellows per match",
        ),
        width="stretch",
    )

T.readout(
    "The two measures move together. Colour is doing analytical work here: amber "
    "marks matches played in front of a crowd, steel blue marks empty stadiums, and "
    "the return of amber on the right is the return of the effect."
)

# --------------------------------------------------------------------------
# 3. Does it hold league by league?
# --------------------------------------------------------------------------

st.markdown("## 3. League by league")

metric = st.radio(
    "Measure",
    ["Home win rate", "Booking bias", "Home goal difference"],
    horizontal=True, label_visibility="collapsed",
)

if metric == "Home win rate":
    src = D.home_win_rate(matches, ["league_short", "crowd_status"])
    fig = C.league_slope(src, "home_win_pct",
                         "Home win rate by league and crowd conditions",
                         "Home wins (% of matches)", suffix="%")
elif metric == "Booking bias":
    src = D.card_gap(matches, ["league_short", "crowd_status"])
    fig = C.league_slope(src, "yellow_gap",
                         "Booking bias by league and crowd conditions",
                         "Away − home yellows per match")
else:
    src = (
        matches.groupby(["league_short", "crowd_status"], observed=True)
        .agg(gd=("goal_difference", "mean"), matches=("match_id", "size"))
        .reset_index()
    )
    src["gd"] = src["gd"].astype(float)
    fig = C.league_slope(src, "gd",
                         "Average home goal difference by league and crowd conditions",
                         "Home goals − away goals per match")

st.plotly_chart(fig, width="stretch")
T.readout(
    "Each line is one league. The tilt between the first two points is the size of "
    "the crowd effect; the tilt between the last two is how much of it came back."
)

# --------------------------------------------------------------------------
# 4. Where else the advantage shows
# --------------------------------------------------------------------------

st.markdown("## 4. The advantage across the whole match")

condition = st.selectbox(
    "Crowd conditions",
    [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST, "All matches"],
    index=0,
)
subset = matches if condition == "All matches" else matches[matches["crowd_status"] == condition]

vm = D.venue_means(
    subset, [],
    {"Shots": "shots", "Shots on target": "shots_on_target",
     "Corners": "corners", "Fouls": "fouls", "Yellow cards": "yellows"},
) if len(subset) else None

if vm is not None and not vm.empty:
    st.plotly_chart(
        C.venue_dumbbell(vm, f"Home versus away averages — {condition.lower()}"),
        width="stretch",
    )
    T.readout(
        "Switching between conditions shows which components of home advantage are "
        "crowd-dependent. Shots and corners barely move; the disciplinary gap is what "
        "closes, which points at officiating rather than at how the teams played."
    )

st.markdown("<hr>", unsafe_allow_html=True)

T.caveat(
    "<strong>How to read this responsibly.</strong> The source data contains no "
    "attendance figures, so each match is classified by the period it was played in: "
    "crowds present before 8 March 2020, empty or restricted until 30 June 2021, "
    "crowds returned thereafter. Attendance policy varied by country and by club, so "
    "the boundaries are an approximation, and a small number of matches inside the "
    "middle window were played in front of partial crowds. The comparison is "
    "observational, not a randomised trial: other things changed in 2020, including "
    "congested fixture lists and five-substitute rules. The consistency of the "
    "pattern across five independent leagues, and its reversal when crowds returned, "
    "is what makes the crowd the most plausible explanation."
)
