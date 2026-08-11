#!/usr/bin/env python3
"""Drive synthetic input traces through the reimplemented inner loop.

These are mechanism tests, not behavioural ones. Each trace is a hand-built
sequence of gaze/hand frames chosen to sit exactly on or just off a threshold
the paper states, so the assertion checks that the implemented rule fires where
the paper says it should. Nothing here estimates how a person would perform, and
no number produced here is comparable to a number in the paper's results.

Usage:
    python src/smoke_test.py [--json results/smoke_test.json]
"""

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinchcatcher import design as D  # noqa: E402
from pinchcatcher import gaze as G  # noqa: E402
from pinchcatcher import layout as L  # noqa: E402
from pinchcatcher import metrics as M  # noqa: E402
from pinchcatcher import params as P  # noqa: E402
from pinchcatcher.pinch_state import PinchDetector, PinchState  # noqa: E402
from pinchcatcher.techniques import Frame, build  # noqa: E402

RESULTS = []


def t(name, fn):
    try:
        detail = fn() or {}
        RESULTS.append({"test": name, "ok": True, "detail": detail})
        print(f"[ok  ] {name}")
        for k, v in detail.items():
            print(f"         {k}: {v}")
    except AssertionError as e:
        RESULTS.append({"test": name, "ok": False, "detail": {"assertion": str(e)}})
        print(f"[FAIL] {name}\n         {e}")


# --------------------------------------------------------------------------
# scene helpers
# --------------------------------------------------------------------------

SCENE = [(0.0, 0.0, 13.5), (1.0, 0.0, 13.5), (2.0, 0.0, 13.5)]
ORIGIN = (0.0, 0.0, 0.0)


def look_at(c):
    return (c[0], c[1], c[2])


def frames(seq):
    """seq: list of dicts overriding the neutral frame."""
    out, base = [], {
        "gaze_origin": ORIGIN, "gaze_dir": look_at(SCENE[0]),
        "dh_palm_pos": (0.0, 0.0, 0.0), "dh_palm_roll_deg": 0.0,
        "dh_pinch_dist_m": 0.05, "ndh_pinch_dist_m": 0.15,
    }
    for i, over in enumerate(seq):
        d = dict(base)
        d.update(over)
        out.append(Frame(t_ms=float(d.pop("t_ms", i * 10)), **d))
    return out


def run(tech, seq, **kw):
    m = build(tech, SCENE, **kw)
    for f in frames(seq):
        m.step(f)
    return m


# --------------------------------------------------------------------------
# 1. pinch state machine (Sec. 3.2, Fig. 3)
# --------------------------------------------------------------------------

def test_pinch_bands():
    d = PinchDetector()
    assert d.update(0.010) is PinchState.FULL, "1 cm should be a full pinch"
    assert d.update(0.050) is PinchState.SEMI, "5 cm is inside the 2-7 cm semi band"
    assert d.update(0.020) is PinchState.SEMI, "2 cm is the stated band edge"
    assert d.update(0.070) is PinchState.SEMI, "7 cm is the stated band edge"
    assert d.update(0.120) is PinchState.RELEASE, "12 cm is past the 10 cm release"
    return {"bands_cm": {"full": "<2", "semi": "2-7", "release": ">=10"}}


def test_dead_band_holds_state():
    d = PinchDetector()
    d.update(0.05)
    assert d.state is PinchState.SEMI
    for x in (0.075, 0.08, 0.09, 0.099):
        assert d.update(x) is PinchState.SEMI, f"{x*100:.1f} cm must not ungroup"
    assert d.update(0.10) is PinchState.RELEASE
    d.update(0.09)
    assert d.state is PinchState.RELEASE, "dead band holds release too"
    return {"dead_band_cm": [P.SEMI_MAX_M * 100, P.RELEASE_M * 100],
            "purpose": "Sec. 3.2 - prevent false activation of the ungrouping function"}


