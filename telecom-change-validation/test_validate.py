import unittest

from validate import compare


def site(successes, attempts=200, duration=30):
    return dict(successes=successes, attempts=attempts, window_minutes=duration, median_latency_ms=220)


class ChangePolicyTests(unittest.TestCase):
    policy = dict(change_id="TEST", minimum_attempts=100, rollback_drop_pp=5)

    def result(self, before, after):
        return compare(before, after, self.policy)["decision"]

    def test_exact_five_point_drop_requires_rollback(self):
        self.assertEqual(self.result({"A": site(198)}, {"A": site(188)}), "rollback recommendation")

    def test_drop_below_boundary_passes(self):
        self.assertEqual(self.result({"A": site(198)}, {"A": site(189)}), "pass")

    def test_missing_site_incompatible_window_and_small_sample_need_review(self):
        for after in ({}, {"A": site(198, duration=15)}, {"A": site(98, attempts=99)}):
            with self.subTest(after=after):
                self.assertEqual(self.result({"A": site(198)}, after), "review")
