# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Research code for a multi-domain Contextual Risk Index (CRI) over Lisbon and Porto (LES2/FEUP; the article is under review). There is no Python package, test suite, linter, or build: the whole pipeline is a sequence of Jupyter notebooks in `notebook/` that read and write GeoJSON/CSV under `data/`. The committed `data/` outputs are the reproducibility artifacts, so re-running a notebook overwrites files that the paper's results depend on.

## Environment and running

A virtualenv lives at `.venv/` (Python 3.12, with geopandas, verus, and jupyter installed). The system `python3` does not have the dependencies. The pipeline needs verus >= 1.1.1 from PyPI: it reads the city GeoJSON in `HexagonGridGenerator`, normalizes vulnerability with a zero baseline (`value / max_vl`), and applies time windows to the loaded POTIs on every `run()`. The verus source is the author's repo at `~/Developer/verus` (releases: a new `## [X.Y.Z]` section in its CHANGELOG pushed to `main` creates the tag and GitHub release; PyPI publishing is a manual `gh workflow run python-publish.yml --ref vX.Y.Z`).

```bash
source .venv/bin/activate          # or call .venv/bin/python / .venv/bin/jupyter directly
pip install -r requirements.txt    # verus>=1.1.1 provides the hex grid and vulnerability model
jupyter lab notebook/              # notebooks use ../data/... paths, so the kernel cwd must be notebook/
```

