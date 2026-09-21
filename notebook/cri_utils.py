"""CRI functions and time-window selection metrics.

normalize_values, compute_entropy_weights, and compute_cri are copied verbatim
from notebook/08_CRI_Analysis_All_Scenarios.ipynb (cell 4). Keep them in sync.
"""

import itertools

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import entropy

# Define CRI Computation Functions

def normalize_values(series, method='min-max', relatioship='positive'):
    """
    Normalize values to 0-1 range
    """
    if method == 'min-max':
        if relatioship == 'positive':
            return (series - series.min()) / (series.max() - series.min())
        elif relatioship == 'negative':
            return (series.max() - series) / (series.max() - series.min())
    elif method == 'z-score':
        return stats.zscore(series)
    else:
        raise ValueError("Method must be 'min-max' or 'z-score'")


def compute_entropy_weights(data_matrix):
    """
    Compute entropy-based weights for indicators using Shannon entropy
    from scipy.stats library for consistency and robustness
    """
    # Handle potential zeros and negative values by adding small constant
    epsilon = 1e-10
    data_matrix = np.maximum(data_matrix, epsilon)

    # Normalize data to create probability distributions for each indicator
    # Each column should sum to 1 (probability distribution)
    prob_matrix = data_matrix / data_matrix.sum(axis=0)

    # Compute Shannon entropy for each column (indicator) using scipy
    shannon_entropy = np.array(
        [entropy(prob_matrix[:, i], base=np.e) for i in range(prob_matrix.shape[1])]
    )

    # Compute maximum possible entropy (when all values are equal)
    max_entropy = np.log(len(data_matrix))

    # Normalize entropy to 0-1 range
    normalized_entropy = shannon_entropy / max_entropy

    # Handle edge case where entropy is maximum (all values equal)
    # In this case, assign equal weights
    if np.allclose(normalized_entropy, 1.0):
        weights = np.ones(len(normalized_entropy)) / len(normalized_entropy)
    else:
        # Compute weights (higher entropy = lower weight, lower diversity = higher weight)
        diversity = 1 - normalized_entropy
        weights = diversity / diversity.sum()

    return weights, shannon_entropy, normalized_entropy


def compute_cri(vulnerability, response, risk, gini, income, gamma=0.5):
    """
    Compute Composite Risk Index using the formula:
    CRI = core_score * (1 + gamma * equity_score)

    Parameters:
    - vulnerability, response, risk: core vulnerability indicators
    - gini, income: equity indicators
    - gamma: equity weight parameter

    Returns:
    - cri: Composite Risk Index values
    - core_score: Core vulnerability score
    - equity_score: Equity score
    - core_weights: Weights used for core indicators
    - equity_weights: Weights used for equity indicators
    - entropy_info: Dictionary with detailed entropy information
    """
    # Normalize all indicators to 0-1 range
    vuln_norm = normalize_values(vulnerability)
    resp_norm = normalize_values(response)
    risk_norm = normalize_values(risk)
    gini_norm = normalize_values(gini, relatioship="negative")
    income_norm = normalize_values(income, relatioship="positive")

    # Compute core score (entropy-weighted average of vulnerability indicators)
    core_indicators = np.column_stack([vuln_norm, resp_norm, risk_norm])
    core_weights, core_entropy, core_norm_entropy = compute_entropy_weights(
        core_indicators
    )
    core_score = np.average(core_indicators, axis=1, weights=core_weights)

    # Compute equity score (entropy-weighted average of equity indicators)
    equity_indicators = np.column_stack([gini_norm, income_norm])
    equity_weights, equity_entropy, equity_norm_entropy = compute_entropy_weights(
        equity_indicators
    )
    equity_score = np.average(equity_indicators, axis=1, weights=equity_weights)

    all_indicators = np.column_stack([vuln_norm, resp_norm, risk_norm, gini_norm, income_norm])
    all_weights, all_entropy, all_norm_entropy = compute_entropy_weights(all_indicators)
    all_score = np.average(all_indicators, axis=1, weights=all_weights)

    # Compute final CRI
    cri = core_score * (1 + gamma * equity_score)

    # Normalize CRI to 0-1 range
    cri = normalize_values(cri, method='min-max', relatioship='positive')
    cri = pd.Series(cri, index=vulnerability.index, name='CRI')
    cri = cri.clip(lower=0, upper=1)  # Ensure CRI is within [0, 1]

    # Prepare detailed entropy information
    entropy_info = {
        "core_entropy": core_entropy,
        "core_normalized_entropy": core_norm_entropy,
        "equity_entropy": equity_entropy,
        "equity_normalized_entropy": equity_norm_entropy,
        "core_indicator_names": ["vulnerability", "response", "risk"],
        "equity_indicator_names": ["gini", "income"],
    }

    return cri, core_score, equity_score, core_weights, equity_weights, entropy_info




