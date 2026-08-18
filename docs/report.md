# Data Visualization Project — Final Report

## Visual Analysis of the Evolution and Characteristics of Football Across Europe's Big Five Leagues Over 20 Seasons

> **This file mirrors the submitted report.** The submission itself is
> `docs/Data_Visualization_Report.pdf`, which carries the final design,
> selectable text and working hyperlinks. This Markdown copy exists so the
> report is readable and diffable inside the repository.

**Live app:** https://european-football-data-visualization-project-i3x6vbk4mnx64psp2.streamlit.app/

**Source code:** https://github.com/FadiKais1/European-Football-Data-Visualization-Project

| # | Name | ID | # | Name | ID |
|---|---|---|---|---|---|
| 1 | Tom Rosenberg | 211622220 | 3 | Fadi Kees | 324222512 |
| 2 | Ofir Kaplan | 214683336 | 4 | Daniel Ifrim | 318400678 |

*Submitted as a group of four with the lecturer's prior approval.*

**Topic:** a seven-dashboard interactive web application that analyses 36,197 matches from Europe's Big Five football leagues across 20 seasons (2006/07–2025/26). It looks at how match characteristics changed over time, how the leagues differ from each other, and what happened to home advantage when COVID-19 emptied the stadiums.

---

## 1 · Introduction

**Topic description.** In this project we visually analyse football matches from Europe's Big Five leagues (the English Premier League, Spanish La Liga, Italian Serie A, German Bundesliga and French Ligue 1) across 20 seasons, from 2006/07 to 2025/26. The data is at the match level: half-time and full-time results, goals, shots, shots on target, corners, fouls and cards, plus the league, season, date, referee and the two teams.

**The main problem.** We wanted to find out how the characteristics of matches in these leagues changed over two decades, and whether there are consistent differences between the leagues in how they play and what the results look like. With this much data these questions cannot be answered by looking at raw tables. One league-season alone is 380 rows, and the full dataset is 36,197 matches across five leagues and twenty years. Some patterns become obvious the moment you draw them (for example, a refereeing bias that stays steady for fourteen seasons and then suddenly disappears), but the same patterns are basically invisible in a spreadsheet. That is why we built an interactive visualization tool: it makes these trends, differences and anomalies something a user can actually explore.

**Why the topic matters.** Looking at 20 seasons lets us separate short-term ups and downs from real long-term change, and see whether a change happened across European football as a whole or only inside one league. The period also contains a very useful event: between March 2020 and mid-2021, matches were played in empty stadiums while everything else (teams, competitions, pitches, travel) stayed the same. In a field where you cannot run controlled experiments, this is a rare natural experiment, and it let us examine the old question of home advantage directly instead of only in theory.

**Potential users.** Football and sports data analysts who compare trends across leagues and eras; sports journalists who need evidence and visual material; fans who want to explore leagues, seasons and teams beyond basic statistics; researchers and students in sports analytics; and referee or competition administrators, for whom the disciplinary findings are directly relevant to their work.

### Research questions

**Main question:** how have match characteristics and outcomes across Europe's Big Five leagues evolved over the last 20 seasons, and how do these patterns differ between the leagues?

- **Q1 · Home advantage** — how has it changed over time, and how strong is it in each of the five leagues?
- **Q2 · Attacking performance** — how have attacking characteristics and scoring efficiency changed over time?
- **Q3 · Fouls and discipline** — how have disciplinary patterns evolved, and how do they differ between leagues?
- **Q4 · League profiles** — which characteristics most distinguish the five leagues, and have these gaps narrowed or widened?

Each supporting question has its own dashboard in the application (see section 5).

---

## 2 · Data description

**Dataset:** https://github.com/datasets/football-datasets — match data for the five leagues, originally from football-data.co.uk and updated automatically. The raw data is 100 CSV files: 20 seasons for each of the five leagues, organised in one folder per league and named `season-0607.csv` … `season-2526.csv`.

| | | | | | |
|---|---|---|---|---|---|
| **36,197** matches | **100** CSV files | **20** seasons | **207** clubs | **22** columns / file | **67** referees (EPL) |

