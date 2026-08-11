#!/usr/bin/env python3
"""Generate a synthetic dataset with the paper's design *shape* only.

READ THIS BEFORE USING THE OUTPUT FOR ANYTHING.

This file does NOT simulate the PinchCatcher user study. It does not model human
performance, it is not calibrated against any number the paper reports, and no
statistic computed from it says anything about the paper's findings. Its only
job is to give `src/analyze.py` an input of the right shape so the analysis
pipeline can be executed and its behaviour checked.

Two generators:

  --mode null     every condition drawn from one identical distribution, so the
                  correct answer is "no effect anywhere". Any significant result
                  here is a bug in the pipeline, not a finding.

  --mode planted  an arbitrary, explicitly stated effect is added (a fixed
                  per-target time cost and a fixed technique offset) so the
                  pipeline can be checked for the ability to recover an effect
                  whose true size is known. The planted values are printed and
                  are not the paper's values.

Usage:
    python src/make_synthetic_log.py --mode null --out results/synthetic_null.csv
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinchcatcher import params as P  # noqa: E402
from pinchcatcher import design as D  # noqa: E402

# Arbitrary generator constants. NOT taken from the paper.
BASE_TCT_MS = 5000.0
PARTICIPANT_SD_MS = 800.0
TRIAL_SD_MS = 600.0
PLANTED_MS_PER_TARGET = 700.0
PLANTED_TECHNIQUE_OFFSET_MS = {
    "FullDH": 0.0, "SemiNDH": 250.0, "SemiDwell": 500.0,
    "SemiSwipe": 750.0, "SemiTilt": 1000.0,
}


def generate(mode, n_participants=P.N_PARTICIPANTS, seed=P.SEED):
    rng = np.random.default_rng(seed)
    orders = D.block_orders(n_participants)
    rows = []
    for pid in range(n_participants):
        p_offset = rng.normal(0.0, PARTICIPANT_SD_MS)
        for block, technique, n_t, rep in D.trial_schedule(pid, orders):
            tct = BASE_TCT_MS + p_offset + rng.normal(0.0, TRIAL_SD_MS)
            if mode == "planted":
                tct += PLANTED_MS_PER_TARGET * n_t
                tct += PLANTED_TECHNIQUE_OFFSET_MS[technique]
            # accident and miss counts scale with the number of targets so that
            # the *ratio* metrics are null too; see smoke_test's
            # test_ratio_metrics_are_denominator_coupled for why that matters
            n_accidental = int(rng.poisson(0.05 * n_t))
            n_missed = int(rng.binomial(n_t, 0.03))
            n_distractors_final = int(rng.binomial(max(n_accidental, 1), 0.25))
            n_grouped_final = max(1, n_t - n_missed + n_distractors_final)
            rows.append({
                "participant": pid,
                "block": block,
                "technique": technique,
                "target_number": n_t,
                "repetition": rep,
                "tct_ms": round(max(500.0, tct), 1),
                "n_subselections": n_t + n_accidental,
                "n_distractors_subselected": n_accidental,
                "n_targets_missed": n_missed,
                "n_distractors_final": n_distractors_final,
                "n_grouped_final": n_grouped_final,
                "hand_movement_m": round(abs(rng.normal(0.4, 0.15)), 4),
                "hand_rotation_deg": round(abs(rng.normal(150.0, 60.0)), 2),
            })
    return pd.DataFrame(rows)


def generate_questionnaire(n_participants=P.N_PARTICIPANTS, seed=P.SEED + 1):
    rng = np.random.default_rng(seed)
    measures = ["sus"] + list(P.NASA_TLX_SUBSCALES) + ["satisfaction"]
    rows = []
    for pid in range(n_participants):
        for tech in P.TECHNIQUES:
            for m in measures:
                rows.append({"participant": pid, "technique": tech, "measure": m,
                             "score": int(rng.integers(P.LIKERT_MIN, P.LIKERT_MAX + 1))})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["null", "planted"], default="null")
    ap.add_argument("--out", required=True)
    ap.add_argument("--questionnaire-out", default=None)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    df = generate(args.mode)
    df.to_csv(args.out, index=False)
    print(f"SYNTHETIC DATA - not the paper's data, not a simulation of the study.")
    print(f"mode={args.mode}  rows={len(df)}  participants={df['participant'].nunique()}")
    print(f"trials per participant={len(df)//df['participant'].nunique()} "
          f"(paper states {P.TRIALS_TOTAL})")
    if args.mode == "planted":
        print(f"planted per-target cost: {PLANTED_MS_PER_TARGET} ms")
        print(f"planted technique offsets: {PLANTED_TECHNIQUE_OFFSET_MS}")
    else:
        print("no effects planted: the correct analysis result is null everywhere")
    print(f"wrote {args.out}")
    if args.questionnaire_out:
        q = generate_questionnaire()
        q.to_csv(args.questionnaire_out, index=False)
        print(f"wrote {args.questionnaire_out} ({len(q)} rows, uniform random scores)")


if __name__ == "__main__":
    main()