# ---------------------------------------------------------------------------
# Time-window helpers
# ---------------------------------------------------------------------------

DAY0 = pd.Timestamp("2023-11-06")  # Monday; time windows cover 2023-11-06..12


def active_state(time_windows_df, epoch):
    """Return the activity state at `epoch` as a sorted tuple of (category, vi).

    Mirrors VERUS._apply_time_windows_to_potis: a window is active when
    ts <= epoch <= te. Categories without an active window keep vi = 0.
    """
    tw = time_windows_df
    act = tw[(tw["ts"] <= epoch) & (tw["te"] >= epoch)]
    return tuple(sorted(set(zip(act["category"], act["vi"]))))


def week_scan(time_windows_df, step_minutes=30, offset_minutes=15):
    """Evaluate the activity state over the week, off the window edges.

    Returns a DataFrame with one row per evaluation time (timestamp, epoch,
    state). Offsets of 15 min avoid the one-minute overlaps at window edges.
    """
    times = pd.date_range(
        DAY0 + pd.Timedelta(minutes=offset_minutes),
        DAY0 + pd.Timedelta(days=7),
        freq=f"{step_minutes}min",
        inclusive="left",
    )
    epochs = (times - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
    rows = [
        {"time": t, "epoch": int(e), "state": active_state(time_windows_df, int(e))}
        for t, e in zip(times, epochs)
    ]
    return pd.DataFrame(rows)


def check_table(time_windows_df):
    """Return overlapping windows within the same category (should be empty)."""
    problems = []
    for cat, g in time_windows_df.sort_values("ts").groupby("category"):
        ts, te = g["ts"].to_numpy(), g["te"].to_numpy()
        for i in range(1, len(g)):
            if ts[i] <= te[i - 1]:
                problems.append((cat, int(ts[i]), int(te[i - 1])))
    return pd.DataFrame(problems, columns=["category", "ts_next", "te_prev"])


def state_label(state):
    return ", ".join(f"{c}={vi:g}" for c, vi in state) if state else "(none)"


# ---------------------------------------------------------------------------
# Discrimination metrics
# ---------------------------------------------------------------------------


def gvf(values, k=5, random_state=42):
    """Goodness of variance fit of k classes from 1D k-means (Jenks-like)."""
    from sklearn.cluster import KMeans

    x = np.asarray(values, dtype=float).reshape(-1, 1)
    sdam = ((x - x.mean()) ** 2).sum()
    if sdam == 0:
        return 0.0
    km = KMeans(n_clusters=k, n_init=10, random_state=random_state).fit(x)
    return 1.0 - km.inertia_ / sdam


def spatial_metrics(cri):
    """Within-scenario spread of a CRI series."""
    q = cri.quantile([0.25, 0.75])
    return {"std": cri.std(), "iqr": q.iloc[1] - q.iloc[0], "gvf5": gvf(cri)}


def top_set(series, frac=0.10):
    n = max(1, int(round(len(series) * frac)))
    return set(series.nlargest(n).index)


def pairwise_temporal(cri_by_scenario, frac=0.10):
    """Temporal distinctness over all pairs of scenarios.

    cri_by_scenario: DataFrame with one CRI column per scenario, same index.
    """
    cols = list(cri_by_scenario.columns)
    rho = cri_by_scenario.corr(method="spearman")
    tops = {c: top_set(cri_by_scenario[c], frac) for c in cols}
    rows = []
    for a, b in itertools.combinations(cols, 2):
        inter = len(tops[a] & tops[b])
        union = len(tops[a] | tops[b])
        rows.append(
            {
                "a": a,
                "b": b,
                "spearman": rho.loc[a, b],
                "jaccard_top": inter / union,
                "mean_abs_diff": (cri_by_scenario[a] - cri_by_scenario[b]).abs().mean(),
            }
        )
    return pd.DataFrame(rows)


def set_summary(cri_by_scenario, frac=0.10):
    """Aggregate temporal distinctness of a scenario set (higher = more distinct)."""
    p = pairwise_temporal(cri_by_scenario, frac)
    return {
        "min_dissim": 1 - p["spearman"].max(),
        "mean_dissim": 1 - p["spearman"].mean(),
        "max_jaccard_top": p["jaccard_top"].max(),
        "mean_jaccard_top": p["jaccard_top"].mean(),
        "mean_abs_diff": p["mean_abs_diff"].mean(),
    }


# ---------------------------------------------------------------------------
# Vulnerability per activity state (cached)
# ---------------------------------------------------------------------------

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

VERUS_CONFIG = {
    # max_vulnerability = 1.0 keeps VL_normalized equal to the raw kernel value,
    # so smoothing never clips and the common rescaling is exact.
    "max_vulnerability": {"Lisbon": 1.0},
    "clustering": {
        "optics": {"min_samples": 5, "xi": 0.05, "min_cluster_size": 5},
        "kmeans": {"init": "predefined", "random_state": 42},
    },
}


def state_table(time_windows_df, step_minutes=30, offset_minutes=15):
    """One row per distinct activity state, with where in the week it occurs."""
    w = week_scan(time_windows_df, step_minutes, offset_minutes)
    w["day"] = w["time"].dt.strftime("%a")
    w["hm"] = w["time"].dt.strftime("%H:%M")
    rows = []
    for i, (state, g) in enumerate(w.groupby("state", sort=False)):
        days = sorted(set(g["day"]), key=WEEKDAYS.index)
        rows.append(
            {
                "state_id": f"S{i:02d}",
                "n_categories": len(state),
                "n_slots": len(g),
                "days": ",".join(days),
                "first_hm": g["hm"].min(),
                "last_hm": g["hm"].max(),
                "rep_time": g["time"].iloc[0],
                "rep_epoch": g["epoch"].iloc[0],
                "label": state_label(state),
                "state": state,
            }
        )
    return pd.DataFrame(rows)


def vulnerability_for_state(poti_df, time_windows_df, grid, epoch, place_name="Lisbon"):
    """Raw smoothed vulnerability per hexagon, with a fresh VERUS per call.

    A fresh assessor avoids the vi carry-over between run() calls on one
    instance (run() overwrites poti_df, so inactive categories would keep the
    previous scenario's vi).
    """
    from verus import VERUS

    assessor = VERUS(place_name=place_name, config=VERUS_CONFIG, verbose=False)
    assessor.load(potis_df=poti_df, time_windows_df=time_windows_df, zones_gdf=grid)
    res = assessor.run(evaluation_time=int(epoch))
    if res.get("vulnerability_zones") is None:
        raise RuntimeError(res.get("error", "VERUS run failed"))
    z = res["vulnerability_zones"]
    return z.set_index("hex_id")["VL_normalized_smoothed"].rename("raw")


def compute_states(poti_df, time_windows_df, grid, out_dir, min_categories=1, log=print):
    """Compute (or load from cache) the raw vulnerability for every state.

    Returns (states DataFrame, DataFrame hex_id x state_id of raw values).
    """
    import os
    import time

    os.makedirs(out_dir, exist_ok=True)
    states = state_table(time_windows_df)
    states.drop(columns="state").to_csv(os.path.join(out_dir, "states.csv"), index=False)
    cols = {}
    for _, s in states[states["n_categories"] >= min_categories].iterrows():
        path = os.path.join(out_dir, f"vuln_{s.state_id}.csv")
        if os.path.exists(path):
            cols[s.state_id] = pd.read_csv(path, index_col="hex_id")["raw"]
            continue
        t0 = time.time()
        v = vulnerability_for_state(poti_df, time_windows_df, grid, s.rep_epoch)
        v.to_csv(path)
        cols[s.state_id] = v
        log(f"{s.state_id} ({s.label}) in {time.time() - t0:.0f}s")
    return states, pd.DataFrame(cols)


# ---------------------------------------------------------------------------
# Time-window tables from a compact spec
# ---------------------------------------------------------------------------

DAY_GROUPS = {"weekday": [0, 1, 2, 3, 4], "weekend": [5, 6], "all": list(range(7))}


def build_table(spec):
    """Expand a spec into the verus time-window format (vi, ts, te, category).

    spec: {category: [(day_group, "HH:MM", "HH:MM", vi), ...]}; "24:00" ends
    at midnight. Ends are exclusive (te = end - 1 s), so consecutive windows
    of one category never overlap.
    """
    rows = []
    for category, windows in spec.items():
        for group, start, end, vi in windows:
            for d in DAY_GROUPS[group]:
                day = DAY0 + pd.Timedelta(days=d)
                ts = day + pd.Timedelta(hours=int(start[:2]), minutes=int(start[3:]))
                te = day + pd.Timedelta(hours=int(end[:2]), minutes=int(end[3:]))
                rows.append(
                    {
                        "vi": vi,
                        "ts": int((ts - pd.Timestamp("1970-01-01")).total_seconds()),
                        "te": int((te - pd.Timestamp("1970-01-01")).total_seconds()) - 1,
                        "category": category,
                    }
                )
    return pd.DataFrame(rows).sort_values(["category", "ts"]).reset_index(drop=True)


def describe_table(time_windows_df):
    """Human-readable (category, days, window, vi) summary of a table."""
    df = time_windows_df.copy()
    s = pd.to_datetime(df["ts"], unit="s")
    e = pd.to_datetime(df["te"] + 1, unit="s")
    df["days"] = s.dt.dayofweek.map(lambda d: "weekday" if d < 5 else "weekend")
    df["window"] = s.dt.strftime("%H:%M") + "-" + e.dt.strftime("%H:%M").replace("00:00", "24:00")
    return (
        df.groupby(["category", "days", "window", "vi"]).size().rename("n_days").reset_index()
    )


# ---------------------------------------------------------------------------
# CRI per state and scenario-set search
# ---------------------------------------------------------------------------


def compute_cri_common_vuln(vulnerability, response, risk, gini, income, gamma=0.5):
    """Diagnostic CRI: same as compute_cri, but vulnerability is taken as
    already normalized by a common max across scenarios (no per-scenario
    min-max), so absolute differences between scenarios survive.
    """
    vuln_norm = vulnerability
    resp_norm = normalize_values(response)
    risk_norm = normalize_values(risk)
    gini_norm = normalize_values(gini, relatioship="negative")
    income_norm = normalize_values(income, relatioship="positive")
    core = np.column_stack([vuln_norm, resp_norm, risk_norm])
    core_w, _, _ = compute_entropy_weights(core)
    equity = np.column_stack([gini_norm, income_norm])
    equity_w, _, _ = compute_entropy_weights(equity)
    core_score = np.average(core, axis=1, weights=core_w)
    equity_score = np.average(equity, axis=1, weights=equity_w)
    cri = pd.Series(core_score * (1 + gamma * equity_score), index=vulnerability.index)
    return cri, core_w


def cri_per_state(V, base, gamma=0.5):
    """CRI for every state column of V (raw vulnerability, index hex_id).

    V is rescaled by its common max across states. `base` holds
    response_value, risk_value, gini_value, income_value indexed by hex_id.
    Returns (vuln, cri, cri_diag, per-state metrics DataFrame).
    """
    base = base.loc[V.index]
    vuln = V / V.to_numpy().max()
    args = [base["response_value"], base["risk_value"], base["gini_value"], base["income_value"]]
    cri, cri_diag, rows = {}, {}, []
    for sid in V.columns:
        c, _, _, core_w, _, _ = compute_cri(vuln[sid], *args, gamma=gamma)
        d, core_w_d = compute_cri_common_vuln(vuln[sid], *args, gamma=gamma)
        cri[sid], cri_diag[sid] = c, d
        sm = spatial_metrics(c)
        rows.append(
            {
                "state_id": sid,
                "vuln_mean": vuln[sid].mean(),
                "vuln_p95": vuln[sid].quantile(0.95),
                "w_vuln": core_w[0],
                "w_resp": core_w[1],
                "w_risk": core_w[2],
                "w_vuln_diag": core_w_d[0],
                **{f"cri_{k}": v for k, v in sm.items()},
            }
        )
    return vuln, pd.DataFrame(cri), pd.DataFrame(cri_diag), pd.DataFrame(rows).set_index("state_id")


def search_sets(cri, candidates, k=4, frac=0.10):
    """Score every k-subset of candidate states by temporal distinctness."""
    rows = []
    for combo in itertools.combinations(candidates, k):
        rows.append({"set": combo, **set_summary(cri[list(combo)], frac)})
    return pd.DataFrame(rows)


def pareto_front(df, maximize, minimize=()):
    """Rows not dominated on the given columns."""
    X = np.column_stack([df[c].to_numpy() for c in maximize] + [-df[c].to_numpy() for c in minimize])
    keep = []
    for i in range(len(X)):
        dominated = np.any(np.all(X >= X[i], axis=1) & np.any(X > X[i], axis=1))
        keep.append(not dominated)
    return df[np.array(keep)]


# ---------------------------------------------------------------------------
# Entropy-weighting variants (all keep Shannon entropy weights)
# ---------------------------------------------------------------------------


def _normalized_indicators(vuln, base):
    """Indicators normalized as in compute_cri. `vuln` may be a pooled series."""
    return {
        "vuln": normalize_values(vuln),
        "resp": normalize_values(base["response_value"]),
        "risk": normalize_values(base["risk_value"]),
        "gini": normalize_values(base["gini_value"], relatioship="negative"),
        "income": normalize_values(base["income_value"], relatioship="positive"),
    }


def floor_weights(weights, floor):
    """Raise weights below `floor` to it and take the difference from the others
    in proportion to their excess over the floor. Keeps the sum at 1."""
    w = np.asarray(weights, dtype=float).copy()
    if floor * len(w) > 1:
        raise ValueError("floor too high for the number of indicators")
    low = w < floor
    deficit = (floor - w[low]).sum()
    excess = w[~low] - floor
    w[low] = floor
    if deficit > 0:
        w[~low] -= deficit * excess / excess.sum()
    return w


def cri_pooled(vuln, base, scenarios, pool=None, gamma=0.5):
    """CRI with entropy weights computed once on indicators pooled over scenarios.

    vuln: DataFrame hex_id x state (common scale). `pool` lists the states whose
    rows are stacked to compute weights and normalization (default: scenarios).
    Normalization and the final min-max also use the pooled range, so the CRI of
    all scenarios shares one scale. Returns (CRI DataFrame, core weights, equity weights).
    """
    pool = list(pool or scenarios)
    base = base.loc[vuln.index]
    n = len(vuln)
    stacked_base = pd.concat([base] * len(pool), ignore_index=True)
    stacked_vuln = pd.concat([vuln[s] for s in pool], ignore_index=True)
    ind = _normalized_indicators(stacked_vuln, stacked_base)
    core_w, _, _ = compute_entropy_weights(np.column_stack([ind["vuln"], ind["resp"], ind["risk"]]))
    equity_w, _, _ = compute_entropy_weights(np.column_stack([ind["gini"], ind["income"]]))

    vmin, vmax = stacked_vuln.min(), stacked_vuln.max()
    resp, risk = ind["resp"].iloc[:n].to_numpy(), ind["risk"].iloc[:n].to_numpy()
    equity = np.average(
        np.column_stack([ind["gini"].iloc[:n], ind["income"].iloc[:n]]), axis=1, weights=equity_w
    )
    raw = {}
    for s in scenarios:
        v = ((vuln[s] - vmin) / (vmax - vmin)).to_numpy()
        core = np.average(np.column_stack([v, resp, risk]), axis=1, weights=core_w)
        raw[s] = core * (1 + gamma * equity)
    raw = pd.DataFrame(raw, index=vuln.index)
    lo, hi = raw.to_numpy().min(), raw.to_numpy().max()
    return (raw - lo) / (hi - lo), core_w, equity_w


def cri_floor(vuln, base, scenarios, floor, gamma=0.5):
    """Per-scenario entropy weights (as compute_cri) with a floor on core weights."""
    base = base.loc[vuln.index]
    out, weights = {}, {}
    for s in scenarios:
        ind = _normalized_indicators(vuln[s], base)
        core_ind = np.column_stack([ind["vuln"], ind["resp"], ind["risk"]])
        eq_ind = np.column_stack([ind["gini"], ind["income"]])
        core_w, _, _ = compute_entropy_weights(core_ind)
        core_w = floor_weights(core_w, floor)
        equity_w, _, _ = compute_entropy_weights(eq_ind)
        c = np.average(core_ind, axis=1, weights=core_w) * (
            1 + gamma * np.average(eq_ind, axis=1, weights=equity_w)
        )
        out[s] = normalize_values(pd.Series(c, index=vuln.index))
        weights[s] = core_w
    return pd.DataFrame(out), weights


def compute_entropy_weights_weighted(data_matrix, row_weights):
    """compute_entropy_weights with row multiplicities (frequency weights).

    Same epsilon, normalization and equal-weight edge case as
    compute_entropy_weights. With integer weights it equals the unweighted
    function on rows replicated that many times; with all weights equal to 1
    it equals compute_entropy_weights. The maximum entropy is ln(sum of weights).
    """
    epsilon = 1e-10
    X = np.maximum(np.asarray(data_matrix, dtype=float), epsilon)
    m = np.asarray(row_weights, dtype=float)[:, None]
    P = X / (m * X).sum(axis=0)
    shannon_entropy = -(m * P * np.log(P)).sum(axis=0)
    normalized_entropy = shannon_entropy / np.log(m.sum())
    if np.allclose(normalized_entropy, 1.0):
        weights = np.ones(len(normalized_entropy)) / len(normalized_entropy)
    else:
        diversity = 1 - normalized_entropy
        weights = diversity / diversity.sum()
    return weights, shannon_entropy, normalized_entropy


def cri_pooled_weighted(vuln, base, scenarios, pool_weights, gamma=0.5):
    """Like cri_pooled, with each pooled state weighted in the entropy.

    pool_weights: {state_id: weight}. Time fractions of the week (summing to 1)
    make the weights invariant to the scan resolution and to splitting a state
    in two, and normalize entropy by ln(N_hex) as the per-scenario method does.
    Returns (CRI DataFrame, core weights, equity weights).
    """
    pool = list(pool_weights)
    base = base.loc[vuln.index]
    n = len(vuln)
    stacked_base = pd.concat([base] * len(pool), ignore_index=True)
    stacked_vuln = pd.concat([vuln[s] for s in pool], ignore_index=True)
    rows_w = np.repeat([pool_weights[s] for s in pool], n)
    ind = _normalized_indicators(stacked_vuln, stacked_base)
    core_w, _, _ = compute_entropy_weights_weighted(
        np.column_stack([ind["vuln"], ind["resp"], ind["risk"]]), rows_w)
    equity_w, _, _ = compute_entropy_weights_weighted(
        np.column_stack([ind["gini"], ind["income"]]), rows_w)

    vmin, vmax = stacked_vuln.min(), stacked_vuln.max()
    resp, risk = ind["resp"].iloc[:n].to_numpy(), ind["risk"].iloc[:n].to_numpy()
    equity = np.average(
        np.column_stack([ind["gini"].iloc[:n], ind["income"].iloc[:n]]), axis=1, weights=equity_w
    )
    raw = {}
    for s in scenarios:
        v = ((vuln[s] - vmin) / (vmax - vmin)).to_numpy()
        core = np.average(np.column_stack([v, resp, risk]), axis=1, weights=core_w)
        raw[s] = core * (1 + gamma * equity)
    raw = pd.DataFrame(raw, index=vuln.index)
    lo, hi = raw.to_numpy().min(), raw.to_numpy().max()
    return (raw - lo) / (hi - lo), core_w, equity_w


def week_fractions(states):
    """Time fraction of the week of each non-empty state (from state_table/states.csv)."""
    s = states[states["n_categories"] > 0]
    return (s["n_slots"] / s["n_slots"].sum()).to_dict()
