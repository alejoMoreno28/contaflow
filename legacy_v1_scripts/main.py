#!/usr/bin/env python3
"""
ContaFlow — Extractor de facturas electrónicas colombianas

Uso básico:
  python main.py factura.pdf
  python main.py carpeta/con/facturas/
  python main.py factura.pdf --output mi_reporte.csv
  python main.py factura.pdf --json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv es opcional; se puede exportar la variable manualmente

from extractor import process_pdf, save_to_csv

DEFAULT_OUTPUT = "output/facturas.csv"


def _fmt_total(value) -> str:
    """Formatea el total para mostrarlo en consola."""
    if isinstance(value, (int, float)):
        return f"${value:,.0f}"
    return str(value) if value is not None else "N/A"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extrae datos estructurados de facturas electrónicas colombianas (PDF).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py FE-0001.pdf
  python main.py facturas/
  python main.py FE-0001.pdf --output reportes/mayo.csv
  python main.py FE-0001.pdf --json
        """,
    )
    parser.add_argument(
        "input",
        help="Ruta al PDF o a una carpeta que contenga PDFs.",
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        metavar="CSV",
        help=f"Archivo CSV de salida (por defecto: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Imprime el JSON extraído en consola para cada factura.",
    )
    args = parser.parse_args()

    # --- Validar API key -------------------------------------------------
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "\nERROR: La variable ANTHROPIC_API_KEY no está configurada.\n"
            "  Opción 1 — Crea un archivo .env en esta carpeta con:\n"
            "             ANTHROPIC_API_KEY=sk-ant-...\n"
            "  Opción 2 — Expórtala en la terminal:\n"
            "             set ANTHROPIC_API_KEY=sk-ant-...   (Windows CMD)\n"
            "             $env:ANTHROPIC_API_KEY='sk-ant-...' (PowerShell)\n"
        )
        return 1

    # --- Resolver archivos a procesar ------------------------------------
    input_path = Path(args.input)
    pdfs: list[Path] = []

    if input_path.is_file():
        pdfs = [input_path]
    elif input_path.is_dir():
        pdfs = sorted(input_path.glob("*.pdf")) + sorted(input_path.glob("*.PDF"))
        if not pdfs:
            print(f"No se encontraron archivos PDF en: {input_path}")
            return 1
    else:
        print(f"ERROR: Ruta no encontrada: {input_path}")
        return 1

    # --- Procesar --------------------------------------------------------
    print(f"\nContaFlow  |  {len(pdfs)} archivo(s) a procesar\n" + "-" * 50)

    results: list[dict] = []
    errors: list[dict] = []

    for idx, pdf_path in enumerate(pdfs, start=1):
        print(f"\n[{idx}/{len(pdfs)}] {pdf_path.name}")
        try:
            data = process_pdf(str(pdf_path))
            results.append(data)

            factura = data.get("numero_factura") or "N/A"
            proveedor = data.get("proveedor_nombre") or "N/A"
            total = _fmt_total(data.get("total_factura"))
            print(f"  [OK] Factura {factura} | {proveedor} | Total: {total}")

            if args.json:
                # Excluir metadatos internos del JSON de consola
                display = {k: v for k, v in data.items() if not k.startswith("_")}
                print(json.dumps(display, ensure_ascii=False, indent=2))

        except Exception as exc:
            print(f"  [!] Error: {exc}")
            errors.append({"archivo": pdf_path.name, "error": str(exc)})

    # --- Guardar CSV -----------------------------------------------------
    print("\n" + "-" * 50)

    if results:
        csv_path = save_to_csv(results, args.output)
        print(f"[OK] {len(results)} factura(s) guardadas en: {csv_path}")

    if errors:
        print(f"[!] {len(errors)} error(es):")
        for err in errors:
            print(f"  - {err['archivo']}: {err['error']}")

    print()
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
