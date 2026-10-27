"""Correctness checks for refresh_days (run: python -m unittest test_refresh_days)."""

import random
import unittest
from datetime import date, timedelta
from itertools import combinations

from refresh_days import refresh_days, windows


def random_intervals(rng, n, hi=20):
    out = []
    for _ in range(n):
        a, b = sorted((rng.randint(0, hi), rng.randint(0, hi)))
        out.append((a, b))
    return out


def covers(days, intervals):
    return all(any(a <= t <= b for t in days) for a, b in intervals)


class RefreshDaysTest(unittest.TestCase):
    def setUp(self):
        rng = random.Random(1)
        self.instances = [random_intervals(rng, rng.randint(0, 40)) for _ in range(300)]

    def test_every_window_covered(self):  # Lemma 1
        for iv in self.instances:
            days, _ = refresh_days(iv)
            self.assertTrue(covers(days, iv))

    def test_witnesses_pairwise_disjoint(self):  # Lemma 2
        for iv in self.instances:
            days, wit = refresh_days(iv)
            self.assertEqual(len(wit), len(days))
            for (a1, b1), (a2, b2) in combinations(wit, 2):
                self.assertTrue(b1 < a2 or b2 < a1)

    def test_brute_force_minimum(self):
        # Checks the implementation on small cases; the proof is Theorem 1.
        rng = random.Random(2)
        for _ in range(300):
            iv = random_intervals(rng, rng.randint(1, 10))
            days, _ = refresh_days(iv)
            for size in range(len(days)):
                for subset in combinations(range(21), size):
                    self.assertFalse(covers(subset, iv), (iv, subset, days))

    def test_worked_example(self):
        iv = [(1, 10), (4, 12), (8, 20), (15, 25), (22, 30)]
        days, wit = refresh_days(iv)
        self.assertEqual(set(days), {10, 25})
        self.assertEqual(wit, [(1, 10), (15, 25)])

    def test_rejects_reversed_interval(self):
        with self.assertRaises(ValueError):
            refresh_days([(3, 2)])

    def test_windows(self):
        today = date(2026, 10, 26)
        rows = [
            {"departure": today + timedelta(days=200), "nights": 4},
            {"departure": today + timedelta(days=200), "nights": 8},
            {"departure": today + timedelta(days=1), "nights": 3},  # closed yesterday
        ]
        self.assertEqual(windows(rows, today, c=2), [(124, 198), (109, 198)])
        # A window that opened in the past starts today.
        self.assertEqual(windows([{"departure": today + timedelta(days=30), "nights": 7}],
                                 today, c=2), [(0, 28)])


if __name__ == "__main__":
    unittest.main()
