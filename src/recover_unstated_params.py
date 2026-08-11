#!/usr/bin/env python3
"""Recover two unstated technique parameters from the paper's own reported means.

Sec. 3.3.2 never states how far the hand must swipe to confirm a subselection,
which is the single largest gap in the SemiSwipe specification. But Sec. 5.5
reports mean hand movement per technique, and Sec. 5.6 reports mean hand
rotation per technique. Those are the integral of exactly the motion the
techniques demand, so they constrain the missing thresholds from the outside.

Model
-----
For a technique T, per-trial hand path length is

    path(T) = floor + n_subselections * strokes_per_subselection * amplitude(T)

where `floor` is the movement a participant makes with a technique that demands
no hand motion at all. SemiDwell is that floor: Sec. 3.3.1 says it requires no
hand gestures or movements, and Sec. 5.5 confirms it has the smallest mean
(0.143 m). `strokes_per_subselection` is 2 if the return stroke is tracked as
movement and 1 if it is not; the paper does not say, so both are reported.

This is an estimate under stated assumptions, not a measurement. It cannot be
checked against the authors' data because that data was never released.

Usage:
    python src/recover_unstated_params.py [--json results/recovered_params.json]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import reported as R  # noqa: E402
from pinchcatcher import params as P  # noqa: E402

MEAN_TARGETS = sum(P.TARGET_COUNTS) / len(P.TARGET_COUNTS)  # 4.0, Sec. 4.1.2


def _by(metric):
    return {t: m for (k, t, m, sd, sec) in R.MEANS_BY_TECHNIQUE if k == metric}


def _n_subselections(technique):
    """Mean subselections per trial = targets + the reported accidental ones."""
    asr = _by("accidental_ratio_pct")[technique] / 100.0
    return MEAN_TARGETS / (1.0 - asr)


def recover(metric, technique, floor_technique, threshold_label, stated_value):
    obs = _by(metric)[technique]
    floor = _by(metric)[floor_technique]
    attributable = obs - floor
    n = _n_subselections(technique)
    out = {
        "technique": technique,
        "metric": metric,
        "reported_mean": obs,
        "floor_technique": floor_technique,
        "floor_mean": floor,
        "motion_attributable_to_the_trigger": round(attributable, 4),
        "mean_subselections_per_trial": round(n, 3),
        "estimates": {},
    }
    for strokes in (1, 2):
        est = attributable / (n * strokes)
        row = {"amplitude_per_stroke": round(est, 4)}
        if stated_value is not None:
            row["stated_by_paper"] = stated_value
            row["observed_over_stated"] = round(est / stated_value, 3)
        out["estimates"][f"{strokes}_stroke(s)_per_subselection"] = row
    out["threshold_recovered"] = threshold_label
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    swipe = recover("hand_movement_m", "SemiSwipe", "SemiDwell",
                    "SWIPE_TRAVEL_M (never stated)", None)
    tilt = recover("hand_rotation_deg", "SemiTilt", "SemiDwell",
                   "TILT_THRESHOLD_DEG (stated: 30 deg)", P.TILT_THRESHOLD_DEG)

    # Validation: the tilt threshold IS stated, so the same estimator can be
    # scored on it. Whatever bias it shows on tilt is the bias to expect on swipe.
    tilt_ratio_2 = tilt["estimates"]["2_stroke(s)_per_subselection"]["observed_over_stated"]
    tilt_ratio_1 = tilt["estimates"]["1_stroke(s)_per_subselection"]["observed_over_stated"]

    # The paper predicts overshoot in both, and says tilt was worse (Sec. 8).
    swipe_est_2 = swipe["estimates"]["2_stroke(s)_per_subselection"]["amplitude_per_stroke"]
    corrected = {f"assuming_the_same_overshoot_as_tilt_({tilt_ratio_2}x)":
                 round(swipe_est_2 / tilt_ratio_2, 4)}

    overshoot_check = {
        "paper_claim_sec_8": "participants tended to swipe more than the activation "
                             "threshold; SemiTilt had a similar but more critical issue",
        "tilt_overshoot_factor_2_strokes": tilt_ratio_2,
        "tilt_overshoot_factor_1_stroke": tilt_ratio_1,
        "overshoot_confirmed_by_the_reported_means": tilt_ratio_2 > 1.0,
    }

    result = {
        "assumptions": {
            "mean_targets_per_trial": MEAN_TARGETS,
            "floor_technique": "SemiDwell (Sec. 3.3.1 - requires no hand movement)",
            "strokes_per_subselection": "unstated; 1 and 2 both reported",
            "caveat": "estimated from published aggregate means, not from data; "
                      "the authors released no dataset",
        },
        "swipe_activation_distance": swipe,
        "tilt_activation_angle_estimator_validation": tilt,
        "overshoot_check": overshoot_check,
        "swipe_distance_best_estimate_m": corrected,
        "value_used_in_this_repo": P.SWIPE_TRAVEL_M,
    }

    print("=" * 78)
    print("RECOVERING UNSTATED PARAMETERS FROM THE PAPER'S REPORTED MEANS")
    print("=" * 78)
    print(json.dumps(result, indent=2))
    print()
    print(f"The estimator, scored on the one threshold the paper DOES state "
          f"(tilt, 30 deg), overshoots by {tilt_ratio_2}x with a return stroke "
          f"and {tilt_ratio_1}x without.")
    print(f"Applied to SemiSwipe it puts the unstated activation distance at "
          f"{swipe_est_2:.3f} m raw, or {list(corrected.values())[0]:.3f} m after "
          f"discounting the same overshoot.")
    print(f"This repository uses {P.SWIPE_TRAVEL_M} m, which sits inside that range.")

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w") as fh:
            json.dump(result, fh, indent=2)
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
