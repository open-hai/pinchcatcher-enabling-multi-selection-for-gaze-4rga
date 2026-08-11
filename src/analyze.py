#!/usr/bin/env python3
"""Re-runnable analysis pipeline for a PinchCatcher-shaped dataset.

This implements the statistical plan the paper declares in Sec. 5:

  * two-way repeated-measures ANOVA, technique (5) x target number (3), both
    within-subject, with a sphericity correction (Greenhouse-Geisser);
  * Bonferroni-corrected pairwise post-hoc tests;
  * Wilcoxon signed-rank post-hoc for accidental subselection ratio and error
    rate, "due to violations of the normality assumption";
  * Friedman + Wilcoxon for the questionnaire data;
  * the two trial-exclusion filters of Sec. 5.

A note on sphericity: pingouin warns that its epsilon estimates may be
inaccurate for a two-way within design in which both factors have more than two
levels, which is this design exactly. The pipeline therefore also computes
Greenhouse-Geisser epsilon directly from the participant x level matrix and
writes it to sphericity.csv, so the correction can be inspected rather than
trusted.

The paper's own dataset was never released (see SOURCES.md), so this pipeline
cannot be pointed at it. It is written against the trial-level schema the
paper's Sec. 4.3 measures imply, so it runs on any dataset with that schema.

Usage:
    python src/analyze.py <trials.csv> [--questionnaire q.csv] [--outdir DIR]
"""

import argparse
import json
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinchcatcher import params as P  # noqa: E402
from pinchcatcher import metrics as M  # noqa: E402

REQUIRED = [
    "participant", "technique", "target_number", "tct_ms",
    "n_subselections", "n_distractors_subselected",
    "n_targets_missed", "n_distractors_final", "n_grouped_final",
    "hand_movement_m", "hand_rotation_deg",
]


def load_trials(path):
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SystemExit(f"input is missing required columns: {missing}\n"
                         f"required schema: {REQUIRED}")
    bad = set(df["technique"].unique()) - set(P.TECHNIQUES)
    if bad:
        raise SystemExit(f"unknown technique labels: {sorted(bad)}")
    return df


def apply_exclusions(df):
    """Sec. 5: drop trials where over 50% of targets were not grouped."""
    missed_frac = df["n_targets_missed"] / df["target_number"]
    if P.MISS_EXCLUSION_STRICTNESS == "strictly_greater":
        drop = missed_frac > P.MISS_EXCLUSION_FRACTION
    else:
        drop = missed_frac >= P.MISS_EXCLUSION_FRACTION
    kept = df.loc[~drop].copy()
    info = {
        "trials_in": int(len(df)),
        "trials_excluded_incomplete": int(drop.sum()),
        "percent_excluded_incomplete": round(100.0 * drop.sum() / max(len(df), 1), 3),
        "rule": f"missed fraction {'>' if P.MISS_EXCLUSION_STRICTNESS == 'strictly_greater' else '>='} 0.50",
    }
    return kept, info


def derive(df):
    df = df.copy()
    df["accidental_ratio"] = [
        M.accidental_subselection_ratio(a, b)
        for a, b in zip(df["n_distractors_subselected"], df["n_subselections"])
    ]
    df["error_rate"] = [
        M.error_rate(a, b, c)
        for a, b, c in zip(df["n_targets_missed"], df["n_distractors_final"],
                           df["n_grouped_final"])
    ]
    df["error_free"] = (df["n_targets_missed"] == 0) & (df["n_distractors_final"] == 0)
    return df


def cell_means(df):
    """Per participant x technique x target number, as RM ANOVA needs."""
    g = df.groupby(["participant", "technique", "target_number"], as_index=False)
    agg = g.agg(
        tct_ms=("tct_ms", "mean"),
        accidental_ratio=("accidental_ratio", "mean"),
        error_rate=("error_rate", "mean"),
        hand_movement_m=("hand_movement_m", "mean"),
        hand_rotation_deg=("hand_rotation_deg", "mean"),
        success_rate=("error_free", lambda s: 100.0 * s.mean()),
        n_trials=("tct_ms", "size"),
    )
    agg["inverse_efficiency_ms"] = [
        M.inverse_efficiency_ms(t, s) if s > 0 else np.nan
        for t, s in zip(agg["tct_ms"], agg["success_rate"])
    ]
    return agg


def gg_epsilon(data_wide):
    """Greenhouse-Geisser epsilon for a one-way within factor (subjects x levels)."""
    x = np.asarray(data_wide, dtype=float)
    n, k = x.shape
    if k < 2:
        return 1.0
    s = np.cov(x, rowvar=False, ddof=1)
    sbar = s.mean()
    rowbar = s.mean(axis=1)
    d = s - rowbar[:, None] - rowbar[None, :] + sbar
    num = (k ** 2) * (np.trace(s) / k - sbar) ** 2
    den = (k - 1) * (np.sum(d ** 2))
    if den == 0:
        return 1.0
    return float(np.clip(num / den, 1.0 / (k - 1), 1.0))


def rm_anova(cells, dv):
    import pingouin as pg

    sub = cells.dropna(subset=[dv])
    aov = pg.rm_anova(data=sub, dv=dv, within=["technique", "target_number"],
                      subject="participant", correction=True, detailed=True)
    return aov


