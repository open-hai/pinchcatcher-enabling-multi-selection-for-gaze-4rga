"""Every numeric constant the PinchCatcher inner loop needs.

Each entry records where the value comes from. `source` is either a section /
figure of the paper (Kim et al., CHI '25, arXiv:2503.05456v2) or the string
"ASSUMED" when the paper does not state it and this reimplementation had to
pick something. Nothing here is a paper claim unless `source` cites the paper.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Provenance registry
# ---------------------------------------------------------------------------

PROVENANCE: Dict[str, Dict[str, Any]] = {}


def stated(name, value, source, note=""):
    PROVENANCE[name] = {"value": value, "source": source, "assumed": False, "note": note}
    return value


def assumed(name, value, where_open, note=""):
    PROVENANCE[name] = {
        "value": value,
        "source": "ASSUMED",
        "assumed": True,
        "where_paper_leaves_it_open": where_open,
        "note": note,
    }
    return value


# ---------------------------------------------------------------------------
# Pinch state detection (Sec. 3.2, Fig. 3)
# ---------------------------------------------------------------------------

SEMI_MIN_M = stated(
    "SEMI_MIN_M", 0.02, "Fig. 3 caption",
    "semi-pinch activated when fingertip distance is between 2 and 7 cm")
SEMI_MAX_M = stated(
    "SEMI_MAX_M", 0.07, "Fig. 3 caption",
    "upper end of the semi-pinch band")
RELEASE_M = stated(
    "RELEASE_M", 0.10, "Sec. 3.2 / Fig. 3 caption",
    "transition from semi-pinch to full-release activated at 10 cm")

FULL_PINCH_M = assumed(
    "FULL_PINCH_M", 0.02,
    "Fig. 3 (A) only says full pinch is 'when both fingertips are touching'; no "
    "numeric contact threshold is given anywhere in the paper.",
    "Taken as the lower edge of the stated semi-pinch band, i.e. d < 2 cm.")

# The paper says a *different* value was used for each direction of transition
# ('a different value was applied for switching from each state to another
# state', Sec. 3.2) but never prints the table. The 7-10 cm gap is the only
# hysteresis the paper quantifies, so this implementation treats (7 cm, 10 cm)
# as a dead band in which the previous state persists, and applies no other
# hysteresis.
HYSTERESIS_DEAD_BAND = assumed(
    "HYSTERESIS_DEAD_BAND", (0.07, 0.10),
    "Sec. 3.2 states per-transition thresholds differ but does not list them.",
    "Interpreted as: distances inside the band do not change the current state.")

FULL_PINCH_HOLD_MS = stated(
    "FULL_PINCH_HOLD_MS", 250, "Sec. 4.1.3 / Sec. 4.2 / Fig. 8",
    "pinch-dwell of 250 ms applied to the trial-ending full pinch")

# ---------------------------------------------------------------------------
# Gaze targeting (Sec. 3.3, Sec. 4.1.3)
# ---------------------------------------------------------------------------

OBJECT_RADIUS_M = stated(
    "OBJECT_RADIUS_M", 0.20, "Sec. 4.1.2 / Sec. 4.1.3", "visible sphere radius")
COLLIDER_SCALE = stated(
    "COLLIDER_SCALE", 3.0, "Sec. 3.3.1 / Sec. 4.1.3",
    "invisible gaze collider is three times the radius of the visible object")
COLLIDER_RADIUS_M = stated(
    "COLLIDER_RADIUS_M", 0.60, "Sec. 4.1.3", "collider radius stated as 60 cm")

GAZE_TIE_BREAK = assumed(
    "GAZE_TIE_BREAK", "min_angle_to_ray",
    "With 0.6 m colliders on a 1 m grid, neighbouring colliders overlap, so a "
    "single gaze ray can hit several. The paper never states how the hit is "
    "resolved.",
    "Resolved to the object whose centre is at the smallest angle from the ray.")

# ---------------------------------------------------------------------------
# SemiDwell (Sec. 3.3.1)
# ---------------------------------------------------------------------------

DWELL_MS = stated(
    "DWELL_MS", 500, "Sec. 3.3.1",
    "gaze must maintain the activated status for 500 ms; 250/500/750 ms were "
    "piloted and 500 ms chosen")

DWELL_REARM = assumed(
    "DWELL_REARM", "on_collider_exit",
    "Sec. 3.3.1 says ungrouping 'proceeded in the same way', i.e. dwell toggles, "
    "but never says what stops a held gaze from toggling again every 500 ms.",
    "After a toggle the same object cannot re-trigger until the gaze ray leaves "
    "its collider.")

DWELL_ACCUMULATION = assumed(
    "DWELL_ACCUMULATION", "reset_on_exit",
    "Sec. 3.3.1 does not say whether dwell time accumulates across brief gaze "
    "losses or resets.",
    "Dwell timer resets to zero whenever the gaze leaves the collider.")

# ---------------------------------------------------------------------------
# SemiSwipe (Sec. 3.3.2)
# ---------------------------------------------------------------------------

SWIPE_GAIN = stated(
    "SWIPE_GAIN", 1.0, "Sec. 6.2",
    "'the linear swipe and 1:1 indicator to hand movements'")
SWIPE_DIRECTION = stated(
    "SWIPE_DIRECTION", "left", "Sec. 3.3.2",
    "only leftward movement counts; the other side is ignored")

SWIPE_TRAVEL_M = assumed(
    "SWIPE_TRAVEL_M", 0.10,
    "Sec. 3.3.2 describes an indicator of three spheres starting to the right "
    "of the target and travelling left until it touches the target, but never "
    "gives the distance the hand must move.",
    "0.10 m of leftward hand travel is used as the activation distance.")

SWIPE_REFERENCE = assumed(
    "SWIPE_REFERENCE", "reset_on_gaze_enter",
    "Sec. 3.3.2 says the indicator moves 'from its initial position' but never "
    "says when that initial position is captured, nor how the hand's return "
    "stroke resets it.",
    "The reference hand position is re-captured whenever the gaze enters a new "
    "object's collider and after every trigger.")

SWIPE_AXIS = assumed(
    "SWIPE_AXIS", "world_x",
    "Sec. 3.3.2 says 'toward the left' without defining the frame (world, head, "
    "or torso relative).",
    "Leftward is taken as the negative world x axis of the study scene.")

# ---------------------------------------------------------------------------
# SemiTilt (Sec. 3.3.3)
# ---------------------------------------------------------------------------

TILT_THRESHOLD_DEG = stated(
    "TILT_THRESHOLD_DEG", 30.0, "Sec. 3.3.3 / Sec. 6.2",
    "users tilt their hand 30 deg to the right; 30 deg was used instead of 90 deg")
TILT_GAIN = stated(
    "TILT_GAIN", 3.0, "Sec. 3.3.3",
    "three times the acceleration applied to the indicator rotation relative to "
    "the actual hand rotation")
TILT_INDICATOR_TRAVEL_DEG = stated(
    "TILT_INDICATOR_TRAVEL_DEG", 90.0, "Sec. 6.2",
    "the 30 deg hand threshold replaces a 90 deg indicator sweep")

TILT_REFERENCE = assumed(
    "TILT_REFERENCE", "reset_on_gaze_enter",
    "Sec. 3.3.3 does not state the zero of the tilt angle nor the reset rule; "
    "participants reported the return-to-neutral action was ambiguous (Sec. 5.8.5).",
    "Same convention as SemiSwipe: reference roll re-captured on gaze enter and "
    "after each trigger.")

TILT_AXIS = assumed(
    "TILT_AXIS", "palm_roll",
    "Sec. 4.3 says palm rotation was logged; Sec. 3.3.3 does not say which "
    "rotational axis drives the indicator.",
    "Roll of the dominant-hand palm about the forearm axis.")

# ---------------------------------------------------------------------------
# SemiNDH / FullDH (Sec. 3.3.4, Sec. 4.1.1)
# ---------------------------------------------------------------------------

NDH_CLICK_EDGE = assumed(
    "NDH_CLICK_EDGE", "rising",
    "Sec. 3.3.4 says a full pinch of the NDH confirms grouping but does not say "
    "whether the trigger is the contact edge or the release edge, nor whether a "
    "pinch-dwell applies as it does to the trial-ending pinch.",
    "Trigger fires on the contact (rising) edge with no dwell.")

FULLDH_UNGROUP_ALL = assumed(
    "FULLDH_UNGROUP_ALL", "ndh_release",
    "Sec. 3.2 binds 'ungroup everything' to a full-release pinch, but in FullDH "
    "the dominant hand must open and close repeatedly to pinch-click, so binding "
    "the rule to the DH would clear the group after every single subselection. "
    "The paper never states what clears the group in the FullDH baseline.",
    "Ungroup-all is bound to the non-dominant hand (the hand that holds the mode) "
    "in FullDH, and to the dominant hand in the four Semi* techniques.")

FULLDH_TRIAL_END = assumed(
    "FULLDH_TRIAL_END", "ndh_release_then_dh_full_pinch",
    "In FullDH the DH full pinch is the subselection trigger (Sec. 4.1.1) but "
    "the trial also ends on a DH full pinch held 250 ms (Sec. 4.2). The paper "
    "never states how the two are told apart; participants reported exactly this "
    "confusion (Sec. 5.8.1).",
    "Trial end is only accepted once the NDH full pinch (the mode) is released.")

# ---------------------------------------------------------------------------
# Stimulus layout (Sec. 4.1.2, Fig. 7A)
# ---------------------------------------------------------------------------

N_OBJECTS = stated("N_OBJECTS", 40, "Sec. 4.1.2", "40 sphere-shaped objects")
GRID_SPACING_M = stated("GRID_SPACING_M", 1.0, "Sec. 4.1.2", "equal intervals of 1 m")
VIEW_DISTANCE_M = stated(
    "VIEW_DISTANCE_M", 13.5, "Sec. 4.1.2",
    "distance between the participant and the layout window")
WINDOW_WIDTH_DEG = stated("WINDOW_WIDTH_DEG", 58.12, "Sec. 4.1.2", "window width")
WINDOW_HEIGHT_DEG = stated("WINDOW_HEIGHT_DEG", 25.06, "Sec. 4.1.2", "window height")

GRID_SHAPE = assumed(
    "GRID_SHAPE", "derived_from_window",
    "Sec. 4.1.2 gives 40 objects, 1 m spacing and an angular window size, but "
    "never gives the number of rows and columns, so it is not stated whether the "
    "40 objects fill the grid or occupy a random subset of a larger lattice.",
    "Columns and rows are derived from the angular window at 13.5 m; the 40 "
    "objects occupy a random subset of the resulting lattice each trial.")

TARGET_COUNTS = stated("TARGET_COUNTS", (2, 4, 6), "Sec. 4.1.2", "2, 4 or 6 targets")

TARGET_PLACEMENT = assumed(
    "TARGET_PLACEMENT", "uniform_without_constraint",
    "Sec. 4.1.2 says objects 'were randomly placed in each trial' but states no "
    "constraint on target adjacency, eccentricity or minimum separation.",
    "Targets are drawn uniformly without replacement from the occupied cells.")

# ---------------------------------------------------------------------------
# Experimental design (Sec. 4.1.2, Sec. 4.2)
# ---------------------------------------------------------------------------

TECHNIQUES = stated(
    "TECHNIQUES", ("FullDH", "SemiNDH", "SemiDwell", "SemiSwipe", "SemiTilt"),
    "Sec. 4.1.2", "five multi-selection techniques")
REPETITIONS = stated("REPETITIONS", 15, "Sec. 4.1.2", "each combination repeated 15 times")
TRIALS_TOTAL = stated("TRIALS_TOTAL", 225, "Sec. 4.1.2", "5 x 3 x 15 = 225 trials")
N_PARTICIPANTS = stated("N_PARTICIPANTS", 30, "Sec. 4.4", "30 participants recruited")
TRAINING_TRIALS_PER_BLOCK = stated(
    "TRAINING_TRIALS_PER_BLOCK", 2, "Sec. 4.1.2",
    "two training trials before each block")
TRAINING_OBJECTS = stated(
    "TRAINING_OBJECTS", 10, "Sec. 4.1.2", "only 10 spheres during training")
COUNTERBALANCING = stated(
    "COUNTERBALANCING", "balanced_latin_square", "Sec. 4.1.2",
    "the order of the blocks was counterbalanced using a Balanced Latin square")

LATIN_SQUARE_FORM = assumed(
    "LATIN_SQUARE_FORM", "williams_10_sequences",
    "Sec. 4.1.2 says 'Balanced Latin square' for five conditions. A Williams "
    "square balancing first-order carry-over needs 2n = 10 sequences when n is "
    "odd; the paper does not say whether 5 or 10 sequences were used, nor how 30 "
    "participants were assigned to them.",
    "10 Williams sequences, 3 participants per sequence.")

# ---------------------------------------------------------------------------
# Exclusion rules (Sec. 5)
# ---------------------------------------------------------------------------

MISS_EXCLUSION_FRACTION = stated(
    "MISS_EXCLUSION_FRACTION", 0.50, "Sec. 5",
    "trials in which participants failed to group over 50 percent of the targets "
    "were filtered out")

MISS_EXCLUSION_STRICTNESS = assumed(
    "MISS_EXCLUSION_STRICTNESS", "strictly_greater",
    "Sec. 5 says 'over 50%', which for the 2-target condition is the difference "
    "between dropping a trial with exactly one target missed and keeping it.",
    "Strictly greater than 50 percent missed, so a 1-of-2 miss is kept.")

# ---------------------------------------------------------------------------
# Questionnaires (Sec. 4.3)
# ---------------------------------------------------------------------------

LIKERT_MIN, LIKERT_MAX = stated(
    "LIKERT_RANGE", (0, 6), "Sec. 4.3", "7-point Likert scale (0 to 6)")
SUS_POSITIVE_ITEMS = stated(
    "SUS_POSITIVE_ITEMS", 3, "Sec. 4.3", "three positive statements")
SUS_NEGATIVE_ITEMS = stated(
    "SUS_NEGATIVE_ITEMS", 3, "Sec. 4.3", "three negative statements")
SUS_REVERSE_BASE = stated(
    "SUS_REVERSE_BASE", 6, "Sec. 4.3",
    "score for the negative statement subtracted from six")
SUS_MIN_USABILITY = stated(
    "SUS_MIN_USABILITY", 4.05, "Sec. 5.7 / Fig. 12",
    "4.05 given as the SUS criterion for minimum usability")

SUS_ITEM_TEXT = assumed(
    "SUS_ITEM_TEXT", None,
    "Sec. 4.3 says a six-item positive/negative SUS variant was used but never "
    "prints the items, so the instrument cannot be reconstructed.",
    "Not recoverable; scoring function is implemented, item wording is not.")

NASA_TLX_SUBSCALES = stated(
    "NASA_TLX_SUBSCALES",
    ("mental", "physical", "temporal", "performance", "effort", "frustration"),
    "Sec. 4.3", "six NASA-TLX features")

NASA_TLX_WEIGHTING = assumed(
    "NASA_TLX_WEIGHTING", "raw_unweighted",
    "Sec. 4.3 lists the six subscales on a 0-6 Likert scale and Fig. 12 plots "
    "them individually; no pairwise weighting procedure is described.",
    "Raw (unweighted) TLX subscales, analysed per subscale.")

# ---------------------------------------------------------------------------
# Statistics (Sec. 5)
# ---------------------------------------------------------------------------

ANOVA_CORRECTION = stated(
    "ANOVA_CORRECTION", "greenhouse_geisser", "Sec. 5",
    "the reported F subscript 'c' and fractional dfs indicate a sphericity "
    "correction; the correction factor is recoverable from the df pairs")
POSTHOC_CORRECTION = stated(
    "POSTHOC_CORRECTION", "bonferroni", "Sec. 5", "with Bonferroni correction")
NONPARAMETRIC_POSTHOC = stated(
    "NONPARAMETRIC_POSTHOC", "wilcoxon_signed_rank", "Sec. 5",
    "Wilcoxon signed-rank tests used for post-hoc on the distractor-grouped case "
    "and error rate metric")
QUESTIONNAIRE_OMNIBUS = stated(
    "QUESTIONNAIRE_OMNIBUS", "friedman", "Sec. 5",
    "Friedman test for the nonparametric questionnaire data")

CORRECTION_NAME_UNSTATED = assumed(
    "CORRECTION_NAME_UNSTATED", "greenhouse_geisser",
    "Sec. 5 never names the sphericity correction; only 'Fc' and fractional dfs "
    "appear. Greenhouse-Geisser and Huynh-Feldt give different epsilons.",
    "Assumed Greenhouse-Geisser; the recovered epsilons are all < 1 and above "
    "the lower bound, which is consistent with but does not prove GG.")

BONFERRONI_FAMILY = assumed(
    "BONFERRONI_FAMILY", "within_metric_pairwise",
    "Sec. 5 says 'with Bonferroni correction' but never states the family size, "
    "i.e. whether correction spans the 10 technique pairs, the 3 target-number "
    "pairs, or every test in the paper.",
    "Correction applied over the pairwise comparisons within each metric and "
    "factor (10 pairs for technique, 3 for target number).")

SEED = assumed(
    "SEED", 20250425,
    "The paper reports no random seed for the per-trial randomisation of object "
    "and target placement.",
    "Fixed so that this repository's synthetic runs are deterministic.")


@dataclass(frozen=True)
class Params:
    """Snapshot of the parameters an inner-loop run actually used."""

    semi_min_m: float = SEMI_MIN_M
    semi_max_m: float = SEMI_MAX_M
    release_m: float = RELEASE_M
    full_pinch_m: float = FULL_PINCH_M
    full_pinch_hold_ms: int = FULL_PINCH_HOLD_MS
    object_radius_m: float = OBJECT_RADIUS_M
    collider_radius_m: float = COLLIDER_RADIUS_M
    dwell_ms: int = DWELL_MS
    swipe_travel_m: float = SWIPE_TRAVEL_M
    swipe_gain: float = SWIPE_GAIN
    tilt_threshold_deg: float = TILT_THRESHOLD_DEG
    tilt_gain: float = TILT_GAIN
    seed: int = SEED
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def assumption_table():
    """Every parameter this implementation had to invent."""
    return {k: v for k, v in PROVENANCE.items() if v["assumed"]}


def stated_table():
    return {k: v for k, v in PROVENANCE.items() if not v["assumed"]}
