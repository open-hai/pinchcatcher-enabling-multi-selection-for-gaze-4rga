"""The five multi-selection techniques as frame-driven state machines.

Paper basis:
  Sec. 3.3.1 SemiDwell  - gaze held on the collider for 500 ms
  Sec. 3.3.2 SemiSwipe  - leftward DH movement drives an indicator 1:1
  Sec. 3.3.3 SemiTilt   - rightward DH roll, indicator geared 3x, 30 deg threshold
  Sec. 3.3.4 SemiNDH    - NDH full pinch while the DH holds the semi-pinch
  Sec. 4.1.1 FullDH     - NDH *full* pinch is the mode, DH full pinch subselects

All four Semi* techniques share the same mode gate: they fire only while the
dominant hand is inside the semi-pinch band (Sec. 3.3, first paragraph).
Grouping is a toggle - Sec. 3.3 says "ungrouping individual objects proceeded
in the same way".
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import params as P
from .pinch_state import PinchDetector, PinchState


@dataclass
class Frame:
    """One tick of input. Positions in metres, angles in degrees, t in ms."""

    t_ms: float
    gaze_origin: Tuple[float, float, float]
    gaze_dir: Tuple[float, float, float]
    dh_palm_pos: Tuple[float, float, float]
    dh_palm_roll_deg: float
    dh_pinch_dist_m: float
    ndh_pinch_dist_m: float


@dataclass
class Event:
    t_ms: float
    kind: str  # "group" | "ungroup" | "mode_enter" | "mode_exit" | "ungroup_all" | "trial_end"
    obj: Optional[int] = None


class _Base:
    """Shared plumbing: pinch states, gaze target tracking, grouped set."""

    name = "base"
    requires_semi = True

    def __init__(self, centres, collider_radius=P.COLLIDER_RADIUS_M,
                 tie_break=P.GAZE_TIE_BREAK, params: Optional[P.Params] = None):
        from .gaze import resolve_gaze_target

        self._resolve = resolve_gaze_target
        self.centres = list(centres)
        self.collider_radius = collider_radius
        self.tie_break = tie_break
        self.p = params or P.Params()

        self.dh = PinchDetector(full_m=self.p.full_pinch_m, semi_min_m=self.p.semi_min_m,
                                semi_max_m=self.p.semi_max_m, release_m=self.p.release_m)
        self.ndh = PinchDetector(full_m=self.p.full_pinch_m, semi_min_m=self.p.semi_min_m,
                                 semi_max_m=self.p.semi_max_m, release_m=self.p.release_m)
        self.grouped: set = set()
        self.events: List[Event] = []
        self.gaze_obj: Optional[int] = None
        self._gaze_since_ms: Optional[float] = None
        self._armed: Dict[int, bool] = {}
        self._full_pinch_since: Optional[float] = None
        self.trial_ended_at: Optional[float] = None
        self.path_length_m = 0.0
        self.rotation_total_deg = 0.0
        self._last_pos = None
        self._last_roll = None

    # -- helpers ----------------------------------------------------------
    def _toggle(self, obj: int, t_ms: float):
        if obj in self.grouped:
            self.grouped.discard(obj)
            self.events.append(Event(t_ms, "ungroup", obj))
        else:
            self.grouped.add(obj)
            self.events.append(Event(t_ms, "group", obj))

    def _track_gaze(self, f: Frame):
        prev = self.gaze_obj
        obj, _hits = self._resolve(f.gaze_origin, f.gaze_dir, self.centres,
                                   self.collider_radius, self.tie_break)
        self.gaze_obj = obj
        if obj != prev:
            self._gaze_since_ms = f.t_ms if obj is not None else None
            if obj is not None:
                self._armed[obj] = True  # re-arm on collider entry
            self.on_gaze_enter(f, obj)
        return obj

    def _track_kinematics(self, f: Frame):
        if self._last_pos is not None:
            dx = f.dh_palm_pos[0] - self._last_pos[0]
            dy = f.dh_palm_pos[1] - self._last_pos[1]
            dz = f.dh_palm_pos[2] - self._last_pos[2]
            self.path_length_m += (dx * dx + dy * dy + dz * dz) ** 0.5
        if self._last_roll is not None:
            self.rotation_total_deg += abs(f.dh_palm_roll_deg - self._last_roll)
        self._last_pos = f.dh_palm_pos
        self._last_roll = f.dh_palm_roll_deg

    def on_gaze_enter(self, f: Frame, obj: Optional[int]):
        pass

    # -- mode -------------------------------------------------------------
    def _mode_hand(self) -> PinchDetector:
        """The hand whose full release clears the group. See params.FULLDH_UNGROUP_ALL."""
        return self.dh

    @property
    def in_mode(self) -> bool:
        return self.dh.state is PinchState.SEMI

    def _check_trial_end(self, f: Frame) -> bool:
        """Trial ends on a DH full pinch held for 250 ms (Sec. 4.2, Fig. 8)."""
        if self.dh.state is PinchState.FULL:
            if self._full_pinch_since is None:
                self._full_pinch_since = f.t_ms
            elif f.t_ms - self._full_pinch_since >= self.p.full_pinch_hold_ms:
                if self.trial_ended_at is None:
                    self.trial_ended_at = f.t_ms
                    self.events.append(Event(f.t_ms, "trial_end"))
                return True
        else:
            self._full_pinch_since = None
        return False

    # -- main -------------------------------------------------------------
    def step(self, f: Frame):
        self._track_kinematics(f)
        was_mode = self.in_mode
        self.dh.update(f.dh_pinch_dist_m)
        self.ndh.update(f.ndh_pinch_dist_m)
        if self.in_mode and not was_mode:
            self.events.append(Event(f.t_ms, "mode_enter"))
        if was_mode and not self.in_mode:
            self.events.append(Event(f.t_ms, "mode_exit"))
        if self._mode_hand().entered_release and self.grouped:
            # Sec. 3.2: a full-release pinch ungroups everything.
            self.grouped.clear()
            self.events.append(Event(f.t_ms, "ungroup_all"))
        self._track_gaze(f)
        if self.trial_ended_at is None:
            self.trigger(f)
            self._check_trial_end(f)
        return self.grouped

    def trigger(self, f: Frame):
        raise NotImplementedError


class SemiDwell(_Base):
    """Sec. 3.3.1 - 500 ms of gaze on the collider."""

    name = "SemiDwell"

    def trigger(self, f: Frame):
        if not self.in_mode or self.gaze_obj is None or self._gaze_since_ms is None:
            return
        if not self._armed.get(self.gaze_obj, False):
            return
        if f.t_ms - self._gaze_since_ms >= self.p.dwell_ms:
            self._toggle(self.gaze_obj, f.t_ms)
            self._armed[self.gaze_obj] = False  # params.DWELL_REARM


class SemiSwipe(_Base):
    """Sec. 3.3.2 - leftward DH translation, 1:1 indicator, ignore rightward."""

    name = "SemiSwipe"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._ref_x: Optional[float] = None

    def on_gaze_enter(self, f: Frame, obj):
        self._ref_x = f.dh_palm_pos[0]  # params.SWIPE_REFERENCE

    def indicator_progress(self, f: Frame) -> float:
        """0..1 fraction of the indicator's travel toward the target."""
        if self._ref_x is None:
            return 0.0
        leftward = max(0.0, self._ref_x - f.dh_palm_pos[0])  # params.SWIPE_AXIS
        return min(1.0, self.p.swipe_gain * leftward / self.p.swipe_travel_m)

    def trigger(self, f: Frame):
        if not self.in_mode or self.gaze_obj is None:
            self._ref_x = f.dh_palm_pos[0]
            return
        if self._ref_x is None:
            self._ref_x = f.dh_palm_pos[0]
            return
        # a rightward return stroke re-arms the reference (the paper ignores the
        # right direction; see params.SWIPE_REFERENCE)
        if f.dh_palm_pos[0] > self._ref_x:
            self._ref_x = f.dh_palm_pos[0]
            return
        if self.indicator_progress(f) >= 1.0 and self._armed.get(self.gaze_obj, False):
            self._toggle(self.gaze_obj, f.t_ms)
            self._armed[self.gaze_obj] = False
            self._ref_x = f.dh_palm_pos[0]


