import math
import unittest

from blind_spot.check_contract import contract_violations
from blind_spot.model import (
    Design, Stimulus, convert_int16, evaluate, oracle_detects, synthetic_trace,
)


class ConversionTests(unittest.TestCase):
    def test_safe_values_and_rounding(self):
        for value, expected in (
            (0.0, 0), (0.5, 1), (-0.5, -1), (1.5, 2), (-1.5, -2),
            (32767.0, 32767), (32767.49, 32767),
            (-32768.0, -32768), (-32768.49, -32768),
            (math.nextafter(32767.5, -math.inf), 32767),
            (math.nextafter(-32768.5, math.inf), -32768),
        ):
            with self.subTest(value=value):
                self.assertEqual(convert_int16(value), expected)

    def test_out_of_range(self):
        for value in (32767.5, 32768.0, -32768.5, -32769.0, 1e100):
            with self.subTest(value=value), self.assertRaises(OverflowError):
                convert_int16(value)

    def test_all_representable_integers(self):
        for value in range(-32768, 32768):
            self.assertEqual(convert_int16(float(value)), value)

    def test_invalid_inputs_are_explicit(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                convert_int16(value)
        with self.assertRaises(TypeError):
            convert_int16(True)
        with self.assertRaises(ValueError):
            Stimulus(1.0, -1.0)
        with self.assertRaises(ValueError):
            Design(replicas=0)
        with self.assertRaises(TypeError):
            Design(conversion_guard=1)


class SystemTests(unittest.TestCase):
    def setUp(self):
        self.hazard = Stimulus(40000.0, 20.0)

    def test_same_bug_defeats_redundancy(self):
        for count in (1, 2, 3):
            outcome = evaluate(self.hazard, Design(replicas=count))
            self.assertEqual(outcome.failed_units, count)
            self.assertTrue(outcome.unsafe_command)
            self.assertTrue(oracle_detects(outcome))
            self.assertFalse(oracle_detects(outcome, "packet"))

    def test_release_contract_rejects_bad_design_and_accepts_intervention(self):
        self.assertEqual(contract_violations(Design()), [
            "positive_overflow_before_cutoff", "negative_overflow_before_cutoff",
        ])
        self.assertEqual(contract_violations(Design(alignment_retained=False)), [])

    def test_phase_boundary(self):
        self.assertFalse(evaluate(Stimulus(40000.0, 39.999)).navigation_available)
        self.assertTrue(evaluate(Stimulus(40000.0, 40.0)).navigation_available)

    def test_containment_and_removal(self):
        for design in (
            Design(alignment_retained=False), Design(conversion_guard=True),
            Design(isolate_alignment_failure=True),
        ):
            self.assertTrue(evaluate(self.hazard, design).navigation_available)
        isolated = evaluate(self.hazard, Design(isolate_alignment_failure=True))
        self.assertTrue(isolated.alignment_exception)
        guarded = evaluate(self.hazard, Design(conversion_guard=True))
        self.assertTrue(guarded.conversion_out_of_range)
        self.assertFalse(guarded.alignment_exception)

    def test_diagnostics_guard_not_a_navigation_repair(self):
        outcome = evaluate(self.hazard, Design(diagnostic_guard=True))
        self.assertFalse(outcome.unsafe_command)
        self.assertFalse(outcome.navigation_available)
        self.assertTrue(oracle_detects(outcome))

    def test_simulator_can_erase_bug(self):
        outcome = evaluate(self.hazard, Design(software_in_loop=False))
        self.assertTrue(outcome.navigation_available)
        self.assertFalse(outcome.conversion_out_of_range)

    def test_unknown_oracle_rejected(self):
        with self.assertRaises(ValueError):
            oracle_detects(evaluate(self.hazard), "typo")

    def test_synthetic_trace_latches_failure(self):
        trace = synthetic_trace(50000.0, duration_s=50.0, step_s=0.1)
        losses = [r for r in trace if not r["navigation_available"]]
        self.assertGreater(len(losses), 0)
        self.assertGreater(losses[0]["time_s"], 32.7)
        self.assertAlmostEqual(losses[0]["time_s"], 32.8)
        self.assertFalse(trace[-1]["navigation_available"])
        self.assertTrue(all(
            r["navigation_available"]
            for r in synthetic_trace(50000.0, Design(alignment_retained=False))
        ))


if __name__ == "__main__":
    unittest.main()
