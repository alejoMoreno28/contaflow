"""
yamaha_app.py — ContaFlow Yamaha
Genera archivos .PRN para Siigo desde facturas CPFE de Incolmotos.
"""

import base64
import io
import json
import os
import zipfile
from pathlib import Path

import unicodedata

import anthropic
import openpyxl
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _normalizar_ciudad(texto: str) -> str:
    """Normaliza nombre de ciudad: elimina tildes, mayúsculas, toma primera palabra."""
    return (
        unicodedata.normalize("NFD", texto)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .upper()
        .strip()
        .split()[0]
    )


def _calcular_cta_inv(codigo_producto: str) -> str:
    """
    Calcula cuenta contable desde código producto Siigo.
    Ejemplos confirmados:
    0020080000001 → 1435010280
    0020089001417 → 1435010289
    0020001000001 → 1435010201
    Regla: "14350102" + str(int(codigo[3:7])).zfill(2)
    """
    try:
        sufijo = str(int(codigo_producto[3:7])).zfill(2)
        return "14350102" + sufijo
    except Exception:
        return ""


def _guardar_referencia_en_sheets(referencia: str, producto: str,
                                   descripcion: str, cta_inv: str) -> bool:
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import json as _json
        from datetime import date

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SPREADSHEET_ID = "1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI"

        creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        if creds_json:
            creds_dict = _json.loads(creds_json)
            creds = Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES
            )
        else:
            creds = Credentials.from_service_account_file(
                "credentials.json", scopes=SCOPES
            )

        gc = gspread.authorize(creds)
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet("INVENARIOS")
        fecha = date.today().strftime("%Y-%m-%d")
        ws.append_row(
            ["", referencia, "'" + str(producto).strip(), descripcion, cta_inv, fecha, "", ""],
            value_input_option="USER_ENTERED"
        )
        return True
    except Exception as e:
        st.error(f"Error guardando en Google Sheets: {e}")
        return False


# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

EXCEL_PATH     = Path("CARGUE FACTURAS DE COMPRA F3 ACT.xlsm")
NIT_INCOLMOTOS = "890916911"
GSHEETS_URL    = "https://docs.google.com/spreadsheets/d/1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI/export?format=xlsx"

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ContaFlow Yamaha",
    page_icon="🏍️",
    layout="wide",
)

st.markdown("""
<style>
  /* Yamaha red accent */
  .stButton > button[kind="primary"] {
      background-color: #B71C1C !important;
      color: white !important;
      border: none !important;
  }
  .btn-green > button {
      background-color: #2E7D32 !important;
      color: white !important;
      border: none !important;
      width: 100% !important;
      font-size: 1.1rem !important;
      padding: 0.6rem !important;
  }
  .ref-row {
      background: #F5F5F5;
      border-radius: 6px;
      padding: 0.5rem;
      margin-bottom: 0.3rem;
  }
</style>
""", unsafe_allow_html=True)

# ─── VALIDACIÓN API KEY ────────────────────────────────────────────────────────

api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    st.error("⚠️ Error de configuración del sistema. Contacta al administrador.")
    st.stop()

# ─── PASO 1: CARGAR EXCEL AL INICIO ───────────────────────────────────────────

def _parse_wb(wb) -> tuple[dict, dict]:
    invenarios: dict[str, dict] = {}
    ws_inv = wb["INVENARIOS"]
    for row in ws_inv.iter_rows(min_row=3, values_only=True):
        ref = row[1]  # col B
        if ref is None or str(ref).strip() == "":
            continue
        producto = row[2]  # col C
        cta_inv  = row[4]  # col E
        invenarios[str(ref).strip()] = {
            "producto": str(producto).strip() if producto is not None else "",
            "cta_inv":  str(cta_inv).strip()  if cta_inv  is not None else "",
        }

    datos_tiendas: dict[str, dict] = {}
    ws_dat = wb["DATOS"]
    for row in ws_dat.iter_rows(min_row=2, values_only=True):
        tienda = row[1]  # col B
        if tienda is None or str(tienda).strip() == "":
            continue
        doc = row[2]  # col C → empresa (COD.COMP [1:4])
        cc  = row[3]  # col D → cc (C.COSTO [67:71])
        datos_tiendas[str(tienda).upper().strip()] = {
            "cc":  int(cc)  if cc  is not None else 0,
            "doc": int(doc) if doc is not None else 0,
        }

    return invenarios, datos_tiendas


