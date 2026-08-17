# Data Visualization Project

## Visual Analysis of the Evolution and Characteristics of Football Across Europe's Big Five Leagues Over 20 Seasons

**Link to the project:** _[INSERT STREAMLIT URL HERE]_  **Source code:** _[INSERT GITHUB URL HERE]_

| # | Name | ID | # | Name | ID |
|---|---|---|---|---|---|
| 1 | Tom Rosenberg | 211622220 | 3 | Fadi Kees | _[ID]_ |
| 2 | Ofir Kaplan | _[ID]_ | 4 | Daniel Ifrim | _[ID]_ |

*Submitted as a group of four with the lecturer's prior approval.*

**Topic:** A six-dashboard interactive web application analysing 36,197 matches from Europe's Big Five football leagues across 20 seasons (2006/07–2025/26), examining how match characteristics have evolved, how the leagues differ, and how home advantage responded when COVID-19 emptied the stadiums.

---

## 1. Introduction

**Topic description.** This project visually analyses football matches from Europe's Big Five leagues — the English Premier League, Spanish La Liga, Italian Serie A, German Bundesliga and French Ligue 1 — across 20 seasons, from 2006/07 through 2025/26. The data is match-level: half-time and full-time results, goals, shots, shots on target, corners, fouls and disciplinary cards, together with league, season, date, referee and the two teams.

**The main problem.** The project investigates how the characteristics of football matches across these leagues have changed over two decades, and to what extent consistent differences exist between the leagues in their playing patterns and outcomes.

Because of the volume of data, the number of variables and the temporal dimension, these patterns cannot be identified from raw tables. One league-season is 380 rows; the full dataset is 36,197 matches across five competitions and twenty years. Patterns that become obvious once drawn — a refereeing bias that holds steady for fourteen seasons and then vanishes, or five leagues slowly converging on a common disciplinary standard — are effectively invisible in a spreadsheet. The project therefore uses interactive visualization to make these trends, differences and anomalies explorable.

**Why the topic matters.** Analysing 20 seasons distinguishes short-term fluctuation from long-term change, identifies which characteristics remain stable, and shows whether change occurs across European football as a whole or within individual leagues. The period also contains an analytically valuable event: between March 2020 and mid-2021 matches were played in empty or severely restricted stadiums while every other condition — teams, competitions, pitches, travel — stayed in place. This is a rare natural experiment in a domain where controlled experiments are impossible, and it allows a long-standing question about home advantage to be examined directly rather than argued from theory.

**Potential users.** Football and sports data analysts comparing trends across leagues and eras; sports journalists needing evidence and visual material; fans exploring leagues, seasons and teams beyond basic statistics; researchers and students in sports analytics; and referee or competition administrators, for whom the disciplinary findings have direct professional relevance.

**Research questions.** The analysis is guided by one main question and four supporting questions, each addressed by a dedicated dashboard (see section 5).

> **Main question:** How have match characteristics and outcomes across Europe's Big Five leagues evolved over the last 20 seasons, and how do these patterns differ between leagues?
>
> **1. Home advantage** — how has it changed over time, and how does its strength differ across the five leagues?
> **2. Attacking performance** — how have attacking characteristics and scoring efficiency changed over time?
> **3. Fouls and discipline** — how have disciplinary patterns evolved, and how do they differ between leagues?
> **4. League profiles** — which characteristics most distinguish the five leagues, and have these differences narrowed or widened?

---

## 2. Data description

**Link to the dataset:** https://github.com/datasets/football-datasets — match data for the five leagues, sourced from football-data.co.uk and updated automatically.

The raw data is **100 CSV files**: 20 seasons for each of the five leagues, 2006/07 through 2025/26, organised one folder per league and named `season-0607.csv` … `season-2526.csv`.

| | | | |
|---|---|---|---|
| Raw CSV files | 100 | Date range | 4 Aug 2006 – 24 May 2026 |
| Total matches | 36,197 | Distinct clubs | 207 |
| Columns per file | 22 | Referees (Premier League) | 67 |

Matches per league: Premier League, Serie A and La Liga 7,600 each; Ligue 1 7,277; Bundesliga 6,120.

**Season length is not constant**, which affects every comparison. The Bundesliga has always had 18 clubs (306 matches per season) while the others historically had 20 (380); Ligue 1 reduced to 18 clubs in 2023/24; and Ligue 1 2019/20 holds only 279 matches because the season was abandoned in April 2020. **All comparisons in the application therefore use per-match rates, never raw counts.**

