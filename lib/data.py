"""
Data access layer.

Loads the Parquet files produced by `preprocess.py`, caches them for the
session, and provides the filter controls that are shared across pages.

Filter state lives in `st.session_state`, so a league or season selection
made on one page is still in force when the user moves to another. That
is what makes the four dashboards behave as one linked system rather than
four separate pages.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

LEAGUE_ORDER = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]

# Session-state keys for the cross-page filters.
K_LEAGUES = "flt_leagues"
K_SEASONS = "flt_seasons"
K_TEAM = "sel_team"


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading match data…")
def load_matches() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "matches.parquet")


@st.cache_data(show_spinner="Loading team data…")
def load_team_matches() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "team_matches.parquet")


@st.cache_data
def season_labels() -> list[str]:
    df = load_matches()
    return (
        df[["season", "season_start_year"]]
        .drop_duplicates()
        .sort_values("season_start_year")["season"]
        .tolist()
    )


@st.cache_data
def team_list(leagues: tuple[str, ...] | None = None) -> list[str]:
    tm = load_team_matches()
    if leagues:
        tm = tm[tm["league_short"].isin(leagues)]
    return sorted(tm["team"].dropna().unique().tolist())


# --------------------------------------------------------------------------
# Shared filters
# --------------------------------------------------------------------------

def init_filters() -> None:
    """Seed the shared filter state on first load."""
    seasons = season_labels()
    st.session_state.setdefault(K_LEAGUES, LEAGUE_ORDER.copy())
    st.session_state.setdefault(K_SEASONS, (seasons[0], seasons[-1]))
    st.session_state.setdefault(K_TEAM, None)


def sidebar_filters(show_seasons: bool = True) -> None:
    """Render the shared filter controls in the sidebar."""
    init_filters()
    seasons = season_labels()

    with st.sidebar:
        st.markdown("## Filters")

        chosen = st.multiselect(
            "Leagues",
            options=LEAGUE_ORDER,
            default=st.session_state[K_LEAGUES],
            key="_leagues_widget",
            help="Applies to every page.",
        )
        # Never let the selection empty out - an empty dashboard reads as
        # a bug rather than a choice.
        st.session_state[K_LEAGUES] = chosen or LEAGUE_ORDER.copy()
        if not chosen:
            st.caption("Showing all leagues — select at least one to narrow.")

        if show_seasons:
            lo, hi = st.select_slider(
                "Season range",
                options=seasons,
                value=st.session_state[K_SEASONS],
                key="_seasons_widget",
            )
            st.session_state[K_SEASONS] = (lo, hi)

        st.markdown("---")
        st.caption(
            "Selections carry across all four dashboards. "
            "Reset the season range to 2006/07–2025/26 to see the full period."
        )


def active_leagues() -> list[str]:
    init_filters()
    return st.session_state[K_LEAGUES]


def active_seasons() -> tuple[str, str]:
    init_filters()
    return st.session_state[K_SEASONS]


# --------------------------------------------------------------------------
# Filtering
# --------------------------------------------------------------------------

def apply_filters(df: pd.DataFrame, use_seasons: bool = True) -> pd.DataFrame:
    """Apply the shared league and season filters to any table."""
    init_filters()
    out = df[df["league_short"].isin(st.session_state[K_LEAGUES])]

    if use_seasons:
        lo, hi = st.session_state[K_SEASONS]
        labels = season_labels()
        i, j = labels.index(lo), labels.index(hi)
        keep = set(labels[i : j + 1])
        out = out[out["season"].isin(keep)]

    return out


# --------------------------------------------------------------------------
# Aggregation helpers
# --------------------------------------------------------------------------

def _rate(series: pd.Series) -> float:
    return float(series.mean() * 100)


def home_win_rate(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Home win percentage and match count for each group."""
    g = (
        df.groupby(by, observed=True)
        .agg(
            home_win_pct=("is_home_win", _rate),
            draw_pct=("is_draw", _rate),
            away_win_pct=("is_away_win", _rate),
            matches=("match_id", "size"),
        )
        .reset_index()
    )
    return g


def card_gap(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """
    Yellow-card bias: away bookings minus home bookings, per match.

    A positive value means the away side was booked more often. This is
    the standard proxy for referee bias towards the home crowd.
    """
    g = (
        df.groupby(by, observed=True)
        .agg(
            home_yellows=("home_yellows", "mean"),
            away_yellows=("away_yellows", "mean"),
            matches=("match_id", "size"),
        )
        .reset_index()
    )
    g["yellow_gap"] = (g["away_yellows"] - g["home_yellows"]).astype(float)
    g["home_yellows"] = g["home_yellows"].astype(float)
    g["away_yellows"] = g["away_yellows"].astype(float)
    return g


def venue_means(df: pd.DataFrame, by: list[str], metrics: dict[str, str]) -> pd.DataFrame:
    """
    Mean home and away values for paired metrics, plus their difference.

    `metrics` maps a display name to the column stem, e.g.
    {"Shots": "shots"} reads `home_shots` and `away_shots`.
    """
    rows = []
    for label, stem in metrics.items():
        hcol, acol = f"home_{stem}", f"away_{stem}"
        if by:
            g = (
                df.groupby(by, observed=True)
                .agg(home=(hcol, "mean"), away=(acol, "mean"),
                     matches=("match_id", "size"))
                .reset_index()
            )
        else:
            # No grouping key: a single overall row per metric.
            g = pd.DataFrame({
                "home": [df[hcol].mean()],
                "away": [df[acol].mean()],
                "matches": [len(df)],
            })
        g["metric"] = label
        g["home"] = g["home"].astype(float)
        g["away"] = g["away"].astype(float)
        g["diff"] = g["home"] - g["away"]
        rows.append(g)
    return pd.concat(rows, ignore_index=True)


def season_axis(df: pd.DataFrame) -> list[str]:
    """Season labels present in `df`, in chronological order."""
    return (
        df[["season", "season_start_year"]]
        .drop_duplicates()
        .sort_values("season_start_year")["season"]
        .tolist()
    )


# --------------------------------------------------------------------------
# Season eras
# --------------------------------------------------------------------------
# Four five-season blocks, carried over from the group's Tableau workbook,
# where they were used as a shape encoding. Grouping seasons into eras lets
# a scatter show change over time without needing twenty separate colours.

ERA_BOUNDS = [
    (2006, 2010, "2006/07–2010/11"),
    (2011, 2015, "2011/12–2015/16"),
    (2016, 2020, "2016/17–2020/21"),
    (2021, 2025, "2021/22–2025/26"),
]

ERA_ORDER = [label for _, _, label in ERA_BOUNDS]

# Plotly marker symbols, matching the Tableau shape encoding:
# circle, square, asterisk, triangle.
ERA_SYMBOLS = {
    ERA_ORDER[0]: "circle-open",
    ERA_ORDER[1]: "square-open",
    ERA_ORDER[2]: "asterisk",
    ERA_ORDER[3]: "triangle-up-open",
}


def add_season_era(df: pd.DataFrame) -> pd.DataFrame:
    """Attach an ordered `season_era` column derived from the start year."""
    out = df.copy()
    era = pd.Series(pd.NA, index=out.index, dtype="object")
    for lo, hi, label in ERA_BOUNDS:
        era[out["season_start_year"].between(lo, hi)] = label
    out["season_era"] = pd.Categorical(era, categories=ERA_ORDER, ordered=True)
    return out
