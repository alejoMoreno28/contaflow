"""Migra de forma auditable las referencias de aceites excluidos en Google Sheets.

El modo predeterminado es solo lectura. Los cambios requieren ``--apply`` y se
respaldan en JSON y CSV antes de escribir una sola celda.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yamaha_catalog import build_catalog_row  # noqa: E402
from yamaha_rules import (  # noqa: E402
    CTA_ACEITES,
    EXCLUDED_OILS,
    IVA_MAYOR_COSTO,
    YamahaRuleError,
    normalize_product_code,
    normalize_reference,
)

SPREADSHEET_ID = "1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI"
WORKSHEET_NAME = "INVENARIOS"


class MigrationConflict(RuntimeError):
    """Impide cualquier escritura cuando la hoja no coincide con lo aprobado."""


@dataclass(frozen=True)
class ExistingUpdate:
    row_number: int
    reference: str
    values: dict[str, str]


@dataclass
class MigrationPlan:
    updates: list[ExistingUpdate] = field(default_factory=list)
    additions: list[list[str]] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApplyResult:
    backup_json: Path | None
    backup_csv: Path | None


def _cell(row: Sequence[object], index: int) -> str:
    if len(row) <= index or row[index] is None:
        return ""
    return str(row[index]).strip()


def plan_migration(
    rows: Sequence[Sequence[object]],
    *,
    creation_date: str | None = None,
) -> MigrationPlan:
    """Construye el plan sin mutar datos y falla cerrado ante ambiguedades."""
    locations: dict[str, list[tuple[int, Sequence[object]]]] = {}
    approved_keys = {reference.upper() for reference in EXCLUDED_OILS}

    for row_number, row in enumerate(rows, start=1):
        reference = normalize_reference(_cell(row, 1))
        key = reference.upper()
        if key in approved_keys:
            locations.setdefault(key, []).append((row_number, row))

    plan = MigrationPlan()
    for reference, oil in EXCLUDED_OILS.items():
        matches = locations.get(reference.upper(), [])
        if len(matches) > 1:
            plan.conflicts.append(
                f"La referencia {reference} esta duplicada en filas "
                + ", ".join(str(row_number) for row_number, _ in matches)
                + "."
            )
            continue
        if not matches:
            continue

        row_number, row = matches[0]
        try:
            current_product = normalize_product_code(_cell(row, 2))
        except YamahaRuleError as exc:
            plan.conflicts.append(
                f"La referencia {reference} tiene producto invalido en fila "
                f"{row_number}: {exc}"
            )
            continue
        if current_product != oil.producto:
            plan.conflicts.append(
                f"La referencia {reference} tiene producto {current_product} en fila "
                f"{row_number}, pero el aprobado es {oil.producto}."
            )

    if plan.conflicts:
        return plan

    for reference, oil in EXCLUDED_OILS.items():
        matches = locations.get(reference.upper(), [])
        if not matches:
            plan.additions.append(
                build_catalog_row(
                    reference,
                    oil.producto,
                    oil.descripcion,
                    IVA_MAYOR_COSTO,
                    creation_date=creation_date or date.today().isoformat(),
                )
            )
            continue

        row_number, row = matches[0]
        target = {
            "E": CTA_ACEITES,
            "G": "003",
            "H": "001",
            "I": IVA_MAYOR_COSTO,
        }
        current = {
            "E": _cell(row, 4),
            "G": _cell(row, 6),
            "H": _cell(row, 7),
            "I": _cell(row, 8),
        }
        if current == target:
            plan.unchanged.append(reference)
        else:
            plan.updates.append(
                ExistingUpdate(
                    row_number=row_number,
                    reference=reference,
                    values=target,
                )
            )

    return plan


def _write_backup(
    rows: Sequence[Sequence[object]],
    backup_dir: Path,
    timestamp: str,
) -> tuple[Path, Path]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    json_path = backup_dir / f"inventarios-before-excluded-oils-{timestamp}.json"
    csv_path = backup_dir / f"inventarios-before-excluded-oils-{timestamp}.csv"

    json_path.write_text(
        json.dumps(
            {
                "created_at": timestamp,
                "spreadsheet_id": SPREADSHEET_ID,
                "worksheet": WORKSHEET_NAME,
                "rows": [list(row) for row in rows],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    return json_path, csv_path


def apply_migration(
    worksheet,
    plan: MigrationPlan,
    *,
    apply: bool = False,
    backup_dir: Path,
    timestamp: str | None = None,
) -> ApplyResult:
    """Aplica un plan validado; en seco no crea archivos ni hace escrituras."""
    if plan.conflicts:
        raise MigrationConflict("\n".join(plan.conflicts))
    if not apply:
        return ApplyResult(backup_json=None, backup_csv=None)

    current_rows = worksheet.get_all_values()
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_json, backup_csv = _write_backup(current_rows, backup_dir, stamp)

    updates = [
        {"range": "I1", "values": [["TRATAMIENTO_IVA"]]},
        {"range": "I5", "values": [["TRATAMIENTO_IVA"]]},
    ]
    for change in plan.updates:
        updates.extend(
            {
                "range": f"{column}{change.row_number}",
                "values": [[value]],
            }
            for column, value in change.values.items()
        )

    worksheet.batch_update(updates, value_input_option="RAW")
    if plan.additions:
        worksheet.append_rows(plan.additions, value_input_option="RAW")

    return ApplyResult(backup_json=backup_json, backup_csv=backup_csv)


def _open_worksheet(credentials_path: Path | None, *, readonly: bool):
    import gspread
    from google.oauth2.service_account import Credentials

    scope = (
        "https://www.googleapis.com/auth/spreadsheets.readonly"
        if readonly
        else "https://www.googleapis.com/auth/spreadsheets"
    )
    credentials_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if credentials_json:
        credentials = Credentials.from_service_account_info(
            json.loads(credentials_json),
            scopes=[scope],
        )
    elif credentials_path:
        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=[scope],
        )
    else:
        raise MigrationConflict(
            "Indica --credentials o define GOOGLE_SHEETS_CREDENTIALS."
        )

    return (
        gspread.authorize(credentials)
        .open_by_key(SPREADSHEET_ID)
        .worksheet(WORKSHEET_NAME)
    )


def _print_plan(plan: MigrationPlan) -> None:
    print(f"Referencias aprobadas: {len(EXCLUDED_OILS)}")
    print(f"Filas existentes por corregir: {len(plan.updates)}")
    print(f"Referencias por agregar: {len(plan.additions)}")
    print(f"Referencias ya correctas: {len(plan.unchanged)}")
    if plan.updates:
        print("Correcciones: " + ", ".join(item.reference for item in plan.updates))
    if plan.conflicts:
        print("CONFLICTOS:")
        for conflict in plan.conflicts:
            print(f"- {conflict}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=ROOT.parent / "contaflow_backups",
    )
    args = parser.parse_args()

    worksheet = _open_worksheet(args.credentials, readonly=not args.apply)
    plan = plan_migration(worksheet.get_all_values())
    _print_plan(plan)
    if plan.conflicts:
        return 2
    if not args.apply:
        print("SIMULACION: no se escribio ninguna celda.")
        return 0

    result = apply_migration(
        worksheet,
        plan,
        apply=True,
        backup_dir=args.backup_dir,
    )
    verification = plan_migration(worksheet.get_all_values())
    if verification.conflicts or verification.updates or verification.additions:
        raise MigrationConflict(
            "La verificacion posterior no quedo idempotente; revisa el respaldo."
        )

    print(f"Respaldo JSON: {result.backup_json}")
    print(f"Respaldo CSV: {result.backup_csv}")
    print(f"VERIFICADO: {len(EXCLUDED_OILS)} referencias correctas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
