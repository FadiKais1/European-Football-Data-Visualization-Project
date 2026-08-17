"""
Chart builders.

Every figure here follows the same rules: an explicit title, labelled
axes with units, a legend whenever more than one series is drawn, and
colour used only where it encodes something. Charts that span the COVID
period carry a shaded band so the reader can locate the empty-stadium
window without consulting a separate legend.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import theme as T

# The empty-stadium window, in season labels.
COVID_SEASONS = ["2019/20", "2020/21"]


# --------------------------------------------------------------------------
# Shared decorations
# --------------------------------------------------------------------------

def add_covid_band(fig: go.Figure, seasons: list[str], label: bool = True) -> go.Figure:
    """Shade the empty-stadium seasons on a categorical season axis."""
    present = [s for s in COVID_SEASONS if s in seasons]
    if not present:
        return fig

    first = seasons.index(present[0])
    last = seasons.index(present[-1])

    fig.add_vrect(
        x0=first - 0.5,
        x1=last + 0.5,
        fillcolor=T.EMPTY,
        opacity=0.08,
        layer="below",
        line_width=0,
    )
    if label:
        fig.add_annotation(
            x=(first + last) / 2,
            y=1.0,
            yref="paper",
            text="Empty stadiums",
            showarrow=False,
            font=dict(family=T.FONT_MONO, size=10, color=T.EMPTY),
            yanchor="bottom",
        )
    return fig


def _season_axis(fig: go.Figure, seasons: list[str]) -> None:
    step = 1 if len(seasons) <= 12 else 2
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=seasons,
        tickmode="array",
        tickvals=seasons[::step],
        tickangle=-45,
    )


# --------------------------------------------------------------------------
# Home advantage over time
# --------------------------------------------------------------------------

def home_win_timeline(df: pd.DataFrame, seasons: list[str],
                      by_league: bool = False) -> go.Figure:
    """Home win percentage by season, optionally split by league."""
    fig = go.Figure()

    if by_league:
        for league, sub in df.groupby("league_short", observed=True):
            sub = sub.set_index("season").reindex(seasons).reset_index()
            fig.add_trace(go.Scatter(
                x=sub["season"], y=sub["home_win_pct"],
                name=league, mode="lines+markers",
                line=dict(width=2, color=T.LEAGUE_COLORS.get(league)),
                marker=dict(size=5),
                hovertemplate="%{y:.1f}% home wins<extra>" + league + "</extra>",
            ))
    else:
        sub = df.set_index("season").reindex(seasons).reset_index()
        fig.add_trace(go.Scatter(
            x=sub["season"], y=sub["home_win_pct"],
            name="All leagues", mode="lines+markers",
            line=dict(width=2.5, color=T.INK),
            marker=dict(size=6, color=T.INK),
            hovertemplate="%{y:.1f}% home wins<br>%{customdata:,} matches<extra></extra>",
            customdata=sub["matches"],
        ))
        baseline = float(
            sub.loc[~sub["season"].isin(COVID_SEASONS), "home_win_pct"].mean()
        )
        fig.add_hline(
            y=baseline, line=dict(color=T.MUTED, width=1, dash="dot"),
            annotation_text=f"Non-COVID average {baseline:.1f}%",
            annotation_position="bottom right",
            annotation_font=dict(family=T.FONT_MONO, size=10, color=T.MUTED),
        )

    add_covid_band(fig, seasons)
    _season_axis(fig, seasons)
    fig.update_layout(
        title="Share of matches won by the home team, by season",
        yaxis_title="Home wins (% of matches)",
        xaxis_title="Season",
        height=430,
        showlegend=by_league,
    )
    fig.update_yaxes(ticksuffix="%")
    return fig


def card_gap_timeline(df: pd.DataFrame, seasons: list[str]) -> go.Figure:
    """
    The signature chart: referee booking bias by season.

    Bars show away yellows minus home yellows per match. The bias is
    remarkably stable for fourteen years, vanishes in empty stadiums,
    and returns when crowds do.
    """
    sub = df.set_index("season").reindex(seasons).reset_index()
    is_covid = sub["season"].isin(COVID_SEASONS)

    fig = go.Figure()

    # Two traces rather than one trace with a colour list, so that the
    # colour encoding appears in the legend. A reader should not have to
    # infer from the surrounding text what the two colours mean.
    for mask, label, colour in (
        (~is_covid, "Crowds present", T.CROWD),
        (is_covid, "Empty / restricted stadiums", T.EMPTY),
    ):
        part = sub[mask]
        if part.empty:
            continue

        # Hover values are formatted here rather than in the template.
        # Under shared-x hover modes a "%{y:.3f}" specifier can be
        # overridden by the axis format, which prints full float
        # precision; pre-formatted strings are immune to that.
        hover = _hover_strings(part)

        fig.add_trace(go.Bar(
            x=part["season"], y=part["yellow_gap"],
            marker=dict(color=colour),
            name=label,
            customdata=hover,
            hovertemplate=(
                "%{customdata[0]} more away bookings per match"
                "<br>%{customdata[1]} home · %{customdata[2]} away"
                "<extra>" + label + "</extra>"
            ),
        ))

    fig.add_hline(y=0, line=dict(color=T.INK, width=1))

    _season_axis(fig, seasons)
    fig.update_layout(
        title="Referee booking bias: extra yellow cards shown to away teams",
        yaxis_title="Away yellows − home yellows (per match)",
        xaxis_title="Season",
        height=430,
        showlegend=True,
        barmode="overlay",
        bargap=0.28,
        hovermode="closest",
    )
    return fig


def _hover_strings(part: pd.DataFrame):
    """Pre-formatted hover values: [signed gap, home mean, away mean]."""
    return [
        [f"{g:+.3f}", f"{h:.2f}", f"{a:.2f}"]
        for g, h, a in zip(
            part["yellow_gap"], part["home_yellows"], part["away_yellows"]
        )
    ]


# --------------------------------------------------------------------------
# Crowd-status comparisons
# --------------------------------------------------------------------------

def crowd_bars(df: pd.DataFrame, value_col: str, title: str,
               y_title: str, suffix: str = "") -> go.Figure:
    """Compare a measure across the three crowd conditions."""
    order = [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST]
    df = df.set_index("crowd_status").reindex(order).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["crowd_status"], y=df[value_col],
        marker=dict(color=[T.CROWD_COLORS[c] for c in df["crowd_status"]]),
        text=[f"{v:,.2f}{suffix}" if abs(v) < 10 else f"{v:,.1f}{suffix}"
              for v in df[value_col]],
        textposition="outside",
        textfont=dict(family=T.FONT_MONO, size=12),
        hovertemplate="%{y:.3f}" + suffix + "<br>%{customdata:,} matches<extra></extra>",
        customdata=df["matches"],
    ))
    fig.update_layout(
        title=title, yaxis_title=y_title, xaxis_title="",
        height=380, showlegend=False, bargap=0.45, hovermode="closest",
    )
    fig.update_xaxes(tickfont=dict(family=T.FONT_BODY, size=11))
    return fig


def league_slope(df: pd.DataFrame, value_col: str, title: str,
                 y_title: str, suffix: str = "") -> go.Figure:
    """
    Slope chart: each league's value under the three crowd conditions.

    A slope chart is used rather than grouped bars because the reader's
    question is about direction of change per league, which a slope
    encodes directly as the tilt of a line.
    """
    order = [T.CROWD_PRE, T.CROWD_EMPTY, T.CROWD_POST]
    short = {T.CROWD_PRE: "Crowds", T.CROWD_EMPTY: "Empty", T.CROWD_POST: "Returned"}

    fig = go.Figure()
    for league, sub in df.groupby("league_short", observed=True):
        sub = sub.set_index("crowd_status").reindex(order).reset_index()
        fig.add_trace(go.Scatter(
            x=[short[c] for c in sub["crowd_status"]],
            y=sub[value_col],
            name=league, mode="lines+markers",
            line=dict(width=2, color=T.LEAGUE_COLORS.get(league)),
            marker=dict(size=8),
            hovertemplate="%{y:.2f}" + suffix + "<extra>" + league + "</extra>",
        ))

    fig.update_layout(
        title=title, yaxis_title=y_title, xaxis_title="Crowd conditions",
        height=420, hovermode="closest",
    )
    return fig


# --------------------------------------------------------------------------
# Venue comparison
# --------------------------------------------------------------------------

def venue_dumbbell(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Home versus away averages for several match statistics.

    Metrics are plotted as a dumbbell so the gap itself — the home
    advantage — is the visually dominant element rather than the two
    absolute values.
    """
    df = df.sort_values("diff")
    fig = go.Figure()

    for _, r in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[r["away"], r["home"]], y=[r["metric"], r["metric"]],
            mode="lines", line=dict(color=T.RULE, width=3),
            showlegend=False, hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter(
        x=df["away"], y=df["metric"], mode="markers", name="Away team",
        marker=dict(size=12, color=T.EMPTY),
        hovertemplate="Away %{x:.2f}<extra>%{y}</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["home"], y=df["metric"], mode="markers", name="Home team",
        marker=dict(size=12, color=T.CROWD),
        hovertemplate="Home %{x:.2f}<extra>%{y}</extra>",
    ))

    fig.update_layout(
        title=title, xaxis_title="Average per match", yaxis_title="",
        height=380, hovermode="closest",
    )
    return fig