Date range: 4 Aug 2006 – 24 May 2026. Matches per league: Premier League, Serie A and La Liga 7,600 each; Ligue 1 7,277; Bundesliga 6,120.

Season length is not constant, and this affects every comparison. The Bundesliga has always had 18 clubs (306 matches per season) while the others historically had 20 (380 matches); Ligue 1 dropped to 18 clubs in 2023/24; and Ligue 1 2019/20 has only 279 matches because the season was abandoned in April 2020. For this reason, every comparison in the application uses per-match rates, never raw counts.

**Original data structure.** Each file has 22 columns, mixing temporal, categorical and quantitative information:

| Column | Type | Description |
|---|---|---|
| `Date` | Date | Match date |
| `HomeTeam` / `AwayTeam` | String | The two teams |
| `FTHG` / `FTAG`, `FTR` | Integer, categorical | Full-time goals and result (H / D / A) |
| `HTHG` / `HTAG`, `HTR` | Integer, categorical | The same three at half time |
| `Referee` | String | Match official |
| `HS` / `AS`, `HST` / `AST` | Integer | Shots and shots on target, home / away |
| `HF` / `AF`, `HC` / `AC` | Integer | Fouls committed and corners, home / away |
| `HY` / `AY`, `HR` / `AR` | Integer | Yellow and red cards, home / away |

**Missing values.** The dataset is largely complete, and full-time goals and results are complete everywhere. We checked the three gaps one by one:

| Column | Missing | Share | Nature of the gap |
|---|---|---|---|
| Referee | 28,217 | 77.95% | Systematic — complete for the Premier League, ~5% for Serie A, absent elsewhere |
| Fouls (HF / AF) | 385 | 1.06% | Systematic — 380 of them are the whole of Ligue 1 2006/07 |
| Other statistics | 3–4 | 0.01% | Isolated matches with no statistics block |

---

## 3 · Pre-processing

The raw data arrived as 100 separate files. We wrote the whole pre-processing stage as one reproducible Python script, `preprocess.py`, which runs from the command line on any machine. Anyone with the raw files can regenerate and check our results.

1. **Schema validation and merge.** Every file is checked against the expected 22-column schema before anything else, so a malformed file fails immediately instead of quietly corrupting the merged result. All 100 files had the same structure and were merged into 36,197 matches.

2. **League and season identification.** A league field was added from each file's folder, and a season field was pulled from the filename with a regular expression (`season-2021.csv` → `2020/21`), plus a numeric `season_start_year`. The numeric field is needed because season labels are strings and would otherwise sort alphabetically instead of chronologically in axes and dropdowns.

3. **Date processing and renaming.** `Date` was converted to a real date type (with the conversion checked for failures), and year, month and day-of-week were derived from it. The short column names were replaced with clear internal names (`FTHG` → `home_goals`), with full descriptive labels kept separately for the interface.

4. **Type correction.** Count statistics were stored as nullable integers. This matters for the analysis: with a plain integer type a missing value has to be replaced by something, and replacing it with zero would record "no shots taken" for a match where shots were simply never recorded, biasing every average computed from that column.

5. **Handling of missing values — nothing was imputed.** We handled the three situations separately. *Referee* (77.95% missing) was kept, not removed: the gap is systematic, not random (100% coverage for the Premier League, about 5% for Serie A, zero elsewhere), and dropping the column would have thrown away 7,600 complete Premier League records and an entire line of analysis just to avoid stating a limitation. Dashboard 4 is limited to the Premier League and says so on screen, so the restricted coverage cannot be mistaken for a Europe-wide result. *Fouls:* 380 of the 385 missing values are the whole of Ligue 1 2006/07, a season the source never recorded fouls for. Imputing a mean would invent a foul rate for a season that has none, so these stay missing and are excluded automatically from foul-based charts. *Three isolated matches* have goals and results but no statistics block; they are kept for result-based analysis and drop out of statistic-based charts by themselves.

