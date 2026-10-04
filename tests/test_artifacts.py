import ast
import csv
import json
import math
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = json.loads((ROOT / "results" / "study.json").read_text(encoding="utf-8"))

    def test_counts_match_analytic_probabilities(self):
        rows = self.results["monte_carlo"]
        self.assertEqual(sum(row["n"] for row in rows), 1600000)
        for row in rows:
            n, p = row["n"], row["expected_detection_p"]
            for key in ("latent_triggers", "navigation_losses", "unsafe_commands", "detected"):
                self.assertTrue(0 <= row[key] <= n)
            self.assertEqual(row["detected_rate"], row["detected"] / n)
            if p == 0:
                self.assertEqual(row["detected"], 0)
            else:
                self.assertLess(abs(row["detected"] - n * p), 6 * math.sqrt(n * p * (1 - p)))

    def test_paired_harness_and_oracle_contrast(self):
        rows = {row["name"]: row for row in self.results["monte_carlo"]}
        baseline = rows["expanded_faithful"]
        for name in ("expanded_idealized_stub", "expanded_packet_oracle", "expanded_alignment_removed"):
            self.assertEqual(rows[name]["seed"], baseline["seed"])
            self.assertEqual(rows[name]["latent_triggers"], baseline["latent_triggers"])
        self.assertEqual(rows["expanded_packet_oracle"]["navigation_losses"], baseline["navigation_losses"])
        self.assertEqual(rows["expanded_idealized_stub"]["navigation_losses"], 0)

    def test_provenance_and_assumption_test_mappings(self):
        catalog = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
        ids = [source["id"] for source in catalog["sources"]]
        self.assertEqual(len(ids), len(set(ids)))
        register = json.loads((ROOT / "data" / "assumptions.json").read_text(encoding="utf-8"))
        for assumption in register["assumptions"]:
            self.assertTrue(set(assumption["evidence"]) <= set(ids))
            module, class_name, method = assumption["test"].split(".")
            tree = ast.parse((ROOT / "tests" / f"{module}.py").read_text(encoding="utf-8"))
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
            self.assertEqual(len(classes), 1)
            self.assertIn(method, [node.name for node in classes[0].body if isinstance(node, ast.FunctionDef)])
        with (ROOT / "data" / "variables.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(all(None not in row and None not in row.values() for row in rows))
        self.assertTrue(all(row["value"] == "" for row in rows if row["evidence_class"] == "unavailable"))

    def test_notebook_story_and_clean_state(self):
        notebook = json.loads((ROOT / "study.ipynb").read_text(encoding="utf-8"))
        code_count = 0
        for i, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                code_count += 1
                self.assertEqual(notebook["cells"][i + 1]["cell_type"], "markdown")
                self.assertFalse(any(out["output_type"] == "error" for out in cell["outputs"]))
                compile("".join(cell["source"]), f"cell-{i}", "exec")
        self.assertEqual(code_count, 5)

    def test_figures_are_parseable_and_accessible(self):
        for path in (ROOT / "results").glob("*.svg"):
            root = ET.parse(path).getroot()
            self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
            self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))

    def test_local_document_links_resolve(self):
        for path in [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("http:", "https:", "#")):
                    continue
                self.assertTrue((path.parent / target.split("#")[0]).exists(), f"{path}: {target}")

    def test_trace_latches_after_cutoff(self):
        with (ROOT / "results" / "synthetic_trace.csv").open(newline="", encoding="utf-8") as stream:
            trace = list(csv.DictReader(stream))
        self.assertEqual(len(trace), 501)
        losses = [row for row in trace if row["navigation_available"] == "False"]
        self.assertAlmostEqual(float(losses[0]["time_s"]), 32.8)
        self.assertEqual(trace[-1]["navigation_available"], "False")
        self.assertTrue(all(row["navigation_with_alignment_removed"] == "True" for row in trace))


if __name__ == "__main__":
    unittest.main()