def _cargar_con_gspread() -> tuple[dict, dict]:
    """Lee catálogo desde Google Sheets usando service account."""
    import gspread
    import json as _json
    from google.oauth2.service_account import Credentials

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SPREADSHEET_ID = "1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI"

    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        creds = Credentials.from_service_account_info(_json.loads(creds_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

    gc = gspread.authorize(creds)
    sp = gc.open_by_key(SPREADSHEET_ID)

    invenarios: dict[str, dict] = {}
    for row in sp.worksheet("INVENARIOS").get_all_values()[2:]:
        ref = row[1] if len(row) > 1 else ""
        if not ref or not str(ref).strip():
            continue
        producto = row[2] if len(row) > 2 else ""
        cta_inv  = row[4] if len(row) > 4 else ""
        invenarios[str(ref).strip()] = {
            "producto": str(producto).strip(),
            "cta_inv":  str(cta_inv).strip(),
        }

    datos_tiendas: dict[str, dict] = {}
    for row in sp.worksheet("DATOS").get_all_values()[1:]:
        tienda = row[1] if len(row) > 1 else ""
        if not tienda or not str(tienda).strip():
            continue
        try:
            doc = int(row[2]) if len(row) > 2 and row[2] else 0  # col C → empresa (COD.COMP [1:4])
        except Exception:
            doc = 0
        try:
            cc = int(row[3]) if len(row) > 3 and row[3] else 0   # col D → cc (C.COSTO [67:71])
        except Exception:
            cc = 0
        datos_tiendas[str(tienda).upper().strip()] = {"cc": cc, "doc": doc}

    return invenarios, datos_tiendas


def _cargar_con_fuente() -> tuple[dict, dict, str]:
    """Intenta Google Sheets primero; si falla, usa archivo local como fallback."""
    try:
        inv, tiendas = _cargar_con_gspread()
        return inv, tiendas, "gsheets"
    except Exception:
        pass

    st.warning(
        "⚠️ No se pudo conectar al catálogo en línea. Se está usando una copia local "
        "que puede estar desactualizada. Haz clic en 'Actualizar catálogo' para reintentar."
    )
    if not EXCEL_PATH.exists():
        return {}, {}, "error"
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, keep_vba=True)
    inv, tiendas = _parse_wb(wb)
    return inv, tiendas, "local"


if "invenarios" not in st.session_state:
    with st.spinner("Cargando referencias de inventarios..."):
        _inv, _tiendas, _fuente = _cargar_con_fuente()
    st.session_state["invenarios"]    = _inv
    st.session_state["datos_tiendas"] = _tiendas
    st.session_state["excel_fuente"]  = _fuente

invenarios    = st.session_state["invenarios"]
datos_tiendas = {_normalizar_ciudad(k): v for k, v in st.session_state["datos_tiendas"].items()}
_fuente       = st.session_state.get("excel_fuente", "local")

if not invenarios:
    st.error(
        "❌ No se pudo cargar el Excel desde OneDrive ni localmente. "
        "Agrega CARGUE FACTURAS DE COMPRA F3 ACT.xlsm a la raíz del proyecto."
    )
    st.stop()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏍️ ContaFlow Yamaha")
    st.divider()
    if _fuente == "gsheets":
        st.success(f"✅ Catálogo Google Sheets")
        st.caption(f"{len(invenarios):,} referencias cargadas")
    else:
        st.warning(f"⚠️ Base local (sin conexión)")
        st.caption(f"{len(invenarios):,} referencias")
    st.caption(f"{len(datos_tiendas)} tiendas configuradas")
    st.divider()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("⚠️ ANTHROPIC_API_KEY no configurada")
    else:
        st.success("✅ Sistema IA activo")

# ─── TÍTULO ───────────────────────────────────────────────────────────────────

st.title("ContaFlow Yamaha — Cargue Facturas CPFE")
st.caption("Genera archivos .PRN para Siigo desde facturas de Incolmotos")

col_refresh, col_spacer = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Actualizar catálogo", type="secondary"):
        for k in ["invenarios", "excel_fuente"]:
            st.session_state.pop(k, None)
        st.rerun()

# ─── PASO 2: SUBIR FACTURAS ───────────────────────────────────────────────────

st.markdown("### 📄 Cargar facturas CPFE")
st.caption("Sube uno o varios archivos PDF de facturas Incolmotos Yamaha (máx. 200 MB por archivo)")

uploaded_files = st.file_uploader(
    "Sube las facturas CPFE (PDF)",
    type=["pdf"],
    accept_multiple_files=True,
)

if "facturas_procesadas" not in st.session_state:
    st.session_state.facturas_procesadas = {}
if "procesando" not in st.session_state:
    st.session_state.procesando = False
def iniciar_proceso():
    st.session_state.procesando = True

if uploaded_files:
    # Avisar si alguna factura ya fue procesada en esta sesión
    ya_procesadas = [f.name for f in uploaded_files if f.name in st.session_state.facturas_procesadas]
    for nombre_ya in ya_procesadas:
        col_w, col_b = st.columns([4, 1])
        with col_w:
            st.warning(f"⚠️ **{nombre_ya}** ya fue procesada en esta sesión. ¿Deseas procesarla de nuevo?")
        with col_b:
            if st.button("Sí, reprocesar", key=f"reprocess_{nombre_ya}"):
                del st.session_state.facturas_procesadas[nombre_ya]
                st.rerun()

    st.button(
        "⚙️ Procesar facturas",
        type="primary",
        on_click=iniciar_proceso,
        disabled=st.session_state.procesando,
    )

if st.session_state.procesando and uploaded_files:
    facturas_extraidas = []

    with st.spinner("Procesando facturas, por favor espera..."):
        client = anthropic.Anthropic(api_key=api_key)

        def _extraer_iterativa(client, pdf_b64, nombre):
            """Extrae datos del PDF con llamadas iterativas de max 50 ítems cada una."""
            import re as _re

            _PROMPT_INICIAL = (
                "Eres un extractor de datos de facturas de Incolmotos Colombia.\n"
                "Extrae estos datos y responde SOLO con JSON válido, sin explicaciones ni markdown:\n"
                "{\n"
                "  \"header\": {\n"
                "    \"numero_factura\": \"CPFE-XXXXXX (número completo con prefijo)\",\n"
                "    \"fecha\": \"YYYY-MM-DD\",\n"
                "    \"ciudad\": \"solo la primera palabra del campo Ciudad del encabezado, "
                "ej: si dice NEIVA HUILA devuelve NEIVA\",\n"
                "    \"direccion_entrega\": \"dirección física del almacén destino tal como aparece en el PDF\",\n"
                "    \"subtotal\": 0.0,\n"
                "    \"iva_total\": 0.0,\n"
                "    \"fecha_vto\": \"YYYYMMDD — buscar primero 'HASTA EL DD-MM-YYYY' "
                "(convertir de DD-MM-YYYY a YYYYMMDD); si no existe usar campo Vencimiento del encabezado\"\n"
                "  },\n"
                "  \"items\": [\n"
                "    {\n"
                "      \"referencia\": \"exactamente como aparece en columna Referencia, sin espacios extra\",\n"
                "      \"descripcion\": \"columna Producto, máximo 50 caracteres\",\n"
                "      \"cantidad\": 1,\n"
                "      \"valor_total\": 0.0,  (columna 'Valor Total' del PDF, ya con descuento aplicado — NO precio unitario × cantidad)\n"
                "      \"tiene_iva\": true\n"
                "    }\n"
                "  ],\n"
                "  \"hay_mas_items\": false\n"
                "}\n\n"
                "INSTRUCCIONES:\n"
                "- Extrae los primeros 50 ítems de la factura.\n"
                "- Si la factura tiene más de 50 ítems, extrae solo los primeros 50 y pon hay_mas_items: true.\n"
                "- Si tiene 50 o menos ítems, extráelos todos y pon hay_mas_items: false.\n"
                "- NUNCA fusiones ni combines ítems con la misma referencia; "
                "cada fila del PDF es un objeto separado en el array.\n"
                "- REGLA ABSOLUTA: el array items debe tener exactamente un objeto "
                "por cada número de ítem visible en el PDF."
            )

            def _pdf_content(pdf_b64):
                return {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_b64,
                    },
                }

            def _llamar_haiku(client, pdf_b64, prompt_text):
                return client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=8192,
                    messages=[{
                        "role": "user",
                        "content": [_pdf_content(pdf_b64), {"type": "text", "text": prompt_text}],
                    }],
                )

            def _limpiar_json(raw):
                raw = _re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
                return _re.sub(r"\n?```\s*$", "", raw).strip()

            # ── Llamada 1: header + primeros 50 ítems ──────────────────────
            msg1 = _llamar_haiku(client, pdf_b64, _PROMPT_INICIAL)
            raw1 = _limpiar_json(msg1.content[0].text)
            try:
                chunk1 = json.loads(raw1)
            except json.JSONDecodeError:
                st.error(f"Error procesando página 1 de {nombre}. Reintenta.")
                return None

            header       = chunk1.get("header", {})
            todos_items  = list(chunk1.get("items", []))
            hay_mas      = chunk1.get("hay_mas_items", False)

            # ── Llamadas siguientes: 50 ítems por vez ──────────────────────
            iteracion = 1
            while hay_mas and iteracion < 10:
                iteracion += 1
                ultimos_3  = todos_items[-3:] if len(todos_items) >= 3 else todos_items
                ultima_ref = ultimos_3[-1].get("referencia", "") if ultimos_3 else ""

                prompt_cont = (
                    "Esta es la misma factura. Ya extraje algunos ítems. Los últimos 3 que tengo son:\n"
                    + json.dumps(ultimos_3, ensure_ascii=False, indent=2)
                    + f"\n\nExtrae los siguientes 50 ítems que aparecen DESPUÉS de la "
                    f"referencia \"{ultima_ref}\" en el PDF.\n"
                    "Responde SOLO con JSON válido, sin explicaciones ni markdown:\n"
                    "{\n"
                    "  \"items\": [...],\n"
                    "  \"hay_mas_items\": false\n"
                    "}\n\n"
                    "Si hay más ítems después de los 50 que extraigas, pon hay_mas_items: true.\n"
                    "Si no hay más ítems, pon hay_mas_items: false.\n"
                    "NUNCA fusiones ni combines ítems con la misma referencia; "
                    "cada fila del PDF es un objeto separado."
                )

                msg_n = _llamar_haiku(client, pdf_b64, prompt_cont)
                raw_n = _limpiar_json(msg_n.content[0].text)
                try:
                    chunk_n = json.loads(raw_n)
                except json.JSONDecodeError:
                    st.error(f"Error procesando página {iteracion} de {nombre}. Reintenta.")
                    return None

                nuevos     = chunk_n.get("items", [])
                todos_items.extend(nuevos)
                hay_mas    = chunk_n.get("hay_mas_items", False)

            if hay_mas:
                st.warning(
                    f"⚠️ **{nombre}**: Factura muy grande — se procesaron {len(todos_items)} ítems. "
                    "Verifica que el total cuadre antes de subir a Siigo."
                )

            return {
                "numero_factura":    header.get("numero_factura", ""),
                "fecha":             header.get("fecha", ""),
                "ciudad":            header.get("ciudad", ""),
                "direccion_entrega": header.get("direccion_entrega", ""),
                "subtotal":          header.get("subtotal", 0.0),
                "iva_total":         header.get("iva_total", 0.0),
                "fecha_vto":         header.get("fecha_vto", ""),
                "items":             todos_items,
            }

        bar     = st.progress(0)
        status  = st.empty()
        total   = len(uploaded_files)

        for idx, archivo in enumerate(uploaded_files, 1):
            status.markdown(f"🧠 Procesando **{idx}/{total}**: `{archivo.name}`...")

            # Cache: si ya fue procesada en esta sesión, reusar resultado
            if archivo.name in st.session_state.facturas_procesadas:
                facturas_extraidas.append(st.session_state.facturas_procesadas[archivo.name])
                bar.progress(idx / total)
                continue

            try:
                pdf_bytes = archivo.read()
                pdf_b64   = base64.standard_b64encode(pdf_bytes).decode("utf-8")

                datos = _extraer_iterativa(client, pdf_b64, archivo.name)
                if datos is None:
                    bar.progress(idx / total)
                    continue

                import re
                pdf_snippet = ""

                # Validación 1: conteo total de ítems vs estimado del PDF
                n_extraidos = len(datos.get("items", []))
                n_en_pdf = 0
                try:
                    pdf_snippet = pdf_bytes.decode("latin-1", errors="ignore")
                    posibles = [
                        int(m) for m in re.findall(r"(?m)^\s*([1-9][0-9]{0,2})\s+[A-Z]", pdf_snippet)
                        if int(m) <= 500
                    ]
                    if posibles:
                        n_en_pdf = max(posibles)
                except Exception:
                    pass
                if n_en_pdf > 0 and n_extraidos < n_en_pdf:
                    st.warning(
                        f"⚠️ Advertencia: El PDF tiene aproximadamente {n_en_pdf} ítems pero solo "
                        f"se extrajeron {n_extraidos}. El PRN puede estar incompleto. Verifica el "
                        f"archivo antes de subirlo a Siigo."
                    )

                # Validación 2: detectar referencias deduplicadas en el JSON extraído
                try:
                    from collections import Counter
                    refs_extraidas = Counter(
                        str(it.get("referencia", "")).strip()
                        for it in datos.get("items", [])
                    )
                    refs_duplicadas_omitidas = []
                    for ref, cnt in refs_extraidas.items():
                        if ref and len(ref) >= 4:
                            cnt_pdf = pdf_snippet.count(ref)
                            if cnt_pdf > cnt:
                                refs_duplicadas_omitidas.append(
                                    f"'{ref}' (en JSON: {cnt}×, en PDF: ~{cnt_pdf} menciones)"
                                )
                    if refs_duplicadas_omitidas:
                        st.warning(
                            f"⚠️ **{archivo.name}**: Posibles referencias deduplicadas — "
                            "la IA puede haber fusionado ítems repetidos: "
                            + ", ".join(refs_duplicadas_omitidas)
                            + ". Verifica el PRN antes de subir a Siigo."
                        )
                except Exception:
                    pass

                datos["_nombre_archivo"] = archivo.name
                st.session_state.facturas_procesadas[archivo.name] = datos
                facturas_extraidas.append(datos)

            except Exception as e:
                st.error(f"Error procesando {archivo.name}: {e}")

            bar.progress(idx / total)

        status.empty()
        bar.empty()

    st.session_state["facturas_extraidas"] = facturas_extraidas
    st.session_state.procesando = False
    st.success(f"✅ {len(facturas_extraidas)} factura(s) procesada(s)")

