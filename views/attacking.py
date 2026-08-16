"""
Attacking and Efficiency.

Answers the second research question: how have attacking characteristics
and scoring efficiency changed over time across the five leagues?

Ported and extended from the group's Tableau worksheets
"04 - Attacking Profile" and "07 - HT FT Transition", reusing the
Shot Accuracy % and Conversion Rate % calculations defined there.
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

T.eyebrow("Dashboard 3 of 6 · Attacking")
st.markdown("# Attacking and efficiency")
T.lede(
    "Volume and efficiency are different questions. A league can take more "
    "shots without scoring more, or score more from fewer chances. This "
    "dashboard separates how much attacking happens from how well it is "
    "converted, and ends with what a half-time lead is actually worth."
)

if matches.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

m = matches.copy()
m["shots"] = (m["home_shots"] + m["away_shots"]).astype("Float64")
m["sot"] = (m["home_shots_on_target"] + m["away_shots_on_target"]).astype("Float64")
m["goals"] = m["total_goals"].astype("Float64")

# --------------------------------------------------------------------------
# Headline figures
# --------------------------------------------------------------------------

tot_shots = float(m["shots"].sum())
tot_sot = float(m["sot"].sum())
tot_goals = float(m["goals"].sum())

T.stat_row([
    {"label": "Goals per match", "value": f"{m['goals'].mean():.2f}", "tone": "amber",
     "note": f"{len(m):,} matches"},
    {"label": "Shots per match", "value": f"{m['shots'].mean():.1f}", "note": "both teams"},
    {"label": "Shot accuracy",
     "value": f"{tot_sot / tot_shots * 100:.1f}%" if tot_shots else "—",
     "tone": "steel", "note": "shots on target ÷ shots"},
    {"label": "Conversion rate",
     "value": f"{tot_goals / tot_shots * 100:.1f}%" if tot_shots else "—",
     "tone": "steel", "note": "goals ÷ shots"},
])

# --------------------------------------------------------------------------
# 1. Volume versus efficiency over time
# --------------------------------------------------------------------------

st.markdown("## Volume and efficiency, season by season")

measure = st.radio(
    "Measure",
    ["Goals per match", "Shots per match", "Shots on target per match",
     "Shot accuracy %", "Conversion rate %"],
    horizontal=True, label_visibility="collapsed",
)

seasons = D.season_axis(matches)


def by_season_league(df: pd.DataFrame) -> pd.DataFrame:
    """Season-league aggregates for each attacking measure.

    Ratios are computed from summed totals rather than as a mean of
    per-match ratios: a match with 4 shots and a match with 30 should not
    carry equal weight in a league's accuracy figure.
    """
    g = (
        df.groupby(["season", "league_short"], observed=True)
        .agg(goals=("goals", "sum"), shots=("shots", "sum"),
             sot=("sot", "sum"), matches=("match_id", "size"))
        .reset_index()
    )
    g["Goals per match"] = g["goals"] / g["matches"]
    g["Shots per match"] = g["shots"] / g["matches"]
    g["Shots on target per match"] = g["sot"] / g["matches"]
    g["Shot accuracy %"] = g["sot"] / g["shots"].where(g["shots"] > 0) * 100
    g["Conversion rate %"] = g["goals"] / g["shots"].where(g["shots"] > 0) * 100
    return g


agg = by_season_league(m)
suffix = "%" if measure.endswith("%") else ""

fig = go.Figure()
for league in [l for l in D.LEAGUE_ORDER if l in set(agg["league_short"])]:
    sub = (
        agg[agg["league_short"] == league]
        .set_index("season").reindex(seasons).reset_index()
    )
    fig.add_trace(go.Scatter(
        x=sub["season"], y=sub[measure].astype(float), name=league,
        mode="lines+markers",
        line=dict(width=2, color=T.LEAGUE_COLORS.get(league)),
        marker=dict(size=5), connectgaps=False,
        hovertemplate="%{y:.2f}" + suffix + "<extra>" + league + "</extra>",
    ))

C.add_covid_band(fig, seasons, label=False)
fig.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
fig.update_layout(
    title=f"{measure}, by league and season",
    xaxis_title="Season", yaxis_title=measure, height=440,
)
if suffix:
    fig.update_yaxes(ticksuffix="%")
st.plotly_chart(fig, width="stretch")

T.readout(
    "Accuracy and conversion are computed from season totals rather than by "
    "averaging per-match ratios, so a match with four shots does not count as "
    "heavily as one with thirty. Switching between volume measures and "
    "efficiency measures shows that the two do not move together."
)

# --------------------------------------------------------------------------
# 2. Volume against efficiency
# --------------------------------------------------------------------------

st.markdown("## More shots, or better shots?")
T.lede(
    "Each point is one league-season. The horizontal axis is how much a league "
    "shoots; the vertical axis is how often those shots become goals. If volume "
    "and efficiency were the same thing, the points would form a rising line."
)

scatter = go.Figure()
for league in [l for l in D.LEAGUE_ORDER if l in set(agg["league_short"])]:
    sub = agg[agg["league_short"] == league]
    scatter.add_trace(go.Scatter(
        x=sub["Shots per match"].astype(float),
        y=sub["Conversion rate %"].astype(float),
        name=league, mode="markers",
        marker=dict(size=9, color=T.LEAGUE_COLORS.get(league),
                    line=dict(width=0.5, color="white")),
        text=sub["season"],
        hovertemplate=(
            "<b>" + league + "</b> %{text}<br>"
            "%{x:.1f} shots per match<br>%{y:.2f}% converted<extra></extra>"
        ),
    ))

scatter.update_layout(
    title="Shot volume against conversion rate, one point per league-season",
    xaxis_title="Shots per match (both teams)",
    yaxis_title="Conversion rate (% of shots scored)",
    height=470, hovermode="closest",
)
scatter.update_yaxes(ticksuffix="%")
st.plotly_chart(scatter, width="stretch")

corr = float(
    agg[["Shots per match", "Conversion rate %"]].astype(float).corr().iloc[0, 1]
)
T.readout(
    f"The correlation between shot volume and conversion is {corr:+.2f}. "
    + (
        "The negative sign means league-seasons that shoot more tend to convert a "
        "smaller share — shooting more often includes shooting from worse positions."
        if corr < -0.1 else
        "Volume and efficiency are close to independent: shooting more does not "
        "reliably mean scoring more per shot."
        if corr < 0.1 else
        "Volume and efficiency rise together in this selection."
    )
)

# --------------------------------------------------------------------------
# 3. Half-time to full-time
# --------------------------------------------------------------------------

st.markdown("## What is a half-time lead worth?")
T.lede(
    "Half-time positions on the left, final results on the right. The width of "
    "each flow is the number of matches that took that path."
)

ht = m.dropna(subset=["result_ht", "result"])
HT_LABEL = {"H": "Home leading at HT", "D": "Level at HT", "A": "Away leading at HT"}
FT_LABEL = {"H": "Home win", "D": "Draw", "A": "Away win"}
HT_KEYS, FT_KEYS = ["H", "D", "A"], ["H", "D", "A"]

cross = pd.crosstab(ht["result_ht"], ht["result"]).reindex(
    index=HT_KEYS, columns=FT_KEYS
).fillna(0)

nodes = [HT_LABEL[k] for k in HT_KEYS] + [FT_LABEL[k] for k in FT_KEYS]
node_colors = [T.CROWD, T.MUTED, T.EMPTY, T.CROWD, T.MUTED, T.EMPTY]

src, tgt, val, link_colors = [], [], [], []
RGBA = {
    "H": "rgba(200,127,30,.40)",
    "D": "rgba(124,138,148,.35)",
    "A": "rgba(46,111,142,.40)",
}
for i, hk in enumerate(HT_KEYS):
    for j, fk in enumerate(FT_KEYS):
        v = int(cross.loc[hk, fk])
        if v:
            src.append(i)
            tgt.append(3 + j)
            val.append(v)
            link_colors.append(RGBA[hk])

sankey = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        label=nodes, color=node_colors, pad=22, thickness=16,
        line=dict(color="white", width=1),
        hovertemplate="%{label}<br>%{value:,} matches<extra></extra>",
    ),
    link=dict(
        source=src, target=tgt, value=val, color=link_colors,
        hovertemplate="%{source.label} → %{target.label}<br>%{value:,} matches<extra></extra>",
    ),
))
sankey.update_layout(
    title="How half-time positions turn into final results",
    height=420, font=dict(family=T.FONT_BODY, size=12, color=T.INK),
)
st.plotly_chart(sankey, width="stretch")

lead_rows = cross.loc["H"].sum()
lead_held = cross.loc["H", "H"]
level_rows = cross.loc["D"].sum()
level_home = cross.loc["D", "H"]
comeback = cross.loc["A", "H"] + cross.loc["H", "A"]

T.readout(
    f"A home team leading at half-time goes on to win {lead_held / lead_rows * 100:.0f}% "
    f"of the time. From level at half-time, the home side still wins "
    f"{level_home / level_rows * 100:.0f}% against the away side's "
    f"{cross.loc['D', 'A'] / level_rows * 100:.0f}% — home advantage operating in the "
    f"second half alone. Full reversals, where the team behind at the break wins, "
    f"account for {comeback:,} matches ({comeback / cross.values.sum() * 100:.1f}%)."
)

# --------------------------------------------------------------------------
# 4. League table
# --------------------------------------------------------------------------

st.markdown("## League averages")

league_tot = (
    m.groupby("league_short", observed=True)
    .agg(matches=("match_id", "size"), goals=("goals", "sum"),
         shots=("shots", "sum"), sot=("sot", "sum"))
)
table = pd.DataFrame({
    "Matches": league_tot["matches"],
    "Goals per match": league_tot["goals"] / league_tot["matches"],
    "Shots per match": league_tot["shots"] / league_tot["matches"],
    "Shots on target per match": league_tot["sot"] / league_tot["matches"],
    "Shot accuracy %": league_tot["sot"] / league_tot["shots"] * 100,
    "Conversion rate %": league_tot["goals"] / league_tot["shots"] * 100,
}).reindex([l for l in D.LEAGUE_ORDER if l in league_tot.index])

st.dataframe(
    table.round(2), width="stretch",
    column_config={
        "Shot accuracy %": st.column_config.NumberColumn(format="%.1f%%"),
        "Conversion rate %": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