6. **Integrity checks.** The merged dataset was tested for internal contradictions, and all checks passed: no duplicate fixtures, no match where the result letter disagrees with the goal columns, no half-time score above its full-time score, and no shots-on-target total above the shots total. Club names were also checked across the twenty seasons — no club appears under two spellings and no name appears in two leagues, so no name-normalisation mapping was needed.

7. **Derived measures.** About twenty analytical fields were computed once here instead of repeatedly in the application: points (3–1–0), goal difference, total goals, shot accuracy and conversion (guarded against division by zero), and home-minus-away differences for shots, corners, fouls and cards.

8. **Crowd-status classification.** The source has no attendance column, so each match was labelled by the conditions it was played under: crowds present before 8 March 2020, empty or restricted until 30 June 2021, and crowds returned after that. This derived variable is what makes the natural experiment in Q1 directly analysable. It is an approximation, and we document it as one in section 5.

9. **Pivot to long format.** A second table was produced where each match contributes two rows, one per team, distinguished by a venue field (Home / Away). This turns every home-versus-away comparison into a single grouping operation instead of repeated conditional logic, and it is the basis of the team dashboard.

10. **Output format.** Both tables were written as Parquet rather than CSV. Parquet keeps the data types (CSV would return dates and nullable integers as plain strings), compresses to roughly a quarter of the size, and loads much faster — which matters for a web application that reloads data on interaction.

**Final datasets.**

| File | Rows | Columns | Description |
|---|---|---|---|
| `matches.parquet` | 36,197 | 50 | One row per match, with derived measures |
| `team_matches.parquet` | 72,394 | 34 | One row per team per match (long format) |
| `data_quality.md` | — | — | Auto-generated data quality report |

The quality report is produced by the same script as the data and computes its figures from the dataset itself, so it cannot fall out of date.

---

## 4 · Tools and libraries

| Tool / library | Purpose |
|---|---|
| **Python 3.12** | Main language for the pre-processing pipeline |
| **pandas** | Reading CSVs, merging, type conversion, validation, reshaping to long format, aggregation |
| **PyArrow** | Writing and reading the Parquet output |
| **pathlib, re, argparse** | File discovery; season extraction from filenames; command-line interface for reproducibility |
| **Streamlit** | Multi-page web application: layout, navigation, widgets, caching, session state |
| **Plotly (graph_objects)** | All visualizations — line, bar, heatmap, scatter, slope, dumbbell, dot-plot, bump, stacked-area and Sankey charts, plus interaction and selection events |
| **NumPy** | Numerical operations and correlations. Also the statistical layer in `lib/stats.py`: Wilson score confidence intervals, two-proportion tests, Welch's test and paired tests, implemented directly rather than by adding a statistics dependency |
| **Custom CSS + Google Fonts** | Typography (Fraunces, Inter, IBM Plex Mono), colour tokens and component styling |
| **Streamlit Community Cloud** | Hosting, providing a public URL usable from any browser |
| **GitHub** | Source code hosting and deployment source |
| **Tableau Desktop** | Exploratory prototyping. We first built a workbook of 12 worksheets, 2 dashboards and a 7-point story to test candidate measures and chart forms. Several measures defined there (shot accuracy, conversion rate, cards per 100 fouls, close-match rate, the half-time to full-time transition) were carried into the final application, together with three chart designs: the competitive-balance bump chart, the season-era shape encoding, and the quadrant scatters for the attacking and disciplinary profiles |

**Use of large language models (disclosed as required).** Claude (Anthropic) was used to review the initial pre-processing notebook and point out data quality issues; to help implement the pre-processing pipeline and the Streamlit application; to discuss chart-type choices for particular questions; and to review and edit the text of this report. All analytical decisions, the choice of research questions, the verification of results and the final content of this report are our own work. Every figure quoted in this report was computed from the dataset by the project's own code.

---

## 5 · The solution

The solution is an interactive web application with seven linked dashboards, a guided story walkthrough and a landing page, built with Streamlit and Plotly and deployed publicly. Each supporting research question has its own dashboard.

