#!/usr/bin/env python3
"""How much do the unstated decisions actually change the inner loop?

Every row of the "hidden decisions" table in REPRODUCIBILITY.md claims a
sensitivity. This script is where those claims come from. Each sweep varies one
assumption over a plausible range and measures how the mechanism's output moves,
on synthetic input with the paper's stated geometry.

These are sensitivities of the *mechanism*, not of the paper's results. A
mechanism that changes here would produce different subselection events for the
same participant behaviour; whether that would change the paper's conclusions is
a question only the missing data could answer.

Usage:
    python src/sensitivity.py [--json results/sensitivity.json]
"""

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinchcatcher import gaze as G  # noqa: E402
from pinchcatcher import layout as L  # noqa: E402
from pinchcatcher import params as P  # noqa: E402
from pinchcatcher.techniques import Frame, build  # noqa: E402

ORIGIN = (0.0, 0.0, 0.0)
N_RAYS = 20000


def _random_rays(rng, n=N_RAYS):
    """Gaze rays uniformly covering the stated angular window."""
    w, h = L.window_extent_m()
    for _ in range(n):
        yield (rng.uniform(-w / 2, w / 2), rng.uniform(-h / 2, h / 2), P.VIEW_DISTANCE_M)


def sweep_collider_radius():
    """How often does one gaze ray pierce more than one collider?"""
    rng = random.Random(P.SEED)
    lay = L.make_trial(6, rng)
    rays = list(_random_rays(random.Random(P.SEED + 1)))
    rows = []
    for scale in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
        r = P.OBJECT_RADIUS_M * scale
        multi = hit = 0
        for d in rays:
            h = G.collider_hits(ORIGIN, d, lay.centres, r)
            if h:
                hit += 1
                if len(h) > 1:
                    multi += 1
        rows.append({
            "collider_scale": scale,
            "collider_radius_m": round(r, 3),
            "rays_hitting_something_pct": round(100.0 * hit / len(rays), 2),
            "of_those_ambiguous_pct": round(100.0 * multi / hit, 2) if hit else None,
        })
    return {
        "parameter": "COLLIDER_SCALE (stated: 3x, Sec. 4.1.3)",
        "question": "how often the unstated tie-break is invoked at all",
        "rows": rows,
    }


def sweep_tie_break():
    """When several colliders are hit, do the candidate rules disagree?"""
    rng = random.Random(P.SEED)
    lay = L.make_trial(6, rng)
    rays = list(_random_rays(random.Random(P.SEED + 2)))
    ambiguous = disagree_first = disagree_nearest = 0
    for d in rays:
        hits = G.collider_hits(ORIGIN, d, lay.centres, P.COLLIDER_RADIUS_M)
        if len(hits) < 2:
            continue
        ambiguous += 1
        a, _ = G.resolve_gaze_target(ORIGIN, d, lay.centres, P.COLLIDER_RADIUS_M,
                                     "min_angle_to_ray")
        b, _ = G.resolve_gaze_target(ORIGIN, d, lay.centres, P.COLLIDER_RADIUS_M, "first")
        c, _ = G.resolve_gaze_target(ORIGIN, d, lay.centres, P.COLLIDER_RADIUS_M, "nearest")
        disagree_first += (a != b)
        disagree_nearest += (a != c)
    return {
        "parameter": "GAZE_TIE_BREAK (ASSUMED; the paper states no rule)",
        "question": "does the choice of rule change which object is subselected",
        "rays_tested": len(rays),
        "ambiguous_rays": ambiguous,
        "ambiguous_pct_of_all_rays": round(100.0 * ambiguous / len(rays), 2),
        "min_angle_vs_scene_order_disagree_pct":
            round(100.0 * disagree_first / ambiguous, 2) if ambiguous else None,
        "min_angle_vs_nearest_disagree_pct":
            round(100.0 * disagree_nearest / ambiguous, 2) if ambiguous else None,
    }


def sweep_swipe_travel():
    """How many objects fit inside one leftward arm budget, per travel setting?

    With the reference position re-captured on each new gaze target
    (params.SWIPE_REFERENCE), subselecting k objects needs k * travel of
    monotonic leftward motion before the hand must be returned. This sweep
    measures that directly instead of asserting it.
    """
    budget_m = 0.60
    n_objects = 8
    scene = [(float(i), 0.0, 13.5) for i in range(n_objects)]
    rows = []
    for travel in (0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30):
        p = P.Params(swipe_travel_m=travel)
        m = build("SemiSwipe", scene, params=p)
        n_frames = 600
        target = 0
        for i in range(n_frames):
            x = -budget_m * i / (n_frames - 1)
            # gaze walks to the next object as soon as the previous one is grouped
            target = min(len(m.grouped), n_objects - 1)
            m.step(Frame(t_ms=i * 10, gaze_origin=ORIGIN, gaze_dir=scene[target],
                         dh_palm_pos=(x, 0.0, 0.0), dh_palm_roll_deg=0.0,
                         dh_pinch_dist_m=0.05, ndh_pinch_dist_m=0.15))
        rows.append({"swipe_travel_m": travel,
                     "objects_grouped_within_0.60m_budget": len(m.grouped),
                     "predicted_floor_budget_over_travel": int(budget_m / travel)})
    return {
        "parameter": "SWIPE_TRAVEL_M (ASSUMED 0.10 m; Sec. 3.3.2 gives no distance)",
        "question": "how many objects one leftward arm excursion can subselect",
        "leftward_budget_m": budget_m,
        "rows": rows,
        "note": "Sec. 3.3.2 raises exactly this problem - 'since hands can only "
                "move a certain distance, a return action is needed' - without "
                "giving the distance that sets the limit",
    }