class SemiTilt(_Base):
    """Sec. 3.3.3 - rightward roll, indicator geared 3x, fires at 30 deg."""

    name = "SemiTilt"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._ref_roll: Optional[float] = None

    def on_gaze_enter(self, f: Frame, obj):
        self._ref_roll = f.dh_palm_roll_deg  # params.TILT_REFERENCE

    def indicator_angle_deg(self, f: Frame) -> float:
        if self._ref_roll is None:
            return 0.0
        rightward = max(0.0, f.dh_palm_roll_deg - self._ref_roll)
        return min(P.TILT_INDICATOR_TRAVEL_DEG, self.p.tilt_gain * rightward)

    def trigger(self, f: Frame):
        if not self.in_mode or self.gaze_obj is None:
            self._ref_roll = f.dh_palm_roll_deg
            return
        if self._ref_roll is None:
            self._ref_roll = f.dh_palm_roll_deg
            return
        if f.dh_palm_roll_deg < self._ref_roll:
            self._ref_roll = f.dh_palm_roll_deg
            return
        if (f.dh_palm_roll_deg - self._ref_roll >= self.p.tilt_threshold_deg
                and self._armed.get(self.gaze_obj, False)):
            self._toggle(self.gaze_obj, f.t_ms)
            self._armed[self.gaze_obj] = False
            self._ref_roll = f.dh_palm_roll_deg