| Page | Question | Role |
|---|---|---|
| **Home** | — | Landing page: dataset, research questions, headline finding, and navigation to each dashboard |
| **The Story** | — | A seven-step guided walkthrough of the central argument, one claim and one chart per step |
| **1 · Home Advantage** | Q1 | Establishes home advantage, its variation by league, and its response to empty stadiums |
| **2 · Evolution of the Big Five** | Main | Any measure across all league-seasons, result composition, competitive balance, with drill-down |
| **3 · Attacking and Efficiency** | Q2 | Attacking volume against scoring efficiency, and what a half-time lead is worth |
| **4 · Team Deep-Dive** | Main (depth) | From league averages down to individual clubs |
| **5 · Referees and Discipline** | Q3 | League refereeing strictness, and the officiating mechanism at referee level |
| **6 · League Profiles** | Q4 | What distinguishes each league, and whether the leagues are converging |
| **7 · Linked Views** | Main | Four coordinated views over one dataset, each of which both drives and responds to a shared selection |

### The main visualization

The most important chart sits on Dashboard 1: the share of matches won by the home team, by season, across twenty seasons, with the empty-stadium seasons shaded and the long-run average drawn as a reference line. It answers Q1 directly and visibly. A "split by league" toggle redraws it as five lines and shows all five leagues moving in the same direction, which rules out an explanation based on the scheduling or officiating of any single competition.

> **~46%** home wins, stable for fourteen straight seasons · **40.3%** during the empty-stadium period · **43.5%** after crowds returned

Directly beneath it sits the chart that explains the mechanism: the difference between yellow cards shown to away and home teams, per match, by season. Referees booked away teams about 0.31 times more per match, consistently, for fourteen seasons. In empty stadiums this fell to 0.015 (effectively zero), then returned to 0.271 when crowds came back. Bars are amber for seasons played before crowds and steel blue for the empty-stadium seasons, so the collapse registers before the axis is even read.

### How the application is used

The application is designed to be read in sequence but can be explored freely. A user arrives on the Home page, which states the dataset, the research questions and the headline finding, and links to the dashboard answering each question, so the structure is visible before any chart is read. Dashboard 1 then presents the argument, and the rest let the user test it: 2 shows any measure across every league-season, 3 separates attacking volume from efficiency, 4 drills down to individual clubs, 5 tests the mechanism at referee level, 6 compares league profiles, and 7 offers four fully cross-filtered views.

### Interaction

**Global filters with cross-page persistence.** League and season-range filters live in the sidebar and are held in session state, so a selection made on one dashboard stays in force on the others. The pages behave as one linked system rather than independent pages.

**Linking and brushing through selection events.** Two mechanisms are used. On Dashboard 2, clicking a cell in the league-season heatmap drives the detail panel beneath it, which redraws with that season's home and away points table and its distribution of outcomes. Dashboard 7 goes further and implements coordinated multiple views: four charts (a league ranking, a league-season grid, a timeline and a detail panel) share one selection held in session state. Each chart both writes to the selection and reads from it, so there is no master chart — clicking a league in the ranking, a cell in the grid, or dragging a box across the timeline all produce the same state, and every view redraws. Unselected leagues are greyed rather than hidden, so a selection is read against the whole, and a banner reports what is currently selected with a control to release it.

**Local controls and detail on demand.** Each dashboard offers controls suited to its question: a league-split toggle, measure selectors, a crowd-condition selector, minimum-match thresholds for rankings, an era slider. Thresholds are exposed rather than fixed because the right cut-off depends on the question being asked. Every chart supplies values, units and underlying match counts on hover, following the overview-first, detail-on-demand principle.

### Why this solution

**Why a custom web application.** The central analysis compares the same measures across three crowd conditions, five leagues, twenty seasons and two venues at the same time. Doing this in a drag-and-drop tool would have required a derived crowd-status variable, a long-format reshape and per-chart normalisation that such tools do not naturally provide. Building the application ourselves let us design the pre-processing and the presentation together, and let the analytical caveats sit inside the interface instead of in a separate document.

