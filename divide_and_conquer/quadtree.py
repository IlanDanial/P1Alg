"""Adaptive quadtree decomposition for capped map search (divide and conquer).

A map-search service (e.g. Airbnb's map view) returns the listings inside a
rectangular window only when the window holds at most k of them; otherwise it
truncates the results. To enumerate every listing in a region we split the
window into four quadrants and recurse until every window fits under the cap.

Abstraction: P is a set of n points in a rectangle R. The leaves of the
recursion form a partition of R into half-open rectangles, each holding at
most k points of P, and the union of their points is exactly P.
"""

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rect:
    """Half-open rectangle [x0, x1) x [y0, y1).

    Half-open bounds guarantee that a point on a split line belongs to exactly
    one quadrant, so no listing is reported twice or skipped.
    """

    x0: float
    y0: float
    x1: float
    y1: float

    def contains(self, p):
        return self.x0 <= p[0] < self.x1 and self.y0 <= p[1] < self.y1

    def area(self):
        return (self.x1 - self.x0) * (self.y1 - self.y0)

    def quadrants(self, xm, ym):
        # Order matches the bucket index (x >= xm) + 2 * (y >= ym) in _collect.
        return (
            Rect(self.x0, self.y0, xm, ym),  # 0: lower-left
            Rect(xm, self.y0, self.x1, ym),  # 1: lower-right
            Rect(self.x0, ym, xm, self.y1),  # 2: upper-left
            Rect(xm, ym, self.x1, self.y1),  # 3: upper-right
        )


@dataclass
class Result:
    points: list = field(default_factory=list)  # every listing found
    leaves: list = field(default_factory=list)  # windows that fit under the cap
    queries: int = 0  # search requests issued (one per recursion node)
    max_depth: int = 0  # height of the quadtree
    unresolved: int = 0  # windows that hit min_width while still over the cap


def bounding_rect(points):
    """Smallest half-open rectangle containing every point.

    The upper bounds are nudged to the next float so the points with the
    largest x or y still fall inside the half-open box.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return Rect(min(xs), min(ys),
                math.nextafter(max(xs), math.inf), math.nextafter(max(ys), math.inf))


def collect(rect, points, k, min_width=1e-9):
    """Return every point in `rect` using windows of at most k points.

    `points` is the ground truth the simulated search service holds for
    `rect`; the algorithm only learns it through the capped query on each
    window. If more than k points share (nearly) the same location no window
    can isolate them, so recursion stops once a window is narrower than
    `min_width` and the window is counted as unresolved.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    result = Result()
    _collect(rect, points, k, min_width, 0, result)
    return result


def _collect(rect, points, k, min_width, depth, result):
    result.queries += 1
    result.max_depth = max(result.max_depth, depth)

    # Base case: the service shows the whole window.
    if len(points) <= k:
        result.points.extend(points)
        result.leaves.append(rect)
        return

    # Cannot zoom any further: keep the truncated page the service shows.
    if rect.x1 - rect.x0 <= min_width or rect.y1 - rect.y0 <= min_width:
        result.points.extend(points[:k])
        result.leaves.append(rect)
        result.unresolved += 1
        return

    # Divide: split the window at its midpoint into four quadrants.
    xm = (rect.x0 + rect.x1) / 2
    ym = (rect.y0 + rect.y1) / 2
    buckets = ([], [], [], [])
    for p in points:
        buckets[(p[0] >= xm) + 2 * (p[1] >= ym)].append(p)

    # Conquer each quadrant; combining is just appending to the shared result.
    for quad, bucket in zip(rect.quadrants(xm, ym), buckets):
        _collect(quad, bucket, k, min_width, depth + 1, result)
