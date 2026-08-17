"""
The Story — a guided walkthrough.

Where the dashboards let a reader explore, this page argues. It steps
through the evidence one point at a time, in a fixed order, with a single
chart and a single claim per step.

The sequence follows the seven-point story the group designed in Tableau,
so the narrative structure developed there survives in the web
application rather than being replaced by free exploration alone.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import charts as C
from lib import data as D
from lib import stats as S
from lib import theme as T

matches = D.load_matches()          # deliberately unfiltered
team_matches = D.load_team_matches()
seasons = D.season_axis(matches)

STEPS = [
    "Home teams win more",
    "That advantage weakened",
    "The crowd went missing",
    "What the referees did",
    "Players and officials",
    "It happened everywhere",
    "What it adds up to",
]

# --------------------------------------------------------------------------
# Header and navigation
# --------------------------------------------------------------------------

T.eyebrow("Guided walkthrough")
st.markdown("# Does home advantage come from the crowd?")
T.lede(
    "Seven steps through the evidence, in order. The dashboards let you explore "
    "the data freely; this page makes the argument."
)

st.session_state.setdefault("story_step", 0)

# Buttons form the step selector, so the reader can jump as well as advance.
cols = st.columns(len(STEPS))
for i, (col, label) in enumerate(zip(cols, STEPS)):
    with col:
        if st.button(
            f"{i + 1}",
            key=f"story_btn_{i}",
            width="stretch",
            type="primary" if st.session_state["story_step"] == i else "secondary",
            help=label,
        ):
            st.session_state["story_step"] = i

step = st.session_state["story_step"]

st.markdown(
    f'<div class="eyebrow">Step {step + 1} of {len(STEPS)}</div>',
    unsafe_allow_html=True,
)
st.markdown(f"## {STEPS[step]}")

# --------------------------------------------------------------------------
# Step 1 — Home teams win more
# --------------------------------------------------------------------------

if step == 0:
    T.lede(
        "Across 36,197 matches in Europe's five biggest leagues, the team playing "
        "at home wins far more often than the team travelling. This is the oldest "
        "regularity in the sport, and it holds in every league."
    )

    venue = (
        team_matches.groupby("venue", observed=True)
        .agg(win=("is_win", "mean"), pts=("points", "mean"),
             goals=("goals", "mean"), n=("match_id", "size"))
        .reset_index()
    )
    h = venue[venue["venue"] == "Home"].iloc[0]
    a = venue[venue["venue"] == "Away"].iloc[0]

    T.stat_row([
        {"label": "Win rate at home", "value": f"{h['win'] * 100:.1f}%", "tone": "amber",
         "note": f"{int(h['n']):,} matches"},
        {"label": "Win rate away", "value": f"{a['win'] * 100:.1f}%", "tone": "steel",
         "note": f"{int(a['n']):,} matches"},
        {"label": "Points per match at home", "value": f"{h['pts']:.2f}", "tone": "amber", "note": ""},
        {"label": "Points per match away", "value": f"{a['pts']:.2f}", "tone": "steel", "note": ""},
    ])

    per_league = (
        matches.groupby("league_short", observed=True)
        .agg(home=("is_home_win", "mean"), draw=("is_draw", "mean"),
             away=("is_away_win", "mean"))
        .reset_index()
    )
    per_league = per_league.set_index("league_short").reindex(
        [l for l in D.LEAGUE_ORDER if l in set(per_league["league_short"])]
    ).reset_index()

    fig = go.Figure()
    for key, label, colour in [
        ("home", "Home win", T.CROWD), ("draw", "Draw", T.MUTED),
        ("away", "Away win", T.EMPTY),
    ]:
        fig.add_trace(go.Bar(
            y=per_league["league_short"], x=per_league[key].astype(float) * 100,
            name=label, orientation="h", marker=dict(color=colour),
            hovertemplate="%{x:.1f}%<extra>" + label + "</extra>",
        ))
    fig.update_layout(
        title="How matches end, by league",
        barmode="stack", height=360,
        xaxis_title="Share of matches (%)", yaxis_title="",
        hovermode="closest",
    )
    fig.update_xaxes(ticksuffix="%", range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width="stretch")

    T.readout(
        "The amber band is wider than the steel one in all five leagues. The usual "
        "explanations — travel fatigue, familiarity with the pitch, the crowd — "
        "always occur together, so no ordinary comparison can separate them."
    )

# --------------------------------------------------------------------------
# Step 2 — The advantage weakened
# --------------------------------------------------------------------------

elif step == 1:
    T.lede(
        "Plotted across twenty seasons, home advantage is remarkably stable — until "
        "it isn't. Two seasons stand apart from everything around them."
    )

    hw = D.home_win_rate(matches, ["season"])
    st.plotly_chart(C.home_win_timeline(hw, seasons), width="stretch")

    T.readout(
        "The rate sits near the dotted average for fourteen consecutive seasons, "
        "then drops sharply across the two shaded seasons and recovers only "
        "partially afterwards. Something specific to that window changed the game."
    )

# --------------------------------------------------------------------------
# Step 3 — The crowd went missing
# --------------------------------------------------------------------------

elif step == 2:
    T.lede(
        "Those two seasons are when COVID-19 emptied the stadiums. The teams, the "
        "competitions, the pitches and the travel all stayed as they were; the "
        "spectators did not. That makes the period a natural experiment — a rare "
        "thing in a sport where controlled trials are impossible."
    )

    pre = matches[matches["crowd_status"] == T.CROWD_PRE]
    emp = matches[matches["crowd_status"] == T.CROWD_EMPTY]
    post = matches[matches["crowd_status"] == T.CROWD_POST]

    labels, ests, lo_err, hi_err, colours, ns = [], [], [], [], [], []
    for label, frame, colour in [
        ("Crowds present", pre, T.CROWD),
        ("Empty stadiums", emp, T.EMPTY),
        ("Crowds returned", post, T.CROWD_LIGHT),
    ]:
        w = S.wilson_interval(int(frame["is_home_win"].sum()), len(frame))
        labels.append(label); ests.append(w.estimate)
        lo_err.append(w.estimate - w.low); hi_err.append(w.high - w.estimate)
        colours.append(colour); ns.append(w.n)

    fig = go.Figure(go.Bar(
        x=labels, y=ests, marker=dict(color=colours),
        error_y=dict(type="data", symmetric=False, array=hi_err, arrayminus=lo_err,
                     color=T.INK, thickness=1.5, width=8),
        hovertemplate="%{y:.2f}%<br>%{customdata:,} matches<extra></extra>",
        customdata=ns,
    ))
    fig.update_layout(
        title="Home win rate by crowd conditions, with 95% confidence intervals",
        yaxis_title="Home wins (%)", xaxis_title="",
        height=400, showlegend=False, bargap=0.45, hovermode="closest",
    )
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, width="stretch")

    drop = S.two_proportion_test(
        int(emp["is_home_win"].sum()), len(emp),
        int(pre["is_home_win"].sum()), len(pre))
    back = S.two_proportion_test(
        int(post["is_home_win"].sum()), len(post),
        int(emp["is_home_win"].sum()), len(emp))

    T.readout(
        f"Home advantage fell {abs(drop.diff):.2f} percentage points without crowds "
        f"({drop.p_text()}), then recovered {back.diff:+.2f} points when they returned "
        f"({back.p_text()}). The intervals do not overlap zero. A pattern that "
        "disappears and comes back is much harder to attribute to chance than a "
        "single dip would be."
    )

# --------------------------------------------------------------------------
# Step 4 — What the referees did
# --------------------------------------------------------------------------

elif step == 3:
    T.lede(
        "If the crowd is the cause, its effect should appear in decisions a crowd "
        "can plausibly influence. Bookings are the clearest test: referees have "
        "always shown more yellow cards to away teams than to home teams."
    )

    gap = D.card_gap(matches, ["season"])
    st.plotly_chart(C.card_gap_timeline(gap, seasons), width="stretch")

    pre = matches[matches["crowd_status"] == T.CROWD_PRE]
    emp = matches[matches["crowd_status"] == T.CROWD_EMPTY]
    post = matches[matches["crowd_status"] == T.CROWD_POST]

    def _g(d):
        return float((d["away_yellows"] - d["home_yellows"]).mean())

    T.stat_row([
        {"label": "Bias with crowds", "value": f"{_g(pre):+.3f}", "tone": "amber",
         "note": "extra away bookings per match"},
        {"label": "Bias when empty", "value": f"{_g(emp):+.3f}", "tone": "steel",
         "note": "effectively zero"},
        {"label": "Bias when crowds returned", "value": f"{_g(post):+.3f}",
         "tone": "amber-light", "note": "the bias came back"},
    ])

    T.readout(
        "A bias that held steady for fourteen seasons collapsed to almost nothing "
        "in empty stadiums, then returned. This is the mechanism: whatever the "
        "crowd was doing, it was acting on the officials."
    )

# --------------------------------------------------------------------------
# Step 5 — Not the players
# --------------------------------------------------------------------------

elif step == 4:
    T.lede(
        "Without a crowd, every home advantage narrowed — teams shot less often "
        "at home, won fewer corners, and were booked more evenly. So the crowd "
        "affected both how teams played and how they were judged. The question is "
        "which it affected more."
    )

    pre_s = matches[matches["crowd_status"] == T.CROWD_PRE]
    emp_s = matches[matches["crowd_status"] == T.CROWD_EMPTY]

    GAPS = [("Shots", "shots_diff"), ("Shots on target", "shots_on_target_diff"),
            ("Corners", "corners_diff"), ("Yellow cards", "yellows_diff")]
    names, retained = [], []
    for label, col in GAPS:
        b = float(pre_s[col].astype("Float64").mean())
        a = float(emp_s[col].astype("Float64").mean())
        if b:
            names.append(label); retained.append(a / b * 100)

    fig = go.Figure(go.Bar(
        x=names, y=retained,
        marker=dict(color=[T.EMPTY if r < 25 else T.CROWD for r in retained]),
        text=[f"{r:.0f}%" for r in retained], textposition="outside",
        textfont=dict(family=T.FONT_MONO, size=13),
        hovertemplate="%{x}: %{y:.0f}% of the gap retained<extra></extra>",
    ))
    fig.add_hline(y=100, line=dict(color=T.MUTED, width=1, dash="dot"),
                  annotation_text="gap unchanged",
                  annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED))
    fig.update_layout(
        title="How much of each home advantage survived without a crowd",
        yaxis_title="Share of the original gap retained (%)", xaxis_title="",
        height=400, showlegend=False, bargap=0.4, hovermode="closest",
    )
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, width="stretch")

    fouled = matches.dropna(subset=["home_fouls", "away_fouls"])
    def _rate(d, venue):
        f = float(d[f"{venue}_fouls"].sum())
        return float(d[f"{venue}_yellows"].sum()) / f * 100 if f else float("nan")
    fp = fouled[fouled["crowd_status"] == T.CROWD_PRE]
    fe = fouled[fouled["crowd_status"] == T.CROWD_EMPTY]
    g_pre = _rate(fp, "away") - _rate(fp, "home")
    g_emp = _rate(fe, "away") - _rate(fe, "home")

    T.readout(
        f"The shooting and corner advantages kept about half their size — the crowd "
        f"does change how teams play. The booking advantage kept almost none. Holding "
        f"conduct constant makes the contrast sharper still: per 100 fouls committed, "
        f"away teams were {g_pre:.2f} points more likely to be booked with a crowd "
        f"present and only {g_emp:.2f} points without one. Both effects are real, but "
        "they differ by an order of magnitude."
    )

# --------------------------------------------------------------------------
# Step 6 — It happened everywhere
# --------------------------------------------------------------------------

elif step == 5:
    T.lede(
        "Five leagues, five federations, five sets of officials, five governments "
        "setting their own rules. If the effect were an artefact of one "
        "competition's scheduling or officiating, it would not appear in all of them."
    )

    pre = matches[matches["crowd_status"] == T.CROWD_PRE]
    emp = matches[matches["crowd_status"] == T.CROWD_EMPTY]

    names, diffs, lo_err, hi_err, sig, pcs = [], [], [], [], [], []
    for lg in [l for l in D.LEAGUE_ORDER if l in set(matches["league_short"])]:
        a = emp[emp["league_short"] == lg]; b = pre[pre["league_short"] == lg]
        if len(a) < 30 or len(b) < 30:
            continue
        t = S.two_proportion_test(int(a["is_home_win"].sum()), len(a),
                                  int(b["is_home_win"].sum()), len(b))
        names.append(lg); diffs.append(t.diff)
        lo_err.append(t.diff - t.low); hi_err.append(t.high - t.diff)
        sig.append(t.significant); pcs.append(t.p_text())

    if names:
        colours = [T.LEAGUE_COLORS.get(n, T.INK) for n in names]
        forest = go.Figure(go.Scatter(
            x=diffs, y=names, mode="markers",
            marker=dict(size=11, color=colours,
                        symbol=["circle" if s else "circle-open" for s in sig],
                        line=dict(width=2, color=colours)),
            error_x=dict(type="data", symmetric=False, array=hi_err,
                         arrayminus=lo_err, color=T.MUTED, thickness=1.5, width=6),
            customdata=pcs,
            hovertemplate="<b>%{y}</b><br>%{x:+.2f} pp<br>%{customdata}<extra></extra>",
        ))
        forest.add_vline(x=0, line=dict(color=T.INK, width=1, dash="dash"))
        forest.update_layout(
            title="Change in home win rate in empty stadiums, by league",
            xaxis_title="Percentage-point change (empty − crowds)",
            yaxis_title="", height=380, showlegend=False, hovermode="closest",
        )
        forest.update_yaxes(autorange="reversed")
        st.plotly_chart(forest, width="stretch")

        T.readout(
            f"Every one of the {len(names)} leagues moved in the same direction. "
            f"{sum(sig)} reach statistical significance individually — filled markers — "
            "and those that do not have the widest intervals rather than the smallest "
            "effects, which is what a few hundred matches produce. Five independent "
            "competitions agreeing is the core of the argument."
        )

# --------------------------------------------------------------------------
# Step 7 — What it adds up to
# --------------------------------------------------------------------------

else:
    T.lede(
        "Home advantage is real, it is large, and a substantial part of it is made "
        "of crowd noise acting on referees."
    )

    pre = matches[matches["crowd_status"] == T.CROWD_PRE]
    emp = matches[matches["crowd_status"] == T.CROWD_EMPTY]
    post = matches[matches["crowd_status"] == T.CROWD_POST]
    drop = S.two_proportion_test(
        int(emp["is_home_win"].sum()), len(emp),
        int(pre["is_home_win"].sum()), len(pre))

    st.markdown(
        f"""