**Why these chart types.** Each chart was chosen for its question, not for variety. Line charts for season timelines, because the question concerns change over an ordered variable. Bar charts with conditional colour for booking bias, because the value is a signed difference and the sign matters. Slope charts for per-league comparison across crowd conditions, because the question is about direction of change, which a slope encodes directly as the tilt of a line. Dumbbell charts for home-versus-away statistics, because the gap is the quantity of interest and a dumbbell makes it the dominant visual element. A heatmap for the league-season grid, because the task is spotting an anomalous cell among a hundred. Bump charts for competitive balance, because the question is which league leads in a given season and how that ordering changes, which a rank line encodes directly while an average conceals it. Quadrant scatters with average crosshairs for the attacking and disciplinary profiles, because they separate two properties a single ratio collapses (how much a league shoots from how well it converts, and how physical a league is from how strictly it is refereed), with marker shape carrying the season era so twenty years of change fit in one plot.

A standardised dot plot is the default view for the league fingerprints, with a radar view offered alongside it. The dot plot is the default because radar encodes magnitude as area, which exaggerates differences, and the shape it draws changes if the axes are reordered; radar is kept as an option because it makes a league's overall shape easier to recognise at a glance, and presenting both lets the reader see the distortion for themselves. A Sankey diagram shows the half-time to full-time transition, because the quantity of interest is how a population divides and recombines between two stages, paired with a row-normalised matrix of the same transition. The pairing is deliberate: a Sankey encodes raw counts, so its band widths mix how often a half-time position arises with what that position is worth, while normalising each row to 100% isolates the second question.

**Why this use of colour.** Colour encodes the analytical variable rather than decorating the page: amber for matches played before a crowd, steel blue for empty stadiums. Because amber returns in the third position of every crowd-condition chart, the palette itself carries the finding — the effect disappears and comes back. Wherever colour carries meaning not already given by an axis label, the categories are exposed in a legend, so no chart depends on its caption to be readable. League colours were chosen to stay distinguishable in greyscale and under common forms of colour vision deficiency.

### Statistical support

Because the project's central claim is that a proportion changed, every headline figure is reported with a 95% confidence interval, and the two key comparisons are tested formally. Wilson score intervals are used rather than the textbook normal approximation, since they stay accurate for the smaller subsets: the empty-stadium window contains 2,255 matches, and individual leagues within it only a few hundred.

