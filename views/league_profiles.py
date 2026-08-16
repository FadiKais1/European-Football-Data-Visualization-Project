"""
Dashboard 5 — League Profiles and Convergence.

Answers the fourth research question: which characteristics distinguish
Europe's Big Five leagues, and have those differences narrowed or
widened over twenty seasons?
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

matches = D.apply_filters(D.load_matches())

T.eyebrow("Dashboard 6 of 6 · Comparison")
st.markdown("# League profiles and convergence")
T.lede(
    "Each league has a reputation: Serie A tactical and foul-heavy, the "
    "Premier League fast and permissive, the Bundesliga high-scoring. This "
    "page tests those reputations against twenty seasons of evidence, and "
    "asks whether the leagues have grown more alike or more distinct."
)

if matches.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

# Match-level totals: league character is a property of the match as a
# whole, so home and away contributions are combined.
m = matches.copy()
m["Goals"] = m["total_goals"].astype("Float64")
m["Shots"] = (m["home_shots"] + m["away_shots"]).astype("Float64")
m["Shots on target"] = (m["home_shots_on_target"] + m["away_shots_on_target"]).astype("Float64")
m["Corners"] = (m["home_corners"] + m["away_corners"]).astype("Float64")
m["Fouls"] = (m["home_fouls"] + m["away_fouls"]).astype("Float64")
m["Yellow cards"] = (m["home_yellows"] + m["away_yellows"]).astype("Float64")

METRICS = ["Goals", "Shots", "Shots on target", "Corners", "Fouls", "Yellow cards"]

# --------------------------------------------------------------------------
# 1. League fingerprints
# --------------------------------------------------------------------------

st.markdown("## What makes each league different")

era = st.select_slider(
    "Compare leagues over",
    options=D.season_axis(matches),
    value=(D.season_axis(matches)[0], D.season_axis(matches)[-1]),
    help="Narrow this to see how each league's character changed between eras.",
)
labels = D.season_axis(matches)
era_seasons = set(labels[labels.index(era[0]): labels.index(era[1]) + 1])
era_df = m[m["season"].isin(era_seasons)]

profile = era_df.groupby("league_short", observed=True)[METRICS].mean()
profile = profile.reindex([l for l in D.LEAGUE_ORDER if l in profile.index])

# Standardise each metric across leagues so quantities on different
# scales (2.7 goals, 28 fouls) can share one axis. Values are read as
# "standard deviations from the five-league average".
z = profile.copy()
for col in METRICS:
    sd = profile[col].std(ddof=0)
    z[col] = (profile[col] - profile[col].mean()) / sd if sd and sd > 0 else 0.0

view_mode = st.radio(
    "View",
    ["Dot plot", "Radar"],
    horizontal=True, label_visibility="collapsed",
    help="The dot plot is the default; radar is offered as an alternative shape comparison.",
)

if view_mode == "Radar":
    fig = go.Figure()
    closed = METRICS + [METRICS[0]]
    for league in z.index:
        vals = [float(z.loc[league, mt]) for mt in METRICS]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=closed,
            name=league, mode="lines+markers",
            line=dict(width=2, color=T.LEAGUE_COLORS.get(league)),
            marker=dict(size=6),
            hovertemplate="<b>" + league + "</b><br>%{theta}: %{r:+.2f} SD<extra></extra>",
        ))
    fig.update_layout(
        title=f"League fingerprints, {era[0]}–{era[1]} (radar view)",
        height=520,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                gridcolor=T.RULE, linecolor=T.RULE,
                tickfont=dict(family=T.FONT_MONO, size=10, color=T.MUTED),
            ),
            angularaxis=dict(
                gridcolor=T.RULE, linecolor=T.RULE,
                tickfont=dict(family=T.FONT_BODY, size=11, color=T.INK_SOFT),
            ),
        ),
    )
    st.plotly_chart(fig, width="stretch")
    T.readout(
        "Values are standard deviations from the five-league average, so the "
        "centre of the circle is not zero — negative values sit toward the middle. "
        "Radar is included because it makes a league's overall shape easy to "
        "recognise at a glance, but the dot plot is the default: radar encodes "
        "magnitude as area, which exaggerates differences, and the shape it draws "
        "changes if the axes are reordered. Compare the two views to see the effect."
    )
else:
    fig = go.Figure()

    # One row per metric, one marker per league.
    for i, metric in enumerate(METRICS):
        fig.add_shape(
            type="line", x0=-2.4, x1=2.4, y0=metric, y1=metric,
            line=dict(color=T.RULE, width=1), layer="below",
        )

    for league in z.index:
        fig.add_trace(go.Scatter(
            x=[z.loc[league, mt] for mt in METRICS],
            y=METRICS,
            mode="markers", name=league,
            marker=dict(size=13, color=T.LEAGUE_COLORS.get(league),
                        line=dict(width=1, color="white")),
            customdata=[[profile.loc[league, mt]] for mt in METRICS],
            hovertemplate=(
                "<b>" + league + "</b><br>%{y}: %{customdata[0]:.2f} per match"
                "<br>%{x:+.2f} SD from the five-league average<extra></extra>"
            ),
        ))

    fig.add_vline(x=0, line=dict(color=T.INK, width=1))
    fig.update_layout(
        title=f"League fingerprints, {era[0]}–{era[1]}",
        xaxis_title="Standard deviations from the five-league average",
        yaxis_title="",
        height=440, hovermode="closest",
    )
    fig.update_yaxes(autorange="reversed", showgrid=False)
    st.plotly_chart(fig, width="stretch")

    T.readout(
        "Each row is one characteristic, standardised so quantities on different "
        "scales share an axis; the vertical line is the five-league average. The "
        "dot plot is the default view because it keeps the mapping from value to "
        "position linear — switch to radar above to compare overall shapes instead."
    )

# Named readings, computed rather than asserted.
extremes = []
for metric in METRICS:
    hi = z[metric].idxmax()
    lo = z[metric].idxmin()
    extremes.append(
        f"**{metric}** — most: {hi} ({profile.loc[hi, metric]:.2f}), "
        f"least: {lo} ({profile.loc[lo, metric]:.2f})"
    )
st.markdown("\n\n".join(f"- {e}" for e in extremes))

# --------------------------------------------------------------------------
# 2. Convergence
# --------------------------------------------------------------------------

st.markdown("## Have the leagues grown more alike?")
T.lede(
    "If the five leagues are converging, the spread between them should "
    "shrink. Each line below is the standard deviation across the five league "
    "averages in a given season: a falling line means the leagues are becoming "
    "harder to tell apart on that characteristic."
)

season_league = (
    m.groupby(["season", "league_short"], observed=True)[METRICS].mean().reset_index()
)
spread = season_league.groupby("season")[METRICS].std(ddof=0)
seasons = D.season_axis(matches)
spread = spread.reindex(seasons)

# Express as a percentage of the first available season, so metrics with
# very different units can be compared on one axis.
show_relative = st.toggle(
    "Show as % of the earliest season", value=True,
    help="Turn off to see the spread in the original units of each metric.",
)

conv = go.Figure()
palette = [T.CROWD, T.EMPTY, T.POSITIVE, T.NEGATIVE, "#8E5A9B", T.MUTED]

for i, metric in enumerate(METRICS):
    series = spread[metric]
    if show_relative:
        base = series.dropna()
        if base.empty:
            continue
        series = series / base.iloc[0] * 100
    conv.add_trace(go.Scatter(
        x=spread.index, y=series, name=metric, mode="lines+markers",
        line=dict(width=2, color=palette[i % len(palette)]),
        marker=dict(size=4),
        hovertemplate="%{y:.1f}" + ("%" if show_relative else "") + "<extra>" + metric + "</extra>",
    ))

if show_relative:
    conv.add_hline(y=100, line=dict(color=T.MUTED, width=1, dash="dot"),
                   annotation_text="Spread in the first season",
                   annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED))

C.add_covid_band(conv, seasons, label=False)
conv.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
conv.update_layout(
    title="Spread between the five leagues, by season",
    xaxis_title="Season",
    yaxis_title="Spread as % of first season" if show_relative else "Standard deviation across leagues",
    height=460,
)
st.plotly_chart(conv, width="stretch")

first_valid = spread.dropna(how="all").index[0]
last_valid = spread.dropna(how="all").index[-1]
changes = []
for metric in METRICS:
    a, b = spread.loc[first_valid, metric], spread.loc[last_valid, metric]
    if pd.notna(a) and pd.notna(b) and a > 0:
        changes.append((metric, (b - a) / a * 100))
changes.sort(key=lambda x: x[1])

if changes:
    narrowed = [c for c in changes if c[1] < 0]
    T.readout(
        f"Between {first_valid} and {last_valid}, the gap between leagues narrowed on "
        f"{len(narrowed)} of {len(changes)} characteristics. The sharpest convergence is in "
        f"{changes[0][0].lower()} ({changes[0][1]:+.0f}%), and the least is in "
        f"{changes[-1][0].lower()} ({changes[-1][1]:+.0f}%). Disciplinary and activity "
        "measures have converged strongly; scoring has not, which suggests the leagues "
        "now referee and play at similar intensity while retaining distinct attacking identities."
    )

T.caveat(
    "<strong>One caveat on the earliest season.</strong> Ligue 1 fouls were never "
    "recorded in 2006/07, so the fouls spread for that season is computed across four "
    "leagues rather than five and is not directly comparable with later seasons. The "
    "convergence conclusion does not rest on it: the same downward trend is visible "
    "from 2007/08 onward."
)

# --------------------------------------------------------------------------
# 3. Metric over time, league by league
# --------------------------------------------------------------------------

st.markdown("## Trace a single characteristic")

metric = st.selectbox("Characteristic", METRICS, index=0)

trend = go.Figure()
for league in [l for l in D.LEAGUE_ORDER if l in set(season_league["league_short"])]:
    sub = (
        season_league[season_league["league_short"] == league]
        .set_index("season").reindex(seasons).reset_index()
    )
    trend.add_trace(go.Scatter(
        x=sub["season"], y=sub[metric].astype(float), name=league,
        mode="lines+markers",
        line=dict(width=2, color=T.LEAGUE_COLORS.get(league)),
        marker=dict(size=5), connectgaps=False,
        hovertemplate="%{y:.2f} per match<extra>" + league + "</extra>",
    ))

C.add_covid_band(trend, seasons, label=False)
trend.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
trend.update_layout(
    title=f"{metric} per match, by league",
    xaxis_title="Season", yaxis_title=f"{metric} per match", height=440,
)
st.plotly_chart(trend, width="stretch")
T.readout(
    "Lines that start far apart and finish bunched together are the convergence "
    "above, seen one characteristic at a time. Gaps indicate seasons where the "
    "statistic was not recorded rather than seasons with a value of zero."
)

# --------------------------------------------------------------------------
# 4. Profile table
# --------------------------------------------------------------------------

st.markdown("## League averages")

table = profile.copy()
table.insert(0, "Matches", era_df.groupby("league_short", observed=True).size().reindex(profile.index))
st.dataframe(
    table.round(2), width="stretch",
    column_config={
        c: st.column_config.NumberColumn(c, format="%.2f") for c in METRICS
    },
)
st.caption(
    f"Averages per match, {era[0]}–{era[1]}. Fouls exclude Ligue 1 2006/07, "
    "where the statistic was never recorded."
)