Run a notebook headless, in place:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebook/08_CRI_Analysis_All_Scenarios.ipynb
```

For verification without touching outputs, load the result files directly (see "Data contract" below) instead of re-executing notebooks.

## Pipeline architecture

Every layer is rasterized onto the same grid: `verus.grid.HexagonGridGenerator(region="../data/cities/{city}.geojson", edge_length=100)`. Layers are joined on `hex_id`. Any new layer must be built with the same generator, city boundary file, and 100 m edge length, or the `hex_id` joins silently produce missing values (which notebook 06 then fills with 0).

Most notebooks are parameterized by a `city = "Lisbon"` / `"Porto"` variable in an early cell, despite filenames like `04_gini_index_porto`. To process the other city, change that variable. Notebook 01 hardcodes Lisbon (`place_name`, paths, and a per-city `max_vulnerability` in the VERUS config, with the Porto value commented out).

| Step | Notebook | Produces |
|---|---|---|
| L3 vulnerability | `01` (VERUS, POTI CSV, time-window table T1g, scenarios s1–s4 from `time_windows/scenarios_T1g.csv`; `max_vulnerability` is computed as the largest raw value over the scenarios) | `vulnerability_layer/{city}/{City}_vulnerability_zones_s{1..4}.geojson` (value column `VL_normalized_smoothed`), `vulnerability_metadata.json` |
| L1 response / L2 flood risk | `02` converts CityZones 100 m square-cell CSVs (`{layer}/raw/`) to hexagons: nearest-hex mapping, max aggregation, min-max normalization, IDW fill of empty hexes | `response_layer/{City}_mitigation_zones.geojson`, `risk_layer/{City}_flood_zones.geojson` (column `value`). Set `layer`/`type` in the parameters cell to switch. |
| Air quality (Lisbon only) | `03` (comments and variables are in Portuguese) | `risk_layer/Lisboa_qualidade_ar_hexagonos.geojson`. This layer is **not** consumed by 06/08. |
| L4 Gini / L5 income | `04`, `05` (area-weighted from freguesia polygons plus `socioeconomic_data_{city}.json`, using EPSG:3763 for area) | `socioeconomic_layer/{City}_gini_index.geojson` (`gini`), `{City}_median_income.geojson` (`median_inc`) |
| Integration | `06` merges all layers onto the grid, fills NaN with 0, and writes layer figures | `multi_layers/{City}_multi_layer_all_scenarios.geojson`, `figures/{City}_layers.pdf` |
| Exploration | `07` is an earlier or exploratory version of the CRI weighting, polar plots, and folium maps | nothing persisted |
| CRI | `08` is the central notebook | `multi_layers/{City}_multi_layer_all_scenarios_with_CRI.geojson`, `multi_layers/{City}_cri_weights.csv`, `figures/{City}_cri_comparison.pdf` |
| Thesis tables | `10` builds tables from the outputs of 01/06/08 and compares with the article's results read from git commit `7cef902` | `docs/thesis/` (CSV per table, `tables.tex`; `README.md` documents T1g and the scenarios) |
| Sensitivity analysis (Lisbon, not part of the pipeline) | `09` scans activity states over the week and scores scenario sets; helpers in `notebook/cri_utils.py` (CRI functions copied verbatim from 08) and table specs in `notebook/tw_specs.py` | `tw_analysis/` (per-state vulnerability cache, metrics, candidate tables, maps). Delete a `tw_analysis/<table>/` folder to force recomputation. |

### CRI definition (notebook 08, `compute_cri`)

- All indicators are min-max normalized. Gini is normalized **negatively** (`max - x`), and income positively.
- Core score is the entropy-weighted mean of (vulnerability, response, risk). Equity score is the entropy-weighted mean of (gini, income). Weights come from Shannon entropy: `w ∝ 1 − normalized_entropy`, or equal weights when every normalized entropy is ≈1.
- `CRI = core * (1 + gamma * equity)`, then min-max normalized and clipped to [0, 1]. `gamma = 0.5`, although one printed message in the notebook still says 0.4.
- The computation runs once per vulnerability scenario, with response, risk, and equity held fixed.
- Entropy weighting is part of the article's core contribution: improve it, never remove or replace it. Known issue: the vulnerability weight falls as a scenario gets busier. Notebook 09 compares variants that keep entropy weights (section 9.9) and tests their robustness (section 9.10). Decision: the pipeline keeps per-scenario weights (E0); E1wd (weights computed once on all activity states of the week, each weighted by its time fraction; `cri_utils.cri_pooled_weighted`) is reported in the thesis as a sensitivity analysis, not adopted.

### Scenarios (thesis setup)

The pipeline uses table T1g (`data/time_windows/time_windows_T1g.csv`) and one scenario per regime (`data/time_windows/scenarios_T1g.csv`): s1 weekday morning rush (Mon 08:30), s2 weekday late morning (Mon 11:00), s3 weekday night (Mon 21:00), s4 Saturday daytime (Sat 11:00), with the article's per-scenario entropy weights (E0). The article's setup (`default_time_windows.csv`, Sat 10:20 / Mon 08:40 / 12:30 / 17:30) and its results are in git commit `7cef902`, tagged `isc2-paper`. Only Lisbon has been run with this setup; Porto still has the article's vulnerability layers and no CRI.

## Data contract

- All saved layers are EPSG:4326. Area and distance work uses EPSG:3763 (Portugal TM06), and basemap plots use EPSG:3857 (contextily).
- Integrated columns: `hex_id, response_value, risk_value, vulnerability_s{1..4}_value, gini_value, income_value`. Notebook 08 adds `s{n}_cri, s{n}_core_score, s{n}_equity_score`.

## Known inconsistencies (verify before relying on them)

- `03` reads `../data/risk_layer/lisbon.json`. The committed raw file is `risk_layer/raw/lisbon_air_quality.json`.
- `06` has a fallback path without the `../` prefix (`data/response_layer/{city}_hexagonal_mitigation_zones.geojson`), and that file does not exist.
- Up to verus 1.1.0, reusing one `VERUS` instance across `run()` calls carried `vi` values over from the previous scenario. The article's s2–s4 layers (commit `7cef902`) were produced that way. Fixed in verus 1.1.1.
- In `default_time_windows.csv` (article), hospital windows overlap by one minute (`te` = end + 59 s), and no category is active on weekday nights. T1g uses exclusive ends (`te` = end - 1 s).
- CARTO basemap tiles (used by 06 and 08) require an API key. The notebooks read it from the `CARTO_API_KEY` environment variable (appended to the tile URL as `?key=`) and warn when it is missing; without it the tiles carry an "API KEY REQUIRED" watermark. The variable is set in `~/.bashrc`, which non-interactive shells do not load: export it before running the notebooks headless, and never write the key into a file or a notebook output.
- The committed `Porto_multi_layer_all_scenarios_with_CRI.geojson` has **no** CRI columns. Only the Lisbon file contains `s{n}_cri`. `08` has not been run for Porto, or its output was overwritten.
- `*_old.geojson` and `porto_fix.geojson` are superseded variants that remain in the repo.
