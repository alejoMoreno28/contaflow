"""
extractor.py — Lógica central de ContaFlow

Responsabilidades:
  1. Leer el texto de un PDF con PyMuPDF (fitz)
  2. Enviar el texto a Claude y obtener JSON estructurado
  3. Guardar los resultados en un CSV acumulativo
"""

import base64
import fitz  # PyMuPDF
import anthropic
import json
import csv
import re
from pathlib import Path
from datetime import datetime

# Extensiones de imagen soportadas → media type para la API de Claude
IMAGE_MEDIA_TYPES: dict[str, str] = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
}


# ---------------------------------------------------------------------------
# Limpieza de strings (elimina basura al inicio/fin)
# ---------------------------------------------------------------------------

def clean_str(value) -> str | None:
    """Limpia espacios, comas y caracteres basura al inicio y fin de un string."""
    if value is None:
        return None
    cleaned = re.sub(r'^[\s,;.\-]+|[\s,;.\-]+$', '', str(value))
    return cleaned if cleaned else None


def clean_items(items: list) -> list:
    """Aplica clean_str a los campos de texto de cada ítem."""
    cleaned = []
    for item in (items or []):
        cleaned.append({
            "descripcion":    clean_str(item.get("descripcion")),
            "cantidad":       item.get("cantidad"),
            "valor_unitario": item.get("valor_unitario"),
            "valor_total":    item.get("valor_total"),
        })
    return cleaned


# ---------------------------------------------------------------------------
# Prompt de extracción
# ---------------------------------------------------------------------------

PROMPT_SISTEMA = """Eres un experto en facturas electrónicas colombianas (DIAN).

Analiza el texto de la factura y extrae los siguientes campos.
Responde ÚNICAMENTE con un objeto JSON válido, sin explicaciones ni bloques de código.

Campos requeridos:
{
  "numero_factura":       string   — código de la factura (ej: "FE-0001234"),
  "proveedor_nombre":     string   — razón social del emisor,
  "proveedor_nit":        string   — NIT del emisor con dígito verificador (ej: "900123456-1"),
  "direccion_proveedor":  string   — dirección física del proveedor (null si no aparece),
  "telefono_proveedor":   string   — teléfono de contacto del proveedor (null si no aparece),
  "comprador_nombre":     string   — razón social del receptor,
  "comprador_nit":        string   — NIT o cédula del comprador,
  "fecha_emision":        string   — formato YYYY-MM-DD,
  "fecha_vencimiento":    string   — formato YYYY-MM-DD (null si no aparece),
  "forma_pago":           string   — ej: "Contado", "Crédito 30 días",
  "total_bruto":          number   — subtotal antes de retenciones (puede ser igual a subtotal),
  "subtotal":             number   — valor antes de IVA (sin puntos de miles ni comas),
  "porcentaje_iva":       number   — tasa aplicada ej: 19 (no 0.19),
  "valor_iva":            number   — monto del IVA,
  "retefuente_porcentaje": number  — porcentaje de retención en la fuente (null si no aplica),
  "retefuente_valor":     number   — valor retenido por retención en la fuente (null si no aplica),
  "reteica_porcentaje":   number   — porcentaje de ReteICA (null si no aplica),
  "reteica_valor":        number   — valor de ReteICA (null si no aplica),
  "reteiva_porcentaje":   number   — porcentaje de ReteIVA (null si no aplica),
  "reteiva_valor":        number   — valor de ReteIVA (null si no aplica),
  "total_a_pagar":        number   — total final después de retenciones,
  "es_autorretenedor":    boolean  — true si el proveedor es autorretenedor,
  "aplica_retefuente":    boolean  — true si se aplica retención en la fuente,
  "items": [
    {
      "descripcion":    string  — descripción limpia del producto o servicio (sin espacios ni comas al inicio),
      "cantidad":       number  — cantidad (ej: 2, 1.5),
      "valor_unitario": number  — precio unitario sin IVA,
      "valor_total":    number  — valor_unitario * cantidad (sin IVA)
    }
  ]
}

Reglas para los ítems:
- Extrae TODOS los ítems o líneas de detalle que aparezcan en la factura.
- Si la factura no tiene detalle de ítems, usa un único ítem con la descripción del proveedor y el subtotal.
- Las descripciones NO deben comenzar ni terminar con espacios, comas, puntos o guiones.
- Los valores numéricos deben ser números (no strings), sin separadores de miles.

Si un campo no está disponible en el documento, usa null.
"""