def sweep_dwell_rearm():
    """A held stare: how many toggles under each re-arm rule?"""
    scene = [(0.0, 0.0, 13.5)]
    rows = []
    for stare_ms in (500, 1000, 2000, 3000):
        m = build("SemiDwell", scene)
        n = stare_ms // 10
        for i in range(n):
            m.step(Frame(t_ms=i * 10, gaze_origin=ORIGIN, gaze_dir=scene[0],
                         dh_palm_pos=(0.0, 0.0, 0.0), dh_palm_roll_deg=0.0,
                         dh_pinch_dist_m=0.05, ndh_pinch_dist_m=0.15))
        implemented = sum(1 for e in m.events if e.kind in ("group", "ungroup"))
        # the alternative reading: the timer simply restarts after each trigger
        naive = stare_ms // P.DWELL_MS
        rows.append({"stare_ms": stare_ms, "toggles_with_exit_rearm": implemented,
                     "toggles_if_timer_just_restarts": naive,
                     "final_state_differs": (implemented % 2) != (naive % 2)})
    return {
        "parameter": "DWELL_REARM (ASSUMED on_collider_exit; Sec. 3.3.1 is silent)",
        "question": "whether a lingering gaze can toggle an object back off",
        "rows": rows,
    }


def sweep_tilt_threshold():
    scene = [(0.0, 0.0, 13.5)]
    rows = []
    for thresh in (10.0, 20.0, 30.0, 45.0, 60.0, 90.0):
        p = P.Params(tilt_threshold_deg=thresh)
        m = build("SemiTilt", scene, params=p)
        for i in range(80):  # 0 -> 79 deg
            m.step(Frame(t_ms=i * 10, gaze_origin=ORIGIN, gaze_dir=scene[0],
                         dh_palm_pos=(0.0, 0.0, 0.0), dh_palm_roll_deg=float(i),
                         dh_pinch_dist_m=0.05, ndh_pinch_dist_m=0.15))
        rows.append({"hand_threshold_deg": thresh,
                     "indicator_sweep_deg": thresh * P.TILT_GAIN,
                     "toggles_in_a_79deg_roll":
                         sum(1 for e in m.events if e.kind in ("group", "ungroup"))})
    return {
        "parameter": "TILT_THRESHOLD_DEG (stated 30 deg, Sec. 3.3.3) with gain 3x",
        "question": "the stated threshold is recoverable; the sweep shows the "
                    "consequence of getting it wrong",
        "rows": rows,
    }


def sweep_full_pinch_threshold():
    """Where does the full-pinch contact threshold sit, given it is never stated?"""
    scene = [(0.0, 0.0, 13.5)]
    rows = []
    # an aperture trace that closes from 12 cm to 1.5 cm and holds
    trace = [0.12 - 0.105 * min(1.0, i / 40.0) for i in range(120)]
    # values above 2 cm are structurally impossible: they would collide with
    # the stated lower edge of the semi-pinch band, which is itself a constraint
    # the paper never spells out but its own Fig. 3 imposes.
    for full_m in (0.005, 0.010, 0.015, 0.020):
        p = P.Params(full_pinch_m=full_m)
        m = build("SemiDwell", scene, params=p)
        for i, d in enumerate(trace):
            m.step(Frame(t_ms=i * 10, gaze_origin=ORIGIN, gaze_dir=scene[0],
                         dh_palm_pos=(0.0, 0.0, 0.0), dh_palm_roll_deg=0.0,
                         dh_pinch_dist_m=d, ndh_pinch_dist_m=0.15))
        rows.append({"full_pinch_threshold_m": full_m,
                     "grouped_before_trial_end": sorted(m.grouped),
                     "trial_end_ms": m.trial_ended_at})
    return {
        "parameter": "FULL_PINCH_M (ASSUMED 0.02 m; Fig. 3 says only 'fingertips touching')",
        "question": "when the quasi-mode collapses into the terminating full pinch",
        "aperture_trace": "12 cm closing to 1.5 cm over 400 ms, then held",
        "upper_bound_forced_by_paper": "2 cm - any larger value would overlap the "
                                       "stated 2-7 cm semi-pinch band (Fig. 3)",
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    sweeps = [
        ("gaze collider size", sweep_collider_radius()),
        ("gaze tie-break rule", sweep_tie_break()),
        ("swipe activation distance", sweep_swipe_travel()),
        ("dwell re-arm rule", sweep_dwell_rearm()),
        ("tilt threshold", sweep_tilt_threshold()),
        ("full-pinch contact threshold", sweep_full_pinch_threshold()),
    ]

    print("=" * 78)
    print("SENSITIVITY OF THE INNER LOOP TO THE PAPER'S UNSTATED DECISIONS")
    print("Synthetic input, the paper's stated geometry. Mechanism only.")
    print("=" * 78)
    for title, s in sweeps:
        print(f"\n### {title}")
        for k, v in s.items():
            if k == "rows":
                for r in v:
                    print("    " + json.dumps(r))
            else:
                print(f"  {k}: {v}")

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w") as fh:
            json.dump({t: s for t, s in sweeps}, fh, indent=2)
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