**Original data structure.** Each file contains 22 columns, combining temporal, categorical and quantitative information.

| Column | Type | Description |
|---|---|---|
| Date | Date | Match date |
| HomeTeam / AwayTeam | String | The two teams |
| FTHG / FTAG | Integer | Full time goals, home / away |
| FTR | Categorical | Full time result (H = home win, D = draw, A = away win) |
| HTHG / HTAG | Integer | Half time goals, home / away |
| HTR | Categorical | Half time result |
| Referee | String | Match referee |
| HS / AS | Integer | Shots, home / away |
| HST / AST | Integer | Shots on target, home / away |
| HF / AF | Integer | Fouls committed, home / away |
| HC / AC | Integer | Corners, home / away |
| HY / AY | Integer | Yellow cards, home / away |
| HR / AR | Integer | Red cards, home / away |

**Missing values.** The dataset is largely complete; full-time goals and results are complete throughout. Three gaps were investigated individually:

| Column | Missing | Share | Nature of the gap |
|---|---|---|---|
| Referee | 28,217 | 77.95% | Systematic — complete for the Premier League, ~5% Serie A, absent elsewhere |
| Fouls (HF / AF) | 385 | 1.06% | Systematic — 380 are the whole of Ligue 1 2006/07 |
| Other statistics | 3–4 | 0.01% | Isolated matches with no statistics block |

---

## 3. Pre-processing

The raw data arrived as 100 separate files. Pre-processing was implemented as a single reproducible Python script, `preprocess.py`, runnable from the command line on any machine with no dependency on a particular cloud environment, so the results can be regenerated and verified by anyone holding the raw files.

**1. Schema validation and merge.** Each file is validated against the expected 22-column schema *before* any transformation, so a malformed file fails immediately rather than silently corrupting the merged result. All 100 files proved identical in structure and were concatenated into 36,197 matches.

**2. League and season identification.** A `league` attribute was added from each file's folder. A `season` attribute was extracted from the filename by regular expression (`season-2021.csv` → `2020/21`), together with a numeric `season_start_year` — necessary because season labels are strings and would otherwise sort alphabetically rather than chronologically in axes and dropdowns.

**3. Date processing.** `Date` was converted to a true date type with the conversion checked for failures, and year, month and day-of-week were derived from it.

**4. Column renaming.** Abbreviated names were replaced with clear internal names (`FTHG` → `home_goals`). Full descriptive labels are held separately and applied in the interface, keeping the code readable while the user still sees complete descriptions.

**5. Type correction.** Count statistics were stored as **nullable integers**. This matters analytically: with an ordinary integer type a missing value must be replaced by something, and replacing it with zero would record "no shots taken" for a match where shots were never recorded, biasing every average computed from that column.

**6. Handling of missing values — nothing was imputed.** Three situations were handled separately:

- *Referee (77.95% missing) was **retained**, not removed.* The gap is systematic, not random: coverage is 100% for the Premier League, about 5% for Serie A and zero elsewhere. Discarding the column would have destroyed 7,600 complete Premier League records — an entire line of analysis — merely to avoid stating a limitation. Dashboard 4 is scoped to the Premier League and declares this on screen, so restricted coverage cannot be mistaken for a Europe-wide result.
- *Fouls.* 380 of the 385 missing values are the whole of Ligue 1 2006/07, a season for which the source never recorded fouls. Imputing a mean would invent a foul rate for a season that has none and distort every home-versus-away foul comparison including it. These are **left missing** and excluded automatically from foul-based charts.
- *Three isolated matches* have goals and results but no statistics block. They are kept for result-based analysis and excluded from statistic-based charts by the missing values themselves.

**7. Integrity checks.** The merged dataset was tested for internal contradictions. All passed: no duplicate fixtures; no match where the result letter disagrees with the goal columns; no half-time score exceeding its full-time score; no shots-on-target total exceeding the shots total. Club names were checked for inconsistent spellings across twenty seasons — no club appears under two names and no name appears in two leagues, so no name-normalisation mapping was needed.

**8. Derived measures.** Roughly twenty analytical fields were computed once here rather than repeatedly in the application: points (3–1–0), goal difference, total goals, shot accuracy and conversion (guarded against division by zero), and home-minus-away differentials for shots, shots on target, corners, fouls, yellow cards, red cards and total cards.

