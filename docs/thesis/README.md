# Time Windows, Scenarios and CRI Tables for the Thesis

This folder documents the revised spatiotemporal setup of the Contextual Risk Index (CRI) for Lisbon: the
time-window table T1g, the four evaluation scenarios, and the result tables. Notebook
`notebook/10-thesis_tables.ipynb` generates the CSV files and `tables.tex` from the pipeline outputs.

| File | Content |
|---|---|
| `table1_time_windows_T1g.csv` | Every time window of T1g: category, day type, start, end (exclusive), $v_i$, and whether it matches the article's table |
| `table2_scenarios.csv` | The four scenarios, their evaluation times, the active categories with $v_i$, and the number of active POTIs |
| `table3_vulnerability_cri.csv` | Vulnerability summary, entropy weights of the five indicators, and CRI summary per scenario |
| `table4_scenario_pairs.csv` | Spearman correlation and top-10% overlap of the CRI for each pair of scenarios |
| `table5_article_vs_revised.csv` | The same separation measures for the article's scenarios and for the revised ones |
| `tables.tex` | The five tables in LaTeX (requires `booktabs`) |

## Time-window table T1g

A time window assigns a vulnerability index $v_i$ to every POTI of a category during an interval of the
week. At an evaluation time, a POTI takes the $v_i$ of its category's active window, or 0 when no window
is active. T1g (`data/time_windows/time_windows_T1g.csv`) revises the table used in the article
(`data/time_windows/default_time_windows.csv`) in three ways.

**Window ends are exclusive.** In the article's table a window ended at the last second of its closing
minute, so consecutive hospital windows overlapped for one minute and the hospital POTIs were counted twice
during that minute. In T1g a window ends one second before the next one starts.

**Occupied periods between peaks are covered.** The article's table described only the peaks of each
category. Between them, and on weekday nights, no category was active, so 110 of the 240 weekday half-hours
had no vulnerability at all. T1g fills these periods with $v_i$ values that already exist in the article's
table, so no new vulnerability level is introduced:

- Hospitals are occupied at all hours. Weekday nights (19:00–07:00) take 0.2, the weekend level.
- Stations run off-peak service between the rush hours (09:00–17:00) and in the evening (19:00–24:00, also
  on weekends) at 0.3, their off-peak level. Bus stations follow the same pattern at 0.2 until 22:00.
- Industrial sites and universities remain occupied between the rush hours (09:00–17:00), at their lowest
  daytime level (0.2 and 0.6), so the rush hours stay the maxima.

**Schools stay active only at the gates** (08:00–10:00 and 16:00–18:00, $v_i = 0.4$), as in the article.
Keeping schools active through class hours was tested in notebook 09: schools are 352 of the 776 POTIs,
and all-day activity made the weekday daytime scenarios nearly identical. Attractions and malls keep the
article's windows.

Table 1 lists every window and marks the ones that differ from the article.

## Scenarios

`data/time_windows/scenarios_T1g.csv` defines one scenario per activity regime of the week:

| Scenario | Regime | Evaluation time |
|---|---|---|
| S1 | Weekday morning rush | Monday 2023-11-06 08:30 |
| S2 | Weekday late morning | Monday 2023-11-06 11:00 |
| S3 | Weekday night | Monday 2023-11-06 21:00 |
| S4 | Saturday daytime | Saturday 2023-11-11 11:00 |

The evening rush is not a separate scenario. In every table tested, the morning and evening rush hours
share the same $v_i$ values for transport, hospitals, industry and universities, and their CRI maps are
almost identical (Spearman ≈ 0.99 in notebook 09). The article's Monday 08:40 and 17:30 scenarios show the
same redundancy. Table 2 lists the categories active in each scenario.

## Method settings

- VERUS 1.1.1, 100 m hexagonal grid (6,569 hexagons for Lisbon).
- Vulnerability is normalized with a zero baseline, `value / max_vulnerability`, where `max_vulnerability`
  is the largest raw vulnerability over the four scenarios (recorded in
  `data/vulnerability_layer/lisbon/vulnerability_metadata.json`). The four layers therefore share one scale.
- The CRI follows the article: per-scenario Shannon entropy weights for the core indicators
  (vulnerability, response, flood risk) and the equity indicators (Gini, income), with
  `CRI = core × (1 + γ × equity)`, γ = 0.5, rescaled to [0, 1] within each scenario.

## Correction relative to the article

VERUS up to 1.1.0 carried the $v_i$ values of one evaluation time into the next when several times were
evaluated with the same assessor, as the article's notebook did. Categories inactive at the new time kept
the $v_i$ of the previously evaluated scenario. For example, the article's Monday 08:40 scenario, evaluated
after Saturday 10:20, kept Saturday's values for attractions and malls, which are closed at 08:40. VERUS 1.1.1 applies the time windows to the loaded POTIs on every run, and the revised results are
computed with it. Table 5 uses the article's published CRI as it stands.

## Reproducing

Run, from `notebook/`: `01-spatiotemporal_vulnerability_assessment.ipynb`,
`06-integrated_hexagonal_grid_porto.ipynb`, `08_CRI_Analysis_All_Scenarios.ipynb`, then
`10-thesis_tables.ipynb`. The maps in 06 and 08 use CARTO basemap tiles, which need the
`CARTO_API_KEY` environment variable. The article's code and data are tagged `isc2-paper` (commit `7cef902`). The sensitivity analysis in `09-time_window_selection.ipynb` (time-window
candidates and entropy-weighting variants) is separate and is not needed to reproduce these results.