# ─── PASO 3: VALIDACIÓN ───────────────────────────────────────────────────────

facturas = st.session_state.get("facturas_extraidas", [])

if not facturas:
    st.stop()

st.divider()
st.subheader("📋 Validación de referencias")

refs_faltantes = []
for fac in facturas:
    for item in fac.get("items", []):
        ref = str(item.get("referencia", "")).strip()
        if ref not in invenarios:
            refs_faltantes.append({
                "Factura":     fac.get("numero_factura", "?"),
                "Referencia":  ref,
                "Descripción": item.get("descripcion", ""),
            })

if refs_faltantes:
    import pandas as pd
    # Deduplicar por referencia (primera descripción encontrada)
    refs_unicas: dict[str, str] = {}
    for r in refs_faltantes:
        if r["Referencia"] not in refs_unicas:
            refs_unicas[r["Referencia"]] = r.get("Descripción", "")

    n = len(refs_unicas)
    st.warning(
        f"📋 Se encontraron {n} referencia(s) nueva(s). "
        "Ingresa el código Siigo para cada una y guarda."
    )
    st.dataframe(
        pd.DataFrame(refs_faltantes),
        use_container_width=True,
        hide_index=True,
    )

    codigos_ingresados = {}
    for ref, desc in refs_unicas.items():
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.markdown(f"**{ref}**  \n{desc}")
        with col2:
            codigo = st.text_input(
                "Código producto Siigo",
                key=f"cod_{ref}",
                placeholder="Ej: 0020089001417"
            )
        with col3:
            if codigo:
                cta = _calcular_cta_inv(codigo)
                st.markdown(f"**CTA-INV calculada:**  \n`{cta}`")
                codigos_ingresados[ref] = {
                    "producto":    codigo,
                    "descripcion": desc,
                    "cta_inv":     cta,
                }
            else:
                st.markdown("*Ingresa el código para ver la cuenta*")

    todos_completos = len(codigos_ingresados) == len(refs_unicas)

    if todos_completos:
        if st.button("✅ Guardar en Google Sheets y continuar", use_container_width=True, type="primary"):
            exitos = 0
            for ref, datos in codigos_ingresados.items():
                if _guardar_referencia_en_sheets(
                    ref,
                    datos["producto"],
                    datos["descripcion"],
                    datos["cta_inv"],
                ):
                    exitos += 1
            if exitos == len(codigos_ingresados):
                st.success(
                    f"✅ {exitos} referencias guardadas correctamente."
                )
                for k in ["invenarios", "excel_fuente"]:
                    st.session_state.pop(k, None)
                st.rerun()
            else:
                st.error(
                    "No se pudo guardar. Intenta de nuevo o contacta al administrador."
                )
    else:
        faltantes_count = len(refs_unicas) - len(codigos_ingresados)
        st.warning(f"Faltan {faltantes_count} código(s) por ingresar.")

    st.stop()