**9. Crowd-status classification.** The source has no attendance column, so each match was labelled by the conditions it was played under: *crowds present* before 8 March 2020, *empty or restricted* until 30 June 2021, *crowds returned* thereafter. This derived variable is what makes the natural experiment in supporting question 1 directly analysable. It is an approximation, documented as such in section 5.

**10. Pivot to long format.** A second table was produced in which each match contributes two rows, one per team, distinguished by a `venue` field (Home / Away). This turns every home-versus-away comparison into a single grouping operation instead of repeated conditional logic, and underlies the team dashboard.

**11. Output format.** Both tables were written as **Parquet** rather than CSV. Parquet preserves data types (CSV would return dates and nullable integers as plain strings), compresses to roughly a quarter of the size and loads substantially faster — which matters for a web application that reloads data on interaction.

**Final datasets.**

| File | Rows | Columns | Description |
|---|---|---|---|
| `matches.parquet` | 36,197 | 50 | One row per match, with derived measures |
| `team_matches.parquet` | 72,394 | 34 | One row per team per match (long format) |
| `data_quality.md` | — | — | Auto-generated data quality report |

The quality report is produced by the same script that produces the data, computing its figures from the dataset itself so it cannot fall out of date if the pipeline is re-run.

---

## 4. Tools and libraries

| Tool / library | Purpose |
|---|---|
| **Python 3.12** | Main language for the pre-processing pipeline |
| **pandas** | Reading CSVs, merging, type conversion, validation, reshaping to long format, aggregation |
| **PyArrow** | Writing and reading the Parquet output |
| **pathlib**, **re**, **argparse** | File discovery; season extraction from filenames; command-line interface for reproducibility |
| **Streamlit** | Multi-page web application: layout, navigation, widgets, caching, session state |
| **Plotly** (`graph_objects`) | All visualizations — line, bar, heatmap, scatter, slope, dumbbell and dot-plot charts, plus interaction and selection events |
| **NumPy** | Numerical operations and correlation calculations |
| **Custom CSS** and **Google Fonts** (Fraunces, Inter, IBM Plex Mono) | Typography, colour tokens and component styling |
| **Streamlit Community Cloud** | Hosting, providing a public URL usable from any browser |
| **GitHub** | Source code hosting and deployment source |
| **Tableau Desktop** | Exploratory prototyping. A workbook of 12 worksheets, 2 dashboards and a 7-point story was built first, to test candidate measures and chart forms. Several measures defined there — shot accuracy, conversion rate, cards per 100 fouls, close-match rate and the half-time to full-time transition — were carried into the final application, together with three chart designs: the competitive-balance bump chart, the season-era shape encoding, and the quadrant scatters for attacking and disciplinary profiles |

**Use of large language models.** As required, LLM use is disclosed. **Claude (Anthropic)** was used to review the initial pre-processing notebook and identify data quality issues; to assist with implementing the pre-processing pipeline and the Streamlit application; to discuss chart-type choices for particular analytical questions; and to review and edit the text of this report. All analytical decisions, the choice of research questions, verification of results and the final content of this report are the group's own work. Every figure quoted here was computed from the dataset by the project's own code.

---

## 5. The solution

The solution is an interactive web application of **six linked dashboards**, built with Streamlit and Plotly and deployed publicly. Each supporting research question has a dedicated dashboard.

| Page | Question | Role |
|---|---|---|
| Home | — | Landing page: dataset, research questions, headline finding, and navigation to each dashboard |
| 1. Home Advantage | Supporting 1 | Establishes home advantage, its variation by league, and its response to empty stadiums |
| 2. Evolution of the Big Five | Main | Any measure across all league-seasons, result composition, competitive balance, with drill-down |
| 3. Attacking and Efficiency | Supporting 2 | Attacking volume against scoring efficiency, and what a half-time lead is worth |
| 4. Team Deep-Dive | Main (depth) | From league averages down to individual clubs |
| 5. Referees and Discipline | Supporting 3 | League refereeing strictness, and the officiating mechanism at referee level |
| 6. League Profiles | Supporting 4 | What distinguishes each league, and whether the leagues are converging |

### The main visualization

