"""
Dashboard 4 — Referees and Discipline.

The mechanism, at the level of the individual official. Referee names are
recorded only for the Premier League, so this page is scoped to that
league and says so on screen rather than quietly filtering.
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

matches_all = D.load_matches()

T.eyebrow("Dashboard 5 of 6 · Discipline")
st.markdown("# Referees and discipline")
T.lede(
    "Dashboard 1 showed that the away-team booking penalty vanished in empty "
    "stadiums. If crowd pressure is the cause, the effect should belong to "
    "referees as individuals: officials who favoured home teams most should "
    "have changed most. This page tests that."
)

# --------------------------------------------------------------------------
# All five leagues: how strictly is a foul punished?
# --------------------------------------------------------------------------

st.markdown("## How strictly does each league punish a foul?")
T.lede(
    "Cards per 100 fouls separates how strictly a league is refereed from how "
    "much it fouls. This section covers all five leagues — only referee *names* "
    "are limited to the Premier League, not the cards and fouls themselves."
)

_all = D.apply_filters(matches_all)
if not _all.empty:
    _all = _all.copy()
    _all["cards"] = (
        _all["home_yellows"] + _all["away_yellows"]
        + _all["home_reds"] + _all["away_reds"]
    ).astype("Float64")
    _all["fouls"] = (_all["home_fouls"] + _all["away_fouls"]).astype("Float64")

    strict = (
        _all.groupby("league_short", observed=True)
        .agg(cards=("cards", "sum"), fouls=("fouls", "sum"), n=("match_id", "size"))
    )
    strict = strict[strict["fouls"] > 0]
    if not strict.empty:
        strict["per100"] = strict["cards"] / strict["fouls"] * 100
        strict["fouls_pm"] = strict["fouls"] / strict["n"]
        strict = strict.sort_values("per100")

        sc = go.Figure(go.Bar(
            x=strict["per100"].astype(float), y=list(strict.index), orientation="h",
            marker=dict(color=[T.LEAGUE_COLORS.get(l, T.MUTED) for l in strict.index]),
            text=[f"{v:.1f}" for v in strict["per100"]],
            textposition="outside",
            textfont=dict(family=T.FONT_MONO, size=12),
            hovertemplate=(
                "%{y}<br>%{x:.2f} cards per 100 fouls"
                "<br>%{customdata:.1f} fouls per match<extra></extra>"
            ),
            customdata=strict["fouls_pm"].astype(float),
        ))
        sc.update_layout(
            title="Cards shown per 100 fouls committed, by league",
            xaxis_title="Cards per 100 fouls", yaxis_title="",
            height=320, showlegend=False, hovermode="closest", bargap=0.35,
        )
        st.plotly_chart(sc, width="stretch")
        T.readout(
            "The leagues that foul most are not the leagues that book most. A high "
            "value here means the same offence is more likely to be punished with a "
            "card — a property of how a league is refereed rather than how it is "
            "played. Ligue 1 2006/07 drops out automatically, since fouls were "
            "never recorded that season."
        )

    # ----------------------------------------------------------------------
    # Fouls against cards, by era
    # ----------------------------------------------------------------------
    # Carried over from the group's Tableau worksheet "05 - Fouls Discipline
    # Profile". The joint distribution separates two things a single ratio
    # collapses: how physical a league is, and how strictly it is refereed.

    st.markdown("### Physicality and strictness are different things")
    T.lede(
        "Each point is one league-season: fouls committed on the horizontal axis, "
        "cards shown on the vertical. Marker shape marks the era. The crosshairs "
        "are the overall averages."
    )

    per_season = (
        _all.groupby(["season", "season_start_year", "league_short"], observed=True)
        .agg(fouls=("fouls", "mean"), cards=("cards", "mean"),
             n=("match_id", "size"))
        .reset_index()
        .dropna(subset=["fouls", "cards"])
    )

    if not per_season.empty:
        per_season = D.add_season_era(per_season)

        quad = go.Figure()
        quad.add_hline(
            y=float(per_season["cards"].astype(float).mean()),
            line=dict(color=T.MUTED, width=1),
            annotation_text="Average", annotation_position="top left",
            annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED),
        )
        quad.add_vline(
            x=float(per_season["fouls"].astype(float).mean()),
            line=dict(color=T.MUTED, width=1),
            annotation_text="Average", annotation_position="bottom right",
            annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED),
        )

        for league in [l for l in D.LEAGUE_ORDER
                       if l in set(per_season["league_short"])]:
            for era in D.ERA_ORDER:
                sub = per_season[
                    (per_season["league_short"] == league)
                    & (per_season["season_era"] == era)
                ]
                if sub.empty:
                    continue
                quad.add_trace(go.Scatter(
                    x=sub["fouls"].astype(float), y=sub["cards"].astype(float),
                    mode="markers", name=league, legendgroup=league,
                    showlegend=(era == D.ERA_ORDER[0]),
                    marker=dict(
                        size=9, symbol=D.ERA_SYMBOLS[era],
                        color=T.LEAGUE_COLORS.get(league),
                        line=dict(width=1.4, color=T.LEAGUE_COLORS.get(league)),
                    ),
                    customdata=list(zip(sub["season"], [era] * len(sub))),
                    hovertemplate=(
                        "<b>" + league + "</b> %{customdata[0]}<br>"
                        "%{x:.1f} fouls · %{y:.2f} cards per match"
                        "<br>%{customdata[1]}<extra></extra>"
                    ),
                ))

        for era in D.ERA_ORDER:
            quad.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers", name=era,
                legendgroup="era", legendgrouptitle_text="Era (marker shape)",
                marker=dict(size=10, symbol=D.ERA_SYMBOLS[era], color=T.INK_SOFT,
                            line=dict(width=1.4, color=T.INK_SOFT)),
                hoverinfo="skip",
            ))

        quad.update_layout(
            title="Fouls against cards per match, one point per league-season",
            xaxis_title="Fouls per match (both teams)",
            yaxis_title="Cards per match (both teams)",
            height=540, hovermode="closest",
            legend=dict(orientation="v", x=1.02, y=1,
                        xanchor="left", yanchor="top"),
        )
        st.plotly_chart(quad, width="stretch")
        T.readout(
            "The upper-left quadrant is the interesting one: few fouls but many "
            "cards, meaning a league punishes strictly rather than one that simply "
            "fouls a lot. Tracking a single league's markers from circles through "
            "to triangles shows how its disciplinary character moved across twenty "
            "years — most leagues drift leftward, committing fewer fouls over time."
        )

st.markdown("## Individual referees, match by match")

T.caveat(
    "<strong>Scope from here on: Premier League only.</strong> The source files "
    "record referee names for every Premier League match, for about 5% of Serie A "
    "matches, and for none at all in Ligue 1, the Bundesliga or La Liga. Rather "
    "than present a league-wide figure built on one league's data, the remaining "
    "charts are restricted to the Premier League and the sidebar league filter "
    "does not apply to them. Season filtering still applies."
)

# Referee coverage is complete only for the Premier League.
epl = matches_all[
    (matches_all["league_short"] == "Premier League") & matches_all["referee"].notna()
]

# Apply the season filter only (league filter is intentionally bypassed).
lo, hi = D.active_seasons()
labels = D.season_labels()
keep = set(labels[labels.index(lo): labels.index(hi) + 1])
epl = epl[epl["season"].isin(keep)]

if epl.empty:
    st.warning("No Premier League matches in the selected season range.")
    st.stop()

epl = epl.copy()
epl["yellow_gap"] = (epl["away_yellows"] - epl["home_yellows"]).astype("Float64")

pre = epl[epl["crowd_status"] == T.CROWD_PRE]
emp = epl[epl["crowd_status"] == T.CROWD_EMPTY]
post = epl[epl["crowd_status"] == T.CROWD_POST]

T.stat_row([
    {"label": "Matches with a named referee", "value": f"{len(epl):,}", "note": "Premier League"},
    {"label": "Distinct referees", "value": f"{epl['referee'].nunique():,}", "note": ""},
    {"label": "Booking bias with crowds",
     "value": f"{float(pre['yellow_gap'].mean()):+.2f}" if len(pre) else "—",
     "tone": "amber", "note": "away − home yellows"},
    {"label": "Booking bias when empty",
     "value": f"{float(emp['yellow_gap'].mean()):+.2f}" if len(emp) else "—",
     "tone": "steel", "note": "away − home yellows"},
])

# --------------------------------------------------------------------------
# Fouls versus cards
# --------------------------------------------------------------------------

st.markdown("## Are away teams booked more because they foul more?")
T.lede(
    "A booking gap could reflect a fouling gap rather than a refereeing one. "
    "Fouling did change between the periods, so cards alone cannot settle it — "
    "but cards per foul holds conduct constant and isolates the judgement."
)

rows = []
for label, sub in [(T.CROWD_PRE, pre), (T.CROWD_EMPTY, emp), (T.CROWD_POST, post)]:
    if not len(sub):
        continue
    rows.append({
        "crowd_status": label,
        "Fouls": float(sub["away_fouls"].mean() - sub["home_fouls"].mean()),
        "Yellow cards": float(sub["away_yellows"].mean() - sub["home_yellows"].mean()),
        "Cards per foul": float(
            (sub["away_yellows"].sum() / sub["away_fouls"].sum())
            - (sub["home_yellows"].sum() / sub["home_fouls"].sum())
        ),
        "matches": len(sub),
    })
comp = pd.DataFrame(rows)

if not comp.empty:
    fig = go.Figure()
    for i, metric in enumerate(["Fouls", "Yellow cards", "Cards per foul"]):
        fig.add_trace(go.Bar(
            x=comp["crowd_status"], y=comp[metric], name=metric,
            marker=dict(color=[T.CROWD, T.EMPTY, T.CROWD_LIGHT][i]),
            hovertemplate="%{y:+.3f}<extra>" + metric + "</extra>",
        ))
    fig.add_hline(y=0, line=dict(color=T.INK, width=1))
    fig.update_layout(
        title="Away minus home, per match, under each crowd condition",
        xaxis_title="", yaxis_title="Away − home (per match)",
        height=400, barmode="group", bargap=0.28, hovermode="closest",
    )
    st.plotly_chart(fig, width="stretch")
    T.readout(
        "Both bars move: fouling itself changed in empty stadiums, so cards alone "
        "cannot separate conduct from judgement. The third bar does separate them — "
        "cards per foul holds conduct constant and still collapses, which means the "
        "same offence became less likely to be punished more harshly for the away side."
    )

# --------------------------------------------------------------------------
# Individual referees
# --------------------------------------------------------------------------



min_matches = st.slider(
    "Minimum matches per referee", 20, 300, 100, step=10,
    help="Referees with few matches produce unstable averages.",
)

ref = (
    epl.groupby("referee", observed=True)
    .agg(matches=("match_id", "size"),
         gap=("yellow_gap", "mean"),
         home_y=("home_yellows", "mean"),
         away_y=("away_yellows", "mean"),
         home_win=("is_home_win", "mean"))
    .reset_index()
)
ref = ref[ref["matches"] >= min_matches].copy()
for c in ("gap", "home_y", "away_y", "home_win"):
    ref[c] = ref[c].astype(float)
ref["home_win"] *= 100

if ref.empty:
    st.info("No referees meet the threshold. Lower the slider.")
    st.stop()

ref = ref.sort_values("gap")

bar = go.Figure()
for label, mask, colour in (
    ("Booked away teams more", ref["gap"] > 0, T.CROWD),
    ("Booked home teams more", ref["gap"] <= 0, T.EMPTY),
):
    part = ref[mask]
    if part.empty:
        continue
    bar.add_trace(go.Bar(
        x=part["gap"], y=part["referee"], orientation="h",
        name=label, marker=dict(color=colour),
        hovertemplate=(
            "<b>%{y}</b><br>%{x:+.3f} extra away bookings per match"
            "<br>%{customdata[0]:,} matches"
            "<br>%{customdata[1]:.2f} home · %{customdata[2]:.2f} away yellows"
            "<extra>" + label + "</extra>"
        ),
        customdata=part[["matches", "home_y", "away_y"]].values,
    ))

bar.add_vline(x=0, line=dict(color=T.INK, width=1))
bar.update_layout(
    title=f"Booking bias by referee ({len(ref)} officials with {min_matches}+ matches)",
    xaxis_title="Away yellows − home yellows (per match)",
    yaxis_title="",
    height=max(460, 22 * len(ref)),
    showlegend=True,
    barmode="overlay", hovermode="closest",
)
st.plotly_chart(bar, width="stretch")
T.readout(
    "Almost every official sits on the amber side, so the league-wide bias is not "
    "the work of a handful of outliers but a general tendency across the profession."
)

# --------------------------------------------------------------------------
# Did the biased referees change most?
# --------------------------------------------------------------------------

st.markdown("## Did the most biased referees change the most?")

pre_r = (
    pre.groupby("referee", observed=True)
    .agg(gap_pre=("yellow_gap", "mean"), n_pre=("match_id", "size")).reset_index()
)
emp_r = (
    emp.groupby("referee", observed=True)
    .agg(gap_emp=("yellow_gap", "mean"), n_emp=("match_id", "size")).reset_index()
)
pair = pre_r.merge(emp_r, on="referee", how="inner")
pair = pair[(pair["n_pre"] >= 30) & (pair["n_emp"] >= 10)].copy()

if len(pair) < 4:
    st.info(
        "Too few referees officiated enough matches both before and during the "
        "empty-stadium period under the current season filter to support this "
        "comparison. Widen the season range to 2006/07–2025/26."
    )
else:
    pair["gap_pre"] = pair["gap_pre"].astype(float)
    pair["gap_emp"] = pair["gap_emp"].astype(float)
    pair["change"] = pair["gap_emp"] - pair["gap_pre"]

    sc = go.Figure()
    sc.add_trace(go.Scatter(
        x=pair["gap_pre"], y=pair["gap_emp"], mode="markers+text",
        marker=dict(size=11, color=T.EMPTY, line=dict(width=0.5, color="white")),
        text=pair["referee"], textposition="top center",
        textfont=dict(size=9, color=T.MUTED),
        name="Referee",
        hovertemplate=(
            "<b>%{text}</b><br>With crowds: %{x:+.3f}"
            "<br>Empty: %{y:+.3f}<extra></extra>"
        ),
    ))

    lo_v = float(min(pair["gap_pre"].min(), pair["gap_emp"].min())) - 0.1
    hi_v = float(max(pair["gap_pre"].max(), pair["gap_emp"].max())) + 0.1
    sc.add_trace(go.Scatter(
        x=[lo_v, hi_v], y=[lo_v, hi_v], mode="lines", name="No change",
        line=dict(color=T.MUTED, width=1, dash="dash"), hoverinfo="skip",
    ))
    sc.add_hline(y=0, line=dict(color=T.RULE, width=1))

    sc.update_layout(
        title="Each referee's booking bias, with crowds versus in empty stadiums",
        xaxis_title="Bias with crowds (away − home yellows per match)",
        yaxis_title="Bias in empty stadiums",
        height=520, hovermode="closest",
    )
    st.plotly_chart(sc, width="stretch")

    corr = float(np.corrcoef(pair["gap_pre"], pair["change"])[0, 1])
    below = int((pair["gap_emp"] < pair["gap_pre"]).sum())
    T.readout(
        f"{below} of {len(pair)} referees show a smaller bias in empty stadiums than "
        f"they did in front of crowds. The correlation between a referee's original "
        f"bias and how much it changed is {corr:.2f} — a negative value means the "
        "officials who favoured home teams most were also the ones who changed most, "
        "which is what a crowd-pressure explanation predicts."
    )

    T.caveat(
        "<strong>Regression to the mean.</strong> A negative correlation between a "
        "starting value and its change is partly expected on statistical grounds "
        "alone, because referees with unusually high measured bias include some who "
        "were simply having an unusual run. This chart is supporting evidence for the "
        "crowd explanation, not proof of it; the stronger evidence is the league-wide "
        "reversal when crowds returned, shown on dashboard 1."
    )

# --------------------------------------------------------------------------
# Discipline over time
# --------------------------------------------------------------------------

st.markdown("## Cards over twenty seasons")

seasons = D.season_axis(epl)
disc = (
    epl.groupby("season", observed=True)
    .agg(home_y=("home_yellows", "mean"), away_y=("away_yellows", "mean"),
         home_r=("home_reds", "mean"), away_r=("away_reds", "mean"))
    .reset_index()
    .set_index("season").reindex(seasons).reset_index()
)

card_type = st.radio("Card type", ["Yellow cards", "Red cards"],
                     horizontal=True, label_visibility="collapsed")
hcol, acol = ("home_y", "away_y") if card_type == "Yellow cards" else ("home_r", "away_r")

line = go.Figure()
for venue, col in [("Home", hcol), ("Away", acol)]:
    line.add_trace(go.Scatter(
        x=disc["season"], y=disc[col].astype(float), name=f"{venue} team",
        mode="lines+markers",
        line=dict(width=2.5, color=T.VENUE_COLORS[venue]), marker=dict(size=5),
        hovertemplate="%{y:.2f} per match<extra>" + venue + "</extra>",
    ))
C.add_covid_band(line, seasons)
line.update_xaxes(categoryorder="array", categoryarray=seasons, tickangle=-45)
line.update_layout(
    title=f"{card_type} shown per match, Premier League",
    xaxis_title="Season", yaxis_title=f"{card_type} per match", height=420,
)
st.plotly_chart(line, width="stretch")
T.readout(
    "The two lines run apart for fourteen seasons, converge inside the shaded "
    "empty-stadium window, and separate again afterwards. That convergence and "
    "recovery is the clearest single image of the crowd's influence on officiating."
)
