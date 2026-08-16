"""
Dashboard 3 — Team Deep-Dive.

Drill-down layer. Home advantage is an average across thousands of
matches; this page asks whether it holds for a specific club, and shows
which clubs lost the most when their stadium fell silent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import charts as C
from lib import data as D
from lib import theme as T

D.sidebar_filters()

tm_all = D.load_team_matches()
tm = D.apply_filters(tm_all)

T.eyebrow("Dashboard 4 of 6 · Drill-down")
st.markdown("# Team deep-dive")
T.lede(
    "An average hides variation. Some clubs are transformed by their home "
    "ground and others barely notice it. This page compares a single club's "
    "home and away record over time, then ranks every club by how much of its "
    "home advantage survived the empty-stadium period."
)

if tm.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

# --------------------------------------------------------------------------
# Team picker (remembers the choice across pages)
# --------------------------------------------------------------------------

teams = sorted(tm["team"].dropna().unique().tolist())
prior = st.session_state.get(D.K_TEAM)
default_idx = teams.index(prior) if prior in teams else 0

col1, col2 = st.columns([2, 3])
with col1:
    team = st.selectbox("Club", teams, index=default_idx)
    st.session_state[D.K_TEAM] = team
with col2:
    min_matches = st.slider(
        "Minimum matches per club (ranking below)", 50, 500, 150, step=25,
        help="Clubs with few matches produce unstable percentages. "
             "Raise this to keep the ranking meaningful.",
    )

club = tm[tm["team"] == team]

home = club[club["venue"] == "Home"]
away = club[club["venue"] == "Away"]

hw = float(home["is_win"].mean() * 100) if len(home) else np.nan
aw = float(away["is_win"].mean() * 100) if len(away) else np.nan

T.stat_row([
    {"label": "Matches", "value": f"{len(club):,}", "note": f"{club['season'].nunique()} seasons"},
    {"label": "Win rate at home", "value": f"{hw:.1f}%", "tone": "amber", "note": f"{len(home):,} matches"},
    {"label": "Win rate away", "value": f"{aw:.1f}%", "tone": "steel", "note": f"{len(away):,} matches"},
    {"label": "Home advantage", "value": f"{hw - aw:+.1f}pp", "tone": "amber",
     "note": "percentage points"},
    {"label": "Goals per match at home", "value": f"{home['goals'].mean():.2f}", "note": ""},
])

# --------------------------------------------------------------------------
# Home vs away over time
# --------------------------------------------------------------------------

st.markdown(f"## {team} — home and away, season by season")

metric_choice = st.radio(
    "Measure", ["Win rate", "Points per match", "Goals scored", "Goals conceded"],
    horizontal=True, label_visibility="collapsed",
)
COLS = {
    "Win rate": ("is_win", 100.0, "Win rate (%)"),
    "Points per match": ("points", 1.0, "Points per match"),
    "Goals scored": ("goals", 1.0, "Goals per match"),
    "Goals conceded": ("goals_conceded", 1.0, "Goals conceded per match"),
}
col, mult, ylab = COLS[metric_choice]

seasons = D.season_axis(club)
series = (
    club.groupby(["season", "venue"], observed=True)[col]
    .mean().mul(mult).astype(float).rename("value").reset_index()
)

fig = go.Figure()
for venue in ["Home", "Away"]:
    sub = series[series["venue"] == venue].set_index("season").reindex(seasons).reset_index()
    fig.add_trace(go.Scatter(
        x=sub["season"], y=sub["value"], name=venue, mode="lines+markers",
        line=dict(width=2.5, color=T.VENUE_COLORS[venue]),
        marker=dict(size=6),
        connectgaps=False,
        hovertemplate="%{y:.2f}<extra>" + venue + "</extra>",
    ))

C.add_covid_band(fig, seasons)
fig.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
fig.update_layout(
    title=f"{team}: {metric_choice.lower()} at home versus away",
    xaxis_title="Season", yaxis_title=ylab, height=420,
)
st.plotly_chart(fig, width="stretch")
T.readout(
    "Gaps in the lines are seasons the club spent in another division — the data "
    "covers only the top flight, so promotion and relegation appear as breaks "
    "rather than as zeros."
)

# --------------------------------------------------------------------------
# The club under each crowd condition
# --------------------------------------------------------------------------

st.markdown("## The same club, with and without a crowd")

cc = (
    club.groupby(["crowd_status", "venue"], observed=True)
    .agg(win_rate=("is_win", lambda s: float(s.mean() * 100)),
         matches=("match_id", "size"))
    .reset_index()
)

order = [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST]
grouped = go.Figure()
for venue in ["Home", "Away"]:
    sub = cc[cc["venue"] == venue].set_index("crowd_status").reindex(order).reset_index()
    grouped.add_trace(go.Bar(
        x=sub["crowd_status"], y=sub["win_rate"], name=venue,
        marker=dict(color=T.VENUE_COLORS[venue]),
        hovertemplate="%{y:.1f}% wins<br>%{customdata:,} matches<extra>" + venue + "</extra>",
        customdata=sub["matches"].fillna(0),
    ))
grouped.update_layout(
    title=f"{team}: win rate by venue and crowd conditions",
    xaxis_title="", yaxis_title="Win rate (%)",
    height=380, barmode="group", bargap=0.3, hovermode="closest",
)
grouped.update_yaxes(ticksuffix="%")
st.plotly_chart(grouped, width="stretch")

small = cc[cc["matches"] < 20]
if not small.empty:
    T.readout(
        "Some bars here rest on fewer than 20 matches — the empty-stadium window was "
        "short, so a single club's figures for it are noisy. The league-wide view on "
        "dashboard 1 is the reliable version of this comparison; this one shows "
        "whether a specific club followed the pattern."
    )

# --------------------------------------------------------------------------
# Ranking: who lost most when the crowds went
# --------------------------------------------------------------------------

st.markdown("## Which clubs depended on their crowd most?")
T.lede(
    "For every club, the size of its home advantage before COVID and during the "
    "empty-stadium period. Clubs far below the diagonal lost the most when their "
    "supporters were locked out."
)

def advantage(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby(["team", "venue"], observed=True)
        .agg(win=("is_win", "mean"), n=("match_id", "size"))
        .reset_index()
        .pivot(index="team", columns="venue", values=["win", "n"])
    )
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    return g


pre = advantage(tm[tm["crowd_status"] == T.CROWD_PRE])
emp = advantage(tm[tm["crowd_status"] == T.CROWD_EMPTY])

joined = pre.join(emp, lsuffix="_pre", rsuffix="_emp", how="inner")
needed = ["win_Home_pre", "win_Away_pre", "win_Home_emp", "win_Away_emp",
          "n_Home_pre", "n_Home_emp"]

if not all(c in joined.columns for c in needed):
    st.info("Not enough data under the current filters to build the ranking.")
else:
    joined = joined.dropna(subset=needed)
    joined["adv_pre"] = (joined["win_Home_pre"] - joined["win_Away_pre"]) * 100
    joined["adv_emp"] = (joined["win_Home_emp"] - joined["win_Away_emp"]) * 100
    joined["change"] = joined["adv_emp"] - joined["adv_pre"]
    joined["total_home"] = joined["n_Home_pre"] + joined["n_Home_emp"]

    elig = joined[joined["n_Home_pre"] >= min_matches / 2].reset_index()

    if elig.empty:
        st.info("No clubs meet the minimum-matches threshold. Lower the slider.")
    else:
        league_of = tm.drop_duplicates("team").set_index("team")["league_short"]
        elig["league"] = elig["team"].map(league_of)

        scatter = go.Figure()
        for league, sub in elig.groupby("league", observed=True):
            scatter.add_trace(go.Scatter(
                x=sub["adv_pre"], y=sub["adv_emp"], name=str(league),
                mode="markers",
                marker=dict(size=9, color=T.LEAGUE_COLORS.get(str(league)),
                            line=dict(width=0.5, color="white")),
                text=sub["team"],
                hovertemplate=(
                    "<b>%{text}</b><br>With crowds: %{x:+.1f}pp"
                    "<br>Empty: %{y:+.1f}pp<extra></extra>"
                ),
            ))

        lo = float(min(elig["adv_pre"].min(), elig["adv_emp"].min())) - 3
        hi = float(max(elig["adv_pre"].max(), elig["adv_emp"].max())) + 3
        scatter.add_trace(go.Scatter(
            x=[lo, hi], y=[lo, hi], mode="lines", name="No change",
            line=dict(color=T.MUTED, width=1, dash="dash"),
            hoverinfo="skip",
        ))

        if team in set(elig["team"]):
            row = elig[elig["team"] == team].iloc[0]
            scatter.add_annotation(
                x=row["adv_pre"], y=row["adv_emp"], text=team,
                showarrow=True, arrowhead=0, arrowcolor=T.INK, ax=28, ay=-28,
                font=dict(family=T.FONT_BODY, size=12, color=T.INK),
                bgcolor="rgba(255,255,255,.85)", bordercolor=T.RULE,
            )

        scatter.update_layout(
            title="Home advantage before COVID versus during empty stadiums",
            xaxis_title="Home advantage with crowds (percentage points)",
            yaxis_title="Home advantage in empty stadiums (percentage points)",
            height=520, hovermode="closest",
        )
        st.plotly_chart(scatter, width="stretch")
        T.readout(
            "The dashed line marks no change. Points below it are clubs whose home "
            "advantage shrank without supporters; the majority of clubs sit below it, "
            "which is the same finding as dashboard 1 seen one club at a time. "
            f"{team} is labelled."
        )

        st.markdown("### Biggest losses of home advantage")
        rank = (
            elig.sort_values("change")
            .loc[:, ["team", "league", "adv_pre", "adv_emp", "change"]]
            .head(15)
            .rename(columns={
                "team": "Club", "league": "League",
                "adv_pre": "With crowds (pp)",
                "adv_emp": "Empty stadiums (pp)",
                "change": "Change (pp)",
            })
        )
        st.dataframe(
            rank.round(1), width="stretch", hide_index=True, height=400,
        )
        T.caveat(
            "<strong>Read the ranking cautiously.</strong> The empty-stadium window "
            "covers roughly one and a half seasons, so each club contributes only a "
            "few dozen home matches to the vertical axis. Individual positions are "
            "noisy; the reliable signal is that most clubs sit below the diagonal, "
            "not the precise order of the table."
        )
