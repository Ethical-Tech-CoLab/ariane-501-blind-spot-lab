"""Execute the notebook in this interpreter without installing a global kernel."""

import argparse
import json
from pathlib import Path
import sys
import tempfile

from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
import nbformat
from nbclient import NotebookClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Execute and validate without persisting outputs")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root / "study.ipynb"
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    with tempfile.TemporaryDirectory(prefix="ariane501-kernel-") as temporary:
        kernels = Path(temporary)
        spec = kernels / "ariane501"
        spec.mkdir()
        (spec / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Ariane 501 local study",
            "language": "python",
        }), encoding="utf-8")
        manager = KernelManager(
            kernel_name="ariane501",
            kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]),
        )
        client = NotebookClient(
            notebook, km=manager, timeout=180, allow_errors=False,
            record_timing=False, resources={"metadata": {"path": str(root)}},
        )
        client.execute(cleanup_kc=True)
    nbformat.validate(notebook)
    if not args.check:
        nbformat.write(notebook, path)
    count = sum(cell.cell_type == "code" for cell in notebook.cells)
    print(f"PASS: executed and validated all {count} notebook code cells.")


if __name__ == "__main__":
    main()
