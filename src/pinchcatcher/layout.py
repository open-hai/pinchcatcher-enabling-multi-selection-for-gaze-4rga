"""Stimulus layout generator (Sec. 4.1.2, Fig. 7A).

Stated by the paper:
  40 sphere-shaped objects, equal 1 m intervals, on a rectangular flat grid
  window; participant 13.5 m from the window; window 58.12 deg wide and
  25.06 deg high; object radius 0.20 m; targets blue, distractors white; the
  objects "were randomly placed in each trial".

Not stated: the number of rows and columns. The angular window converts to
15.00 m x 6.00 m at 13.5 m, which at 1 m spacing admits a 16 x 7 = 112 cell
lattice - far more than 40 cells. So either the 40 objects occupy a random
subset of a larger lattice, or the window figure and the spacing figure refer
to different things. This module implements the subset reading and exposes the
arithmetic so the discrepancy is visible. See params.GRID_SHAPE.
"""

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

from . import params as P


def window_extent_m(width_deg=P.WINDOW_WIDTH_DEG, height_deg=P.WINDOW_HEIGHT_DEG,
                    distance_m=P.VIEW_DISTANCE_M) -> Tuple[float, float]:
    """Angular window -> metric window at the stated viewing distance."""
    w = 2.0 * distance_m * math.tan(math.radians(width_deg) / 2.0)
    h = 2.0 * distance_m * math.tan(math.radians(height_deg) / 2.0)
    return w, h


def lattice(spacing_m=P.GRID_SPACING_M) -> List[Tuple[float, float]]:
    """Candidate cell centres, centred on the window, at the stated spacing."""
    w, h = window_extent_m()
    ncols = int(math.floor(w / spacing_m)) + 1
    nrows = int(math.floor(h / spacing_m)) + 1
    x0 = -spacing_m * (ncols - 1) / 2.0
    y0 = -spacing_m * (nrows - 1) / 2.0
    return [(x0 + c * spacing_m, y0 + r * spacing_m)
            for r in range(nrows) for c in range(ncols)]


@dataclass
class Layout:
    centres: List[Tuple[float, float, float]]
    targets: List[int]
    distractors: List[int]

    @property
    def n_targets(self):
        return len(self.targets)


def make_trial(n_targets: int, rng: random.Random,
               n_objects=P.N_OBJECTS, distance_m=P.VIEW_DISTANCE_M) -> Layout:
    """One trial's object placement and target assignment."""
    if n_targets not in P.TARGET_COUNTS:
        raise ValueError(f"n_targets must be one of {P.TARGET_COUNTS}")
    cells = lattice()
    if len(cells) < n_objects:
        raise ValueError("lattice smaller than the required object count")
    chosen = rng.sample(cells, n_objects)  # params.GRID_SHAPE
    centres = [(x, y, distance_m) for (x, y) in chosen]
    idx = list(range(n_objects))
    targets = sorted(rng.sample(idx, n_targets))  # params.TARGET_PLACEMENT
    distractors = [i for i in idx if i not in set(targets)]
    return Layout(centres=centres, targets=targets, distractors=distractors)


def geometry_report():
    """Numbers a reimplementer needs, and the ones that do not line up."""
    w, h = window_extent_m()
    cells = lattice()
    ncols = int(math.floor(w / P.GRID_SPACING_M)) + 1
    nrows = int(math.floor(h / P.GRID_SPACING_M)) + 1
    obj_deg = 2.0 * math.degrees(math.atan2(P.OBJECT_RADIUS_M, P.VIEW_DISTANCE_M))
    col_deg = 2.0 * math.degrees(math.atan2(P.COLLIDER_RADIUS_M, P.VIEW_DISTANCE_M))
    spacing_deg = 2.0 * math.degrees(math.atan2(P.GRID_SPACING_M / 2, P.VIEW_DISTANCE_M))
    return {
        "window_width_m": w,
        "window_height_m": h,
        "lattice_cols": ncols,
        "lattice_rows": nrows,
        "lattice_cells": len(cells),
        "objects_placed": P.N_OBJECTS,
        "cells_unused": len(cells) - P.N_OBJECTS,
        "object_angular_diameter_deg": obj_deg,
        "collider_angular_diameter_deg": col_deg,
        "cell_pitch_deg": spacing_deg,
        "collider_diameter_m": 2 * P.COLLIDER_RADIUS_M,
        "colliders_overlap_orthogonal_neighbour":
            2 * P.COLLIDER_RADIUS_M > P.GRID_SPACING_M,
        "colliders_overlap_diagonal_neighbour":
            2 * P.COLLIDER_RADIUS_M > P.GRID_SPACING_M * math.sqrt(2),
    }