# --------------------------------------------------------------------------
# 2. gaze targeting (Sec. 3.3.1, Sec. 4.1.3)
# --------------------------------------------------------------------------

def test_collider_enlargement():
    # aimed straight at object 1
    on_centre = G.collider_hits(ORIGIN, look_at(SCENE[1]), SCENE, P.COLLIDER_RADIUS_M)
    assert on_centre == [1], f"an on-centre ray should hit one collider; got {on_centre}"
    # aimed into the 0.2 m overlap lens between objects 0 and 1, nearer to 1
    between = (0.55, 0.0, 13.5)
    small = G.collider_hits(ORIGIN, between, SCENE, P.OBJECT_RADIUS_M)
    big = G.collider_hits(ORIGIN, between, SCENE, P.COLLIDER_RADIUS_M)
    assert small == [], "with the visible 0.2 m radius this ray hits nothing"
    assert set(big) == {0, 1}, f"0.6 m colliders on a 1 m pitch must overlap; got {big}"
    chosen, _ = G.resolve_gaze_target(ORIGIN, between, SCENE, P.COLLIDER_RADIUS_M)
    first, _ = G.resolve_gaze_target(ORIGIN, between, SCENE, P.COLLIDER_RADIUS_M,
                                     tie_break="first")
    assert chosen == 1 and first == 0, (
        f"the two tie-break rules must disagree here; got {chosen} and {first}")
    return {"ray_aimed_at": between,
            "hits_with_visible_radius": small, "hits_with_collider_radius": big,
            "chosen_by_min_angle": chosen, "chosen_by_scene_order": first,
            "overlap_lens_width_m": round(2 * P.COLLIDER_RADIUS_M - P.GRID_SPACING_M, 3),
            "consequence": "the unstated tie-break selects a different object for "
                           "the same gaze ray whenever it falls in the overlap"}


def test_angular_sizes():
    obj = G.angular_diameter_deg(P.OBJECT_RADIUS_M, P.VIEW_DISTANCE_M)
    col = G.angular_diameter_deg(P.COLLIDER_RADIUS_M, P.VIEW_DISTANCE_M)
    assert 1.6 < obj < 1.8, obj
    assert 5.0 < col < 5.2, col
    return {"visible_object_deg": round(obj, 3), "gaze_collider_deg": round(col, 3),
            "ratio": round(col / obj, 3)}


# --------------------------------------------------------------------------
# 3. the five techniques
# --------------------------------------------------------------------------

def test_semidwell_fires_at_500ms():
    hold = [{"t_ms": i * 10, "gaze_dir": look_at(SCENE[0]), "dh_pinch_dist_m": 0.05}
            for i in range(0, 60)]  # 590 ms
    m = run("SemiDwell", hold)
    assert m.grouped == {0}, f"500 ms of gaze should group; got {m.grouped}"
    short = [{"t_ms": i * 10, "gaze_dir": look_at(SCENE[0]), "dh_pinch_dist_m": 0.05}
             for i in range(0, 40)]  # 390 ms
    m2 = run("SemiDwell", short)
    assert m2.grouped == set(), f"390 ms must not group; got {m2.grouped}"
    return {"threshold_ms": P.DWELL_MS, "at_590ms": sorted(m.grouped),
            "at_390ms": sorted(m2.grouped)}


def test_semidwell_needs_the_mode():
    hold = [{"t_ms": i * 10, "dh_pinch_dist_m": 0.15} for i in range(0, 100)]
    m = run("SemiDwell", hold)
    assert m.grouped == set(), "dwell must not fire outside the semi-pinch quasi-mode"
    return {"dh_distance_cm": 15, "grouped": sorted(m.grouped)}


