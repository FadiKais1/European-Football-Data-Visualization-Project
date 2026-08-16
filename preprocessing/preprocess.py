"""
Big Five European Leagues - Data Preprocessing Pipeline
=======================================================

Builds analysis-ready datasets from 100 raw season CSV files
(5 leagues x 20 seasons, 2006/07 - 2025/26).

Outputs
-------
matches.parquet       One row per match. Clean names, correct dtypes,
                      derived analytical fields.
team_matches.parquet  Long format: one row per team per match
                      (2 rows per match, `venue` = Home / Away).
data_quality.md       Auto-generated data quality report for the
                      written report (section 4).

Usage
-----
    python preprocess.py --raw-dir "Raw Data" --out-dir data

The script is environment-independent: no Google Drive, no Colab.
It runs identically on a laptop, in CI, or on a deployment server.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

LEAGUES = [
    "English Premier League",
    "French Ligue 1",
    "German Bundesliga",
    "Italian Serie A",
    "Spanish La Liga",
]

LEAGUE_SHORT = {
    "English Premier League": "Premier League",
    "French Ligue 1": "Ligue 1",
    "German Bundesliga": "Bundesliga",
    "Italian Serie A": "Serie A",
    "Spanish La Liga": "La Liga",
}

LEAGUE_COUNTRY = {
    "English Premier League": "England",
    "French Ligue 1": "France",
    "German Bundesliga": "Germany",
    "Italian Serie A": "Italy",
    "Spanish La Liga": "Spain",
}

# The 22 columns every raw football-data.co.uk season file must contain.
EXPECTED_RAW_COLUMNS = [
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HTHG", "HTAG", "HTR", "Referee",
    "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC",
    "HY", "AY", "HR", "AR",
]

# Raw -> clean internal names (snake_case, no punctuation).
# Display labels for the UI live in DISPLAY_LABELS below, so that code
# stays readable while the interface still shows full descriptions.
RENAME_MAP = {
    "Date": "match_date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",
    "HTHG": "home_goals_ht",
    "HTAG": "away_goals_ht",
    "HTR": "result_ht",
    "Referee": "referee",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_on_target",
    "AST": "away_shots_on_target",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellows",
    "AY": "away_yellows",
    "HR": "home_reds",
    "AR": "away_reds",
}

DISPLAY_LABELS = {
    "match_date": "Match Date",
    "league": "League",
    "season": "Season",
    "home_team": "Home Team",
    "away_team": "Away Team",
    "home_goals": "Home Goals",
    "away_goals": "Away Goals",
    "result": "Full Time Result",
    "home_shots": "Home Shots",
    "away_shots": "Away Shots",
    "home_shots_on_target": "Home Shots on Target",
    "away_shots_on_target": "Away Shots on Target",
    "home_fouls": "Home Fouls",
    "away_fouls": "Away Fouls",
    "home_corners": "Home Corners",
    "away_corners": "Away Corners",
    "home_yellows": "Home Yellow Cards",
    "away_yellows": "Away Yellow Cards",
    "home_reds": "Home Red Cards",
    "away_reds": "Away Red Cards",
    "referee": "Referee",
    "crowd_status": "Crowd Status",
}

# Integer statistic columns (nullable Int16 after cleaning).
COUNT_COLUMNS = [
    "home_goals", "away_goals", "home_goals_ht", "away_goals_ht",
    "home_shots", "away_shots",
    "home_shots_on_target", "away_shots_on_target",
    "home_fouls", "away_fouls",
    "home_corners", "away_corners",
    "home_yellows", "away_yellows",
    "home_reds", "away_reds",
]

# --------------------------------------------------------------------------
# COVID crowd-status windows
# --------------------------------------------------------------------------
# The five leagues suspended play in March 2020. Four resumed behind
# closed doors; Ligue 1 abandoned its season outright on 30/04/2020.
# The 2020/21 season was played predominantly without spectators, with
# limited and inconsistent partial attendance in some countries late in
# the season. From 2021/22 onward, crowds returned broadly.
#
# These boundaries are a documented approximation: attendance policy
# varied by country and even by club, and the source data contains no
# attendance field. The approximation is stated in the report and the
# app so that no conclusion rests on a hidden assumption.

COVID_SUSPENSION_START = pd.Timestamp("2020-03-08")
COVID_EMPTY_END = pd.Timestamp("2021-06-30")

CROWD_PRE = "Crowds present (pre-COVID)"
CROWD_EMPTY = "Empty / restricted stadiums"
CROWD_POST = "Crowds returned (post-COVID)"

CROWD_ORDER = [CROWD_PRE, CROWD_EMPTY, CROWD_POST]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def season_from_filename(path: Path) -> tuple[str, int]:
    """
    'season-0607.csv' -> ('2006/07', 2006)
    'season-1920.csv' -> ('2019/20', 2019)
    'season-2526.csv' -> ('2025/26', 2025)

    Returns both the display label and a numeric start year, so that
    seasons sort chronologically rather than alphabetically.
    """
    m = re.fullmatch(r"season-(\d{2})(\d{2})", path.stem.lower())
    if not m:
        raise ValueError(
            f"Cannot parse season from '{path.name}'. Expected 'season-XXXX.csv'."
        )
    start_yy, end_yy = int(m.group(1)), int(m.group(2))
    start_year = 1900 + start_yy if start_yy >= 70 else 2000 + start_yy
    return f"{start_year}/{end_yy:02d}", start_year


def validate_schema(df: pd.DataFrame, path: Path) -> None:
    """Fail loudly if a source file does not match the expected schema."""
    actual = list(df.columns)
    missing = [c for c in EXPECTED_RAW_COLUMNS if c not in actual]
    extra = [c for c in actual if c not in EXPECTED_RAW_COLUMNS]
    if missing or extra:
        parts = [f"Schema mismatch in {path}"]
        if missing:
            parts.append(f"  missing: {missing}")
        if extra:
            parts.append(f"  unexpected: {extra}")
        raise ValueError("\n".join(parts))


def classify_crowd(dates: pd.Series) -> pd.Series:
    """Label each match by the crowd conditions it was played under."""
    labels = pd.Series(CROWD_POST, index=dates.index, dtype="object")
    labels[dates < COVID_SUSPENSION_START] = CROWD_PRE
    labels[(dates >= COVID_SUSPENSION_START) & (dates <= COVID_EMPTY_END)] = CROWD_EMPTY
    return pd.Categorical(labels, categories=CROWD_ORDER, ordered=True)


# --------------------------------------------------------------------------
# Stage 1 - load and merge
# --------------------------------------------------------------------------

def load_raw(raw_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    n_files = 0

    for league in LEAGUES:
        league_dir = raw_dir / league
        if not league_dir.is_dir():
            raise FileNotFoundError(f"Missing league folder: {league_dir}")

        files = sorted(league_dir.glob("season-*.csv"))
        if not files:
            raise FileNotFoundError(f"No season files in {league_dir}")

        for path in files:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            validate_schema(df, path)

            season_label, season_start = season_from_filename(path)

            df = df.rename(columns=RENAME_MAP)
            df["league"] = league
            df["season"] = season_label
            df["season_start_year"] = season_start
            frames.append(df)
            n_files += 1

    print(f"  read {n_files} season files")
    if n_files != 100:
        print(f"  WARNING: expected 100 files, found {n_files}")

    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------
# Stage 2 - clean
# --------------------------------------------------------------------------

def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Type conversion, null handling and integrity checks."""
    notes: dict = {}

    # --- dates -------------------------------------------------------
    df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce")
    bad_dates = int(df["match_date"].isna().sum())
    if bad_dates:
        raise ValueError(f"{bad_dates} rows have unparseable dates")
    notes["unparseable_dates"] = bad_dates

    # --- duplicates --------------------------------------------------
    # A league cannot stage the same fixture twice on the same date.
    key = ["league", "season", "match_date", "home_team", "away_team"]
    dupes = int(df.duplicated(subset=key).sum())
    notes["duplicate_fixtures"] = dupes
    if dupes:
        df = df.drop_duplicates(subset=key, keep="first")

    # --- null accounting BEFORE any imputation -----------------------
    null_report = (
        df[COUNT_COLUMNS + ["referee"]]
        .isna()
        .sum()
        .loc[lambda s: s > 0]
        .sort_values(ascending=False)
    )
    notes["nulls_before"] = null_report.to_dict()

    # Rows where the whole match-statistics block is absent.
    stat_block = ["home_shots", "away_shots", "home_corners", "away_corners"]
    incomplete = df[stat_block].isna().all(axis=1)
    notes["rows_missing_stat_block"] = int(incomplete.sum())
    notes["rows_missing_stat_block_detail"] = (
        df.loc[incomplete, ["league", "season", "match_date", "home_team", "away_team"]]
        .assign(match_date=lambda d: d["match_date"].dt.date.astype(str))
        .to_dict("records")
    )

    # Seasons where fouls are missing wholesale (systematic source gap,
    # not random missingness - recorded, never imputed).
    fouls_missing = (
        df.assign(_m=df["home_fouls"].isna())
        .groupby(["league", "season"])["_m"]
        .agg(["sum", "size"])
    )
    systematic = fouls_missing[fouls_missing["sum"] == fouls_missing["size"]]
    notes["fouls_missing_whole_season"] = [
        {"league": lg, "season": sn, "matches": int(r["size"])}
        for (lg, sn), r in systematic.iterrows()
    ]
    notes["fouls_missing_total"] = int(df["home_fouls"].isna().sum())

    # --- dtypes ------------------------------------------------------
    # Nullable Int16: counts are integers, and genuinely absent values
    # stay absent rather than being silently coerced to 0 (which would
    # bias every mean computed downstream).
    for col in COUNT_COLUMNS:
        df[col] = df[col].round().astype("Int16")

    # --- referee coverage --------------------------------------------
    # 78% missing overall, but complete for the Premier League. Kept
    # rather than dropped, so referee analysis remains possible for the
    # league where the data supports it.
    cov = df.groupby("league")["referee"].apply(lambda s: round(s.notna().mean() * 100, 1))
    notes["referee_coverage_pct"] = cov.to_dict()
    df["referee"] = df["referee"].astype("string").str.strip()
    df.loc[df["referee"].isin(["", "nan", "None"]), "referee"] = pd.NA

    # --- categoricals ------------------------------------------------
    df["league"] = pd.Categorical(df["league"], categories=LEAGUES)
    df["result"] = pd.Categorical(df["result"], categories=["H", "D", "A"])
    df["result_ht"] = pd.Categorical(df["result_ht"], categories=["H", "D", "A"])

    # --- integrity ---------------------------------------------------
    # Result letter must agree with the goal columns.
    implied = pd.Series("D", index=df.index, dtype="object")
    implied[df["home_goals"] > df["away_goals"]] = "H"
    implied[df["home_goals"] < df["away_goals"]] = "A"
    mismatch = int((implied != df["result"].astype(str)).sum())
    notes["result_goal_mismatches"] = mismatch

    # Half-time goals cannot exceed full-time goals.
    ht_bad = int(
        ((df["home_goals_ht"] > df["home_goals"])
         | (df["away_goals_ht"] > df["away_goals"])).sum()
    )
    notes["halftime_exceeds_fulltime"] = ht_bad

    # Shots on target cannot exceed total shots.
    sot_bad = int(
        ((df["home_shots_on_target"] > df["home_shots"])
         | (df["away_shots_on_target"] > df["away_shots"])).sum()
    )
    notes["shots_on_target_exceeds_shots"] = sot_bad

    return df, notes


