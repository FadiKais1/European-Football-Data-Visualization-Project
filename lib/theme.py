"""
Visual identity for the application.

Colour is used as an analytical variable, not decoration:

    amber  -> matches played in front of a crowd
    steel  -> matches played in empty or restricted stadiums

Because the same amber returns after the COVID window, the palette
itself carries the project's central finding: the crowd effect
disappears and then comes back.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------

INK = "#14202B"          # deep navy-black, primary text
INK_SOFT = "#4A5B69"     # secondary text
MUTED = "#7C8A94"        # captions, axis labels
PAPER = "#F6F7F4"        # cool off-white background
SURFACE = "#FFFFFF"      # cards
RULE = "#DEE3DD"         # hairlines

CROWD = "#C87F1E"        # amber - crowds present
CROWD_LIGHT = "#E3A94E"  # lighter amber - crowds returned
EMPTY = "#2E6F8E"        # steel blue - empty stadiums
EMPTY_LIGHT = "#6FA3BC"

POSITIVE = "#2F7A55"
NEGATIVE = "#A63A32"

# Crowd-status categories, in the order defined by the preprocessing step.
CROWD_PRE = "Crowds present (pre-COVID)"
CROWD_EMPTY = "Empty / restricted stadiums"
CROWD_POST = "Crowds returned (post-COVID)"

CROWD_COLORS = {
    CROWD_PRE: CROWD,
    CROWD_EMPTY: EMPTY,
    CROWD_POST: CROWD_LIGHT,
}

VENUE_COLORS = {"Home": CROWD, "Away": EMPTY}

# Five leagues, chosen to stay distinguishable in greyscale and for the
# most common forms of colour vision deficiency.
LEAGUE_COLORS = {
    "Premier League": "#1F4E79",
    "La Liga": "#C0392B",
    "Serie A": "#2E7D5B",
    "Bundesliga": "#8E5A9B",
    "Ligue 1": "#B4711B",
}

FONT_BODY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_DISPLAY = "Fraunces, Georgia, serif"
FONT_MONO = "'IBM Plex Mono', ui-monospace, monospace"


# --------------------------------------------------------------------------
# Plotly template
# --------------------------------------------------------------------------

def _build_template() -> go.layout.Template:
    axis = dict(
        showgrid=True,
        gridcolor=RULE,
        gridwidth=1,
        zeroline=False,
        linecolor=RULE,
        ticks="outside",
        tickcolor=RULE,
        ticklen=4,
        tickfont=dict(family=FONT_MONO, size=11, color=MUTED),
        title=dict(font=dict(family=FONT_BODY, size=12, color=INK_SOFT)),
        automargin=True,
    )

    return go.layout.Template(
        layout=dict(
            font=dict(family=FONT_BODY, size=13, color=INK),
            title=dict(
                font=dict(family=FONT_DISPLAY, size=19, color=INK),
                x=0, xanchor="left", y=0.97, yanchor="top",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=list(LEAGUE_COLORS.values()),
            xaxis=axis,
            yaxis=axis,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="left", x=0,
                font=dict(size=12, color=INK_SOFT),
                bgcolor="rgba(0,0,0,0)",
                title=dict(font=dict(size=11, color=MUTED)),
            ),
            margin=dict(l=8, r=8, t=64, b=8),
            hoverlabel=dict(
                bgcolor=INK, bordercolor=INK,
                font=dict(family=FONT_BODY, size=12, color="#FFFFFF"),
            ),
            # "closest" rather than "x unified": under shared-x hover a
            # "%{y:.2f}" specifier in a hovertemplate can be overridden by
            # the axis format and print full float precision. Charts that
            # genuinely benefit from a shared label set it locally and
            # pass an explicit yhoverformat.
            hovermode="closest",
            separators=".,",
        )
    )


PLOTLY_TEMPLATE = "matchday"
pio.templates[PLOTLY_TEMPLATE] = _build_template()
pio.templates.default = PLOTLY_TEMPLATE


# --------------------------------------------------------------------------
# Page styling
# --------------------------------------------------------------------------

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

.stApp {{ background: {PAPER}; }}

/* Trim Streamlit's default top padding: on a laptop screen this alone
   pushes the headline figures below the fold. */
.block-container {{ padding-top: 3.4rem !important; padding-bottom: 3rem; }}

html, body, [class*="css"] {{ font-family: {FONT_BODY}; color: {INK}; }}

h1, h2, h3 {{
    font-family: {FONT_DISPLAY};
    color: {INK};
    letter-spacing: -0.015em;
    font-weight: 600;
}}
h1 {{ font-size: 1.95rem; line-height: 1.15; margin-bottom: .15rem; margin-top: .1rem; }}
h2 {{ font-size: 1.3rem; margin-top: 1.8rem; }}
h3 {{ font-size: 1.05rem; margin-top: 1.2rem; }}

/* Eyebrow label above a section: encodes what kind of content follows. */
.eyebrow {{
    font-family: {FONT_MONO};
    font-size: .72rem;
    letter-spacing: .16em;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: .35rem;
}}

.lede {{
    font-size: .96rem;
    line-height: 1.55;
    color: {INK_SOFT};
    max-width: 70ch;
    margin: .1rem 0 .5rem;
}}

/* Scoreboard figures */
.stat-row {{ display: flex; gap: .9rem; flex-wrap: wrap; margin: 1.1rem 0 .4rem; }}
.stat {{
    flex: 1 1 170px;
    background: {SURFACE};
    border: 1px solid {RULE};
    border-radius: 3px;
    padding: .85rem .95rem;
    border-top: 3px solid {RULE};
}}
.stat.amber {{ border-top-color: {CROWD}; }}
.stat.steel {{ border-top-color: {EMPTY}; }}
.stat.amber-light {{ border-top-color: {CROWD_LIGHT}; }}
.stat-label {{
    font-family: {FONT_MONO};
    font-size: .68rem;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: .3rem;
    line-height: 1.35;
}}
.stat-value {{
    font-family: {FONT_MONO};
    font-size: 1.6rem;
    font-weight: 500;
    color: {INK};
    line-height: 1;
    font-variant-numeric: tabular-nums;
}}
.stat-note {{ font-size: .78rem; color: {MUTED}; margin-top: .35rem; }}

/* Caption beneath a chart: states what the reader should take from it. */
.readout {{
    font-size: .85rem;
    color: {INK_SOFT};
    border-left: 2px solid {RULE};
    padding: .1rem 0 .1rem .75rem;
    margin: .1rem 0 1.6rem;
    max-width: 74ch;
}}

.caveat {{
    background: {SURFACE};
    border: 1px solid {RULE};
    border-left: 3px solid {EMPTY};
    border-radius: 3px;
    padding: .85rem 1rem;
    font-size: .85rem;
    color: {INK_SOFT};
    line-height: 1.55;
}}
.caveat strong {{ color: {INK}; }}

hr {{ border: none; border-top: 1px solid {RULE}; margin: 2rem 0 1.2rem; }}

[data-testid="stSidebar"] {{
    background: {SURFACE};
    border-right: 1px solid {RULE};
}}
[data-testid="stSidebar"] h2 {{ font-size: 1.05rem; margin-top: 1rem; }}

[data-testid="stMetricValue"] {{
    font-family: {FONT_MONO};
    font-variant-numeric: tabular-nums;
}}

.stDataFrame {{ font-variant-numeric: tabular-nums; }}

/* Keyboard focus stays visible. */
*:focus-visible {{ outline: 2px solid {EMPTY} !important; outline-offset: 2px; }}

@media (prefers-reduced-motion: reduce) {{
    * {{ animation: none !important; transition: none !important; }}
}}
</style>
"""


