# Does home advantage come from the crowd?

An interactive analysis of **36,197 football matches** from Europe's Big Five
leagues (2006/07–2025/26), using the COVID-19 empty-stadium period as a natural
experiment on the source of home advantage.

**🔗 Live application:** _add the Streamlit Cloud URL here after deploying_

> Course project in Information Visualization.
> Tom Rosenberg · Ofir Kaplan · Fadi Kees · Daniel Ifrim

---

## The finding

Home teams win far more often than away teams, and the usual explanations —
travel fatigue, familiarity with the pitch, crowd support — are difficult to
separate because they always occur together. In 2020 they came apart.

| Crowd conditions | Home win rate | Referee booking bias\* |
|---|---:|---:|
| Crowds present (to Mar 2020) | 46.2% | +0.310 |
| **Empty / restricted stadiums** | **40.3%** | **+0.015** |
| Crowds returned (from Jul 2021) | 43.5% | +0.271 |

\* extra yellow cards shown to the away team, per match

Referees booked away teams 0.31 times more per match than home teams —
consistently, for fourteen seasons. In empty stadiums that bias fell to 0.015,
effectively zero, and returned to 0.271 when supporters came back. The *fouls*
gap barely moved across the same period: away teams did not start fouling less,
they stopped being punished more for it.

## Dashboards

| Dashboard | Question it answers |
|---|---|
| **Home Advantage** | How has home advantage changed, and how does it differ by league? |
| **Evolution of the Big Five** | Any measure across all league-seasons, with click-to-drill detail |
| **Attacking & Efficiency** | How have attacking volume and scoring efficiency changed? |
| **Team Deep-Dive** | Does the pattern hold for an individual club? |
| **Referees & Discipline** | How strictly is each league refereed, and do individual officials show the crowd effect? |
| **League Profiles** | What distinguishes the five leagues, and are they converging? |
| **About & Method** | Data source, processing, assumptions, limitations |

Several measures and views — shot accuracy, conversion rate, cards per 100 fouls,
competitive balance, the half-time to full-time transition, and the radar profile —
originate in the group's exploratory Tableau workbook and were reimplemented here.

League and season filters are shared across pages: a selection made on one
dashboard stays in force on the others.

## Quick start

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The application reads the Parquet files in `data/`, which are committed to the
repository, so it runs immediately after cloning.

## Rebuilding the data

The raw CSVs are committed too, so the entire pipeline is reproducible:

```bash
python preprocessing/preprocess.py --raw-dir data/raw --out-dir data
```

This regenerates `matches.parquet`, `team_matches.parquet` and
`data_quality.md`. Add `--csv` to also write CSV copies.

## Running the tests

```bash
python all_pages_test.py
```

Executes every view under four filter states — including season ranges that
exclude the COVID window entirely, which are the likeliest failure paths.

## Deploying

1. Push this repository to GitHub (public).
2. At [share.streamlit.io](https://share.streamlit.io): **New app** → select the
   repository → set the main file to **`streamlit_app.py`** → Deploy.
3. Put the resulting URL at the top of this README and at the top of the report.

Free Streamlit apps sleep after a period without traffic. Open the link once
shortly before submitting so a reviewer arrives at a running application.

## Structure

```
streamlit_app.py              Entry point; declares navigation
views/
  home_advantage.py           Dashboard 1
  explorer.py                 Dashboard 2
  attacking.py                Dashboard 3
  team_deep_dive.py           Dashboard 4
  referees.py                 Dashboard 5
  league_profiles.py          Dashboard 6
  about.py                    Method, assumptions, limitations
lib/
  theme.py                    Colour tokens, CSS, Plotly template
  data.py                     Cached loading, shared filters, aggregation
  charts.py                   Reusable figure builders
preprocessing/
  preprocess.py               Raw CSVs -> Parquet, one command
data/
  raw/                        100 source CSV files, 5 leagues x 20 seasons
  matches.parquet             36,197 matches x 50 columns
  team_matches.parquet        72,394 rows, one per team per match
  data_quality.md             Auto-generated quality report
docs/
  report.md                   Project report (source)
  report.docx                 Project report (submission format)
all_pages_test.py             Smoke tests
```

## Data

Match results and statistics from
[football-data.co.uk](https://www.football-data.co.uk/), obtained via
[github.com/datasets/football-datasets](https://github.com/datasets/football-datasets):
100 CSV files covering 5 leagues × 20 seasons, 36,197 matches, 22 columns each.

## Tools

Python 3.12 · pandas · PyArrow · Streamlit · Plotly · NumPy ·
Streamlit Community Cloud · Tableau (exploratory prototyping)

**LLM use:** Claude (Anthropic) was used to review the initial preprocessing
notebook and identify data quality issues, to assist with implementing the
pipeline and application code, to discuss chart-type choices, and to edit the
written report. All analytical decisions, the choice of research questions, and
verification of results are the group's own work.

## Design notes

Colour encodes the analytical variable rather than decorating the page: **amber**
marks matches played in front of a crowd, **steel blue** marks empty stadiums.
Because amber returns in the third position of every crowd-status chart, the
palette itself carries the finding.

Charts are chosen for the question being asked — slope charts where direction of
change per league matters, dumbbell charts where the gap between two values is
the point, a heatmap where the task is spotting an anomaly among a hundred
combinations. A radar chart was considered for the league profiles and rejected:
radar encodes magnitude as area, which exaggerates differences, and its shape
depends on the arbitrary ordering of the axes.

## Limitations

The source data contains no attendance figures, so crowd conditions are inferred
from the match date, and the boundaries are approximate. The comparison is
observational — other things changed in 2020, including fixture congestion and
five-substitution rules. The strength of the evidence comes from the pattern
holding across five independent leagues and reversing when crowds returned.

Referee names are recorded only for the Premier League, so that dashboard is
scoped to it and says so on screen.
