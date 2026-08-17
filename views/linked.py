"""
Linked Views — coordinated multiple views with cross-filtering.

Four charts over one dataset, each of which both *drives* and *responds
to* a shared selection. Clicking a league in the ranking, a cell in the
league-season grid, or a set of points in the timeline updates every
other view on the page.

The selection lives in `st.session_state`, so each chart reads the same
state and writes to it, rather than one chart owning the filter and the
rest following. That is what makes this coordinated views rather than a
master-detail layout.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import charts as C
from lib import data as D
from lib import theme as T

D.sidebar_filters()

base = D.apply_filters(D.load_matches())
team_matches = D.apply_filters(D.load_team_matches())

# --------------------------------------------------------------------------
# Shared selection state
# --------------------------------------------------------------------------

K_SEL_LEAGUES = "xf_leagues"
K_SEL_SEASONS = "xf_seasons"

st.session_state.setdefault(K_SEL_LEAGUES, [])
st.session_state.setdefault(K_SEL_SEASONS, [])


def toggle(key: str, value) -> None:
    """Add or remove a value from a selection list."""
    current = list(st.session_state[key])
    if value in current:
        current.remove(value)
    else:
        current.append(value)
    st.session_state[key] = current


def clear_all() -> None:
    st.session_state[K_SEL_LEAGUES] = []
    st.session_state[K_SEL_SEASONS] = []


def selected(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the cross-filter selection to any frame."""
    out = df
    if st.session_state[K_SEL_LEAGUES]:
        out = out[out["league_short"].isin(st.session_state[K_SEL_LEAGUES])]
    if st.session_state[K_SEL_SEASONS]:
        out = out[out["season"].isin(st.session_state[K_SEL_SEASONS])]
    return out


T.eyebrow("Dashboard 7 of 7 · Linked views")
st.markdown("# Linked views")
T.lede(
    "Four views of the same data, wired together. Click a league, a season cell, or "
    "a run of seasons in any chart and every other chart follows. Click the same "
    "element again to release it."
)

if base.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

seasons = D.season_axis(base)
leagues = [l for l in D.LEAGUE_ORDER if l in set(base["league_short"])]

# --------------------------------------------------------------------------
# Active selection banner
# --------------------------------------------------------------------------

sel_leagues = st.session_state[K_SEL_LEAGUES]
sel_seasons = st.session_state[K_SEL_SEASONS]
view = selected(base)
view_teams = selected(team_matches)

bar_l, bar_r = st.columns([4, 1])
with bar_l:
    if sel_leagues or sel_seasons:
        parts = []
        if sel_leagues:
            parts.append("<strong>Leagues:</strong> " + ", ".join(sel_leagues))
        if sel_seasons:
            shown = ", ".join(sorted(sel_seasons)[:6])
            if len(sel_seasons) > 6:
                shown += f" +{len(sel_seasons) - 6} more"
            parts.append("<strong>Seasons:</strong> " + shown)
        st.markdown(
            f'<div class="caveat">Active selection — {" · ".join(parts)}. '
            f"Showing {len(view):,} of {len(base):,} matches.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="caveat">No selection. Showing all {len(base):,} matches — '
            "click any chart element to filter every view.</div>",
            unsafe_allow_html=True,
        )
with bar_r:
    st.button("Clear selection", width="stretch", on_click=clear_all,
              disabled=not (sel_leagues or sel_seasons))

if view.empty:
    st.warning("That combination contains no matches. Clear the selection to continue.")
    st.stop()

# --------------------------------------------------------------------------
# View 1 and 2 — league ranking, and the grid
# --------------------------------------------------------------------------

MEASURES = {
    "Home win rate": ("is_home_win", "rate", "%"),
    "Goals per match": ("total_goals", "mean", ""),
    "Cards per match": ("cards", "cards", ""),
    "Close match rate": ("close", "close", "%"),
}
measure = st.selectbox("Measure", list(MEASURES), index=0)
col, kind, unit = MEASURES[measure]


