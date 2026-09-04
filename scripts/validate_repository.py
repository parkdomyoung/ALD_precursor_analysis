"""Fast, offline validation for repository data and notebook structure."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ("ALD_GNN.ipynb", "ALD_LGBM.ipynb", "ALD_textmining.ipynb")
REQUIRED_TMQM_COLUMNS = {
    "CSD_code",
    "Electronic_E",
    "Dispersion_E",
    "Dipole_M",
    "Metal_q",
    "HL_Gap",
    "HOMO_Energy",
    "LUMO_Energy",
    "Polarizability",
    "CSD_years",
    "SMILES",
}
PRIVATE_METADATA_KEYS = {"authorship_tag", "userId", "displayName"}


def walk_keys(value: Any) -> set[str]:
    """Collect mapping keys recursively."""
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys.update(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(walk_keys(child))
    return keys


def validate_notebook(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path.name}: invalid notebook JSON: {exc}"]

    if notebook.get("nbformat") != 4:
        errors.append(f"{path.name}: expected nbformat 4")
    cells = notebook.get("cells")
    if not isinstance(cells, list) or not cells:
        errors.append(f"{path.name}: notebook has no cells")
        return errors

    leaked_keys = walk_keys(notebook.get("metadata", {})) & PRIVATE_METADATA_KEYS
    for index, cell in enumerate(cells):
        leaked_keys.update(walk_keys(cell.get("metadata", {})) & PRIVATE_METADATA_KEYS)
        if cell.get("cell_type") == "code":
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            try:
                compile(source, f"{path.name}:cell-{index}", "exec")
            except SyntaxError as exc:
                errors.append(
                    f"{path.name}: cell {index} has invalid Python syntax: "
                    f"{exc.msg} (line {exc.lineno})"
                )
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(
                    f"{path.name}: cell {index} stores an error output "
                    f"({output.get('ename', 'unknown')})"
                )
    if leaked_keys:
        errors.append(
            f"{path.name}: private notebook metadata keys: "
            + ", ".join(sorted(leaked_keys))
        )
    return errors


def validate_tmqm(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=";")
            header = next(reader)
    except (OSError, StopIteration) as exc:
        return [f"tmQM_y.csv: cannot read header: {exc}"]

    missing = REQUIRED_TMQM_COLUMNS - set(header)
    return [f"tmQM_y.csv: missing columns: {sorted(missing)}"] if missing else []


def validate_dft_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        return [f"{path}: cannot read: {exc}"]

    if len(rows) != 10:
        errors.append(f"{path}: expected 10 precursor rows, found {len(rows)}")

    compounds: set[str] = set()
    for row in rows:
        compound = row.get("compound", "")
        if not compound or compound in compounds:
            errors.append(f"{path}: missing or duplicate compound {compound!r}")
        compounds.add(compound)

        relative_output = row.get("dft_output_file", "")
        output_path = ROOT / relative_output
        if not output_path.is_file():
            errors.append(f"{path}: missing {relative_output}")
            continue
        try:
            text = output_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{relative_output}: cannot read: {exc}")
            continue
        if "ORCA TERMINATED NORMALLY" not in text:
            errors.append(f"{relative_output}: ORCA did not terminate normally")

        try:
            if float(row.get("hl_gap_hartree", "")) <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"{path}: invalid gap for {compound}")
    return errors


def main() -> int:
    errors: list[str] = []
    for name in NOTEBOOKS:
        errors.extend(validate_notebook(ROOT / name))
    errors.extend(validate_tmqm(ROOT / "tmQM_y.csv"))
    errors.extend(validate_dft_manifest(ROOT / "data/ald_precursors.csv"))

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
