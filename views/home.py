"""
Home — the landing page.

Orients a first-time reader before they reach any dashboard: what the
data is, what is being asked, what was found, and where to go for each
question. Deliberately light on analysis, since every claim made here is
examined properly on the page it links to.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import charts as C
from lib import data as D
from lib import theme as T

matches = D.load_matches()

# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------

T.eyebrow("Information Visualization · Course Project")
st.markdown("# Twenty seasons of European football")
T.lede(
    "An interactive analysis of every match played in Europe's Big Five leagues "
    "between 2006/07 and 2025/26 — how the game changed, how the five leagues "
    "differ, and what happened to home advantage when COVID-19 emptied the "
    "stadiums."
)

T.stat_row([
    {"label": "Matches analysed", "value": f"{len(matches):,}", "note": "one row each"},
    {"label": "Leagues", "value": "5", "note": "England, Spain, Italy, Germany, France"},
    {"label": "Seasons", "value": "20", "note": "2006/07 – 2025/26"},
    {"label": "Source files", "value": "100", "note": "CSV, one per league-season"},
    {"label": "Clubs", "value": "207", "note": "top flight only"},
])

st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# The question
# --------------------------------------------------------------------------

left, right = st.columns([1.05, 1], gap="large")

with left:
    st.markdown("## The question")
    st.markdown(
        """
**How have match characteristics and outcomes across Europe's Big Five
leagues evolved over the last 20 seasons, and how do these patterns
differ between leagues?**

Four supporting questions follow from it — on home advantage, attacking
performance, discipline, and what distinguishes each league. Each has a
dashboard of its own.

A single league-season is 380 rows and 22 columns; the full dataset is
36,197 matches across five competitions and twenty years. Patterns that
become obvious once drawn — a refereeing bias that holds for fourteen
seasons and then vanishes, or five leagues converging on a common
disciplinary standard — are invisible in a spreadsheet.
"""
    )

with right:
    st.markdown("## The headline finding")

    hw = D.home_win_rate(matches, ["crowd_status"])
    order = [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST]
    hw = hw.set_index("crowd_status").reindex(order).reset_index()
    short = {T.CROWD_PRE: "Crowds", T.CROWD_EMPTY: "Empty", T.CROWD_POST: "Returned"}

    fig = go.Figure(go.Bar(
        x=[short[c] for c in hw["crowd_status"]],
        y=hw["home_win_pct"],
        marker=dict(color=[T.CROWD_COLORS[c] for c in hw["crowd_status"]]),
        text=[f"{v:.1f}%" for v in hw["home_win_pct"]],
        textposition="outside",
        textfont=dict(family=T.FONT_MONO, size=13),
        hovertemplate="%{y:.1f}% of matches won at home<extra></extra>",
    ))
    fig.update_layout(
        title="Home win rate, by crowd conditions",
        yaxis_title="Home wins (%)", xaxis_title="",
        height=300, showlegend=False, bargap=0.45, hovermode="closest",
        margin=dict(t=52, b=8),
    )
    fig.update_yaxes(ticksuffix="%", range=[0, 55])
    st.plotly_chart(fig, width="stretch")

    T.readout(
        "Home teams won roughly 46% of matches for fourteen consecutive seasons. "
        "In empty stadiums that fell to 40.3%, then partly recovered. The "
        "mechanism — a refereeing bias that disappeared and came back — is on "
        "the Home Advantage dashboard."
    )

st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Where to go
# --------------------------------------------------------------------------

st.markdown("## Where to go")
T.lede(
    "Six dashboards, each answering one part of the question. League and season "
    "filters in the sidebar apply to all of them, so a selection made on one "
    "page stays in force on the others."
)

PAGES = [
    ("views/home_advantage.py", "1 · Home Advantage", "Supporting question 1",
     "Does home advantage come from the crowd? Twenty seasons of home win rates, "
     "and the refereeing bias that vanished when stadiums emptied."),
    ("views/explorer.py", "2 · Evolution of the Big Five", "Main question",
     "Any of nine measures across every league-season as a heatmap. Click a cell "
     "to drill into that season."),
    ("views/attacking.py", "3 · Attacking & Efficiency", "Supporting question 2",
     "Shooting volume against scoring efficiency, and what a half-time lead is "
     "actually worth."),
    ("views/team_deep_dive.py", "4 · Team Deep-Dive", "Depth",
     "From league averages down to a single club: its home and away record over "
     "time, and how much of its advantage survived empty stadiums."),
    ("views/referees.py", "5 · Referees & Discipline", "Supporting question 3",
     "How strictly each league punishes a foul, and whether individual referees "
     "show the crowd effect."),
    ("views/league_profiles.py", "6 · League Profiles", "Supporting question 4",
     "What distinguishes each league — and whether twenty years have made them "
     "more alike."),
]

for row_start in (0, 2, 4):
    cols = st.columns(2, gap="large")
    for col, (path, title, tag, blurb) in zip(cols, PAGES[row_start:row_start + 2]):
        with col:
            st.markdown(f'<div class="eyebrow">{tag}</div>', unsafe_allow_html=True)
            st.page_link(path, label=f"**{title}**")
            st.markdown(
                f'<div class="nav-blurb">{blurb}</div>', unsafe_allow_html=True
            )

st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# How to use it
# --------------------------------------------------------------------------

how, about = st.columns([1, 1], gap="large")

with how:
    st.markdown("## How to use it")
    st.markdown(
        """
- **Filters persist.** League and season selections in the sidebar apply
  to every dashboard, so the pages behave as one linked system.
- **The heatmap is clickable.** On *Evolution of the Big Five*, selecting
  a cell redraws the detail panel beneath it for that league-season.
- **Hover for detail.** Every chart reports values, units and the number
  of matches behind each point.
- **Read the notes.** A short line under each chart states what to take
  from it; boxed notes flag small samples and other limitations.
"""
    )

with about:
    st.markdown("## About")
    st.markdown(
        """
**Data.** Match results and statistics from
[football-data.co.uk](https://www.football-data.co.uk/), obtained via
[datasets/football-datasets](https://github.com/datasets/football-datasets).

**Built with** Python, pandas and PyArrow for the preprocessing pipeline;
Streamlit and Plotly for the application. An earlier Tableau workbook was
used for exploratory prototyping, and several of its measures and chart
designs were carried into this application.

**Method, assumptions and limitations** are documented on the
*About & Method* page, together with the full data quality report.
"""
    )
    st.page_link("views/about.py", label="**Read the method →**")

st.markdown("<hr>", unsafe_allow_html=True)
st.caption(
    "Tom Rosenberg · Ofir Kaplan · Fadi Kees · Daniel Ifrim  |  "
    "Information Visualization course project"
)