The home win rate fell 5.84 percentage points when stadiums emptied (95% CI [3.73, 7.96], p < 0.001) and rose 3.22 points when crowds returned (95% CI [0.95, 5.49], p = 0.006). The booking bias fell 0.295 cards per match (95% CI [0.223, 0.368], p < 0.001, Welch's test) and recovered by 0.256 (p < 0.001).

Each league was also tested separately, and the results are shown as a forest plot on the Home Advantage dashboard. All five moved in the same direction; four reach significance individually, while Serie A does not (−4.03 points, 95% CI [−8.52, +0.45], p = 0.081). The leagues falling short of significance have the widest intervals rather than the smallest effects, which is exactly what a few hundred matches produce. We report this openly because five independently administered competitions moving together is the substance of the argument, and overstating the individual tests would weaken it rather than strengthen it.

Two further checks address the most obvious alternative explanations. First, if a different mix of teams happened to be playing, the effect would be an artefact of composition; pairing every club with its own earlier record removes that, since squad quality, stadium and league are then held constant. Across the 92 clubs that played in both periods, home advantage fell by an average of 12.1 percentage points (95% CI [8.9, 15.4], p < 0.001), and 71 of the 92 declined. Second, the cards-per-foul comparison in section 6 holds player conduct constant and still shows the disciplinary gap collapsing and recovering. The tests are implemented directly on NumPy in `lib/stats.py` rather than by adding a statistics dependency.

### Advantages

- It answers a question that could not be answered without it — the disappearance and return of referee bias is invisible in the raw files.
- The central claim is quantified, not just asserted: confidence intervals, formal tests, a per-league forest plot, and two robustness checks.
- Every claim is checkable — filters, toggles and cross-filtering let a user reproduce or challenge each statement.
- The dashboards form a real hierarchy (argument, exploration, drill-down, mechanism, context), not variations of one view.
- Limitations are visible in the product, right beside the charts they qualify.
- The pipeline is reproducible: one command regenerates the datasets and the quality report from the raw files.

### Disadvantages and limitations

- Streamlit reloads the page on interaction, so cross-filtering is less immediate than in a purpose-built JavaScript app; caching reduces but does not remove the redraw.
- Cross-filtering is confined to Dashboard 7; extending it to every page would have required a different framework.
- Crowd status is inferred, not measured — the classification is date-based and approximate; policy varied by country and club, and some matches in the middle window had partial crowds.
- Dashboard 4 covers one league, since referee names exist only for the Premier League. The mechanism is demonstrated, not proven Europe-wide.
- The empty-stadium window is short (about 2,255 matches) — enough for league-level conclusions but thin for individual clubs and referees, hence the sample-size warnings on those views.
- Free hosting suspends inactive applications, so the first visit after a quiet period may show a brief loading screen.

---

## 6 · Findings

**Home advantage (Q1).** Home teams won 45.1% of all matches and away teams 29.3%, averaging 1.61 points per match at home against 1.14 away. The advantage exists in all five leagues — largest in La Liga (46.9%) and smallest in Serie A (44.2%). The crowd is a substantial part of it: 46.2% home wins with crowds, 40.3% in empty stadiums, 43.5% after they returned — a fall of 5.84 percentage points (95% CI [3.73, 7.96], p < 0.001) and a partial recovery of 3.22 points (p = 0.006). All five leagues moved in the same direction.

**Attacking performance (Q2).** Scoring rose modestly, from 2.48 goals per match in 2006/07 to 2.76 in 2025/26, but volume and efficiency did not move together: the correlation between shots per match and conversion rate across league-seasons is negative, so shooting more means shooting from worse positions. The Premier League has the highest shot accuracy (41.2%), while conversion sits within one percentage point across all five leagues — the leagues differ far more in how much they shoot than in how well they finish. A half-time lead converts to a home win 79% of the time.

**Fouls and discipline (Q3).** Referees showed away teams about 0.31 more yellow cards per match than home teams for fourteen consecutive seasons; the gap fell to 0.015 in empty stadiums and recovered to 0.271. Interpreting this required care, and we revised the analysis once we examined the differentials properly. Every home-away gap narrowed without a crowd, not only the disciplinary one: the shooting advantage kept 51% of its size, shots on target 50%, corners 40%. What separates them is magnitude — the booking advantage kept under 5%. The cleanest evidence holds conduct constant: measured as cards per 100 fouls committed, away teams were 1.68 percentage points more likely to be punished than home teams with crowds present, 0.36 points in empty stadiums, and 1.84 points once crowds returned. Since the offence is held constant, this cannot be explained by away teams fouling differently. The crowd affected both players and officials, but its effect on officiating was close to total while its effect on play was partial.

**League profiles (Q4).** The leagues keep recognisable identities — Serie A and La Liga are the most heavily refereed (4.71 and 5.31 cards per match against the Premier League's 3.50), and the Bundesliga is the highest-scoring (2.99 goals) — but they have converged sharply. Since 2007/08 the spread between leagues has fallen from about 6.0 to 1.8 in fouls per match, 0.86 to 0.31 in cards, and 3.2 to 0.74 in shots. Goals are the exception. European football has grown more uniform in how it is officiated and how intensely it is played, while keeping distinct attacking characters.

**Interpretation and caution.** The comparison is observational, not a randomised experiment, and other things changed in 2020 too — fixture congestion and five substitutions among them. The evidence rests on four properties of the pattern: it appears in five independently administered leagues; it reverses when crowds return; it survives pairing every club with its own earlier record (a mean fall of 12.1 points, p < 0.001, across 92 clubs); and it persists when conduct is held constant. That combination is difficult to explain by scheduling or substitution rules.
