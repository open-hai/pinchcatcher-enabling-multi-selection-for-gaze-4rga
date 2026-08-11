#!/usr/bin/env python3
"""Audit the paper's own printed numbers for internal consistency.

The PinchCatcher dataset was never released, so the reported statistics cannot
be recomputed from data. They can, however, be checked against each other:
degrees of freedom, sphericity epsilons, partial eta squared, p-values, trial
counts, exclusion percentages and the scene geometry are all over-determined by
what the paper prints. Every check below either confirms a printed number or
names the one that does not fit.

Usage:
    python src/audit_reported_stats.py [--json results/audit.json]
"""

import argparse
import json
import math
import os
import sys

from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import reported as R  # noqa: E402
from pinchcatcher import design as D  # noqa: E402
from pinchcatcher import layout as L  # noqa: E402
from pinchcatcher import metrics as M  # noqa: E402
from pinchcatcher import params as P  # noqa: E402

TOL_EPS = 5e-4      # rounding slack on epsilon recovered from 3-decimal dfs
TOL_ETA = 6e-4      # eta squared printed to 3 decimals


def check(results, name, ok, detail, kind="consistency"):
    results.append({"check": name, "ok": bool(ok), "kind": kind, "detail": detail})
    return ok


def audit_degrees_of_freedom(res):
    """A GG/HF-corrected F test multiplies both dfs by the same epsilon."""
    worst = 0.0
    for metric, effect, df1c, df2c, F, p, eta, sec in R.ANOVA:
        df1, df2 = R.DF_UNCORRECTED[effect]
        e1, e2 = df1c / df1, df2c / df2
        worst = max(worst, abs(e1 - e2))
        ok = abs(e1 - e2) < TOL_EPS and 1.0 / df1 - 1e-9 <= e1 <= 1.0 + 1e-9
        check(res, f"df/epsilon consistency: {metric} x {effect} (Sec. {sec})", ok,
              {"epsilon_from_df1": round(e1, 6), "epsilon_from_df2": round(e2, 6),
               "difference": round(abs(e1 - e2), 6),
               "epsilon_lower_bound": round(1.0 / df1, 4),
               "implied_N": R.N_PARTICIPANTS})
    check(res, "all 21 F tests imply the same N=30 design and one epsilon per test",
          worst < TOL_EPS, {"max_epsilon_disagreement": round(worst, 6)})


def audit_partial_eta_squared(res):
    """eta_p^2 = F*df1 / (F*df1 + df2) with UNCORRECTED dfs."""
    for metric, effect, df1c, df2c, F, p, eta, sec in R.ANOVA:
        df1, df2 = R.DF_UNCORRECTED[effect]
        recomputed = F * df1 / (F * df1 + df2)
        ok = abs(recomputed - eta) <= TOL_ETA
        check(res, f"partial eta^2: {metric} x {effect} (Sec. {sec})", ok,
              {"reported": eta, "recomputed": round(recomputed, 4),
               "delta": round(recomputed - eta, 5)})


def audit_p_values(res):
    """Recompute each p from F and the corrected dfs."""
    for metric, effect, df1c, df2c, F, p_rep, eta, sec in R.ANOVA:
        p_calc = float(stats.f.sf(F, df1c, df2c))
        if p_rep.startswith("<"):
            ok = p_calc < float(p_rep[1:])
            expect = f"p {p_rep}"
        else:
            target = float(p_rep[1:])
            ok = abs(p_calc - target) <= 0.0015
            expect = f"p {p_rep}"
        check(res, f"p-value: {metric} x {effect} (Sec. {sec})", ok,
              {"reported": expect, "recomputed": f"{p_calc:.3e}",
               "F": F, "df": [df1c, df2c]},
              kind="consistency" if ok else "mismatch")


def audit_subselection_count(res):
    """28385 subselections must square with the design and the reported error rates."""
    per_participant = P.REPETITIONS * sum(P.TARGET_COUNTS) * len(P.TECHNIQUES)
    minimum = per_participant * R.N_PARTICIPANTS
    asr = [m for m in R.MEANS_BY_TECHNIQUE if m[0] == "accidental_ratio_pct"]
    mean_asr = sum(m[2] for m in asr) / len(asr)
    predicted = minimum / (1.0 - mean_asr / 100.0)
    reported = R.COUNTS["subselections_collected"][0]
    rel = abs(predicted - reported) / reported
    check(res, "reported 28385 subselections vs design + reported accidental ratios",
          rel < 0.01,
          {"minimum_if_no_accidents": minimum,
           "mean_accidental_subselection_ratio_pct": round(mean_asr, 3),
           "predicted_total": round(predicted, 1),
           "reported_total": reported,
           "relative_error": f"{rel*100:.2f}%",
           "note": "27000 is the floor: 30 participants x 5 techniques x 15 reps "
                   "x (2+4+6) targets, assuming every target subselected once"})