def test_semidwell_does_not_retoggle():
    hold = [{"t_ms": i * 10, "dh_pinch_dist_m": 0.05} for i in range(0, 300)]  # 3 s
    m = run("SemiDwell", hold)
    toggles = [e for e in m.events if e.kind in ("group", "ungroup")]
    assert m.grouped == {0}, m.grouped
    assert len(toggles) == 1, (
        f"a 3 s stare produced {len(toggles)} toggles; the paper never states the "
        f"re-arm rule (params.DWELL_REARM)")
    return {"stare_ms": 2990, "toggles": len(toggles),
            "assumption": P.DWELL_REARM}


def test_semiswipe_direction_and_distance():
    left = [{"t_ms": i * 10, "dh_palm_pos": (-0.005 * i, 0.0, 0.0),
             "dh_pinch_dist_m": 0.05} for i in range(0, 30)]  # 0.145 m left
    m = run("SemiSwipe", left)
    assert m.grouped == {0}, f"0.145 m leftward should group; got {m.grouped}"
    right = [{"t_ms": i * 10, "dh_palm_pos": (0.005 * i, 0.0, 0.0),
              "dh_pinch_dist_m": 0.05} for i in range(0, 30)]
    m2 = run("SemiSwipe", right)
    assert m2.grouped == set(), "rightward movement is ignored (Sec. 3.3.2)"
    short = [{"t_ms": i * 10, "dh_palm_pos": (-0.005 * i, 0.0, 0.0),
              "dh_pinch_dist_m": 0.05} for i in range(0, 15)]  # 0.07 m
    m3 = run("SemiSwipe", short)
    assert m3.grouped == set(), "0.07 m is under the assumed 0.10 m travel"
    return {"travel_threshold_m_ASSUMED": P.SWIPE_TRAVEL_M,
            "left_0.145m": sorted(m.grouped), "right_0.145m": sorted(m2.grouped),
            "left_0.070m": sorted(m3.grouped),
            "caveat": "the paper never states the swipe distance; this threshold "
                      "is the single most load-bearing assumption in SemiSwipe"}


def test_semitilt_gain_and_threshold():
    tilt = [{"t_ms": i * 10, "dh_palm_roll_deg": 1.0 * i, "dh_pinch_dist_m": 0.05}
            for i in range(0, 35)]  # up to 34 deg
    m = run("SemiTilt", tilt)
    assert m.grouped == {0}, f"34 deg right should group; got {m.grouped}"
    under = [{"t_ms": i * 10, "dh_palm_roll_deg": 1.0 * i, "dh_pinch_dist_m": 0.05}
             for i in range(0, 29)]  # 28 deg
    m2 = run("SemiTilt", under)
    assert m2.grouped == set(), "28 deg is under the stated 30 deg threshold"
    probe = build("SemiTilt", SCENE)
    for f in frames([{"t_ms": i * 10, "dh_palm_roll_deg": 1.0 * i,
                      "dh_pinch_dist_m": 0.05} for i in range(0, 11)]):
        probe.step(f)
        last = f
    ind = probe.indicator_angle_deg(last)
    assert abs(ind - 3.0 * 10.0) < 1e-6, f"indicator should be geared 3x; got {ind}"
    return {"hand_threshold_deg": P.TILT_THRESHOLD_DEG, "gain": P.TILT_GAIN,
            "indicator_at_10deg_hand": ind,
            "indicator_sweep_at_threshold": P.TILT_GAIN * P.TILT_THRESHOLD_DEG}


def test_semindh_click():
    seq = [{"t_ms": 0, "dh_pinch_dist_m": 0.05, "ndh_pinch_dist_m": 0.15},
           {"t_ms": 10, "dh_pinch_dist_m": 0.05, "ndh_pinch_dist_m": 0.01},
           {"t_ms": 20, "dh_pinch_dist_m": 0.05, "ndh_pinch_dist_m": 0.15}]
    m = run("SemiNDH", seq)
    assert m.grouped == {0}, m.grouped
    off = [{"t_ms": 0, "dh_pinch_dist_m": 0.15, "ndh_pinch_dist_m": 0.15},
           {"t_ms": 10, "dh_pinch_dist_m": 0.15, "ndh_pinch_dist_m": 0.01}]
    m2 = run("SemiNDH", off)
    assert m2.grouped == set(), "NDH click must not fire without the DH semi-pinch"
    return {"with_semi": sorted(m.grouped), "without_semi": sorted(m2.grouped)}