The most important chart is on Dashboard 1: **the share of matches won by the home team, by season**, across twenty seasons, with the empty-stadium seasons shaded and the long-run average drawn as a reference line. It answers the first supporting question directly and visibly. Home advantage is stable at roughly 46% of matches for fourteen consecutive seasons, falls to 40.3% during the empty-stadium period, and recovers to 43.5% when crowds return. A "split by league" toggle redraws it as five lines, showing all five leagues moving in the same direction — which rules out an explanation based on the scheduling or officiating of any single competition.

Directly beneath sits the chart explaining the mechanism: **the difference between yellow cards shown to away and home teams, per match, by season.** Referees booked away teams about 0.31 times more per match, consistently, for fourteen seasons. In empty stadiums this fell to 0.015 — effectively zero — then returned to 0.271 when crowds came back. Bars are amber for seasons played before crowds and steel blue for the empty-stadium seasons, so the collapse registers before the axis is read.

### How the application is used

It is designed to be read in sequence but explored freely. A user arrives on the **Home** page, which states the dataset, the research questions and the headline finding, and links to the dashboard that answers each question — so the structure of the project is visible before any single chart is read. From there a user typically moves to **Dashboard 1**, which presents the argument. Having seen the claim, they can test it: **Dashboard 2** shows any of nine measures across every league-season as a heatmap, so the user can look for the empty-stadium band where it should appear and confirm its absence where it should not. **Dashboard 3** separates attacking volume from scoring efficiency. **Dashboard 4** moves from averages to individual clubs, asking whether the pattern holds for a team the user knows. **Dashboard 5** tests the mechanism at the level of individual referees. **Dashboard 6** steps back to how the five leagues differ and whether they are converging.

### Interaction

**Global filters with cross-page persistence.** League and season-range filters live in the sidebar and are held in session state, so a selection made on one dashboard remains in force on the others. The five pages behave as one linked system rather than five independent pages.

**Linking and brushing through selection events.** On Dashboard 2, clicking a cell in the league-season heatmap drives the detail panel beneath it, which redraws with that season's home and away points table and its distribution of match outcomes. The user selects the anomaly they noticed in the overview and immediately sees its underlying detail.

**Local controls and detail on demand.** Each dashboard offers controls suited to its question — a league-split toggle, measure selectors, a crowd-condition selector, minimum-match thresholds for rankings, an era slider. Thresholds are exposed rather than fixed because the right cut-off depends on the question being asked. Every chart supplies values, units and underlying match counts on hover, following overview-first, detail-on-demand.

### Why this solution

**Why a custom web application.** The central analysis compares the same measures across three crowd conditions, five leagues, twenty seasons and two venues simultaneously. Expressing this in a drag-and-drop tool would have required a derived crowd-status variable, a long-format reshape and per-chart normalisation that such tools do not naturally provide. Building the application let the pre-processing and the presentation be designed together, and let the analytical caveats sit in the interface rather than in a separate document.

**Why these chart types** — each chosen for its question, not for variety. *Line charts* for season timelines, because the question concerns change over an ordered variable. *Bar charts with conditional colour* for booking bias, because the value is a signed difference and the sign matters. *Slope charts* for per-league comparison across crowd conditions, because the question is about direction of change, which a slope encodes directly as the tilt of a line. *Dumbbell charts* for home-versus-away statistics, because the gap is the quantity of interest and a dumbbell makes it the dominant visual element. *A heatmap* for the league-season grid, because the task is spotting an anomalous cell among a hundred. *Bump charts* for competitive balance, because the question is which league leads in a given season and how that ordering changes, which a rank line encodes directly while an average conceals it. *Quadrant scatters* with average crosshairs for the attacking and disciplinary profiles, because they separate two properties a single ratio collapses — how much a league shoots from how well it converts, and how physical a league is from how strictly it is refereed — with marker shape carrying the season era so twenty years of change fit in one plot. *A standardised dot plot* for the league fingerprints, with a radar view offered alongside it. The dot plot is the default because radar encodes magnitude as area, which exaggerates differences, and the shape it draws changes if the axes are reordered; radar is retained as an option because it makes a league's overall shape easier to recognise at a glance, and presenting both lets the reader see the distortion for themselves. *A Sankey diagram* for the half-time to full-time transition, because the quantity of interest is how a population divides and recombines between two stages, paired with a row-normalised matrix of the same transition. The pairing is deliberate: a Sankey encodes raw counts, so its band widths mix how often a half-time position arises with what that position is worth, while normalising each row to 100% isolates the second question.

