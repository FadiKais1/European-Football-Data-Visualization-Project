"""
Does home advantage come from the crowd?
========================================

Entry point for the Streamlit application.

Analyses 36,197 matches from Europe's Big Five football leagues
(2006/07-2025/26), using the COVID-19 empty-stadium period as a natural
experiment on the source of home advantage.

Run locally with:

    streamlit run streamlit_app.py

Navigation is declared here rather than inferred from filenames, so each
dashboard carries a readable title and icon in the sidebar.
"""

from __future__ import annotations

import streamlit as st

from lib import theme as T

# Page configuration and styling run once, before any view.
T.configure_page()
T.inject_css()

DASHBOARDS = [
    st.Page(
        "views/home_advantage.py",
        title="Home Advantage",
        icon=":material/stadium:",
        default=True,
    ),
    st.Page(
        "views/explorer.py",
        title="Evolution of the Big Five",
        icon=":material/grid_view:",
    ),
    st.Page(
        "views/attacking.py",
        title="Attacking & Efficiency",
        icon=":material/sports_soccer:",
    ),
    st.Page(
        "views/team_deep_dive.py",
        title="Team Deep-Dive",
        icon=":material/groups:",
    ),
    st.Page(
        "views/referees.py",
        title="Referees & Discipline",
        icon=":material/sports:",
    ),
    st.Page(
        "views/league_profiles.py",
        title="League Profiles",
        icon=":material/insights:",
    ),
]

REFERENCE = [
    st.Page(
        "views/about.py",
        title="About & Method",
        icon=":material/info:",
    ),
]

navigation = st.navigation({"Dashboards": DASHBOARDS, "Reference": REFERENCE})

with st.sidebar:
    st.markdown(
        '<div class="eyebrow">Europe\'s Big Five · 2006/07–2025/26</div>',
        unsafe_allow_html=True,
    )

navigation.run()