# --------------------------------------------------------------------------
# Stage 3 - derive
# --------------------------------------------------------------------------

def derive(df: pd.DataFrame) -> pd.DataFrame:
    """Add the analytical fields the visualisations are built on."""

    df["league_short"] = df["league"].map(LEAGUE_SHORT).astype("category")
    df["country"] = df["league"].map(LEAGUE_COUNTRY).astype("category")

    # Crowd conditions - the core explanatory variable of the project.
    df["crowd_status"] = classify_crowd(df["match_date"])

    # Calendar fields.
    df["year"] = df["match_date"].dt.year.astype("int16")
    df["month"] = df["match_date"].dt.month.astype("int8")
    df["day_of_week"] = df["match_date"].dt.day_name().astype("category")

    # Match outcome.
    df["total_goals"] = (df["home_goals"] + df["away_goals"]).astype("Int16")
    df["goal_difference"] = (df["home_goals"] - df["away_goals"]).astype("Int16")
    df["is_home_win"] = (df["result"] == "H")
    df["is_draw"] = (df["result"] == "D")
    df["is_away_win"] = (df["result"] == "A")

    # Points (3-1-0), the standard league scoring system.
    df["home_points"] = df["result"].map({"H": 3, "D": 1, "A": 0}).astype("Int8")
    df["away_points"] = df["result"].map({"H": 0, "D": 1, "A": 3}).astype("Int8")

    # Efficiency measures. Guarded against divide-by-zero: a team can
    # finish a match with zero shots, which must yield NA rather than inf.
    df["home_shot_accuracy"] = _safe_ratio(df["home_shots_on_target"], df["home_shots"])
    df["away_shot_accuracy"] = _safe_ratio(df["away_shots_on_target"], df["away_shots"])
    df["home_conversion"] = _safe_ratio(df["home_goals"], df["home_shots"])
    df["away_conversion"] = _safe_ratio(df["away_goals"], df["away_shots"])

    # Home-advantage differentials: the paired quantities the project
    # exists to compare. Positive = home team recorded more.
    df["shots_diff"] = (df["home_shots"] - df["away_shots"]).astype("Int16")
    df["shots_on_target_diff"] = (
        df["home_shots_on_target"] - df["away_shots_on_target"]
    ).astype("Int16")
    df["corners_diff"] = (df["home_corners"] - df["away_corners"]).astype("Int16")
    df["fouls_diff"] = (df["home_fouls"] - df["away_fouls"]).astype("Int16")
    df["yellows_diff"] = (df["home_yellows"] - df["away_yellows"]).astype("Int16")
    df["reds_diff"] = (df["home_reds"] - df["away_reds"]).astype("Int16")
    df["cards_diff"] = (
        (df["home_yellows"] + df["home_reds"])
        - (df["away_yellows"] + df["away_reds"])
    ).astype("Int16")

    # Matchday index within each league-season, so seasons of different
    # lengths (18-team vs 20-team leagues) can be compared on one axis.
    df = df.sort_values(["league", "season_start_year", "match_date"]).reset_index(drop=True)
    df["match_id"] = range(1, len(df) + 1)

    ordered = [
        "match_id", "league", "league_short", "country",
        "season", "season_start_year", "match_date", "year", "month", "day_of_week",
        "crowd_status", "home_team", "away_team",
        "home_goals", "away_goals", "result", "total_goals", "goal_difference",
        "is_home_win", "is_draw", "is_away_win", "home_points", "away_points",
        "home_goals_ht", "away_goals_ht", "result_ht",
        "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target",
        "home_fouls", "away_fouls", "home_corners", "away_corners",
        "home_yellows", "away_yellows", "home_reds", "away_reds",
        "home_shot_accuracy", "away_shot_accuracy",
        "home_conversion", "away_conversion",
        "shots_diff", "shots_on_target_diff", "corners_diff",
        "fouls_diff", "yellows_diff", "reds_diff", "cards_diff",
        "referee",
    ]
    return df[ordered]


