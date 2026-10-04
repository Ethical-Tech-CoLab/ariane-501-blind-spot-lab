import math
import unittest

from blind_spot.coverage import all_rows, coverage_experiment, interactions
from blind_spot.experiments import Experiment, reported_probability, run_experiment
from blind_spot.statistics import (
    detection_probability, tests_for_detection, wilson_interval, zero_failure_upper,
)


class StatisticsTests(unittest.TestCase):
    def test_exact_detection(self):
        self.assertEqual(detection_probability(0, 1000000), 0)
        self.assertEqual(detection_probability(1, 1), 1)
        self.assertAlmostEqual(detection_probability(0.25, 10), 1 - 0.75 ** 10)
        self.assertIsNone(tests_for_detection(0))
        for p in (0.000001, 0.0005, 0.01, 0.25):
            n = tests_for_detection(p)
            self.assertGreaterEqual(detection_probability(p, n), 0.95)
            self.assertLess(detection_probability(p, n - 1), 0.95)

    def test_intervals(self):
        self.assertAlmostEqual(zero_failure_upper(1000000), 0.000002995727786, places=14)
        low, high = wilson_interval(0, 100)
        self.assertGreaterEqual(low, 0)
        self.assertGreater(high, 0)
        low, high = wilson_interval(25, 100)
        self.assertLess(low, 0.25)
        self.assertGreater(high, 0.25)

    def test_invalid_statistics_inputs(self):
        for p in (-0.1, 1.1, math.nan):
            with self.assertRaises(ValueError):
                detection_probability(p, 10)
        for n in (0, -1, 0.5, True):
            with self.assertRaises(ValueError):
                zero_failure_upper(n)
        with self.assertRaises(ValueError):
            wilson_interval(11, 10)


class ExperimentTests(unittest.TestCase):
    def test_publication_precision_ignores_only_last_bit_noise(self):
        windows = 0.6321207427683548
        linux = 0.632120742768355
        self.assertEqual(reported_probability(windows), reported_probability(linux))
        self.assertLess(abs(reported_probability(windows) - windows), 1e-12)
        self.assertNotEqual(reported_probability(0.25), reported_probability(0.250001))

    def test_reproducible_and_expected_distribution(self):
        spec = Experiment("test", "expanded", 20000, 42, 0.25)
        result = run_experiment(spec)
        self.assertEqual(result, run_experiment(spec))
        self.assertLess(abs(result["detected_rate"] - 0.25), 0.02)
        self.assertEqual(result["latent_triggers"], result["detected"])

    def test_narrow_support(self):
        result = run_experiment(Experiment("test", "legacy", 10000, 42, 0))
        self.assertEqual(result["detected"], 0)
        self.assertEqual(result["latent_triggers"], 0)

    def test_pairwise_counterexample_and_exhaustive(self):
        result = coverage_experiment()
        self.assertEqual(result["pair_universe"], math.comb(8, 2) * 4)
        self.assertEqual(result["suites"]["exhaustive"]["cases"], 256)
        self.assertEqual(result["suites"]["exhaustive"]["navigation_losses"], 4)
        self.assertEqual(result["suites"]["exhaustive"]["detected"], 2)
        for suite in result["suites"].values():
            self.assertEqual(suite["pair_coverage"], 1)
            actual = set().union(*(interactions(tuple(row)) for row in suite["rows"]))
            self.assertEqual(len(actual), 112)
        witness = result["suites"]["pairwise_blind_witness"]
        self.assertEqual(witness["navigation_losses"], 0)
        self.assertEqual(witness["detected"], 0)

    def test_full_binary_grid_unique(self):
        self.assertEqual(len(set(all_rows())), 256)


if __name__ == "__main__":
    unittest.main()