def compute(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    if kind == "rate":
        out = df.groupby(by, observed=True)[col].mean().mul(100)
    elif kind == "close":
        out = (
            df.assign(_c=(df["goal_difference"].abs() <= 1))
            .groupby(by, observed=True)["_c"].mean().mul(100)
        )
    elif kind == "cards":
        out = (
            df.assign(_c=(df["home_yellows"] + df["away_yellows"]
                          + df["home_reds"] + df["away_reds"]).astype("Float64"))
            .groupby(by, observed=True)["_c"].mean()
        )
    else:
        out = df.groupby(by, observed=True)[col].mean()
    return out.astype(float).rename("value").reset_index()


left, right = st.columns([1, 1.4], gap="large")

# --- View 1: league ranking (click a bar to select a league) --------------
with left:
    st.markdown("#### By league")
    st.caption("Click a bar to select or release that league.")

    rank = compute(base, ["league_short"]).set_index("league_short").reindex(leagues).reset_index()
    highlight = [
        T.LEAGUE_COLORS.get(l, T.MUTED) if (not sel_leagues or l in sel_leagues)
        else "#D8DDD8"
        for l in rank["league_short"]
    ]

    rank_fig = go.Figure(go.Bar(
        x=rank["value"], y=rank["league_short"], orientation="h",
        marker=dict(color=highlight),
        hovertemplate="%{y}<br>%{x:.2f}" + unit + "<extra>click to filter</extra>",
    ))
    rank_fig.update_layout(
        title=f"{measure} by league", xaxis_title=measure, yaxis_title="",
        height=330, showlegend=False, bargap=0.35, hovermode="closest",
        margin=dict(t=52, b=8),
    )
    if unit:
        rank_fig.update_xaxes(ticksuffix=unit)
    rank_fig.update_yaxes(autorange="reversed")

    ev_rank = st.plotly_chart(
        rank_fig, width="stretch",
        key="xf_rank", on_select="rerun", selection_mode="points",
    )
    pts = (ev_rank or {}).get("selection", {}).get("points", [])
    if pts:
        toggle(K_SEL_LEAGUES, pts[0]["y"])
        st.rerun()

# --- View 2: league x season grid (click a cell to select both) ----------
with right:
    st.markdown("#### By league and season")
    st.caption("Click a cell to select that league and season together.")

    grid = compute(base, ["league_short", "season"])
    pivot = (
        grid.pivot(index="league_short", columns="season", values="value")
        .reindex(index=leagues, columns=seasons)
    )

    heat = go.Figure(go.Heatmap(
        z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
        colorscale=[[0, "#EDF2F5"], [0.55, T.CROWD_LIGHT], [1, "#8A4C10"]],
        hovertemplate="<b>%{y}</b> · %{x}<br>%{z:.2f}" + unit
                      + "<extra>click to filter</extra>",
        colorbar=dict(thickness=10, len=0.9, outlinewidth=0,
                      tickfont=dict(family=T.FONT_MONO, size=9)),
        xgap=2, ygap=2,
    ))
    heat.update_layout(
        title=f"{measure} by league and season", xaxis_title="", yaxis_title="",
        height=330, hovermode="closest", margin=dict(t=52, b=8),
    )
    heat.update_xaxes(tickangle=-45, showgrid=False, tickfont=dict(size=9))
    heat.update_yaxes(showgrid=False, autorange="reversed")

    ev_heat = st.plotly_chart(
        heat, width="stretch",
        key="xf_heat", on_select="rerun", selection_mode="points",
    )
    pts = (ev_heat or {}).get("selection", {}).get("points", [])
    if pts:
        st.session_state[K_SEL_LEAGUES] = [pts[0]["y"]]
        st.session_state[K_SEL_SEASONS] = [pts[0]["x"]]
        st.rerun()

# --------------------------------------------------------------------------
# View 3 — timeline (box-select a run of seasons)
# --------------------------------------------------------------------------

st.markdown("#### Over time")
st.caption(
    "Drag a box across the chart to select a run of seasons, or click a single point. "
    "Unselected leagues are greyed rather than hidden, so the selection stays in context."
)

trend = compute(base, ["league_short", "season"])
line = go.Figure()
for lg in leagues:
    sub = trend[trend["league_short"] == lg].set_index("season").reindex(seasons).reset_index()
    active = (not sel_leagues) or (lg in sel_leagues)
    line.add_trace(go.Scatter(
        x=sub["season"], y=sub["value"], name=lg, mode="lines+markers",
        line=dict(width=2.2 if active else 1,
                  color=T.LEAGUE_COLORS.get(lg) if active else "#D8DDD8"),
        marker=dict(size=6 if active else 4),
        opacity=1.0 if active else 0.55,
        hovertemplate="%{y:.2f}" + unit + "<extra>" + lg + "</extra>",
    ))

if sel_seasons:
    idx = [seasons.index(s) for s in sel_seasons if s in seasons]
    if idx:
        line.add_vrect(x0=min(idx) - 0.5, x1=max(idx) + 0.5,
                       fillcolor=T.CROWD, opacity=0.10, layer="below", line_width=0)

C.add_covid_band(line, seasons, label=False)
line.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
line.update_layout(
    title=f"{measure} over time", xaxis_title="Season", yaxis_title=measure,
    height=420, hovermode="closest", dragmode="select",
)
if unit:
    line.update_yaxes(ticksuffix=unit)

ev_line = st.plotly_chart(
    line, width="stretch",
    key="xf_line", on_select="rerun", selection_mode=("points", "box"),
)
pts = (ev_line or {}).get("selection", {}).get("points", [])
if pts:
    picked = sorted({p["x"] for p in pts})
    if picked != sorted(sel_seasons):
        st.session_state[K_SEL_SEASONS] = picked
        st.rerun()

# --------------------------------------------------------------------------
# View 4 — the selection in detail
# --------------------------------------------------------------------------

st.markdown("#### The current selection")

close_rate = float((view["goal_difference"].abs() <= 1).mean() * 100)
cards = (view["home_yellows"] + view["away_yellows"]
         + view["home_reds"] + view["away_reds"]).astype("Float64")

T.stat_row([
    {"label": "Matches", "value": f"{len(view):,}",
     "note": f"{len(view) / len(base) * 100:.0f}% of the filtered data"},
    {"label": "Home win rate", "value": f"{view['is_home_win'].mean() * 100:.1f}%",
     "tone": "amber", "note": ""},
    {"label": "Goals per match", "value": f"{view['total_goals'].mean():.2f}", "note": ""},
    {"label": "Cards per match", "value": f"{cards.mean():.2f}", "tone": "steel", "note": ""},
    {"label": "Close matches", "value": f"{close_rate:.1f}%", "tone": "steel",
     "note": "decided by ≤1 goal"},
])

d1, d2 = st.columns([1, 1], gap="large")

with d1:
    dist = view["goal_difference"].astype("Int16").value_counts().sort_index().reset_index()
    dist.columns = ["goal_difference", "count"]

    bar = go.Figure()
    for label, mask, colour in (
        ("Home win", dist["goal_difference"] > 0, T.CROWD),
        ("Draw", dist["goal_difference"] == 0, T.MUTED),
        ("Away win", dist["goal_difference"] < 0, T.EMPTY),
    ):
        part = dist[mask]
        if part.empty:
            continue
        bar.add_trace(go.Bar(
            x=part["goal_difference"], y=part["count"], name=label,
            marker=dict(color=colour),
            hovertemplate="Goal difference %{x}<br>%{y:,} matches<extra>"
                          + label + "</extra>",
        ))
    lo = int(dist["goal_difference"].min()) - 1
    hi = int(dist["goal_difference"].max()) + 1
    bar.update_layout(
        title="Outcomes in the selection",
        xaxis_title="Home goals − away goals", yaxis_title="Matches",
        height=340, barmode="overlay", hovermode="closest",
        xaxis=dict(range=[lo, hi], dtick=1), yaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(bar, width="stretch")

with d2:
    if not view_teams.empty:
        table = (
            view_teams.groupby("team", observed=True)
            .agg(played=("match_id", "size"), points=("points", "sum"),
                 goals=("goals", "sum"))
            .reset_index()
        )
        table = table[table["played"] >= 5]
        table["Points per match"] = (table["points"] / table["played"]).astype(float)
        table = table.sort_values("Points per match", ascending=False).head(12)

        st.markdown("**Strongest clubs in the selection**")
        st.dataframe(
            table[["team", "played", "Points per match"]]
            .rename(columns={"team": "Club", "played": "Matches"})
            .round(2),
            width="stretch", hide_index=True, height=340,
        )
        st.caption("Clubs with at least five matches in the current selection.")

T.readout(
    "Every view above reads from the same selection and writes back to it, so there "
    "is no single master chart: a league chosen in the ranking, in the grid, or in the "
    "timeline produces the same state. Greying rather than hiding unselected leagues "
    "keeps the comparison visible, which is the point of brushing — the selection is "
    "meant to be read against the whole, not in place of it."
)
