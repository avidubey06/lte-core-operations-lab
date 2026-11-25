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

    def test_canary_drop_controls_decision_despite_improving_aggregate(self):
        before = {"A": site(1960, attempts=2000), "SITE-03": site(198)}
        after = {"A": site(1980, attempts=2000), "SITE-03": site(182)}
        report = compare(before, after, self.policy)
        self.assertGreater(report["after_totals"]["success_pct"], report["before_totals"]["success_pct"])
        self.assertEqual(report["decision"], "rollback recommendation")
        self.assertEqual(report["sites"][1]["change_pp"], -8)