def test_fulldh_baseline():
    seq = [{"t_ms": 0, "dh_pinch_dist_m": 0.15, "ndh_pinch_dist_m": 0.01},
           {"t_ms": 10, "dh_pinch_dist_m": 0.01, "ndh_pinch_dist_m": 0.01},
           {"t_ms": 20, "dh_pinch_dist_m": 0.15, "ndh_pinch_dist_m": 0.01}]
    m = run("FullDH", seq)
    assert m.grouped == {0}, m.grouped
    assert m.trial_ended_at is None, (
        "while the NDH holds the mode, a DH pinch must subselect, not end the trial")
    no_mode = [{"t_ms": 0, "dh_pinch_dist_m": 0.15, "ndh_pinch_dist_m": 0.15},
               {"t_ms": 10, "dh_pinch_dist_m": 0.01, "ndh_pinch_dist_m": 0.15}]
    m2 = run("FullDH", no_mode)
    assert m2.grouped == set(), "no NDH mode -> no multi-selection"
    return {"with_ndh_mode": sorted(m.grouped), "without": sorted(m2.grouped),
            "assumption": P.FULLDH_TRIAL_END}


def test_full_release_ungroups_all():
    seq = [{"t_ms": i * 10, "dh_pinch_dist_m": 0.05} for i in range(0, 60)]
    seq += [{"t_ms": 600 + i * 10, "dh_pinch_dist_m": 0.15} for i in range(0, 5)]
    m = run("SemiDwell", seq)
    assert m.grouped == set(), "a full-release pinch must ungroup everything (Sec. 3.2)"
    assert any(e.kind == "ungroup_all" for e in m.events)
    return {"events": [e.kind for e in m.events]}


def test_trial_end_requires_250ms():
    warm = [{"t_ms": i * 10, "dh_pinch_dist_m": 0.05} for i in range(0, 60)]
    brief = warm + [{"t_ms": 600 + i * 10, "dh_pinch_dist_m": 0.01} for i in range(0, 15)]
    m = run("SemiDwell", brief)  # 140 ms of full pinch
    assert m.trial_ended_at is None, "140 ms of full pinch must not end the trial"
    held = warm + [{"t_ms": 600 + i * 10, "dh_pinch_dist_m": 0.01} for i in range(0, 30)]
    m2 = run("SemiDwell", held)  # 290 ms
    assert m2.trial_ended_at is not None, "290 ms of full pinch should end the trial"
    return {"hold_required_ms": P.FULL_PINCH_HOLD_MS,
            "ended_after_140ms": m.trial_ended_at, "ended_after_290ms": m2.trial_ended_at,
            "grouped_at_end": sorted(m2.grouped)}


def test_all_five_group_the_same_target():
    """Each technique, given its own correct input, groups exactly object 0."""
    drives = {
        "SemiDwell": [{"t_ms": i * 10, "dh_pinch_dist_m": 0.05} for i in range(60)],
        "SemiSwipe": [{"t_ms": i * 10, "dh_pinch_dist_m": 0.05,
                       "dh_palm_pos": (-0.005 * i, 0.0, 0.0)} for i in range(30)],
        "SemiTilt": [{"t_ms": i * 10, "dh_pinch_dist_m": 0.05,
                      "dh_palm_roll_deg": 1.0 * i} for i in range(35)],
        "SemiNDH": [{"t_ms": 0, "dh_pinch_dist_m": 0.05, "ndh_pinch_dist_m": 0.15},
                    {"t_ms": 10, "dh_pinch_dist_m": 0.05, "ndh_pinch_dist_m": 0.01}],
        "FullDH": [{"t_ms": 0, "dh_pinch_dist_m": 0.15, "ndh_pinch_dist_m": 0.01},
                   {"t_ms": 10, "dh_pinch_dist_m": 0.01, "ndh_pinch_dist_m": 0.01}],
    }
    got = {}
    for name, seq in drives.items():
        m = run(name, seq)
        got[name] = sorted(m.grouped)
        assert m.grouped == {0}, f"{name} grouped {m.grouped}"
    return got


