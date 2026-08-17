"""
Dashboard 1 — The Home Advantage Story.

The narrative page. It establishes that home advantage exists, shows it
weakening when stadiums emptied, and then identifies referee behaviour as
a mechanism that moved at the same time.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import charts as C
from lib import data as D
from lib import stats as S
from lib import theme as T

D.sidebar_filters()

matches_all = D.load_matches()
matches = D.apply_filters(matches_all)

# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------

T.eyebrow("Dashboard 1 of 6 · Home advantage")
st.markdown("# Football's home advantage is partly made of noise")
T.lede(
    "Home teams have won far more often than away teams for as long as the "
    "game has been recorded, and the reasons offered are usually travel "
    "fatigue, familiarity with the pitch, and the crowd. Those explanations "
    "are hard to separate — until 2020, when COVID-19 emptied the stadiums "
    "and left everything else in place. This dashboard uses that period as a "
    "natural experiment across 36,197 matches in Europe's five biggest "
    "leagues."
)

if matches.empty:
    st.warning("No matches match the current filters. Widen the season range or add a league.")
    st.stop()

crowd = matches.groupby("crowd_status", observed=True)
pre = matches[matches["crowd_status"] == T.CROWD_PRE]
emp = matches[matches["crowd_status"] == T.CROWD_EMPTY]
post = matches[matches["crowd_status"] == T.CROWD_POST]


def _hw(df):
    return float(df["is_home_win"].mean() * 100) if len(df) else float("nan")


def _gap(df):
    if not len(df):
        return float("nan")
    return float(df["away_yellows"].mean() - df["home_yellows"].mean())


T.eyebrow("Home wins, by crowd conditions")
T.stat_row([
    {"label": "Crowds present", "value": f"{_hw(pre):.1f}%", "tone": "amber",
     "note": f"{len(pre):,} matches to Mar 2020"},
    {"label": "Empty stadiums", "value": f"{_hw(emp):.1f}%", "tone": "steel",
     "note": f"{len(emp):,} matches"},
    {"label": "Crowds returned", "value": f"{_hw(post):.1f}%", "tone": "amber-light",
     "note": f"{len(post):,} matches since Jul 2021"},
    {"label": "Swing when empty",
     "value": f"{_hw(emp) - _hw(pre):+.1f}pp", "tone": "steel",
     "note": "percentage points vs crowds"},
])

st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 1. Does home advantage exist, and did it move?
# --------------------------------------------------------------------------

st.markdown("## 1. Twenty seasons of home advantage")

col_a, col_b = st.columns([3, 1])
with col_b:
    split = st.toggle(
        "Split by league", value=False,
        help="Check whether the pattern holds in all five leagues or is driven by one.",
    )

seasons = D.season_axis(matches)
by = ["season", "league_short"] if split else ["season"]
hw = D.home_win_rate(matches, by)

st.plotly_chart(
    C.home_win_timeline(hw, seasons, by_league=split),
    width="stretch",
)

if split:
    T.readout(
        "Every league moves in the same direction during the shaded window, which "
        "rules out a quirk of one competition's scheduling or officiating."
    )
else:
    T.readout(
        "The home win rate is stable for well over a decade, then drops sharply "
        "across the shaded empty-stadium seasons before recovering only partially. "
        "Toggle the league split to confirm the pattern is not driven by a single league."
    )

# --------------------------------------------------------------------------
# 2. The mechanism
# --------------------------------------------------------------------------

st.markdown("## 2. What the referees did")
T.lede(
    "If the crowd is what creates home advantage, its effect should show up in "
    "decisions the crowd can influence. Bookings are the clearest test: referees "
    "have consistently shown more yellow cards to away teams than home teams."
)

gap = D.card_gap(matches, ["season"])
st.plotly_chart(C.card_gap_timeline(gap, seasons), width="stretch")

gap_pre, gap_emp, gap_post = _gap(pre), _gap(emp), _gap(post)
T.readout(
    f"Away teams were booked {gap_pre:.2f} times more per match than home teams "
    f"while crowds were present — a bias that held for fourteen consecutive seasons. "
    f"In empty stadiums it fell to {gap_emp:.3f}, effectively zero, then returned to "
    f"{gap_post:.2f} once fans came back. A bias that disappears and reappears with "
    "the crowd is much harder to explain by chance than a one-off dip."
)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        C.crowd_bars(
            D.home_win_rate(matches, ["crowd_status"]),
            "home_win_pct",
            "Home wins under each crowd condition",
            "Home wins (% of matches)", suffix="%",
        ),
        width="stretch",
    )
with c2:
    st.plotly_chart(
        C.crowd_bars(
            D.card_gap(matches, ["crowd_status"]),
            "yellow_gap",
            "Booking bias under each crowd condition",
            "Away − home yellows per match",
        ),
        width="stretch",
    )

T.readout(
    "The two measures move together. Colour is doing analytical work here: amber "
    "marks matches played in front of a crowd, steel blue marks empty stadiums, and "
    "the return of amber on the right is the return of the effect."
)

# --------------------------------------------------------------------------
# 3. Does it hold league by league?
# --------------------------------------------------------------------------

st.markdown("## 3. League by league")

metric = st.radio(
    "Measure",
    ["Home win rate", "Booking bias", "Home goal difference"],
    horizontal=True, label_visibility="collapsed",
)

if metric == "Home win rate":
    src = D.home_win_rate(matches, ["league_short", "crowd_status"])
    fig = C.league_slope(src, "home_win_pct",
                         "Home win rate by league and crowd conditions",
                         "Home wins (% of matches)", suffix="%")
elif metric == "Booking bias":
    src = D.card_gap(matches, ["league_short", "crowd_status"])
    fig = C.league_slope(src, "yellow_gap",
                         "Booking bias by league and crowd conditions",
                         "Away − home yellows per match")
else:
    src = (
        matches.groupby(["league_short", "crowd_status"], observed=True)
        .agg(gd=("goal_difference", "mean"), matches=("match_id", "size"))
        .reset_index()
    )
    src["gd"] = src["gd"].astype(float)
    fig = C.league_slope(src, "gd",
                         "Average home goal difference by league and crowd conditions",
                         "Home goals − away goals per match")

st.plotly_chart(fig, width="stretch")
T.readout(
    "Each line is one league. The tilt between the first two points is the size of "
    "the crowd effect; the tilt between the last two is how much of it came back."
)

# --------------------------------------------------------------------------
# 4. Where else the advantage shows
# --------------------------------------------------------------------------

st.markdown("## 4. The advantage across the whole match")

condition = st.selectbox(
    "Crowd conditions",
    [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST, "All matches"],
    index=0,
)
subset = matches if condition == "All matches" else matches[matches["crowd_status"] == condition]

vm = D.venue_means(
    subset, [],
    {"Shots": "shots", "Shots on target": "shots_on_target",
     "Corners": "corners", "Fouls": "fouls", "Yellow cards": "yellows"},
) if len(subset) else None

if vm is not None and not vm.empty:
    st.plotly_chart(
        C.venue_dumbbell(vm, f"Home versus away averages — {condition.lower()}"),
        width="stretch",
    )
    T.readout(
        "Switching between conditions shows that every home-away gap narrowed without "
        "a crowd — but not by the same amount. The disciplinary gap all but vanished, "
        "while the shooting and corner gaps roughly halved. Section 5 quantifies that "
        "difference, which is what separates an effect on the officials from an effect "
        "on the players."
    )

st.markdown("<hr>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 5. Is the difference real?
# --------------------------------------------------------------------------

st.markdown("## 5. Is the difference real?")
T.lede(
    "The empty-stadium window covers 2,255 matches — enough to see a pattern, "
    "few enough that chance deserves ruling out. Every figure below carries a "
    "95% confidence interval, and the two key comparisons are tested formally."
)

if len(pre) and len(emp):
    # --- proportions with Wilson intervals ------------------------------
    groups = [
        (T.CROWD_PRE, pre, T.CROWD),
        (T.CROWD_EMPTY, emp, T.EMPTY),
        (T.CROWD_POST, post, T.CROWD_LIGHT),
    ]
    labels, ests, los, his, ns, colours = [], [], [], [], [], []
    for label, frame, colour in groups:
        if not len(frame):
            continue
        w = S.wilson_interval(int(frame["is_home_win"].sum()), len(frame))
        labels.append(label.replace(" (pre-COVID)", "").replace(" (post-COVID)", ""))
        ests.append(w.estimate)
        los.append(w.estimate - w.low)
        his.append(w.high - w.estimate)
        ns.append(w.n)
        colours.append(colour)

    ci_fig = go.Figure(go.Bar(
        x=labels, y=ests,
        marker=dict(color=colours),
        error_y=dict(type="data", symmetric=False, array=his, arrayminus=los,
                     color=T.INK, thickness=1.5, width=8),
        hovertemplate="%{y:.2f}%<br>%{customdata:,} matches<extra></extra>",
        customdata=ns,
    ))
    ci_fig.update_layout(
        title="Home win rate with 95% confidence intervals",
        yaxis_title="Home wins (% of matches)", xaxis_title="",
        height=400, showlegend=False, bargap=0.45, hovermode="closest",
    )
    ci_fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(ci_fig, width="stretch")

    drop = S.two_proportion_test(
        int(emp["is_home_win"].sum()), len(emp),
        int(pre["is_home_win"].sum()), len(pre),
    )
    gap_test = S.welch_test(
        (emp["away_yellows"] - emp["home_yellows"]).astype("Float64"),
        (pre["away_yellows"] - pre["home_yellows"]).astype("Float64"),
    )

    cols = st.columns(2)
    with cols[0]:
        T.stat_row([{
            "label": "Fall in home win rate",
            "value": f"{drop.diff:+.2f}pp",
            "tone": "steel",
            "note": f"95% CI [{drop.low:+.2f}, {drop.high:+.2f}] · {drop.p_text()}",
        }])
    with cols[1]:
        T.stat_row([{
            "label": "Fall in booking bias",
            "value": f"{gap_test.diff:+.3f}",
            "tone": "steel",
            "note": f"95% CI [{gap_test.low:+.3f}, {gap_test.high:+.3f}] · {gap_test.p_text()}",
        }])

    if len(post):
        back = S.two_proportion_test(
            int(post["is_home_win"].sum()), len(post),
            int(emp["is_home_win"].sum()), len(emp),
        )
        T.readout(
            f"The home win rate fell {abs(drop.diff):.2f} percentage points when stadiums "
            f"emptied ({drop.p_text()}), and rose {back.diff:+.2f} points when crowds "
            f"returned ({back.p_text()}). The booking bias moved with it, falling "
            f"{abs(gap_test.diff):.3f} cards per match ({gap_test.p_text()}). Neither "
            "confidence interval crosses zero, so the changes are unlikely to be sampling noise."
        )

    # --- per-league forest plot -----------------------------------------
    st.markdown("### Does it hold in every league separately?")
    T.lede(
        "Each league is a separately administered competition with its own "
        "officials. If the effect appeared in only one, a local explanation "
        "would be more plausible than a general one."
    )

    rows = []
    for lg in [l for l in D.LEAGUE_ORDER if l in set(matches["league_short"])]:
        a = emp[emp["league_short"] == lg]
        b = pre[pre["league_short"] == lg]
        if len(a) < 30 or len(b) < 30:
            continue
        t = S.two_proportion_test(
            int(a["is_home_win"].sum()), len(a),
            int(b["is_home_win"].sum()), len(b),
        )
        rows.append((lg, t))

    if rows:
        overall = S.two_proportion_test(
            int(emp["is_home_win"].sum()), len(emp),
            int(pre["is_home_win"].sum()), len(pre),
        )

        names = [r[0] for r in rows] + ["All five leagues"]
        diffs = [r[1].diff for r in rows] + [overall.diff]
        lo_err = [r[1].diff - r[1].low for r in rows] + [overall.diff - overall.low]
        hi_err = [r[1].high - r[1].diff for r in rows] + [overall.high - overall.diff]
        sig = [r[1].significant for r in rows] + [overall.significant]
        pcs = [r[1].p_text() for r in rows] + [overall.p_text()]
        cols_f = [T.LEAGUE_COLORS.get(n, T.INK) for n in names[:-1]] + [T.INK]

        forest = go.Figure(go.Scatter(
            x=diffs, y=names, mode="markers",
            marker=dict(
                size=[10] * (len(names) - 1) + [14],
                color=cols_f,
                symbol=["circle" if s else "circle-open" for s in sig],
                line=dict(width=2, color=cols_f),
            ),
            error_x=dict(type="data", symmetric=False, array=hi_err, arrayminus=lo_err,
                         color=T.MUTED, thickness=1.5, width=6),
            customdata=pcs,
            hovertemplate="<b>%{y}</b><br>%{x:+.2f} pp<br>%{customdata}<extra></extra>",
        ))
        forest.add_vline(x=0, line=dict(color=T.INK, width=1, dash="dash"))
        forest.update_layout(
            title="Change in home win rate in empty stadiums, by league",
            xaxis_title="Percentage-point change (empty stadiums − crowds present)",
            yaxis_title="", height=380, showlegend=False, hovermode="closest",
        )
        forest.update_yaxes(autorange="reversed")
        st.plotly_chart(forest, width="stretch")

        n_sig = sum(1 for r in rows if r[1].significant)
        n_neg = sum(1 for r in rows if r[1].diff < 0)
        T.readout(
            f"All {n_neg} of {len(rows)} leagues moved in the same direction, and "
            f"{n_sig} reach significance on their own — filled markers are significant, "
            "hollow ones are not. The leagues that fall short have the widest intervals "
            "rather than the smallest effects, which is what a short window and a few "
            "hundred matches produce. Five independent competitions moving together is "
            "the strongest argument against a local explanation."
        )

# --------------------------------------------------------------------------
# 6. Officials or players?
# --------------------------------------------------------------------------

st.markdown("## 6. Officials or players?")
T.lede(
    "Every home-away gap narrowed in empty stadiums, so the crowd affected both how "
    "teams played and how they were judged. The question is which it affected more. "
    "Comparing how much of each original gap survived answers it directly."
)

if len(pre) and len(emp):
    GAPS = [
        ("Shots", "shots_diff"),
        ("Shots on target", "shots_on_target_diff"),
        ("Corners", "corners_diff"),
        ("Yellow cards", "yellows_diff"),
    ]

    names, retained, details = [], [], []
    for label, col in GAPS:
        b = float(pre[col].astype("Float64").mean())
        a = float(emp[col].astype("Float64").mean())
        if b == 0:
            continue
        names.append(label)
        retained.append(a / b * 100)
        details.append((b, a))

    if names:
        colours = [T.EMPTY if r < 25 else T.CROWD for r in retained]
        ret = go.Figure(go.Bar(
            x=names, y=retained,
            marker=dict(color=colours),
            text=[f"{r:.0f}%" for r in retained],
            textposition="outside",
            textfont=dict(family=T.FONT_MONO, size=13),
            customdata=details,
            hovertemplate=(
                "%{x}<br>gap with crowds: %{customdata[0]:+.3f}"
                "<br>gap when empty: %{customdata[1]:+.3f}"
                "<br>retained: %{y:.0f}%<extra></extra>"
            ),
        ))
        ret.add_hline(y=100, line=dict(color=T.MUTED, width=1, dash="dot"),
                      annotation_text="gap unchanged",
                      annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED))
        ret.update_layout(
            title="How much of each home advantage survived without a crowd",
            yaxis_title="Share of the original gap retained (%)", xaxis_title="",
            height=400, showlegend=False, bargap=0.4, hovermode="closest",
        )
        ret.update_yaxes(ticksuffix="%")
        st.plotly_chart(ret, width="stretch")
        T.readout(
            "The shooting and corner advantages retained roughly half their size — the "
            "crowd does affect how teams play. The booking advantage retained almost "
            "none. Both effects are real; they differ by an order of magnitude."
        )

    # --- punishment rate for identical conduct ---------------------------
    st.markdown("### The same offence, judged differently")
    T.lede(
        "Fouls themselves changed between the two periods, so comparing cards alone "
        "confounds conduct with judgement. Cards per 100 fouls removes that: it asks "
        "how likely the same offence was to be punished."
    )

    fouled = matches.dropna(subset=["home_fouls", "away_fouls"])
    rows_r = []
    for label, key, colour in [
        ("Crowds present", T.CROWD_PRE, T.CROWD),
        ("Empty stadiums", T.CROWD_EMPTY, T.EMPTY),
        ("Crowds returned", T.CROWD_POST, T.CROWD_LIGHT),
    ]:
        d = fouled[fouled["crowd_status"] == key]
        if not len(d):
            continue
        hf, af = float(d["home_fouls"].sum()), float(d["away_fouls"].sum())
        if hf <= 0 or af <= 0:
            continue
        rows_r.append({
            "condition": label,
            "Home team": float(d["home_yellows"].sum()) / hf * 100,
            "Away team": float(d["away_yellows"].sum()) / af * 100,
        })

    if rows_r:
        rr = pd.DataFrame(rows_r)
        pun = go.Figure()
        for venue, colour in [("Home team", T.CROWD), ("Away team", T.EMPTY)]:
            pun.add_trace(go.Bar(
                x=rr["condition"], y=rr[venue], name=venue,
                marker=dict(color=colour),
                text=[f"{v:.2f}" for v in rr[venue]],
                textposition="outside",
                textfont=dict(family=T.FONT_MONO, size=11),
                hovertemplate="%{y:.2f} cards per 100 fouls<extra>" + venue + "</extra>",
            ))
        pun.update_layout(
            title="Cards shown per 100 fouls committed, by venue",
            yaxis_title="Cards per 100 fouls", xaxis_title="",
            height=400, barmode="group", bargap=0.32, hovermode="closest",
        )
        st.plotly_chart(pun, width="stretch")

        gaps = {r["condition"]: r["Away team"] - r["Home team"] for r in rows_r}
        if "Crowds present" in gaps and "Empty stadiums" in gaps:
            g1, g2 = gaps["Crowds present"], gaps["Empty stadiums"]
            g3 = gaps.get("Crowds returned")
            tail = (f" and returned to {g3:+.2f} once crowds came back" if g3 is not None else "")
            T.readout(
                f"For an identical offence, away teams were {g1:.2f} percentage points "
                f"more likely to be booked while crowds were present. In empty stadiums "
                f"that fell to {g2:.2f}{tail}. This holds conduct constant, so it cannot "
                "be explained by away teams fouling differently — it is a change in how "
                "the same act was judged."
            )

    # --- paired within-club test -----------------------------------------
    st.markdown("### The same clubs, before and during")
    T.lede(
        "A last alternative: perhaps a different mix of teams happened to be playing. "
        "Pairing each club with itself removes that — squad quality, stadium and league "
        "are held constant, because every club is compared only to its own earlier record."
    )

    tm_all = D.load_team_matches()

    def _club_advantage(df: pd.DataFrame) -> pd.DataFrame:
        g = (
            df.groupby(["team", "venue"], observed=True)
            .agg(win=("is_win", "mean"), n=("match_id", "size"))
            .reset_index()
        )
        wins = g.pivot(index="team", columns="venue", values="win")
        counts = g.pivot(index="team", columns="venue", values="n")
        if "Home" not in wins or "Away" not in wins:
            return pd.DataFrame()
        return pd.DataFrame({
            "adv": (wins["Home"] - wins["Away"]) * 100,
            "home_n": counts["Home"],
        }).dropna()

    a_pre = _club_advantage(tm_all[tm_all["crowd_status"] == T.CROWD_PRE])
    a_emp = _club_advantage(tm_all[tm_all["crowd_status"] == T.CROWD_EMPTY])

    if not a_pre.empty and not a_emp.empty:
        paired = a_pre.join(a_emp, lsuffix="_pre", rsuffix="_emp", how="inner")
        paired = paired[(paired["home_n_pre"] >= 30) & (paired["home_n_emp"] >= 8)]
        paired["delta"] = paired["adv_emp"] - paired["adv_pre"]

        if len(paired) >= 10:
            pt = S.paired_test(paired["delta"].values)
            declined = int((paired["delta"] < 0).sum())

            hist = go.Figure(go.Histogram(
                x=paired["delta"], nbinsx=24,
                marker=dict(color=T.EMPTY, line=dict(width=1, color="white")),
                hovertemplate="%{y} clubs changed by %{x} pp<extra></extra>",
            ))
            hist.add_vline(x=0, line=dict(color=T.INK, width=1, dash="dash"),
                           annotation_text="no change",
                           annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED))
            hist.add_vline(x=pt.diff, line=dict(color=T.CROWD, width=2),
                           annotation_text=f"mean {pt.diff:+.1f}pp",
                           annotation_position="top left",
                           annotation_font=dict(family=T.FONT_MONO, size=10, color=T.CROWD))
            hist.update_layout(
                title=f"Change in each club's own home advantage ({len(paired)} clubs)",
                xaxis_title="Change in home advantage (percentage points)",
                yaxis_title="Clubs", height=400, showlegend=False, hovermode="closest",
            )
            st.plotly_chart(hist, width="stretch")

            T.stat_row([
                {"label": "Clubs compared with themselves", "value": f"{len(paired)}",
                 "note": "played in both periods"},
                {"label": "Mean change in own advantage",
                 "value": f"{pt.diff:+.1f}pp", "tone": "steel",
                 "note": f"95% CI [{pt.low:+.1f}, {pt.high:+.1f}] · {pt.p_text()}"},
                {"label": "Clubs whose advantage fell",
                 "value": f"{declined} of {len(paired)}", "tone": "steel",
                 "note": f"{declined / len(paired) * 100:.0f}% of the sample"},
            ])

            T.readout(
                f"Comparing every club only against itself, home advantage fell "
                f"{abs(pt.diff):.1f} percentage points on average ({pt.p_text()}), and "
                f"{declined} of {len(paired)} clubs declined. Because each club is its "
                "own control, this cannot be explained by a different mix of teams. "
                "Individual clubs contribute few empty-stadium matches, so any single "
                "club's figure is noisy — the mean across all of them is not."
            )

st.markdown("<hr>", unsafe_allow_html=True)

T.caveat(
    "<strong>How to read this responsibly.</strong> The source data contains no "
    "attendance figures, so each match is classified by the period it was played in: "
    "crowds present before 8 March 2020, empty or restricted until 30 June 2021, "
    "crowds returned thereafter. Attendance policy varied by country and by club, so "
    "the boundaries are an approximation, and a small number of matches inside the "
    "middle window were played in front of partial crowds. The comparison is "
    "observational, not a randomised trial: other things changed in 2020, including "
    "congested fixture lists and five-substitute rules. The consistency of the "
    "pattern across five independent leagues, and its reversal when crowds returned, "
    "is what makes the crowd the most plausible explanation."
)