def audit_trial_counts(res):
    trials = len(P.TECHNIQUES) * len(P.TARGET_COUNTS) * P.REPETITIONS
    check(res, "225 trials per participant = 5 x 3 x 15", trials == 225,
          {"computed": trials, "reported": R.COUNTS["trials_per_participant"][0]})
    total = trials * R.N_PARTICIPANTS
    n_excl, pct_excl = (R.COUNTS["trials_excluded_incomplete"][0],
                        R.COUNTS["percent_excluded_incomplete"][0])
    calc = 100.0 * n_excl / total
    check(res, "0.44% incomplete-trial exclusion matches 30/6750",
          abs(calc - pct_excl) < 0.006,
          {"total_trials": total, "excluded": n_excl,
           "recomputed_pct": round(calc, 4), "reported_pct": pct_excl})
    n_ef, pct_ef = (R.COUNTS["trials_excluded_error_free_tct"][0],
                    R.COUNTS["percent_excluded_error_free_tct"][0])
    calc_all = 100.0 * n_ef / total
    calc_kept = 100.0 * n_ef / (total - n_excl)
    ok = min(abs(calc_all - pct_ef), abs(calc_kept - pct_ef)) < 0.05
    check(res, "6.5% error-free exclusion matches 445 trials", ok,
          {"445/6750": round(calc_all, 3), "445/6720": round(calc_kept, 3),
           "reported_pct": pct_ef,
           "note": "both readings round to 6.6%, not 6.5%"},
          kind="consistency" if ok else "mismatch")
    check(res, "'two training trials before each block, consisting of 45 trials' "
               "is arithmetically consistent",
          P.TRAINING_TRIALS_PER_BLOCK * len(P.TECHNIQUES)
          == R.COUNTS["training_trials_total"][0],
          {"computed_from_2_per_block": P.TRAINING_TRIALS_PER_BLOCK * len(P.TECHNIQUES),
           "reported": R.COUNTS["training_trials_total"][0],
           "note": "Sec. 4.1.2 says 'two training trials before each block, "
                   "consisting of 45 trials'; 2 x 5 = 10, not 45, so 'trial' must "
                   "mean two training *phases* of variable length - Sec. 4.2 reports "
                   "10.77 multi-selections per phase, i.e. about 108 in total"},
          kind="mismatch")


def audit_inverse_efficiency(res):
    """IE = TCT / success rate should recover a plausible success rate per cell."""
    tct = {t: m for (k, t, m, sd, sec) in R.MEANS_BY_TARGET if k == "tct_ms"}
    ie = {t: m for (k, t, m, sd, sec) in R.MEANS_BY_TARGET if k == "inverse_efficiency_ms"}
    rows = {}
    ok_all = True
    for n_t in sorted(tct):
        implied = 100.0 * tct[n_t] / ie[n_t]
        rows[n_t] = {"tct_ms": tct[n_t], "ie_ms": ie[n_t],
                     "implied_success_rate_pct": round(implied, 2)}
        ok_all &= 50.0 < implied <= 100.0
    monotone = (rows[2]["implied_success_rate_pct"] > rows[4]["implied_success_rate_pct"]
                > rows[6]["implied_success_rate_pct"])
    check(res, "IE = TCT / success rate implies a valid success rate at each target count",
          ok_all, rows)
    check(res, "implied success rate falls as targets increase", monotone,
          {"implied": {k: v["implied_success_rate_pct"] for k, v in rows.items()}})
    # round trip through the implemented function
    rt = M.inverse_efficiency_ms(tct[6], rows[6]["implied_success_rate_pct"])
    check(res, "metrics.inverse_efficiency_ms round-trips the reported 6-target IE",
          abs(rt - ie[6]) < 1.0, {"recomputed": round(rt, 2), "reported": ie[6]})