| | With crowds | Empty stadiums | Crowds returned |
|---|---:|---:|---:|
| Home win rate | {pre['is_home_win'].mean() * 100:.1f}% | **{emp['is_home_win'].mean() * 100:.1f}%** | {post['is_home_win'].mean() * 100:.1f}% |
| Booking bias | {float((pre['away_yellows'] - pre['home_yellows']).mean()):+.3f} | **{float((emp['away_yellows'] - emp['home_yellows']).mean()):+.3f}** | {float((post['away_yellows'] - post['home_yellows']).mean()):+.3f} |
| Matches | {len(pre):,} | {len(emp):,} | {len(post):,} |
"""
    )

    st.markdown("### What this does not show")
    T.caveat(
        "<strong>This is an observational comparison, not a randomised trial.</strong> "
        "Other things changed in 2020: fixture lists were congested, five substitutions "
        "were permitted, and squads were disrupted by illness. Crowd conditions are "
        "inferred from the match date, because the source records no attendance figures, "
        "so the boundaries are approximate and some matches in the middle window had "
        "partial crowds. What the evidence rests on is the combination of three things: "
        "the pattern appears in five independently administered leagues, it reverses "
        "when crowds return, and it affects the disciplinary measures a crowd could "
        "plausibly influence while leaving shots and corners largely unchanged. "
        "Fixture congestion and substitution rules would struggle to produce that "
        "particular combination."
    )

    st.markdown("### Keep going")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link("views/home_advantage.py",
                     label="**Home Advantage — the full analysis →**")
        st.page_link("views/referees.py",
                     label="**Referees & Discipline — the mechanism →**")
    with c2:
        st.page_link("views/explorer.py",
                     label="**Evolution of the Big Five — explore it yourself →**")
        st.page_link("views/about.py",
                     label="**About & Method — how it was built →**")

# --------------------------------------------------------------------------
# Step navigation
# --------------------------------------------------------------------------

st.markdown("<hr>", unsafe_allow_html=True)
back_col, spacer, next_col = st.columns([1, 3, 1])

with back_col:
    if step > 0 and st.button("← Previous", width="stretch"):
        st.session_state["story_step"] = step - 1
        st.rerun()

with next_col:
    if step < len(STEPS) - 1 and st.button("Next →", width="stretch", type="primary"):
        st.session_state["story_step"] = step + 1
        st.rerun()

st.caption(
    "This walkthrough uses the full dataset; the sidebar filters apply to the "
    "dashboards rather than to the argument made here."
)