def configure_page() -> None:
    """
    Configure the Streamlit page.

    Called once, from the entry script only: st.set_page_config must not
    run more than once per session.
    """
    st.set_page_config(
        page_title="Home Advantage · Europe's Big Five Leagues",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_css() -> None:
    """Apply the shared stylesheet. Safe to call on every rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Small presentation helpers
# --------------------------------------------------------------------------

def eyebrow(text: str) -> None:
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)


def lede(text: str) -> None:
    st.markdown(f'<p class="lede">{text}</p>', unsafe_allow_html=True)


def readout(text: str) -> None:
    """One line under a chart saying what the reader should take from it."""
    st.markdown(f'<div class="readout">{text}</div>', unsafe_allow_html=True)


def caveat(text: str) -> None:
    st.markdown(f'<div class="caveat">{text}</div>', unsafe_allow_html=True)


def stat_row(stats: list[dict]) -> None:
    """
    Scoreboard figures.

    Each dict: {"label": str, "value": str, "note": str, "tone": str}
    where tone is one of "", "amber", "steel", "amber-light".
    """
    cards = []
    for s in stats:
        note = f'<div class="stat-note">{s["note"]}</div>' if s.get("note") else ""
        cards.append(
            f'<div class="stat {s.get("tone", "")}">'
            f'<div class="stat-label">{s["label"]}</div>'
            f'<div class="stat-value">{s["value"]}</div>'
            f"{note}</div>"
        )
    st.markdown(f'<div class="stat-row">{"".join(cards)}</div>', unsafe_allow_html=True)
