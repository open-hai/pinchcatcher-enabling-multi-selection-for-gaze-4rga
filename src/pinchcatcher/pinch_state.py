"""Three-state pinch detector from thumb-index fingertip distance.

Paper basis: Sec. 3.2 and Fig. 3 of Kim et al. (CHI '25).

  Fig. 3 (A) FULL     - "both fingertips are touching"        (no number given)
  Fig. 3 (B) SEMI     - fingertip distance between 2 and 7 cm
  Fig. 3 (C) RELEASE  - distance over 10 cm

The 7-10 cm gap is the only hysteresis the paper quantifies. Sec. 3.2 says a
different threshold was used per transition direction but never lists them, so
this implementation treats the gap as a dead band in which the current state is
held. See params.HYSTERESIS_DEAD_BAND.
"""

from enum import Enum

from .params import FULL_PINCH_M, RELEASE_M, SEMI_MAX_M, SEMI_MIN_M


class PinchState(Enum):
    FULL = "full_pinch"
    SEMI = "semi_pinch"
    RELEASE = "full_release"


class PinchDetector:
    def __init__(
        self,
        full_m: float = FULL_PINCH_M,
        semi_min_m: float = SEMI_MIN_M,
        semi_max_m: float = SEMI_MAX_M,
        release_m: float = RELEASE_M,
        initial: PinchState = PinchState.RELEASE,
    ):
        if not full_m <= semi_min_m <= semi_max_m <= release_m:
            raise ValueError("thresholds must be ordered")
        self.full_m = full_m
        self.semi_min_m = semi_min_m
        self.semi_max_m = semi_max_m
        self.release_m = release_m
        self.state = initial
        self.previous = initial

    def update(self, distance_m: float) -> PinchState:
        self.previous = self.state
        if distance_m < self.full_m:
            self.state = PinchState.FULL
        elif self.semi_min_m <= distance_m <= self.semi_max_m:
            self.state = PinchState.SEMI
        elif distance_m >= self.release_m:
            self.state = PinchState.RELEASE
        # else: inside the (semi_max, release) dead band -> hold current state
        return self.state

    @property
    def entered_full(self) -> bool:
        return self.state is PinchState.FULL and self.previous is not PinchState.FULL

    @property
    def entered_release(self) -> bool:
        return self.state is PinchState.RELEASE and self.previous is not PinchState.RELEASE

    @property
    def in_multiselect_band(self) -> bool:
        return self.state is PinchState.SEMI