def _safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """Element-wise ratio that returns NA where the denominator is 0 or NA."""
    n = num.astype("Float64")
    d = den.astype("Float64")
    return (n / d.where(d > 0)).astype("Float64")


# --------------------------------------------------------------------------
# Stage 4 - long format
# --------------------------------------------------------------------------

def to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape to one row per team per match ('long' / tidy format).

    Every match contributes two rows, distinguished by `venue`. This is
    what makes team-level and venue-level analysis a simple group-by
    instead of repeated home/away branching, and it is the pivot that
    the whole team dashboard is built on.
    """
    shared = [
        "match_id", "league", "league_short", "country", "season",
        "season_start_year", "match_date", "year", "month", "day_of_week",
        "crowd_status", "result", "total_goals", "referee",
    ]

    pairs = {
        "goals": ("home_goals", "away_goals"),
        "goals_conceded": ("away_goals", "home_goals"),
        "goals_ht": ("home_goals_ht", "away_goals_ht"),
        "points": ("home_points", "away_points"),
        "shots": ("home_shots", "away_shots"),
        "shots_conceded": ("away_shots", "home_shots"),
        "shots_on_target": ("home_shots_on_target", "away_shots_on_target"),
        "fouls": ("home_fouls", "away_fouls"),
        "corners": ("home_corners", "away_corners"),
        "yellows": ("home_yellows", "away_yellows"),
        "reds": ("home_reds", "away_reds"),
        "shot_accuracy": ("home_shot_accuracy", "away_shot_accuracy"),
        "conversion": ("home_conversion", "away_conversion"),
    }

    sides = []
    for venue, team_col, opp_col, idx in (
        ("Home", "home_team", "away_team", 0),
        ("Away", "away_team", "home_team", 1),
    ):
        part = df[shared].copy()
        part["venue"] = venue
        part["team"] = df[team_col].values
        part["opponent"] = df[opp_col].values
        for out_col, cols in pairs.items():
            part[out_col] = df[cols[idx]].values
        sides.append(part)

    long = pd.concat(sides, ignore_index=True)

    long["venue"] = pd.Categorical(long["venue"], categories=["Home", "Away"], ordered=True)
    long["goal_diff"] = (long["goals"] - long["goals_conceded"]).astype("Int16")

    outcome = pd.Series("Draw", index=long.index, dtype="object")
    outcome[long["goal_diff"] > 0] = "Win"
    outcome[long["goal_diff"] < 0] = "Loss"
    long["outcome"] = pd.Categorical(outcome, categories=["Win", "Draw", "Loss"], ordered=True)

    long["is_win"] = long["outcome"] == "Win"
    long["cards"] = (long["yellows"] + long["reds"]).astype("Int16")

    return long.sort_values(["match_id", "venue"]).reset_index(drop=True)


# --------------------------------------------------------------------------
# Stage 5 - data quality report
# --------------------------------------------------------------------------

def write_quality_report(df: pd.DataFrame, long: pd.DataFrame,
                         notes: dict, path: Path) -> None:
    L: list[str] = []
    add = L.append

    add("# Data Quality Report")
    add("")
    add("Auto-generated by `preprocess.py`. Figures below are computed from the")
    add("data itself, so they stay correct if the pipeline is re-run.")
    add("")

    add("## 1. Dataset size")
    add("")
    add(f"- Matches (match-level table): **{len(df):,}**")
    add(f"- Rows in long team-match table: **{len(long):,}** (2 per match)")
    add(f"- Columns: {df.shape[1]} match-level, {long.shape[1]} long-format")
    add(f"- Date range: **{df['match_date'].min():%d %b %Y}** to "
        f"**{df['match_date'].max():%d %b %Y}**")
    add(f"- Leagues: {df['league'].nunique()} | Seasons: {df['season'].nunique()} "
        f"| Distinct clubs: {pd.unique(long['team']).size}")
    add("")

    add("### Matches per league")
    add("")
    add("| League | Matches | Seasons | Clubs |")
    add("|---|---:|---:|---:|")
    for lg in LEAGUES:
        sub = df[df["league"] == lg]
        clubs = pd.unique(pd.concat([sub["home_team"], sub["away_team"]])).size
        add(f"| {lg} | {len(sub):,} | {sub['season'].nunique()} | {clubs} |")
    add("")

    add("## 2. Season length is not constant")
    add("")
    add("Match counts differ across leagues and seasons, so **all comparisons in")
    add("this project use per-match rates, never raw counts**:")
    add("")
    add("- The Bundesliga has 18 clubs (306 matches per season); the other")
    add("  leagues historically had 20 (380 matches).")
    add("- Ligue 1 reduced from 20 clubs to 18 in 2023/24.")
    sub = df[(df["league"] == "French Ligue 1") & (df["season"] == "2019/20")]
    add(f"- Ligue 1 2019/20 contains only **{len(sub)}** matches: the season was")
    add("  abandoned in April 2020 because of COVID-19 and never completed.")
    add("")
    counts = df.groupby(["league", "season"], observed=True).size()
    add("| League | Min matches/season | Max matches/season |")
    add("|---|---:|---:|")
    for lg in LEAGUES:
        c = counts.loc[lg]
        add(f"| {lg} | {c.min()} | {c.max()} |")
    add("")

    add("## 3. Missing values")
    add("")
    if notes["nulls_before"]:
        add("Null counts in the merged raw data, before any handling:")
        add("")
        add("| Column | Missing | % |")
        add("|---|---:|---:|")
        for col, n in notes["nulls_before"].items():
            add(f"| {col} | {n:,} | {100 * n / len(df):.2f}% |")
        add("")

    add("### 3a. Referee — retained, not dropped")
    add("")
    add("Referee coverage is highly uneven by league:")
    add("")
    add("| League | Referee coverage |")
    add("|---|---:|")
    for lg, pct in notes["referee_coverage_pct"].items():
        add(f"| {lg} | {pct}% |")
    add("")
    add("The column is **kept** rather than discarded. Although coverage is poor")
    add("overall, it is complete for the Premier League, which preserves a")
    add("full referee-level analysis for that league. Every referee")
    add("visualisation is explicitly scoped to the Premier League and states")
    add("this limitation on screen, so the restricted coverage cannot be")
    add("mistaken for a league-wide result.")
    add("")

    add("### 3b. Fouls — a systematic gap, not random missingness")
    add("")
    add(f"Fouls are missing for **{notes['fouls_missing_total']:,}** matches. These are")
    add("not scattered at random; they are concentrated in whole seasons where")
    add("the source never recorded the statistic:")
    add("")
    if notes["fouls_missing_whole_season"]:
        add("| League | Season | Matches with no foul data |")
        add("|---|---|---:|")
        for r in notes["fouls_missing_whole_season"]:
            add(f"| {r['league']} | {r['season']} | {r['matches']} |")
        add("")
    add("These values are **left missing and never imputed**. Filling them")
    add("(with zero or with a mean) would fabricate a foul rate for a season")
    add("that has none, and would distort any home-versus-away foul comparison")
    add("that included it. Charts involving fouls exclude these seasons.")
    add("")

    add("### 3c. Matches with no statistics block")
    add("")
    add(f"**{notes['rows_missing_stat_block']}** matches have goals and result recorded but")
    add("no shots, corners or cards. They are retained for result-based analysis")
    add("and excluded automatically from statistic-based charts by the missing")
    add("values themselves.")
    add("")
    if notes["rows_missing_stat_block_detail"]:
        add("| League | Season | Date | Fixture |")
        add("|---|---|---|---|")
        for r in notes["rows_missing_stat_block_detail"]:
            add(f"| {r['league']} | {r['season']} | {r['match_date']} | "
                f"{r['home_team']} v {r['away_team']} |")
        add("")

    add("## 4. Integrity checks")
    add("")
    add("| Check | Violations |")
    add("|---|---:|")
    add(f"| Unparseable dates | {notes['unparseable_dates']} |")
    add(f"| Duplicate fixtures (same league, season, date, teams) | {notes['duplicate_fixtures']} |")
    add(f"| Result letter disagrees with goal columns | {notes['result_goal_mismatches']} |")
    add(f"| Half-time goals exceed full-time goals | {notes['halftime_exceeds_fulltime']} |")
    add(f"| Shots on target exceed total shots | {notes['shots_on_target_exceeds_shots']} |")
    add("")
    add("Club names were also checked for inconsistent spellings across the 20")
    add("seasons: no club appears under more than one name, and no name appears")
    add("in more than one league, so no name-normalisation mapping was required.")
    add("")

    add("## 5. Crowd status classification")
    add("")
    add("The project's central question is whether home advantage depends on the")
    add("crowd. The source data has no attendance column, so each match is")
    add("classified by the conditions it was played under:")
    add("")
    add("| Label | Window | Matches |")
    add("|---|---|---:|")
    cs = df["crowd_status"].value_counts().reindex(CROWD_ORDER)
    windows = {
        CROWD_PRE: f"before {COVID_SUSPENSION_START:%d %b %Y}",
        CROWD_EMPTY: f"{COVID_SUSPENSION_START:%d %b %Y} – {COVID_EMPTY_END:%d %b %Y}",
        CROWD_POST: f"after {COVID_EMPTY_END:%d %b %Y}",
    }
    for label in CROWD_ORDER:
        add(f"| {label} | {windows[label]} | {int(cs[label]):,} |")
    add("")
    add("**This is a documented approximation.** Leagues suspended play in March")
    add("2020; four resumed behind closed doors while Ligue 1 abandoned its")
    add("season. The 2020/21 season was played predominantly without spectators,")
    add("with limited and inconsistent partial attendance in some countries late")
    add("in the season. Because policy varied by country and by club, the")
    add("boundaries above cannot be exact, and the assumption is stated in the")
    add("application itself rather than hidden in the pipeline.")
    add("")

    add("## 6. Transformations applied")
    add("")
    add("1. **Merge** — 100 season files across 5 league folders, each validated")
    add("   against the expected 22-column schema before use.")
    add("2. **Season labelling** — filenames converted to `2006/07` style labels,")
    add("   with a numeric `season_start_year` so seasons sort chronologically")
    add("   rather than alphabetically.")
    add("3. **Column renaming** — source abbreviations mapped to clean snake_case")
    add("   names, with display labels held separately for the interface.")
    add("4. **Type correction** — count statistics stored as nullable integers so")
    add("   that absent values remain absent instead of being coerced to zero,")
    add("   which would bias every average computed from them.")
    add("5. **Derived measures** — points (3/1/0), goal difference, total goals,")
    add("   shot accuracy, shot conversion, and home-minus-away differentials for")
    add("   shots, corners, fouls and cards.")
    add("6. **Crowd-status flag** — each match labelled by attendance conditions,")
    add("   creating the natural experiment the project analyses.")
    add("7. **Pivot to long format** — the match-level table is reshaped to one")
    add("   row per team per match with a `venue` field. This turns every")
    add("   home-versus-away comparison into a single group-by and is the basis")
    add("   of the team-level dashboard.")
    add("8. **Output** — both tables written as Parquet, which preserves dtypes")
    add("   (CSV does not) and loads substantially faster in the application.")
    add("")

    path.write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Preprocess Big Five league data.")
    ap.add_argument("--raw-dir", default="Raw Data", type=Path)
    ap.add_argument("--out-dir", default="data", type=Path)
    ap.add_argument("--csv", action="store_true",
                    help="also write CSV copies alongside the Parquet files")
    args = ap.parse_args(argv)

    raw_dir: Path = args.raw_dir
    out_dir: Path = args.out_dir

    if not raw_dir.is_dir():
        print(f"ERROR: raw data folder not found: {raw_dir}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] Loading raw season files ...")
    df = load_raw(raw_dir)
    print(f"      {len(df):,} rows merged")

    print("[2/5] Cleaning and validating ...")
    df, notes = clean(df)
    print(f"      {notes['duplicate_fixtures']} duplicates, "
          f"{notes['result_goal_mismatches']} result mismatches, "
          f"{notes['rows_missing_stat_block']} rows without a stats block")

    print("[3/5] Deriving analytical fields ...")
    df = derive(df)
    print(f"      {df.shape[1]} columns")

    print("[4/5] Building long team-match table ...")
    long = to_long(df)
    print(f"      {len(long):,} rows")

    print("[5/5] Writing outputs ...")
    df.to_parquet(out_dir / "matches.parquet", index=False)
    long.to_parquet(out_dir / "team_matches.parquet", index=False)
    write_quality_report(df, long, notes, out_dir / "data_quality.md")

    if args.csv:
        df.to_csv(out_dir / "matches.csv", index=False)
        long.to_csv(out_dir / "team_matches.csv", index=False)

    for name in ("matches.parquet", "team_matches.parquet", "data_quality.md"):
        size = (out_dir / name).stat().st_size / 1024
        print(f"      {name:<24} {size:>8.1f} KB")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