class SemiNDH(_Base):
    """Sec. 3.3.4 - NDH full pinch confirms while the DH holds the semi-pinch."""

    name = "SemiNDH"

    def trigger(self, f: Frame):
        if not self.in_mode or self.gaze_obj is None:
            return
        if self.ndh.entered_full:  # params.NDH_CLICK_EDGE
            self._toggle(self.gaze_obj, f.t_ms)


class FullDH(_Base):
    """Sec. 4.1.1 baseline - NDH *full* pinch is the mode, DH full pinch confirms.

    The DH full pinch is both the subselection trigger here and, in Sec. 4.2,
    the trial-ending gesture. The paper never resolves the collision; this
    implementation only accepts a trial-ending pinch once the NDH has released
    the mode. See params.FULLDH_TRIAL_END.
    """

    name = "FullDH"
    requires_semi = False

    def _mode_hand(self) -> PinchDetector:
        # params.FULLDH_UNGROUP_ALL: the DH opens and closes on every pinch-click
        # here, so ungroup-all follows the NDH instead.
        return self.ndh

    @property
    def in_mode(self) -> bool:
        return self.ndh.state is PinchState.FULL

    def _check_trial_end(self, f: Frame) -> bool:
        if self.in_mode:
            self._full_pinch_since = None
            return False
        return super()._check_trial_end(f)

    def trigger(self, f: Frame):
        if not self.in_mode or self.gaze_obj is None:
            return
        if self.dh.entered_full:
            self._toggle(self.gaze_obj, f.t_ms)


TECHNIQUES = {
    "SemiDwell": SemiDwell,
    "SemiSwipe": SemiSwipe,
    "SemiTilt": SemiTilt,
    "SemiNDH": SemiNDH,
    "FullDH": FullDH,
}


def build(name: str, centres, **kw):
    if name not in TECHNIQUES:
        raise KeyError(f"unknown technique {name!r}; have {sorted(TECHNIQUES)}")
    return TECHNIQUES[name](centres, **kw)
