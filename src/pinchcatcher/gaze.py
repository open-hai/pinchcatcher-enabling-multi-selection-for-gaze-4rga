"""Gaze target resolution against enlarged invisible colliders.

Paper basis: Sec. 3.3.1 and Sec. 4.1.3. The visible spheres have radius 0.20 m;
the invisible gaze collider is three times that radius, i.e. 0.60 m, "to
prevent tracking issues caused by eye-tracking".

The paper never says how a hit is resolved when several colliders are pierced
by the same ray. On a 1 m lattice, 0.60 m colliders overlap with all four
orthogonal neighbours (centre separation 1.00 m < 1.20 m), so the ambiguity is
not hypothetical: it is the common case near a cell boundary. See
params.GAZE_TIE_BREAK.
"""

import math
from typing import List, Optional, Sequence, Tuple

Vec3 = Tuple[float, float, float]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a: Vec3) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: Vec3) -> Vec3:
    n = _norm(a)
    if n == 0.0:
        raise ValueError("zero-length vector")
    return (a[0] / n, a[1] / n, a[2] / n)


def ray_hits_sphere(origin: Vec3, direction: Vec3, centre: Vec3, radius: float) -> bool:
    """True if the forward ray intersects the sphere."""
    d = _unit(direction)
    oc = _sub(centre, origin)
    t_ca = _dot(oc, d)
    if t_ca < 0 and _norm(oc) > radius:
        return False
    d2 = _dot(oc, oc) - t_ca * t_ca
    return d2 <= radius * radius


def angle_to_ray_deg(origin: Vec3, direction: Vec3, centre: Vec3) -> float:
    d = _unit(direction)
    oc = _sub(centre, origin)
    n = _norm(oc)
    if n == 0.0:
        return 0.0
    c = max(-1.0, min(1.0, _dot(oc, d) / n))
    return math.degrees(math.acos(c))


def collider_hits(
    origin: Vec3, direction: Vec3, centres: Sequence[Vec3], radius: float
) -> List[int]:
    """Indices of every collider the ray pierces, in scene order."""
    return [i for i, c in enumerate(centres) if ray_hits_sphere(origin, direction, c, radius)]


def resolve_gaze_target(
    origin: Vec3,
    direction: Vec3,
    centres: Sequence[Vec3],
    radius: float,
    tie_break: str = "min_angle_to_ray",
) -> Tuple[Optional[int], List[int]]:
    """Return (chosen index or None, all hit indices).

    `tie_break` is an assumption of this reimplementation, not of the paper:
      min_angle_to_ray - smallest angular offset between ray and centre
      nearest          - closest centre to the ray origin
      first            - lowest scene index (Unity's arbitrary raycast order)
    """
    hits = collider_hits(origin, direction, centres, radius)
    if not hits:
        return None, hits
    if len(hits) == 1:
        return hits[0], hits
    if tie_break == "min_angle_to_ray":
        return min(hits, key=lambda i: angle_to_ray_deg(origin, direction, centres[i])), hits
    if tie_break == "nearest":
        return min(hits, key=lambda i: _norm(_sub(centres[i], origin))), hits
    if tie_break == "first":
        return hits[0], hits
    raise ValueError(f"unknown tie_break {tie_break!r}")


def angular_diameter_deg(radius_m: float, distance_m: float) -> float:
    return 2.0 * math.degrees(math.atan2(radius_m, distance_m))