**Why this use of colour.** Colour encodes the analytical variable rather than decorating the page: amber for matches played before a crowd, steel blue for empty stadiums. Because amber returns in the third position of every crowd-condition chart, the palette itself carries the finding — the effect disappears and comes back. Wherever colour carries meaning that is not already given by an axis label, the categories are exposed in a legend rather than explained only in the surrounding text, so no chart depends on its caption to be readable. League colours were chosen to stay distinguishable in greyscale and under common forms of colour vision deficiency.

### Advantages

- **It answers a question that could not be answered without it.** The disappearance and return of referee bias is invisible in the raw files.
- **Every claim is checkable** — filters and toggles let the user reproduce or challenge each statement rather than accept a static chart.
- **The six dashboards form a genuine hierarchy** — argument, exploration, drill-down, mechanism, context — not five variations of one view.
- **Limitations are visible in the product**, beside the charts they qualify, rather than buried in documentation.
- **The pipeline is reproducible**: one command regenerates the datasets and the quality report from the raw files.

### Disadvantages and limitations

- **Streamlit reloads the page on interaction**, so cross-filtering is less immediate than in a purpose-built JavaScript application; caching reduces but does not remove the redraw.
- **Selection-based linking exists on one dashboard only.** Plotly selection events work well for the Dashboard 2 heatmap, but fully brushable linking across every page would have needed a different framework.
- **Crowd status is inferred, not measured.** No attendance data exists in the source, so the classification is date-based and approximate; policy varied by country and club, and some matches in the middle window had partial crowds.
- **Dashboard 4 covers one league**, since referee names exist only for the Premier League. The mechanism is demonstrated, not proven Europe-wide.
- **The empty-stadium window is short** — about 2,255 matches, ample for league-level conclusions but thin for individual clubs and referees, hence the sample-size warnings on those views.
- **Free hosting** suspends inactive applications, so the first visit after a quiet period may show a brief loading screen.

---

## 6. Findings

**Home advantage (Q1).** Across all 36,197 matches, home teams won 45.1% and away teams 29.3%, averaging 1.61 points per match at home against 1.14 away. Home advantage exists in all five leagues, largest in La Liga (46.9% home wins) and smallest in Serie A (44.2%). The crowd is a substantial component of it: 46.2% home wins with crowds, 40.3% in empty stadiums, 43.5% after they returned — and the drop appears in all five leagues.

**Attacking performance (Q2).** Scoring has risen modestly, from 2.48 goals per match in 2006/07 to 2.76 in 2025/26, but volume and efficiency have not moved together. Across all league-seasons the correlation between shots per match and conversion rate is negative: shooting more often means shooting from worse positions. The Premier League has the highest shot accuracy (41.5% of shots on target) while conversion rates sit within one percentage point across all five leagues (11.6–12.1%), so leagues differ far more in how much they shoot than in how well they finish. A half-time lead converts to a home win 79% of the time, and from level at half-time the home side still wins substantially more often than the away side — home advantage operating in the second half alone.

**Fouls and discipline (Q3).** The strongest result in the project. Referees showed away teams about 0.31 more yellow cards per match than home teams for fourteen consecutive seasons; the gap fell to 0.015 in empty stadiums and recovered to 0.271 afterwards. Crucially the *fouls* gap barely moved across the same period: away teams did not begin fouling less, they stopped being punished more for it. This locates the change with the officials rather than the players.

**League profiles (Q4).** The leagues keep recognisable identities — Serie A and La Liga are the most heavily refereed (4.71 and 5.31 yellow cards per match against the Premier League's 3.50), the Bundesliga the highest-scoring (2.99 goals per match) — but they have converged sharply. Since 2007/08 the spread between leagues has fallen from about 6.0 to 1.8 in fouls per match, from 0.86 to 0.31 in yellow cards and from 3.2 to 0.74 in shots. Goals are the exception, showing no convergence. European football has grown more uniform in how it is officiated and how intensely it is played, while retaining distinct attacking characters.

**Interpretation and caution.** The COVID comparison is observational, not a randomised experiment. Other things changed in 2020, including fixture congestion and the move to five substitutions. The evidence for the crowd explanation rests on three properties of the pattern: it appears in five independently administered leagues; it reverses when crowds return; and it appears in the disciplinary measures a crowd could plausibly influence while leaving shot and corner counts largely unaffected. That combination is difficult to explain by scheduling or substitution rules.