def audit_technique_orderings(res):
    """Rank orders the text asserts must match the printed means."""
    hm = {t: m for (k, t, m, sd, sec) in R.MEANS_BY_TECHNIQUE if k == "hand_movement_m"}
    order = [t for t, _ in sorted(hm.items(), key=lambda kv: -kv[1])]
    # Sec. 5.5: "most in SemiSwipe, followed by SemiTilt and FullDH ... least when
    # using SemiNDH and SemiDwell"
    expect_mov = ["SemiSwipe", "SemiTilt", "FullDH", "SemiNDH", "SemiDwell"]
    check(res, "Sec. 5.5 hand-movement ordering matches its own means",
          order == expect_mov, {"from_means": order, "stated_in_text": expect_mov})
    hr = {t: m for (k, t, m, sd, sec) in R.MEANS_BY_TECHNIQUE if k == "hand_rotation_deg"}
    order_r = [t for t, _ in sorted(hr.items(), key=lambda kv: -kv[1])]
    # Sec. 5.6: "SemiTilt made participants rotate their hands most, and then
    # SemiSwipe and FullDH followed ... SemiNDH and SemiDwell the lowest"
    expect_rot = ["SemiTilt", "SemiSwipe", "FullDH", "SemiNDH", "SemiDwell"]
    check(res, "Sec. 5.6 hand-rotation ordering matches its own means",
          order_r == expect_rot, {"from_means": order_r, "stated_in_text": expect_rot})
    er = {t: m for (k, t, m, sd, sec) in R.MEANS_BY_TECHNIQUE if k == "error_rate_pct"}
    body_ok = er["SemiSwipe"] < er["SemiDwell"] and er["SemiSwipe"] < er["SemiTilt"] \
        and er["SemiSwipe"] > er["FullDH"]
    check(res, "Sec. 5.3 body text ordering matches its own error-rate means",
          body_ok, {"means_pct": er})
    caption_claim = er["SemiSwipe"] > er["SemiNDH"] and er["SemiSwipe"] > er["FullDH"] \
        and er["SemiSwipe"] > er["SemiTilt"]
    check(res, "Fig. 10 caption ('SemiDwell and SemiSwipe higher than other "
               "techniques') agrees with the Sec. 5.3 body text",
          caption_claim,
          {"means_pct": er,
           "body_sec_5_3": R.CROSS_CHECKS[0]["body_sec_5_3"],
           "caption_fig_10": R.CROSS_CHECKS[0]["caption_fig_10"],
           "note": "the means make SemiTilt the highest error rate at 11.648%, so "
                   "the caption's pairing of SemiDwell with SemiSwipe contradicts "
                   "both the body text and the printed means; the caption most "
                   "likely meant SemiDwell and SemiTilt"},
          kind="mismatch")


def audit_technique_mechanics(res):
    check(res, "SemiTilt: 3x gain on a 30 deg hand rotation sweeps the indicator 90 deg",
          abs(P.TILT_GAIN * P.TILT_THRESHOLD_DEG - P.TILT_INDICATOR_TRAVEL_DEG) < 1e-9,
          {"gain": P.TILT_GAIN, "hand_threshold_deg": P.TILT_THRESHOLD_DEG,
           "indicator_travel_deg": P.TILT_GAIN * P.TILT_THRESHOLD_DEG,
           "paper_sec_6_2": "the threshold of 30 deg was employed instead of 90 deg"})
    check(res, "pinch bands are ordered and non-overlapping",
          P.FULL_PINCH_M <= P.SEMI_MIN_M < P.SEMI_MAX_M < P.RELEASE_M,
          {"full_<": P.FULL_PINCH_M, "semi": [P.SEMI_MIN_M, P.SEMI_MAX_M],
           "release_>=": P.RELEASE_M,
           "dead_band_cm": [P.SEMI_MAX_M * 100, P.RELEASE_M * 100]})
    check(res, "SUS minimum-usability criterion 4.05 on a 0-6 scale equals the "
               "conventional 68/100",
          abs(100.0 * P.SUS_MIN_USABILITY / 6.0 - 68.0) < 1.0,
          {"reported_criterion": P.SUS_MIN_USABILITY,
           "as_percent_of_scale": round(100.0 * P.SUS_MIN_USABILITY / 6.0, 2),
           "conventional_sus_threshold": 68})
    sus = M.sus_score([5, 5, 4], [1, 1, 2])
    check(res, "six-item SUS scoring reverses negatives against 6", sus["n_items"] == 6,
          {"example_positive": [5, 5, 4], "example_negative": [1, 1, 2], "score": sus})


