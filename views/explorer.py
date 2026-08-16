"""
Dashboard 2 — League and Season Explorer.

Comparison layer. Where dashboard 1 argues a case, this page lets the
user interrogate it: pick any measure, see it across leagues and seasons
as a heatmap, and click a cell to drill into that league-season.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import charts as C
from lib import data as D
from lib import theme as T

D.sidebar_filters()

matches = D.apply_filters(D.load_matches())

T.eyebrow("Dashboard 2 of 6 · Evolution")
st.markdown("# Evolution of the Big Five")
T.lede(
    "Twenty seasons, five leagues, one measure at a time. The heatmap shows "
    "every league-season combination at once, so unusual seasons stand out "
    "against their neighbours rather than having to be hunted for. Select a "
    "cell to inspect that season in detail."
)

if matches.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

# --------------------------------------------------------------------------
# Headline figures for the current selection
# --------------------------------------------------------------------------

_cards = (
    matches["home_yellows"] + matches["away_yellows"]
    + matches["home_reds"] + matches["away_reds"]
).astype("Float64")
_close = (matches["goal_difference"].abs() <= 1)

T.stat_row([
    {"label": "Matches", "value": f"{len(matches):,}",
     "note": f"{matches['season'].nunique()} seasons"},
    {"label": "Goals per match", "value": f"{matches['total_goals'].mean():.2f}",
     "tone": "amber", "note": "both teams"},
    {"label": "Home win rate", "value": f"{matches['is_home_win'].mean() * 100:.1f}%",
     "tone": "amber", "note": "share of matches"},
    {"label": "Cards per match", "value": f"{_cards.mean():.2f}",
     "tone": "steel", "note": "yellow and red"},
    {"label": "Close matches", "value": f"{_close.mean() * 100:.1f}%",
     "tone": "steel", "note": "decided by ≤1 goal"},
])

# --------------------------------------------------------------------------
# Measure selection
# --------------------------------------------------------------------------

MEASURES = {
    "Home win rate": dict(col="is_home_win", agg="rate", unit="%",
                          desc="Share of matches won by the home team."),
    "Away win rate": dict(col="is_away_win", agg="rate", unit="%",
                          desc="Share of matches won by the away team."),
    "Draw rate": dict(col="is_draw", agg="rate", unit="%",
                      desc="Share of matches drawn."),
    "Goals per match": dict(col="total_goals", agg="mean", unit="",
                            desc="Combined goals scored by both teams."),
    "Home goal difference": dict(col="goal_difference", agg="mean", unit="",
                                 desc="Home goals minus away goals, per match."),
    "Booking bias": dict(col="yellows_diff", agg="mean_neg", unit="",
                         desc="Away yellow cards minus home yellow cards, per match."),
    "Shots difference": dict(col="shots_diff", agg="mean", unit="",
                             desc="Home shots minus away shots, per match."),
    "Cards per match": dict(col="cards", agg="cards", unit="",
                            desc="Total yellow and red cards shown to both teams."),
    "Close match rate": dict(col="close", agg="close", unit="%",
                             desc="Share of matches decided by one goal or fewer — a measure of competitive balance."),
}

c1, c2 = st.columns([2, 1])
with c1:
    measure = st.selectbox("Measure", list(MEASURES), index=0)
with c2:
    normalise = st.toggle(
        "Centre on each league's own average", value=False,
        help="Shows deviation from that league's typical value, so leagues with "
             "different baselines can be compared on shape rather than level.",
    )

spec = MEASURES[measure]
st.caption(spec["desc"])


def compute(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = df.groupby(by, observed=True)
    if spec["agg"] == "rate":
        out = g[spec["col"]].mean().mul(100)
    elif spec["agg"] == "close":
        out = (
            df.assign(_c=(df["goal_difference"].abs() <= 1))
            .groupby(by, observed=True)["_c"].mean().mul(100)
        )
    elif spec["agg"] == "cards":
        out = (
            g[["home_yellows", "away_yellows", "home_reds", "away_reds"]]
            .mean().sum(axis=1)
        )
    elif spec["agg"] == "mean_neg":
        out = g[spec["col"]].mean().mul(-1)  # away minus home
    else:
        out = g[spec["col"]].mean()
    out = out.astype(float).rename("value").reset_index()
    out["matches"] = g.size().values
    return out


# --------------------------------------------------------------------------
# Heatmap
# --------------------------------------------------------------------------

grid = compute(matches, ["league_short", "season"])
seasons = D.season_axis(matches)
leagues = [l for l in D.LEAGUE_ORDER if l in set(grid["league_short"])]

pivot = (
    grid.pivot(index="league_short", columns="season", values="value")
    .reindex(index=leagues, columns=seasons)
)
counts = (
    grid.pivot(index="league_short", columns="season", values="matches")
    .reindex(index=leagues, columns=seasons)
)

if normalise:
    pivot = pivot.sub(pivot.mean(axis=1), axis=0)
    colorbar_title = "Deviation"
    scale = [[0, T.EMPTY], [0.5, "#F2F2EE"], [1, T.CROWD]]
    zmid = 0.0
else:
    colorbar_title = measure
    scale = [[0, "#EDF2F5"], [0.55, T.CROWD_LIGHT], [1, "#8A4C10"]]
    zmid = None

heat = go.Figure(go.Heatmap(
    z=pivot.values,
    x=list(pivot.columns),
    y=list(pivot.index),
    colorscale=scale,
    zmid=zmid,
    customdata=counts.values,
    hovertemplate=(
        "<b>%{y}</b> · %{x}<br>"
        + measure + ": %{z:.2f}" + spec["unit"]
        + "<br>%{customdata:,} matches<extra></extra>"
    ),
    colorbar=dict(
        title=dict(text=colorbar_title, font=dict(size=11)),
        thickness=12, len=0.85, outlinewidth=0,
        tickfont=dict(family=T.FONT_MONO, size=10),
    ),
    xgap=2, ygap=2,
))
heat.update_layout(
    title=f"{measure} by league and season",
    xaxis_title="Season", yaxis_title="",
    height=340, hovermode="closest",
)
heat.update_xaxes(tickangle=-45, showgrid=False)
heat.update_yaxes(showgrid=False, autorange="reversed")

event = st.plotly_chart(
    heat, width="stretch",
    key="heatmap", on_select="rerun", selection_mode="points",
)
T.readout(
    "Darker cells are higher values. The empty-stadium seasons (2019/20 and "
    "2020/21) read as a visible band across all five leagues on the home-win and "
    "booking-bias measures — a coincidence would not line up this neatly. "
    "Click any cell to inspect that league-season below."
)

# --------------------------------------------------------------------------
# Trend lines
# --------------------------------------------------------------------------

st.markdown("## Trends over time")

trend = go.Figure()
for league in leagues:
    sub = grid[grid["league_short"] == league].set_index("season").reindex(seasons).reset_index()
    trend.add_trace(go.Scatter(
        x=sub["season"], y=sub["value"], name=league, mode="lines+markers",
        line=dict(width=2, color=T.LEAGUE_COLORS.get(league)),
        marker=dict(size=5),
        hovertemplate="%{y:.2f}" + spec["unit"] + "<extra>" + league + "</extra>",
    ))

C.add_covid_band(trend, seasons)
trend.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
trend.update_layout(
    title=f"{measure} over time",
    xaxis_title="Season", yaxis_title=measure + (f" ({spec['unit']})" if spec["unit"] else ""),
    height=420,
)
st.plotly_chart(trend, width="stretch")

# --------------------------------------------------------------------------
# Result composition
# --------------------------------------------------------------------------

st.markdown("## What results look like over time")

comp = (
    matches.groupby("season", observed=True)
    .agg(home=("is_home_win", "mean"), draw=("is_draw", "mean"),
         away=("is_away_win", "mean"), n=("match_id", "size"))
    .reset_index().set_index("season").reindex(seasons).reset_index()
)

stack = go.Figure()
for key, label, colour in [
    ("home", "Home win", T.CROWD),
    ("draw", "Draw", T.MUTED),
    ("away", "Away win", T.EMPTY),
]:
    stack.add_trace(go.Scatter(
        x=comp["season"], y=comp[key].astype(float) * 100,
        name=label, mode="lines", stackgroup="one",
        line=dict(width=0.5, color=colour),
        fillcolor=colour,
        hovertemplate="%{y:.1f}%<extra>" + label + "</extra>",
    ))

C.add_covid_band(stack, seasons, label=False)
stack.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
stack.update_layout(
    title="Composition of results by season",
    xaxis_title="Season", yaxis_title="Share of matches (%)",
    height=400, hovermode="x unified",
)
stack.update_yaxes(ticksuffix="%", range=[0, 100])
st.plotly_chart(stack, width="stretch")
T.readout(
    "The amber band is home wins. Its narrowing across the shaded empty-stadium "
    "seasons, and the corresponding widening of the steel-blue away band, is the "
    "same finding as Dashboard 1 expressed as a share of all outcomes."
)

# --------------------------------------------------------------------------
# Competitive balance
# --------------------------------------------------------------------------

st.markdown("## Which league is the most competitive?")
T.lede(
    "A match decided by one goal or fewer is a close match. The higher the "
    "share, the less predictable the league."
)

bal = (
    matches.assign(_c=(matches["goal_difference"].abs() <= 1))
    .groupby("league_short", observed=True)
    .agg(close=("_c", "mean"), n=("match_id", "size"))
    .reset_index().sort_values("close")
)
bal["close"] = bal["close"].astype(float) * 100

rank = go.Figure(go.Bar(
    x=bal["close"], y=bal["league_short"], orientation="h",
    marker=dict(color=[T.LEAGUE_COLORS.get(l, T.MUTED) for l in bal["league_short"]]),
    text=[f"{v:.1f}%" for v in bal["close"]],
    textposition="outside",
    textfont=dict(family=T.FONT_MONO, size=12),
    hovertemplate="%{y}<br>%{x:.1f}% of matches decided by ≤1 goal"
                  "<br>%{customdata:,} matches<extra></extra>",
    customdata=bal["n"],
))
rank.update_layout(
    title="Share of matches decided by one goal or fewer",
    xaxis_title="Close matches (% of all matches)", yaxis_title="",
    height=320, showlegend=False, hovermode="closest", bargap=0.35,
)
rank.update_xaxes(ticksuffix="%")
st.plotly_chart(rank, width="stretch")
T.readout(
    "A higher share means more matches were decided by a single goal, which is "
    "usually read as greater competitive balance — though it also reflects how "
    "much a league scores overall, since high-scoring leagues produce wider margins."
)

# --------------------------------------------------------------------------
# Drill-down on the selected cell
# --------------------------------------------------------------------------

st.markdown("## Season detail")

selection = (event or {}).get("selection", {}).get("points", [])
if selection:
    sel_league = selection[0]["y"]
    sel_season = selection[0]["x"]
else:
    sel_league, sel_season = leagues[0], seasons[-1]
    st.caption("No cell selected — showing the most recent season of the first league.")

detail = matches[
    (matches["league_short"] == sel_league) & (matches["season"] == sel_season)
]

if detail.empty:
    st.info(f"No matches for {sel_league} in {sel_season} under the current filters.")
    st.stop()

st.markdown(f"### {sel_league} · {sel_season}")

T.stat_row([
    {"label": "Matches", "value": f"{len(detail):,}", "note": ""},
    {"label": "Home wins", "value": f"{detail['is_home_win'].mean() * 100:.1f}%", "tone": "amber", "note": ""},
    {"label": "Draws", "value": f"{detail['is_draw'].mean() * 100:.1f}%", "note": ""},
    {"label": "Away wins", "value": f"{detail['is_away_win'].mean() * 100:.1f}%", "tone": "steel", "note": ""},
    {"label": "Goals per match", "value": f"{detail['total_goals'].mean():.2f}", "note": ""},
])

d1, d2 = st.columns(2)

with d1:
    tm = D.load_team_matches()
    tm = tm[(tm["league_short"] == sel_league) & (tm["season"] == sel_season)]
    table = (
        tm.groupby(["team", "venue"], observed=True)
        .agg(points=("points", "sum"), played=("match_id", "size"))
        .reset_index()
        .pivot(index="team", columns="venue", values="points")
        .fillna(0)
    )
    for col in ("Home", "Away"):
        if col not in table:
            table[col] = 0
    table["Total"] = table["Home"] + table["Away"]
    table["Home share"] = (table["Home"] / table["Total"].replace(0, pd.NA) * 100).round(1)
    table = table.sort_values("Total", ascending=False)

    st.markdown("**Points won at home and away**")
    st.dataframe(
        table[["Home", "Away", "Total", "Home share"]].astype(float).round(1),
        width="stretch", height=330,
        column_config={
            "Home share": st.column_config.NumberColumn(
                "Home share (%)", help="Percentage of the team's points won at home.",
                format="%.1f%%",
            )
        },
    )

with d2:
    dist = (
        detail["goal_difference"].astype("Int16").value_counts().sort_index().reset_index()
    )
    dist.columns = ["goal_difference", "count"]
    colors = [
        T.CROWD if v > 0 else (T.EMPTY if v < 0 else T.MUTED)
        for v in dist["goal_difference"]
    ]
    bar = go.Figure(go.Bar(
        x=dist["goal_difference"], y=dist["count"],
        marker=dict(color=colors),
        hovertemplate="Goal difference %{x}<br>%{y:,} matches<extra></extra>",
    ))
    bar.update_layout(
        title="Match outcomes by goal difference",
        xaxis_title="Home goals − away goals",
        yaxis_title="Matches", height=330, showlegend=False, hovermode="closest",
    )
    st.plotly_chart(bar, width="stretch")
    T.readout(
        "Amber bars are home wins, steel blue away wins, grey draws. "
        "An asymmetric distribution is home advantage made visible."
    )
