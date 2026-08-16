"""
About and Method.

Reference page. Documents the data source, the processing pipeline, the
assumptions the analysis rests on, and its limitations — placed inside
the application rather than in a separate document, so that anyone
reading a chart can check what stands behind it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from lib import data as D
from lib import theme as T

matches = D.load_matches()
team_matches = D.load_team_matches()

T.eyebrow("Reference")
st.markdown("# About this project")
T.lede(
    "An interactive analysis of 36,197 football matches from Europe's Big Five "
    "leagues across twenty seasons, asking how match characteristics have "
    "evolved, how the leagues differ, and how much of home advantage comes "
    "from the crowd."
)

# --------------------------------------------------------------------------
# Dataset at a glance
# --------------------------------------------------------------------------

T.stat_row([
    {"label": "Matches", "value": f"{len(matches):,}", "note": "one row each"},
    {"label": "Seasons", "value": f"{matches['season'].nunique()}", "note": "2006/07–2025/26"},
    {"label": "Leagues", "value": f"{matches['league'].nunique()}", "note": "Europe's Big Five"},
    {"label": "Clubs", "value": f"{pd.unique(team_matches['team']).size}", "note": "top flight only"},
    {"label": "Source files", "value": "100", "note": "CSV, one per league-season"},
])

st.markdown("## The question")
st.markdown(
    """
Home teams win far more often than away teams. The usual explanations —
travel fatigue, familiarity with the pitch, crowd support — are hard to
separate, because they always occur together.

In 2020 they came apart. COVID-19 emptied the stadiums while leaving the
teams, the competitions, the pitches and the travel in place. That makes
the period a natural experiment: whatever changed can reasonably be
attributed to the absence of the crowd.
"""
)

st.markdown("## Research questions")
st.markdown(
    """
**Main question.** How have match characteristics and outcomes across
Europe's Big Five leagues evolved over the last 20 seasons, and how do
these patterns differ between leagues?

| | Supporting question | Dashboard |
|---|---|---|
| 1 | How has home advantage changed, and how does it differ by league? | Home Advantage |
| 2 | How have attacking characteristics and scoring efficiency changed? | League & Season Explorer |
| 3 | How have fouls and disciplinary patterns evolved? | Referees & Discipline |
| 4 | What distinguishes the leagues, and are the differences narrowing? | League Profiles |
"""
)

# --------------------------------------------------------------------------
# Data and processing
# --------------------------------------------------------------------------

st.markdown("## Data and processing")
st.markdown(
    """
**Source.** [github.com/datasets/football-datasets](https://github.com/datasets/football-datasets),
which publishes match data for the five leagues sourced from
[football-data.co.uk](https://www.football-data.co.uk/). The raw data is
100 CSV files: 20 seasons for each of the five leagues.

**Processing.** A single reproducible script, `preprocessing/preprocess.py`,
validates every file against the expected 22-column schema, merges them,
corrects data types, handles missing values explicitly, derives the
analytical fields, and writes two Parquet tables plus a data quality
report. It runs from the command line with no dependency on a particular
cloud environment.
"""
)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Match-level table**")
    st.markdown(
        f"`matches.parquet` — {len(matches):,} rows × {matches.shape[1]} columns. "
        "One row per match, with derived measures: points, goal difference, "
        "shot accuracy and conversion, and home-minus-away differentials."
    )
with c2:
    st.markdown("**Long team-match table**")
    st.markdown(
        f"`team_matches.parquet` — {len(team_matches):,} rows × {team_matches.shape[1]} columns. "
        "Each match contributes two rows, one per team, distinguished by "
        "`venue`. This makes every home-versus-away comparison a single "
        "grouping operation."
    )

# --------------------------------------------------------------------------
# Assumptions
# --------------------------------------------------------------------------

st.markdown("## The one assumption everything rests on")

cs = matches["crowd_status"].value_counts().reindex(
    [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST]
)
st.markdown(
    f"""
The source data contains **no attendance figures**. Crowd conditions are
therefore inferred from the match date:

| Label | Window | Matches |
|---|---|---:|
| Crowds present | before 8 March 2020 | {int(cs.iloc[0]):,} |
| Empty / restricted | 8 March 2020 – 30 June 2021 | {int(cs.iloc[1]):,} |
| Crowds returned | after 30 June 2021 | {int(cs.iloc[2]):,} |
"""
)

T.caveat(
    "<strong>This is an approximation, and it is stated rather than hidden.</strong> "
    "The five leagues suspended play in March 2020; four resumed behind closed "
    "doors while Ligue 1 abandoned its season. The 2020/21 season was played "
    "predominantly without spectators, but attendance policy varied by country "
    "and even by club, and some matches inside the middle window were played in "
    "front of partial crowds. The boundaries above cannot be exact."
)

st.markdown("## Limitations")
st.markdown(
    """
- **The comparison is observational, not a randomised experiment.** Other
  things changed in 2020, including fixture congestion and the move to five
  substitutions. The evidence for the crowd explanation rests on the pattern
  appearing in five independently administered leagues, reversing when crowds
  returned, and affecting disciplinary measures while leaving shots and corners
  largely unchanged.
- **Referee names exist only for the Premier League** (100% coverage), with
  about 5% for Serie A and none elsewhere. The Referees dashboard is scoped
  accordingly.
- **Fouls were never recorded for Ligue 1 2006/07.** These values are left
  missing rather than imputed, and foul-based charts exclude that season.
- **The empty-stadium window is short** — roughly 2,255 matches. That is ample
  for league-level conclusions but thin for individual clubs and referees,
  where sample-size warnings appear beside the affected charts.
- **Season length is not constant** across leagues and years, so every
  comparison uses per-match rates rather than raw counts.
"""
)

# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------

st.markdown("## Tools and libraries")
st.markdown(
    """
| Tool | Purpose |
|---|---|
| Python 3.12 | Preprocessing pipeline and application |
| pandas | Cleaning, reshaping, aggregation |
| PyArrow | Parquet read and write |
| Streamlit | Multi-page application, widgets, caching, session state |
| Plotly (`graph_objects`) | All visualisations and selection events |
| NumPy | Numerical operations |
| Streamlit Community Cloud | Hosting |

**Use of large language models.** Claude (Anthropic) was used to review the
initial preprocessing notebook and identify data quality issues, to assist
with implementing the pipeline and application code, to discuss chart-type
choices, and to edit the written report. All analytical decisions, the choice
of research questions, and verification of results are the group's own work.
"""
)

# --------------------------------------------------------------------------
# Data quality report
# --------------------------------------------------------------------------

st.markdown("## Data quality report")
st.caption(
    "Generated automatically by the preprocessing script, computing its figures "
    "from the dataset itself so it cannot fall out of date."
)

report_path = Path(__file__).resolve().parent.parent / "data" / "data_quality.md"
try:
    with st.expander("Read the full data quality report"):
        st.markdown(report_path.read_text(encoding="utf-8"))
except OSError:
    st.info("The data quality report is generated by `preprocessing/preprocess.py`.")

st.markdown("---")
st.caption(
    "Course project in Information Visualization. Data from football-data.co.uk "
    "via the datasets/football-datasets repository."
)