# --------------------------------------------------------------------------
# 4. layout, design, metrics
# --------------------------------------------------------------------------

def test_layout_generator():
    rng = random.Random(P.SEED)
    lay = L.make_trial(6, rng)
    assert len(lay.centres) == P.N_OBJECTS
    assert lay.n_targets == 6
    assert len(set(lay.centres)) == P.N_OBJECTS, "objects must not share a cell"
    for (x, y, z) in lay.centres:
        assert abs(z - P.VIEW_DISTANCE_M) < 1e-9
    pitches = set()
    for (x, y, _) in lay.centres:
        pitches.add((round(x % P.GRID_SPACING_M, 6), round(y % P.GRID_SPACING_M, 6)))
    assert len(pitches) == 1, "every object must sit on the same 1 m lattice"
    g = L.geometry_report()
    return {"objects": len(lay.centres), "targets": lay.n_targets,
            "distractors": len(lay.distractors),
            "window_m": (round(g["window_width_m"], 2), round(g["window_height_m"], 2)),
            "lattice": f'{g["lattice_cols"]}x{g["lattice_rows"]}',
            "cells_left_empty": g["cells_unused"]}


def test_design_generator():
    d = D.design_report()
    assert d["trials_per_participant"] == P.TRIALS_TOTAL
    assert d["carryover_balanced"], "Williams square must balance first-order carry-over"
    orders = D.block_orders()
    counts = {}
    for o in orders:
        for pos, techq in enumerate(o):
            counts[(techq, pos)] = counts.get((techq, pos), 0) + 1
    assert len(set(counts.values())) == 1, (
        f"each technique should appear equally often in each position; got {counts}")
    return {"trials_per_participant": d["trials_per_participant"],
            "sequences": d["williams_sequences"],
            "participants_per_sequence": d["participants_per_sequence"],
            "each_technique_in_each_position": sorted(set(counts.values()))}


def test_metric_definitions():
    assert M.accidental_subselection_ratio(2, 8) == 25.0
    assert M.error_rate(1, 1, 4) == 50.0
    assert M.accidental_subselection_ratio(0, 0) is None
    assert M.error_rate(2, 0, 0) is None, "an empty final group makes error rate undefined"
    ie = M.inverse_efficiency_ms(6000.0, 80.0)
    assert abs(ie - 7500.0) < 1e-9
    sus = M.sus_score([6, 5, 5], [0, 1, 1])
    assert sus["n_items"] == 6 and abs(sus["mean"] - 32 / 6) < 1e-9
    path = M.path_length_m([(0, 0, 0), (1, 0, 0), (1, 1, 0)])
    assert abs(path - 2.0) < 1e-9
    return {"asr(2 of 8)": 25.0, "error_rate(1 missed,1 distractor,4 grouped)": 50.0,
            "ie(6000ms, 80%)": ie, "sus_mean": round(sus["mean"], 4), "path_m": path,
            "undefined_cases": ["asr with zero subselections",
                                "error rate with an empty final group"]}