# ---------------------------------------------------------------------------
# Paso 1 — Leer el PDF
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto del PDF usando PyMuPDF."""
    doc = fitz.open(pdf_path)
    pages_text = []

    for num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            pages_text.append(f"--- Página {num} ---\n{text}")

    doc.close()

    if not pages_text:
        raise ValueError(
            "No se encontró texto en el PDF. "
            "El archivo puede ser una imagen escaneada sin OCR."
        )

    return "\n\n".join(pages_text)


# ---------------------------------------------------------------------------
# Paso 2 — Extraer datos con Claude
# ---------------------------------------------------------------------------

def extract_invoice_data(pdf_text: str) -> dict:
    """Envía el texto a la API de Claude y devuelve los datos como dict."""
    client = anthropic.Anthropic()  # Lee ANTHROPIC_API_KEY del entorno

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=PROMPT_SISTEMA,
        messages=[
            {
                "role": "user",
                "content": f"Texto de la factura:\n\n{pdf_text}"
            }
        ]
    )

    raw = message.content[0].text.strip()

    # Tolerancia: si Claude envuelve el JSON en ```json ... ```
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        raw = raw.rstrip("`").strip()

    data = json.loads(raw)

    # Limpiar descripciones basura en los ítems
    if "items" in data and isinstance(data["items"], list):
        data["items"] = clean_items(data["items"])

    return data


# ---------------------------------------------------------------------------
# Pipeline completo para un archivo
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: str) -> dict:
    """Lee el PDF, extrae los datos con Claude y añade metadatos."""
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo no es un PDF: {path.name}")

    print(f"  > Leyendo PDF...")
    text = extract_text_from_pdf(str(path))
    char_count = len(text)

    print(f"  > Consultando Claude ({char_count:,} caracteres extraidos)...")
    data = extract_invoice_data(text)

    # Metadatos de auditoría
    data["_archivo_fuente"] = path.name
    data["_procesado_en"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return data


# ---------------------------------------------------------------------------
# Paso 2b — Extraer datos con Claude Vision (imágenes)
# ---------------------------------------------------------------------------

def extract_invoice_image(image_path: str) -> dict:
    """Envía una imagen de factura a Claude Vision y devuelve los datos como dict."""
    path = Path(image_path)
    media_type = IMAGE_MEDIA_TYPES.get(path.suffix.lower(), "image/jpeg")

    with open(path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=PROMPT_SISTEMA,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": media_type,
                            "data":       image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Analiza esta imagen de factura y extrae todos los datos solicitados.",
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        raw = raw.rstrip("`").strip()

    data = json.loads(raw)

    if "items" in data and isinstance(data["items"], list):
        data["items"] = clean_items(data["items"])

    return data


def process_image(image_path: str) -> dict:
    """Extrae datos de una imagen de factura con Claude Vision y añade metadatos."""
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    if path.suffix.lower() not in IMAGE_MEDIA_TYPES:
        raise ValueError(
            f"Formato de imagen no soportado: {path.name}. "
            f"Usa: {', '.join(IMAGE_MEDIA_TYPES)}"
        )

    print(f"  > Procesando imagen con Claude Vision...")
    data = extract_invoice_image(str(path))

    data["_archivo_fuente"] = path.name
    data["_procesado_en"]   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return data


# ---------------------------------------------------------------------------
# Guardar en CSV
# ---------------------------------------------------------------------------

CAMPOS_CSV = [
    "numero_factura",
    "proveedor_nombre",
    "proveedor_nit",
    "direccion_proveedor",
    "telefono_proveedor",
    "comprador_nombre",
    "comprador_nit",
    "fecha_emision",
    "fecha_vencimiento",
    "forma_pago",
    "total_bruto",
    "subtotal",
    "porcentaje_iva",
    "valor_iva",
    "retefuente_porcentaje",
    "retefuente_valor",
    "reteica_porcentaje",
    "reteica_valor",
    "reteiva_porcentaje",
    "reteiva_valor",
    "total_a_pagar",
    "es_autorretenedor",
    "aplica_retefuente",
    "items",
    "_archivo_fuente",
    "_procesado_en",
]


def save_to_csv(records: list[dict], output_path: str) -> str:
    """
    Agrega los registros al CSV de salida.
    Si el archivo no existe lo crea con encabezados.
    Los ítems se serializan como JSON dentro de la celda.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()

    rows_to_write = []
    for record in records:
        row = dict(record)
        # Serializar ítems como JSON string para el CSV
        if "items" in row and isinstance(row["items"], list):
            row["items"] = json.dumps(row["items"], ensure_ascii=False)
        rows_to_write.append(row)

    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CAMPOS_CSV,
            extrasaction="ignore",   # ignora claves extra del dict
        )
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows_to_write)

    return str(path)
