"""Correctness checks for quadtree.collect (run: python -m unittest test_quadtree)."""

import csv
import random
import unittest
from collections import Counter
from pathlib import Path

from quadtree import Rect, bounding_rect, collect

DATA = Path(__file__).parent / "data" / "rincon_listings.csv"


def check_partition(test, root, result, points, k):
    # Every point reported exactly once.
    test.assertEqual(Counter(result.points), Counter(points))
    test.assertEqual(result.unresolved, 0)
    # Leaves tile the root: areas add up and no point falls in two leaves.
    test.assertAlmostEqual(sum(r.area() for r in result.leaves), root.area(), places=9)
    for p in points:
        test.assertEqual(sum(r.contains(p) for r in result.leaves), 1)
    # Every leaf fits under the cap.
    for r in result.leaves:
        test.assertLessEqual(sum(r.contains(p) for p in points), k)
    # The quadtree has 4 children per internal node: queries = 4 * internal + 1.
    test.assertEqual((result.queries - 1) % 4, 0)
    test.assertEqual(len(result.leaves), 3 * (result.queries - 1) // 4 + 1)


class CollectTest(unittest.TestCase):
    def test_uniform_random(self):
        rng = random.Random(1)
        for n, k in [(0, 5), (1, 1), (10, 3), (500, 7), (2000, 50)]:
            pts = [(rng.random(), rng.random()) for _ in range(n)]
            root = Rect(0.0, 0.0, 1.0, 1.0)
            check_partition(self, root, collect(root, pts, k), pts, k)

    def test_points_on_split_lines(self):
        # Midlines of the unit square at every level are dyadic fractions.
        pts = [(i / 8, j / 8) for i in range(8) for j in range(8)]
        root = Rect(0.0, 0.0, 1.0, 1.0)
        check_partition(self, root, collect(root, pts, 3), pts, 3)

    def test_duplicates_within_cap(self):
        pts = [(0.3, 0.3)] * 4 + [(0.7, 0.2), (0.1, 0.9)]
        root = Rect(0.0, 0.0, 1.0, 1.0)
        check_partition(self, root, collect(root, pts, 4), pts, 4)

    def test_duplicates_over_cap_terminate(self):
        pts = [(0.3, 0.3)] * 5
        result = collect(Rect(0.0, 0.0, 1.0, 1.0), pts, 4)
        self.assertEqual(result.unresolved, 1)
        self.assertEqual(len(result.points), 4)

    def test_rincon_listings(self):
        with open(DATA) as f:
            pts = [(float(r["lng"]), float(r["lat"])) for r in csv.DictReader(f)]
        root = bounding_rect(pts)
        check_partition(self, root, collect(root, pts, 20), pts, 20)


if __name__ == "__main__":
    unittest.main()
