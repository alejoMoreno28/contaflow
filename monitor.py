#!/usr/bin/env python3
"""
ContaFlow Monitor — Vigila una carpeta de Google Drive

Cuando detecta un PDF nuevo:
  1. Lo descarga
  2. Lo procesa con Claude (extractor.py)
  3. Agrega los datos al Excel de Drive (ContaFlow_Facturas.xlsx)

Uso:
  python monitor.py                        # Bucle continuo (Ctrl+C para parar)
  python monitor.py --once                 # Procesa una vez y termina
  python monitor.py --folder FOLDER_ID     # Sobreescribe el ID del .env
  python monitor.py --interval 120         # Revisar cada 2 minutos
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from drive_client import (
    get_drive_service,
    list_pdfs,
    download_file,
    find_file_in_folder,
    upload_file,
)
from excel_writer import (
    load_or_create_workbook,
    append_records,
    save_workbook,
    EXCEL_FILENAME,
)
from extractor import process_pdf

PROCESSED_LOG = "processed_files.json"
DEFAULT_INTERVAL = 60
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
LOCAL_EXCEL = Path("output") / EXCEL_FILENAME


# ---------------------------------------------------------------------------
# Registro de archivos ya procesados
# ---------------------------------------------------------------------------

def _load_processed() -> set:
    if Path(PROCESSED_LOG).exists():
        with open(PROCESSED_LOG, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def _save_processed(ids: set):
    with open(PROCESSED_LOG, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, indent=2)


# ---------------------------------------------------------------------------
# Logica principal de una revision
# ---------------------------------------------------------------------------

def _process_new_pdfs(service, folder_id: str, processed_ids: set) -> list[dict]:
    """
    Compara los PDFs de la carpeta con los ya procesados.
    Descarga y extrae los nuevos. Retorna lista de dicts con los datos.
    """
    all_pdfs = list_pdfs(service, folder_id)
    new_pdfs = [f for f in all_pdfs if f["id"] not in processed_ids]

    if not new_pdfs:
        return []

    print(f"  {len(new_pdfs)} PDF(s) nuevo(s) detectado(s)")
    results = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        for pdf_meta in new_pdfs:
            name    = pdf_meta["name"]
            file_id = pdf_meta["id"]
            print(f"\n  [{name}]")
            try:
                local_pdf = str(Path(tmp_dir) / name)
                print(f"    > Descargando desde Drive...")
                download_file(service, file_id, local_pdf)

                data = process_pdf(local_pdf)
                data["_archivo_fuente"] = name  # nombre original de Drive

                total = data.get("total_factura")
                total_str = f"${total:,.0f}" if isinstance(total, (int, float)) else str(total or "N/A")
                print(f"    [OK] Factura {data.get('numero_factura', 'N/A')} | Total: {total_str}")

                results.append(data)
                processed_ids.add(file_id)

            except Exception as exc:
                print(f"    [!] Error: {exc}")

    return results


def _sync_excel_to_drive(service, folder_id: str, records: list[dict]):
    """
    Descarga el Excel actual de Drive (si existe), agrega las filas nuevas
    y vuelve a subir el archivo actualizado.
    """
    LOCAL_EXCEL.parent.mkdir(parents=True, exist_ok=True)
    existing_id = find_file_in_folder(service, folder_id, EXCEL_FILENAME)

    if existing_id:
        print(f"  > Descargando Excel existente de Drive...")
        download_file(service, existing_id, str(LOCAL_EXCEL))

    wb = load_or_create_workbook(str(LOCAL_EXCEL))
    append_records(wb, records)
    save_workbook(wb, str(LOCAL_EXCEL))

    print(f"  > Subiendo Excel a Drive...")
    file_id = upload_file(
        service,
        folder_id,
        str(LOCAL_EXCEL),
        mime_type=EXCEL_MIME,
        existing_id=existing_id,
    )
    print(f"  [OK] Excel sincronizado (Drive ID: {file_id})")


def run_once(service, folder_id: str) -> int:
    """
    Ejecuta una revision completa.
    Retorna la cantidad de facturas nuevas procesadas.
    """
    processed = _load_processed()
    records = _process_new_pdfs(service, folder_id, processed)

    if records:
        _sync_excel_to_drive(service, folder_id, records)
        _save_processed(processed)
        print(f"\n[OK] {len(records)} factura(s) procesada(s) y guardadas en Drive.")
    else:
        print("  Sin PDFs nuevos.")

    return len(records)


def run_loop(service, folder_id: str, interval: int):
    print(f"Monitor activo | Carpeta: {folder_id} | Intervalo: {interval}s")
    print("Presiona Ctrl+C para detener.\n")

    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Revisando carpeta...")
        try:
            run_once(service, folder_id)
        except Exception as exc:
            print(f"  [!] Error en el ciclo: {exc}")
        print(f"  Proxima revision en {interval}s...\n")
        time.sleep(interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Monitorea una carpeta de Google Drive y procesa facturas PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python monitor.py
  python monitor.py --once
  python monitor.py --folder 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs --interval 120
        """,
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Ejecuta una sola revision y termina.",
    )
    parser.add_argument(
        "--folder", "-f",
        default=os.getenv("DRIVE_FOLDER_ID"),
        metavar="FOLDER_ID",
        help="ID de la carpeta de Google Drive (tambien puede ir en .env como DRIVE_FOLDER_ID).",
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=int(os.getenv("POLL_INTERVAL", DEFAULT_INTERVAL)),
        metavar="SEG",
        help=f"Segundos entre revisiones (por defecto: {DEFAULT_INTERVAL}).",
    )
    args = parser.parse_args()

    # --- Validaciones previas ------------------------------------------------
    if not args.folder:
        print(
            "\nERROR: Falta el ID de la carpeta de Google Drive.\n"
            "\n"
            "  Como obtenerlo:\n"
            "    1. Abre la carpeta en drive.google.com\n"
            "    2. Copia la parte final de la URL:\n"
            "       https://drive.google.com/drive/folders/<<ESTE_ES_EL_ID>>\n"
            "\n"
            "  Opciones para configurarlo:\n"
            "    - Agrega al .env:        DRIVE_FOLDER_ID=1abc...xyz\n"
            "    - Usa el flag:           python monitor.py --folder 1abc...xyz\n"
        )
        return 1

    if not Path(CREDENTIALS_PATH := "credentials.json").exists():
        print(
            "\nERROR: No se encontro 'credentials.json'.\n"
            "\n"
            "  Pasos para crearlo:\n"
            "    1. Ve a https://console.cloud.google.com\n"
            "    2. Crea un proyecto (o usa uno existente)\n"
            "    3. Activa la API: APIs y servicios > Biblioteca > 'Google Drive API'\n"
            "    4. Crea credenciales: APIs y servicios > Credenciales\n"
            "       - Tipo: ID de cliente de OAuth\n"
            "       - Tipo de aplicacion: Aplicacion de escritorio\n"
            "    5. Descarga el JSON y guardalo como 'credentials.json' en esta carpeta\n"
        )
        return 1

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "\nERROR: La variable ANTHROPIC_API_KEY no esta configurada en .env.\n"
        )
        return 1

    # --- Ejecutar ------------------------------------------------------------
    try:
        print("Autenticando con Google Drive...")
        service = get_drive_service()
        print("[OK] Autenticacion exitosa.\n")

        if args.once:
            run_once(service, args.folder)
        else:
            run_loop(service, args.folder, args.interval)

    except KeyboardInterrupt:
        print("\nMonitor detenido.")
    except Exception as exc:
        print(f"\n[!] Error fatal: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