def pairwise(cells, dv, factor, test):
    """Bonferroni-corrected pairwise comparisons over one factor's levels."""
    wide = cells.pivot_table(index="participant", columns=factor, values=dv)
    wide = wide.dropna()
    levels = list(wide.columns)
    rows = []
    pairs = list(combinations(levels, 2))
    for a, b in pairs:
        xa, xb = wide[a].to_numpy(), wide[b].to_numpy()
        if test == "wilcoxon":
            if np.allclose(xa, xb):
                stat, p = np.nan, 1.0
            else:
                stat, p = stats.wilcoxon(xa, xb)
            label = "W"
        else:
            stat, p = stats.ttest_rel(xa, xb)
            label = "t"
        rows.append({
            "dv": dv, "factor": factor, "a": a, "b": b,
            "mean_a": float(np.mean(xa)), "mean_b": float(np.mean(xb)),
            "diff": float(np.mean(xa) - np.mean(xb)),
            "stat_kind": label, "stat": float(stat) if stat == stat else None,
            "p_uncorrected": float(p),
            "p_bonferroni": float(min(1.0, p * len(pairs))),
            "n_pairs_in_family": len(pairs),
        })
    return pd.DataFrame(rows)


def questionnaire_analysis(path):
    q = pd.read_csv(path)
    need = {"participant", "technique", "measure", "score"}
    if not need.issubset(q.columns):
        raise SystemExit(f"questionnaire csv needs columns {sorted(need)}")
    out_omni, out_post = [], []
    for measure, sub in q.groupby("measure"):
        wide = sub.pivot_table(index="participant", columns="technique",
                               values="score").dropna()
        if wide.shape[1] < 3 or wide.shape[0] < 3:
            continue
        chi, p = stats.friedmanchisquare(*[wide[c].to_numpy() for c in wide.columns])
        out_omni.append({"measure": measure, "test": "friedman",
                         "chi2": float(chi), "df": wide.shape[1] - 1,
                         "p": float(p), "n": int(wide.shape[0])})
        long = wide.reset_index().melt(id_vars="participant", var_name="technique",
                                       value_name=measure)
        out_post.append(pairwise(long.rename(columns={"technique": "technique"}),
                                 measure, "technique", "wilcoxon"))
    post = pd.concat(out_post, ignore_index=True) if out_post else pd.DataFrame()
    return pd.DataFrame(out_omni), post


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trials", help="trial-level CSV")
    ap.add_argument("--questionnaire", default=None)
    ap.add_argument("--outdir", default="results/analysis")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    raw = load_trials(args.trials)
    kept, excl = apply_exclusions(raw)
    kept = derive(kept)
    cells = cell_means(kept)
    cells.to_csv(os.path.join(args.outdir, "cell_means.csv"), index=False)

    # error-free subset, the paper's second TCT analysis (Sec. 5.1)
    ef = kept.loc[kept["error_free"]].copy()
    excl["trials_excluded_for_errorfree_tct"] = int(len(kept) - len(ef))
    excl["percent_excluded_for_errorfree_tct"] = round(
        100.0 * (len(kept) - len(ef)) / max(len(kept), 1), 3)

    dvs = ["tct_ms", "accidental_ratio", "error_rate",
           "inverse_efficiency_ms", "hand_movement_m", "hand_rotation_deg"]
    nonparametric = {"accidental_ratio", "error_rate"}

    anovas, posthocs, eps_rows = [], [], []
    for dv in dvs:
        aov = rm_anova(cells, dv)
        aov.insert(0, "dv", dv)
        anovas.append(aov)
        for factor in ["technique", "target_number"]:
            wide = cells.pivot_table(index="participant", columns=factor,
                                     values=dv).dropna()
            eps_rows.append({"dv": dv, "factor": factor,
                             "greenhouse_geisser_epsilon": gg_epsilon(wide),
                             "k_levels": wide.shape[1], "n_subjects": wide.shape[0]})
            posthocs.append(pairwise(cells, dv, factor,
                                     "wilcoxon" if dv in nonparametric else "ttest"))

    aov_all = pd.concat(anovas, ignore_index=True)
    post_all = pd.concat(posthocs, ignore_index=True)
    aov_all.to_csv(os.path.join(args.outdir, "rm_anova.csv"), index=False)
    post_all.to_csv(os.path.join(args.outdir, "posthoc.csv"), index=False)
    pd.DataFrame(eps_rows).to_csv(os.path.join(args.outdir, "sphericity.csv"), index=False)

    if len(ef):
        ef_cells = cell_means(ef)
        aov_ef = rm_anova(ef_cells, "tct_ms")
        aov_ef.insert(0, "dv", "tct_ms_error_free")
        aov_ef.to_csv(os.path.join(args.outdir, "rm_anova_tct_error_free.csv"), index=False)

    summary = {
        "input": os.path.abspath(args.trials),
        "exclusions": excl,
        "n_participants": int(raw["participant"].nunique()),
        "n_cells": int(len(cells)),
        "design": {"techniques": sorted(raw["technique"].unique()),
                   "target_numbers": sorted(int(x) for x in raw["target_number"].unique())},
        "dvs_analysed": dvs,
        "outputs": sorted(os.listdir(args.outdir)),
    }
    if args.questionnaire:
        omni, post = questionnaire_analysis(args.questionnaire)
        omni.to_csv(os.path.join(args.outdir, "questionnaire_friedman.csv"), index=False)
        post.to_csv(os.path.join(args.outdir, "questionnaire_posthoc.csv"), index=False)
        summary["questionnaire_measures"] = omni["measure"].tolist()

    with open(os.path.join(args.outdir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print(json.dumps(summary, indent=2))
    print("\n--- RM ANOVA (technique x target number) ---")
    cols = [c for c in ["dv", "Source", "F", "p-unc", "p-GG-corr", "ng2", "eps"]
            if c in aov_all.columns]
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(aov_all[cols].to_string(index=False))


if __name__ == "__main__":
    main()