def test_ratio_metrics_are_denominator_coupled():
    """A fixed number of accidents per trial does not give a fixed ratio.

    Sec. 4.3 divides accidental subselections by "the total number of
    subselections performed per trial", and that denominator grows with the
    target count. So the same underlying accident rate per trial reads as a
    falling ratio across the 2/4/6 conditions. Any target-number effect on this
    measure is partly definitional. The paper reports exactly this factor as
    marginal (Sec. 5.2, p=.058).
    """
    fixed_accidents = 1
    ratios = {n: M.accidental_subselection_ratio(fixed_accidents, n + fixed_accidents)
              for n in P.TARGET_COUNTS}
    assert ratios[2] > ratios[4] > ratios[6], ratios
    per_target = {n: M.accidental_subselection_ratio(round(0.05 * n), n + round(0.05 * n))
                  for n in P.TARGET_COUNTS}
    return {"one_accident_per_trial_ratio_pct": {k: round(v, 2) for k, v in ratios.items()},
            "constant_per_target_accident_rate_ratio_pct":
                {k: round(v, 2) for k, v in per_target.items()},
            "implication": "the accidental subselection ratio is not scale free "
                           "across the target-number factor"}


def test_kinematics_logging():
    seq = [{"t_ms": i * 10, "dh_palm_pos": (0.01 * i, 0.0, 0.0),
            "dh_palm_roll_deg": 2.0 * i, "dh_pinch_dist_m": 0.05} for i in range(11)]
    m = run("SemiNDH", seq)
    assert abs(m.path_length_m - 0.10) < 1e-9, m.path_length_m
    assert abs(m.rotation_total_deg - 20.0) < 1e-9, m.rotation_total_deg
    return {"path_length_m": round(m.path_length_m, 4),
            "rotation_total_deg": round(m.rotation_total_deg, 2),
            "definition": "Sec. 4.3 - palm translation and rotation per frame"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    print("=" * 78)
    print("INNER-LOOP MECHANISM SMOKE TEST - PinchCatcher reimplementation")
    print("Synthetic input traces only. No human data, no behavioural claims.")
    print("=" * 78)

    t("pinch state bands (Sec. 3.2, Fig. 3)", test_pinch_bands)
    t("7-10 cm dead band holds the current state (Sec. 3.2)", test_dead_band_holds_state)
    t("3x gaze collider overlaps neighbours (Sec. 4.1.3)", test_collider_enlargement)
    t("angular sizes of object and collider at 13.5 m", test_angular_sizes)
    t("SemiDwell fires at 500 ms, not before (Sec. 3.3.1)", test_semidwell_fires_at_500ms)
    t("SemiDwell is gated by the semi-pinch quasi-mode (Sec. 3.3)",
      test_semidwell_needs_the_mode)
    t("SemiDwell does not re-toggle on a held stare (ASSUMED)",
      test_semidwell_does_not_retoggle)
    t("SemiSwipe: leftward only, past the travel threshold (Sec. 3.3.2)",
      test_semiswipe_direction_and_distance)
    t("SemiTilt: 30 deg hand, 3x geared indicator (Sec. 3.3.3)",
      test_semitilt_gain_and_threshold)
    t("SemiNDH: NDH pinch click while DH holds semi (Sec. 3.3.4)", test_semindh_click)
    t("FullDH baseline: NDH full pinch is the mode (Sec. 4.1.1)", test_fulldh_baseline)
    t("full-release pinch ungroups everything (Sec. 3.2)", test_full_release_ungroups_all)
    t("trial ends on a 250 ms full pinch (Sec. 4.2, Fig. 8)", test_trial_end_requires_250ms)
    t("all five techniques group the gazed target", test_all_five_group_the_same_target)
    t("stimulus layout generator (Sec. 4.1.2)", test_layout_generator)
    t("design and counterbalancing generator (Sec. 4.1.2)", test_design_generator)
    t("metric definitions (Sec. 4.3)", test_metric_definitions)
    t("ratio metrics are denominator-coupled to target number (Sec. 4.3)",
      test_ratio_metrics_are_denominator_coupled)
    t("palm translation / rotation logging (Sec. 4.3)", test_kinematics_logging)

    ok = sum(1 for r in RESULTS if r["ok"])
    print("-" * 78)
    print(f"{ok}/{len(RESULTS)} mechanism tests passed")
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w") as fh:
            json.dump({"passed": ok, "total": len(RESULTS), "tests": RESULTS}, fh, indent=2)
        print(f"wrote {args.json}")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