def audit_geometry(res):
    g = L.geometry_report()
    check(res, "stated angular window at 13.5 m converts to a metric window", True,
          {k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()},
          kind="derivation")
    check(res, "the 1 m lattice inside the stated window holds far more than 40 cells",
          g["lattice_cells"] > P.N_OBJECTS,
          {"lattice": f'{g["lattice_cols"]} x {g["lattice_rows"]} = {g["lattice_cells"]}',
           "objects_stated": P.N_OBJECTS,
           "note": "Sec. 4.1.2 gives 40 objects at 1 m spacing inside a "
                   "58.12 x 25.06 deg window at 13.5 m, i.e. 15.0 x 6.0 m. Rows and "
                   "columns are never stated, so a reimplementation must guess "
                   "whether the 40 objects fill a smaller grid or sparsely occupy "
                   "this one"},
          kind="underspecified")
    check(res, "0.6 m gaze colliders overlap on a 1 m lattice",
          g["colliders_overlap_orthogonal_neighbour"],
          {"collider_diameter_m": g["collider_diameter_m"],
           "cell_pitch_m": P.GRID_SPACING_M,
           "overlaps_diagonal_neighbour_too": g["colliders_overlap_diagonal_neighbour"],
           "object_angular_diameter_deg": round(g["object_angular_diameter_deg"], 3),
           "collider_angular_diameter_deg": round(g["collider_angular_diameter_deg"], 3),
           "note": "a single gaze ray can therefore pierce several colliders and the "
                   "paper states no tie-break rule"},
          kind="underspecified")


def audit_design(res):
    d = D.design_report()
    check(res, "the generated schedule reproduces 225 trials per participant",
          d["trials_per_participant"] == d["trials_stated_by_paper"], d)
    check(res, "a balanced (Williams) square over 5 techniques needs 10 sequences, "
               "not 5",
          d["williams_sequences"] == 10 and d["carryover_balanced"],
          {"williams_sequences": d["williams_sequences"],
           "cyclic_sequences": d["cyclic_sequences"],
           "carryover_balanced": d["carryover_balanced"],
           "participants_per_sequence": d["participants_per_sequence"],
           "note": "Sec. 4.1.2 says 'Balanced Latin square' without saying which; "
                   "30 participants divides evenly by both 5 and 10"},
          kind="underspecified")


def audit_ranking(res):
    r = R.RANKING
    check(res, "ranking counts do not exceed the participant count",
          all(v[0] <= R.N_PARTICIPANTS for v in r.values()),
          {k: v[0] for k, v in r.items()})
    both = r["SemiDwell_first"][0] + r["SemiDwell_last"][0]
    check(res, "SemiDwell is simultaneously most and least preferred, consistent "
               "with the polarisation Sec. 5.8 claims",
          both <= R.N_PARTICIPANTS,
          {"ranked_first": r["SemiDwell_first"][0], "ranked_last": r["SemiDwell_last"][0],
           "sum": both, "participants": R.N_PARTICIPANTS})


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    res = []
    audit_degrees_of_freedom(res)
    audit_partial_eta_squared(res)
    audit_p_values(res)
    audit_subselection_count(res)
    audit_trial_counts(res)
    audit_inverse_efficiency(res)
    audit_technique_orderings(res)
    audit_technique_mechanics(res)
    audit_geometry(res)
    audit_design(res)
    audit_ranking(res)

    passed = [r for r in res if r["ok"]]
    failed = [r for r in res if not r["ok"]]

    print("=" * 78)
    print("INTERNAL CONSISTENCY AUDIT - PinchCatcher (CHI '25, 10.1145/3706598.3713530)")
    print("Recomputes the paper's printed numbers against each other.")
    print("No dataset was released, so nothing here is recomputed from raw data.")
    print("=" * 78)
    for r in res:
        if not r["ok"]:
            mark = "FLAG"
        elif r["kind"] in ("mismatch", "underspecified"):
            mark = "NOTE"  # the arithmetic holds, but the paper is under-specified
        else:
            mark = "PASS"
        print(f"[{mark}] {r['check']}")
        for k, v in r["detail"].items():
            print(f"         {k}: {v}")
    print("-" * 78)
    print(f"{len(passed)} checks consistent, {len(failed)} flagged, {len(res)} total")
    for r in failed:
        print(f"  FLAGGED: {r['check']}")

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w") as fh:
            json.dump({"n_checks": len(res), "n_consistent": len(passed),
                       "n_flagged": len(failed), "checks": res}, fh, indent=2)
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