# ── Todas las referencias existen — mostrar resumen por factura ────────────────

import pandas as pd

for fac in facturas:
    num = fac.get("numero_factura", "?")
    subtotal  = float(fac.get("subtotal",  0))
    iva_total = float(fac.get("iva_total", 0))
    total_fac = subtotal + iva_total

    with st.expander(f"📄 {num}", expanded=True):
        filas = []
        for item in fac.get("items", []):
            ref  = str(item.get("referencia", "")).strip()
            look = invenarios.get(ref, {})
            filas.append({
                "Referencia":  ref,
                "Descripción": item.get("descripcion", ""),
                "Cuenta":      look.get("cta_inv", "—"),
                "Cantidad":    item.get("cantidad", 0),
                "Valor Total": item.get("valor_total", 0),
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Subtotal",  f"${subtotal:,.0f}")
        m2.metric("IVA",       f"${iva_total:,.0f}")
        m3.metric("TOTAL",     f"${total_fac:,.0f}")

# ── Validar códigos producto duplicados dentro de cada factura ────────────────

prods_duplicados = []
for fac in facturas:
    vistos: dict[str, str] = {}  # producto -> primera referencia que lo usó
    for item in fac.get("items", []):
        ref  = str(item.get("referencia", "")).strip()
        prod = invenarios.get(ref, {}).get("producto", "")
        if not prod:
            continue
        if prod in vistos and vistos[prod] != ref:
            prods_duplicados.append({
                "Factura":          fac.get("numero_factura", "?"),
                "Referencia":       ref,
                "Descripción":      item.get("descripcion", ""),
                "Código Producto":  prod,
                "Conflicto con":    vistos[prod],
            })
        else:
            vistos[prod] = ref

if prods_duplicados:
    st.error(
        "⛔ Error: referencias con código contable duplicado. "
        "Verificar en Siigo antes de continuar."
    )
    st.dataframe(
        pd.DataFrame(prods_duplicados),
        use_container_width=True,
        hide_index=True,
    )
    st.stop()

# ─── PASO 4 + 5: GENERACIÓN Y DESCARGA PRN ───────────────────────────────────

# Nota: BELALCÁZAR normaliza a BELALCAZAR (NFD + ascii ignore), no duplicar.
_IBAGUE_PRINCIPAL_KEYWORDS = [
    "CARRERA 5", "CRA 5", "CRR 5", "CR 5", "QUINTA", "20-39", "20 39",
    "CARRERA QUINTA", "PRINCIPAL", "B 1 CARMEN",
]
_IBAGUE_SEXTA_KEYWORDS = [
    "CARRERA 6", "CRA 6", "CRR 6", "CR 6", "BELALCAZAR",
    "BRR BELALCAZAR", "SEXTA", "CARRERA SEXTA", "25-40", "25 40",
]


def _resolver_tienda_ibague(direccion: str) -> tuple:
    """
    Retorna (cc, doc) según la dirección de entrega para las dos tiendas de Ibagué.
    Principal (Cra 5 / B1 Carmen): cc=14, doc=7  → empresa 007, CC 0014
    Sexta     (Cra 6 / Belalcázar): cc=1,  doc=1  → empresa 001, CC 0001
    Retorna (None, None) si no se puede determinar.
    Evaluación: Principal primero, Sexta segundo, fallback a Sexta con warning.
    """
    dir_norm = (
        unicodedata.normalize("NFD", str(direccion))
        .encode("ascii", "ignore")
        .decode("utf-8")
        .upper()
    )
    for kw in _IBAGUE_PRINCIPAL_KEYWORDS:
        if kw in dir_norm:
            return 14, 7
    for kw in _IBAGUE_SEXTA_KEYWORDS:
        if kw in dir_norm:
            return 1, 1
    return None, None


def generar_prn_lines(
    factura_data: dict,
    inv: dict,
    tiendas: dict,
) -> list[str]:
    ciudad = _normalizar_ciudad(factura_data["ciudad"])

    if "IBAGU" in ciudad:
        direccion = str(factura_data.get("direccion_entrega", ""))
        cc, doc = _resolver_tienda_ibague(direccion)
        if cc is None:
            st.warning(
                f"⚠️ No se pudo determinar la tienda de Ibagué automáticamente. "
                f"Dirección detectada: {direccion or '(vacía)'}. "
                "Por favor verifica el PRN antes de subir a Siigo."
            )
            cc, doc = 1, 1  # Fallback: Sexta (empresa 001, CC 0001)
    elif ciudad not in tiendas:
        raise ValueError(
            f"Ciudad '{ciudad}' no encontrada en Excel DATOS. "
            f"Ciudades disponibles: {list(tiendas.keys())}"
        )
    else:
        cc  = tiendas[ciudad]["cc"]
        doc = tiendas[ciudad]["doc"]

    num_doc = (
        factura_data["numero_factura"]
        .replace("CPFE-", "")
        .replace("CPFE",  "")
        .strip()
    )
    fecha     = factura_data["fecha"].replace("-", "")      # YYYYMMDD
    _fvto     = str(factura_data.get("fecha_vto", "")).strip()
    fecha_vto = _fvto if (_fvto.isdigit() and len(_fvto) == 8) else "00000000"

    def fmt_line(
        sec: int,
        cuenta: str,
        producto: str,
        descripcion: str,
        deb_cred: str,
        valor: float,
        cantidad: float,
    ) -> str:
        descripcion = str(descripcion).encode("latin-1", errors="replace").decode("latin-1")
        line = (
            "P"                                          # TIPO           1
            + str(doc).zfill(3)                          # COD.COMP       3
            + num_doc.zfill(11)                          # NUM.DOC       11
            + str(sec).zfill(5)                          # SEC            5
            + NIT_INCOLMOTOS.zfill(13)                   # NIT           13
            + "000"                                      # SUCURSAL       3
            + str(cuenta).ljust(10)[:10]                 # CUENTA        10
            + str(producto).ljust(13)[:13]               # PRODUCTO      13
            + fecha                                      # FECHA DOC      8
            + str(cc).zfill(4)                           # C.COSTO        4
            + "000"                                      # S.COSTO        3
            + str(descripcion).ljust(50)[:50]            # DESCRIPCION   50
            + deb_cred                                   # DEB.CRED       1
            + str(int(round(valor * 100))).zfill(15)     # VR.MOVIM      15
            + "000000000000000"                          # BASE RET      15
            + "0000"                                     # COD.VEND       4
            + "0000"                                     # COD.CIUDAD     4
            + "000"                                      # COD.ZONA       3
            + str(cc).zfill(4)                           # COD.BODEGA     4
            + "000"                                      # COD.UB         3
            + str(int(round(cantidad * 100000))).zfill(15)  # CANTIDAD   15
            + " "                                        # TIPO D.CRUCE   1
            + "000"                                      # COD.D.CRUCE    3
            + "00000000000"                              # NUM.D.CRUCE   11
            + "000"                                      # SEC.DOC.CRUCE  3
            + "00000000"                                 # FECHA VENC     8
            + "0000"                                     # COD.FORMA PAGO 4
            + "00"                                       # COD.BANCO      2
        )
        if len(line) != 220:
            raise ValueError(f"Error interno generando PRN: línea tiene {len(line)} caracteres (esperado 220). Contacta al administrador.")
        return line

    lines: list[str] = []
    sec = 1

    # Líneas D — ítems de inventario
    for item in factura_data.get("items", []):
        ref  = str(item["referencia"]).strip()
        look = inv[ref]
        if not look.get("cta_inv", "").strip():
            raise ValueError(f"La referencia '{ref}' no tiene cuenta contable en el catálogo. Verifica el Excel.")
        lines.append(fmt_line(
            sec         = sec,
            cuenta      = look["cta_inv"],
            producto    = look["producto"],
            descripcion = item.get("descripcion", ""),
            deb_cred    = "D",
            valor       = float(item.get("valor_total", 0)),
            cantidad    = float(item.get("cantidad", 1)),
        ))
        sec += 1

    # Línea C — CXP proveedor (campos de cruce y vencimiento específicos)
    total_fac = float(factura_data.get("subtotal", 0)) + float(factura_data.get("iva_total", 0))
    cxp_line = (
        "P"                                              # TIPO           1
        + str(doc).zfill(3)                              # COD.COMP       3
        + num_doc.zfill(11)                              # NUM.DOC       11
        + str(sec).zfill(5)                              # SEC            5
        + NIT_INCOLMOTOS.zfill(13)                       # NIT           13
        + "000"                                          # SUCURSAL       3
        + "2205010000"                                   # CUENTA        10
        + "0000000000000"                                # PRODUCTO      13
        + fecha                                          # FECHA DOC      8
        + str(cc).zfill(4)                               # C.COSTO        4
        + "000"                                          # S.COSTO        3
        + "INCOLMOTOS SAS".ljust(50)[:50]                # DESCRIPCION   50
        + "C"                                            # DEB.CRED       1
        + str(int(round(total_fac * 100))).zfill(15)     # VR.MOVIM      15
        + "000000000000000"                              # BASE RET      15
        + "0000"                                         # COD.VEND       4
        + "0000"                                         # COD.CIUDAD     4
        + "000"                                          # COD.ZONA       3
        + str(cc).zfill(4)                               # COD.BODEGA     4
        + "000"                                          # COD.UB         3
        + "000000000000000"                              # CANTIDAD      15
        + "P"                                            # TIPO D.CRUCE   1
        + str(doc).zfill(3)                              # COD.D.CRUCE    3
        + num_doc.zfill(11)                              # NUM.D.CRUCE   11
        + "001"                                          # SEC.DOC.CRUCE  3
        + fecha_vto                                      # FECHA VENC     8
        + "0000"                                         # COD.FORMA PAGO 4
        + "00"                                           # COD.BANCO      2
    )
    if len(cxp_line) != 220:
        raise ValueError(f"Error interno generando PRN: línea tiene {len(cxp_line)} caracteres (esperado 220). Contacta al administrador.")
    lines.append(cxp_line)
    sec += 1

    # Línea D — IVA descontable (si aplica)
    iva = float(factura_data.get("iva_total", 0))
    if iva > 0:
        lines.append(fmt_line(
            sec         = sec,
            cuenta      = "2408020100",
            producto    = "0000000000000",
            descripcion = "INCOLMOTOS SAS",
            deb_cred    = "D",
            valor       = iva,
            cantidad    = 1,
        ))

    return lines


st.markdown("---")
st.markdown("### ⬇️ Descargar archivos PRN")

if st.button("✅ Generar archivos PRN", type="primary", use_container_width=True):
    archivos_prn: list[tuple[str, bytes]] = []
    error_generacion = False

    for fac in facturas:
        num = (
            fac.get("numero_factura", "0")
            .replace("CPFE-", "")
            .replace("CPFE",  "")
            .strip()
        )
        nombre = f"INT{num}.prn"

        try:
            lines   = generar_prn_lines(fac, invenarios, datos_tiendas)
            content = "\r\n".join(lines) + "\r\n"
            archivos_prn.append((nombre, content.encode("latin-1", errors="replace")))
        except ValueError as e:
            st.error(str(e))
            error_generacion = True
            break
        except Exception as e:
            st.error(f"Error generando {nombre}: {e}")
            error_generacion = True
            break

    if not error_generacion and archivos_prn:
        if len(archivos_prn) == 1:
            nombre, datos_prn = archivos_prn[0]
            st.download_button(
                label              = f"⬇️ Descargar {nombre}",
                data               = datos_prn,
                file_name          = nombre,
                mime               = "application/octet-stream",
                use_container_width=True,
            )
        else:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for nombre, datos_prn in archivos_prn:
                    zf.writestr(nombre, datos_prn)
            zip_buf.seek(0)
            st.download_button(
                label              = "⬇️ Descargar CPFE_facturas.zip",
                data               = zip_buf,
                file_name          = "CPFE_facturas.zip",
                mime               = "application/zip",
                use_container_width=True,
            )

        # ── Tabla de verificación ──────────────────────────────────────────
        st.subheader("✅ Verifica estos totales contra las facturas físicas")
        verificacion = []
        for fac in facturas:
            subtotal  = float(fac.get("subtotal",  0))
            iva_total = float(fac.get("iva_total", 0))
            verificacion.append({
                "Factura":  fac.get("numero_factura", "?"),
                "N° ítems": len(fac.get("items", [])),
                "Subtotal": f"${subtotal:,.0f}",
                "IVA":      f"${iva_total:,.0f}",
                "TOTAL":    f"${subtotal + iva_total:,.0f}",
            })
        st.dataframe(
            pd.DataFrame(verificacion),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "El TOTAL debe coincidir exactamente con el TOTAL A PAGAR "
            "de cada factura PDF"
        )
