from dataclasses import replace
from itertools import product
import unittest

from blind_spot.model import Design, Stimulus, evaluate, oracle_detects
from blind_spot.readiness import (
    BASE_DETECTION_P, FACTORS, SHORT_BUDGET, TARGET, TARGET_BUDGET,
    readiness_experiment, readiness_row,
)
from blind_spot.statistics import detection_probability


class ReadinessTests(unittest.TestCase):
    def test_all_joint_gates_and_exact_conditions(self):
        experiment = readiness_experiment()
        rows = experiment["rows"]
        self.assertEqual(len(rows), 128)
        self.assertEqual(len({tuple(row["gates"].values()) for row in rows}), 128)
        for bits, row in zip(product((False, True), repeat=7), rows):
            exposure, lifecycle, faithful, safety, budget, retain, respond = bits
            detected = exposure and lifecycle and faithful and safety
            self.assertEqual(row["gates"], dict(zip(FACTORS, bits)))
            self.assertEqual(row["actual_navigation_loss"], exposure and lifecycle)
            self.assertEqual(row["harness_navigation_loss"], exposure and lifecycle and faithful)
            self.assertEqual(row["injected_control_detected"], detected)
            self.assertEqual(row["campaign_detection_p"], BASE_DETECTION_P if detected else 0)
            self.assertEqual(row["replay_case"] is not None, detected and retain)
            self.assertEqual(row["modeled_response_blocks"], detected and retain and respond)
            self.assertEqual(row["discovery_target_met"], detected and budget)
            self.assertEqual(row["response_target_met"], detected and budget and retain and respond)
        self.assertEqual(experiment["summary"], {
            "cases": 128, "actual_navigation_losses": 32, "injected_detections": 8,
            "replayable_findings": 4, "modeled_response_blocks": 2,
            "discovery_target_met": 4, "response_target_met": 1,
        })

    def test_each_removal_changes_only_its_gate(self):
        controls = readiness_experiment()["ablations"]
        baseline = controls[0]
        for index, row in enumerate(controls[1:-1]):
            changed = [key for key in FACTORS if row["gates"][key] != baseline["gates"][key]]
            self.assertEqual(changed, [FACTORS[index]])
            self.assertEqual(row["removed_gate"], FACTORS[index])
            self.assertEqual(row["design"], baseline["design"])
        self.assertEqual(len(controls), 9)

    def test_budget_is_not_necessary_for_an_injected_detection(self):
        row = readiness_row((True, True, True, True, False, True, True))
        self.assertTrue(row["injected_control_detected"])
        self.assertTrue(row["modeled_response_blocks"])
        self.assertFalse(row["discovery_target_met"])
        self.assertEqual(row["campaign_budget"], SHORT_BUDGET)
        self.assertGreater(row["campaign_detection_probability"], 0)
        self.assertLess(row["campaign_detection_probability"], TARGET)

    def test_minimal_rare_event_budget_is_computed_not_assumed(self):
        self.assertEqual(TARGET_BUDGET, 5990)
        self.assertGreaterEqual(detection_probability(BASE_DETECTION_P, TARGET_BUDGET), TARGET)
        self.assertLess(detection_probability(BASE_DETECTION_P, TARGET_BUDGET - 1), TARGET)
        for index in range(4):
            bits = tuple(i != index for i in range(7))
            self.assertEqual(readiness_row(bits)["campaign_detection_probability"], 0)

    def test_replay_and_response_are_downstream_of_detection(self):
        baseline = readiness_row((True,) * 7)
        for index in (5, 6):
            row = readiness_row(tuple(i != index for i in range(7)))
            self.assertTrue(row["injected_control_detected"])
            self.assertTrue(row["discovery_target_met"])
            self.assertEqual(row["campaign_detection_probability"], baseline["campaign_detection_probability"])
            self.assertFalse(row["modeled_response_blocks"])
            self.assertFalse(row["response_target_met"])

    def test_every_saved_witness_replays_a_detection(self):
        for row in readiness_experiment()["rows"]:
            case = row["replay_case"]
            if case is not None:
                actual = oracle_detects(evaluate(Stimulus(**case["stimulus"]), Design(**case["design"])), case["oracle"])
                self.assertEqual(actual, case["expected_detection"])
                self.assertTrue(actual)

    def test_guarded_negative_control_and_containment(self):
        control = readiness_experiment()["ablations"][-1]
        self.assertTrue(all(control["gates"].values()))
        self.assertTrue(control["design"]["conversion_guard"])
        self.assertFalse(control["actual_navigation_loss"])
        self.assertFalse(control["injected_control_detected"])
        self.assertEqual(control["campaign_detection_probability"], 0)
        for design in (Design(alignment_retained=False), Design(isolate_alignment_failure=True)):
            self.assertFalse(readiness_row((True,) * 7, design)["injected_control_detected"])
        diagnostic_only = readiness_row((True,) * 7, Design(diagnostic_guard=True))
        self.assertTrue(diagnostic_only["injected_control_detected"])

    def test_snapshot_conditions_match_the_existing_finite_model_grid(self):
        for flags in product((False, True), repeat=4):
            retained, guarded, isolated, diagnostics = flags
            design = Design(retained, guarded, isolated, diagnostics)
            for gates in product((False, True), repeat=4):
                row = readiness_row((*gates, True, True, True), design)
                stimulus = Stimulus(**row["stimulus"])
                outcome = evaluate(stimulus, replace(design, software_in_loop=gates[2]))
                self.assertEqual(row["injected_control_detected"], oracle_detects(outcome, "safety" if gates[3] else "packet"))
                expected = gates[0] and gates[1] and retained and not guarded and not isolated and gates[2] and gates[3]
                self.assertEqual(row["injected_control_detected"], expected)

    def test_bad_rows_are_rejected(self):
        for row in ((True,) * 6, (True,) * 8, (True,) * 6 + (1,), ("yes",) * 7):
            with self.assertRaises(ValueError):
                readiness_row(row)
