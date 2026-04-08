from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import base64
import json
import os
import unicodedata
from pathlib import Path
import zipfile
import io
import re
import anthropic
import openpyxl
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ContaFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_PATH = Path(__file__).parent.parent / "CARGUE FACTURAS DE COMPRA F3 ACT.xlsm"
NIT_INCOLMOTOS = "890916911"

# --- Globals caching ---
CACHE_INVENARIOS = {}
CACHE_TIENDAS = {}

# --- Funciones Utilitarias (Migradas de Streamlit) ---

def _resolver_tienda_ibague(direccion: str):
    d = unicodedata.normalize('NFD', str(direccion)).encode('ascii','ignore').decode().upper()
    PRINCIPAL_KW = ['CR 5','CRR 5','CARRERA 5','CRA 5','QUINTA','20 39','20-39','B 1 CARMEN','PRINCIPAL']
    SEXTA_KW    = ['CR 6','CRR 6','CARRERA 6','CRA 6','BELALCAZAR','BRR BELALCAZAR','SEXTA','25 40','25-40']
    
    for kw in PRINCIPAL_KW:
        if kw in d:
            return 7, 14
    for kw in SEXTA_KW:
        if kw in d:
            return 1, 1
    return 1, 1

def _normalizar_ciudad(texto: str) -> str:
    return (
        unicodedata.normalize("NFD", texto)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .upper()
        .strip()
        .split()[0]
    )

def _calcular_cta_inv(codigo_producto: str) -> str:
    try:
        sufijo = str(int(codigo_producto[3:7])).zfill(2)
        return "14350102" + sufijo
    except Exception:
        return ""

def _cargar_con_gspread():
    import gspread
    from google.oauth2.service_account import Credentials
    
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SPREADSHEET_ID = "1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI"

    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(Path(__file__).parent.parent / "credentials.json", scopes=SCOPES)

    gc = gspread.authorize(creds)
    sp = gc.open_by_key(SPREADSHEET_ID)

    inv, dt = {}, {}
    for row in sp.worksheet("INVENARIOS").get_all_values()[2:]:
        ref = row[1] if len(row) > 1 else ""
        if not ref or not str(ref).strip(): continue
        inv[str(ref).strip()] = {
            "producto": str(row[2]).strip() if len(row) > 2 else "",
            "cta_inv":  str(row[4]).strip() if len(row) > 4 else "",
        }

    for row in sp.worksheet("DATOS").get_all_values()[1:]:
        tienda = row[1] if len(row) > 1 else ""
        if not tienda or not str(tienda).strip(): continue
        try: cc = int(row[2]) if len(row) > 2 and row[2] else 0
        except Exception: cc = 0
        try: doc = int(row[3]) if len(row) > 3 and row[3] else 0
        except Exception: doc = 0
        dt[str(tienda).upper().strip()] = {"cc": cc, "doc": doc}

    return inv, dt

def _parse_wb(wb):
    inv, dt = {}, {}
    for row in wb["INVENARIOS"].iter_rows(min_row=3, values_only=True):
        if row[1] and str(row[1]).strip():
            inv[str(row[1]).strip()] = {
                "producto": str(row[2]).strip() if row[2] else "",
                "cta_inv":  str(row[4]).strip() if row[4] else "",
            }
    for row in wb["DATOS"].iter_rows(min_row=2, values_only=True):
        if row[1] and str(row[1]).strip():
            dt[str(row[1]).upper().strip()] = {
                "cc": int(row[2]) if row[2] else 0,
                "doc": int(row[3]) if row[3] else 0,
            }
    return inv, dt

def get_catalogo():
    global CACHE_INVENARIOS, CACHE_TIENDAS
    if not CACHE_INVENARIOS:
        try:
            inv, tiendas = _cargar_con_gspread()
            CACHE_INVENARIOS, CACHE_TIENDAS = inv, tiendas
        except Exception as e:
            print("Fallo GSheets, intentando local", e)
            if EXCEL_PATH.exists():
                wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, keep_vba=True)
                inv, tiendas = _parse_wb(wb)
                CACHE_INVENARIOS, CACHE_TIENDAS = inv, tiendas
    
    return CACHE_INVENARIOS, {_normalizar_ciudad(k): v for k, v in CACHE_TIENDAS.items()}


def _extraer_iterativa(client, pdf_b64, base_prompt):
    todos_items = []
    header = None
    iteracion = 0
    hay_mas = True
    
    while hay_mas and iteracion < 10:
        iteracion += 1
        if iteracion == 1:
            prompt = f"{base_prompt}\n\nMUESTRA LOS PRIMEROS 50 ÍTEMS. Si hay más de 50 ítems, marca 'hay_mas_items: true'."
        else:
            ultimos = todos_items[-3:] if len(todos_items) >= 3 else todos_items
            ultimos_str = json.dumps(ultimos, ensure_ascii=False)
            ultima_ref = todos_items[-1].get('referencia', '') if todos_items else ''
            prompt = f"Extrae SOLO el JSON válido. Misma factura. Los últimos 3 fueron: {ultimos_str}. Extrae los siguientes 50 ítems después de \"{ultima_ref}\". Si terminaste envía los ítems y pon \"hay_mas_items\": false. Si siguen más pon true."
            
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=8192,
                messages=[
                    {"role": "user", "content": [
                        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                        {"type": "text", "text": prompt}
                    ]},
                    {"role": "assistant", "content": "{"}
                ]
            )
            raw = "{" + resp.content[0].text
            raw = raw.strip()
            if raw.endswith("```"): raw = raw[:-3].strip()
            data = json.loads(raw)
        except Exception as e:
            print("Error parsing AI JSON", e)
            return None
        
        if iteracion == 1:
            header = {
                "numero_factura": data.get("numero_factura", ""),
                "fecha": data.get("fecha", ""),
                "ciudad": data.get("ciudad", ""),
                "direccion_entrega": data.get("direccion_entrega", ""),
                "subtotal": data.get("subtotal", 0.0),
                "iva_total": data.get("iva_total", 0.0),
                "fecha_vto": data.get("fecha_vto", "")
            }
        
        todos_items.extend(data.get('items', []))
        hay_mas = data.get('hay_mas_items', False)
        
    return {"header": header or {}, "items": todos_items}

# --- ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/extract")
async def extract_invoice(file: UploadFile = File(...)):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key de Anthropic no configurada")
    
    client = anthropic.Anthropic(api_key=api_key)
    inv, tiendas = get_catalogo()
    
    pdf_bytes = await file.read()
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    
    prompt = (
        "<instructions>\n"
        "Eres un extractor experto de datos de facturas de Incolmotos Colombia.\n"
        "Tu única tarea es extraer datos del documento PDF adjunto y estructurarlos exactamente bajo el esquema JSON proveido.\n"
        "</instructions>\n\n"
        "<anti_hallucination_rules>\n"
        "1. Extrae ÚNICAMENTE información que esté literalmente presente en el documento.\n"
        "2. No infieras, no 'limpies', ni inventes ceros ni caracteres extra. Transcribe el texto EXACTAMENTE como se ve.\n"
        "3. Las referencias de Yamaha generalmente tienen 10 o 12 caracteres. Extráelas literal, sin rellenar con ceros fantasmas.\n"
        "4. La factura puede tener múltiples páginas. Extrae ABSOLUTAMENTE TODOS los ítems de TODAS las páginas.\n"
        "5. Crea exactamente un objeto por cada número de ítem visible en el PDF. NUNCA fusiones ítems similares o repetidos.\n"
        "</anti_hallucination_rules>\n\n"
        "<schema_json>\n"
        "Debes responder SOLO y EXCLUSIVAMENTE emitiendo código JSON puramente válido, sin formato markdown, sin intro ni outro.\n"
        "{\n"
        "  \"numero_factura\": \"CPFE-XXXXXX\",\n"
        "  \"fecha\": \"YYYY-MM-DD\",\n"
        "  \"ciudad\": \"solo la primera palabra del campo Ciudad del encabezado\",\n"
        "  \"direccion_entrega\": \"dirección de envío o sucursal destino\",\n"
        "  \"subtotal\": 0.0,\n"
        "  \"iva_total\": 0.0,\n"
        "  \"fecha_vto\": \"YYYYMMDD\",\n"
        "  \"items\": [\n"
        "    {\n"
        "      \"referencia\": \"literal de la columna Referencia\",\n"
        "      \"descripcion\": \"columna Producto\",\n"
        "      \"cantidad\": 1,\n"
        "      \"valor_total\": 0.0,\n"
        "      \"tiene_iva\": true\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "</schema_json>"
    )
    
    extracted = _extraer_iterativa(client, pdf_b64, prompt)
    if not extracted:
        raise HTTPException(status_code=500, detail="Fallo al extraer JSON de la IA")
        
    datos = extracted["header"]
    datos["items"] = extracted["items"]
    
    missing_refs = []
    
    for item in datos.get("items", []):
        ref = str(item.get("referencia", "")).strip()
        # Autocorrección de ceros fantasmas
        if ref and ref not in inv:
            if ref.endswith("00") and ref[:-2] in inv:
                ref = ref[:-2]
                item["referencia"] = ref
            elif ref.endswith("0") and ref[:-1] in inv:
                ref = ref[:-1]
                item["referencia"] = ref
            elif (ref + "0") in inv:
                ref = ref + "0"
                item["referencia"] = ref
            elif (ref + "00") in inv:
                ref = ref + "00"
                item["referencia"] = ref
                
        if ref not in inv:
            missing_refs.append({
                "referencia": ref,
                "descripcion": item.get("descripcion", ""),
            })

    # Extraer items duplicados en la factura como en streamlit
    prods_duplicados = []
    vistos = {}
    for item in datos.get("items", []):
        ref = str(item.get("referencia", "")).strip()
        prod = inv.get(ref, {}).get("producto", "")
        if not prod: continue
        if prod in vistos and vistos[prod] != ref:
            prods_duplicados.append({
                "referencia": ref,
                "descripcion": item.get("descripcion", ""),
                "codigo_producto": prod,
            })
        else:
            vistos[prod] = ref

    return {
        "status": "success",
        "factura": datos,
        "missing_refs": missing_refs,
        "duplicados": prods_duplicados
    }

class RefData(BaseModel):
    referencia: str
    producto: str
    descripcion: str
    cta_inv: str

@app.post("/api/add-reference")
def add_reference(refs: List[RefData]):
    import gspread
    from google.oauth2.service_account import Credentials
    from datetime import date
    
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SPREADSHEET_ID = "1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI"
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(Path(__file__).parent.parent / "credentials.json", scopes=SCOPES)

    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SPREADSHEET_ID).worksheet("INVENARIOS")
    fecha = date.today().strftime("%Y-%m-%d")
    
    global CACHE_INVENARIOS
    
    for r in refs:
        ws.append_row(["", r.referencia, f"'{r.producto.strip()}", r.descripcion, r.cta_inv, fecha, "", ""], value_input_option="USER_ENTERED")
        CACHE_INVENARIOS[r.referencia] = {
            "producto": r.producto.strip(),
            "cta_inv": r.cta_inv.strip()
        }
        
    return {"status": "success"}

class FacturaRequest(BaseModel):
    facturas: List[Dict[str, Any]]

@app.post("/api/generate-prn")
def generate_prn(data: FacturaRequest):
    inv, tiendas = get_catalogo()
    archivos_prn = []
    
    for fac in data.facturas:
        ciudad = _normalizar_ciudad(fac.get("ciudad", ""))
        if "IBAGU" in ciudad:
            cc, doc = _resolver_tienda_ibague(fac.get("direccion_entrega", ""))
        else:
            if ciudad not in tiendas:
                raise HTTPException(status_code=400, detail=f"Ciudad '{ciudad}' no registrada.")
            cc = tiendas[ciudad]["cc"]
            doc = tiendas[ciudad]["doc"]
            
        num_doc = fac.get("numero_factura", "").replace("CPFE-", "").replace("CPFE",  "").strip()
        fecha = fac.get("fecha", "").replace("-", "")
        _fvto = str(fac.get("fecha_vto", "")).strip()
        fecha_vto = _fvto if (_fvto.isdigit() and len(_fvto) == 8) else "00000000"

        lines = []
        sec = 1
        
        def fmt_line(s, cuenta, prd, desc, d_c, val, cant):
            desc_lin = unicodedata.normalize('NFKD', str(desc)).encode('ascii', 'ignore').decode('utf-8').upper()
            line = (
                "P" + str(doc).zfill(3) + num_doc.zfill(11) + str(s).zfill(5) + 
                NIT_INCOLMOTOS.zfill(13) + "000" + str(cuenta).ljust(10)[:10] + 
                str(prd).ljust(13)[:13] + fecha + str(cc).zfill(4) + "000" + 
                str(desc_lin).ljust(50)[:50] + d_c + str(int(round(float(val) * 100))).zfill(15) + 
                "000000000000000" + "0000" + "0000" + "000" + str(cc).zfill(4) + 
                "000" + str(int(round(float(cant) * 100000))).zfill(15) + " " + 
                "000" + "00000000000" + "000" + "00000000" + "0000" + "00"
            )
            if len(line) != 220: raise ValueError(f"Error PRN size: {len(line)}")
            return line

        for item in fac.get("items", []):
            ref = str(item["referencia"]).strip()
            look = inv.get(ref)
            if not look: raise HTTPException(status_code=400, detail=f"Ref {ref} sin cta_inv")
            lines.append(fmt_line(sec, look["cta_inv"], look["producto"], item.get("descripcion", ""), "D", item.get("valor_total", 0), item.get("cantidad", 1)))
            sec += 1

        total_fac = float(fac.get("subtotal", 0)) + float(fac.get("iva_total", 0))
        lines.append(
            "P" + str(doc).zfill(3) + num_doc.zfill(11) + str(sec).zfill(5) + 
            NIT_INCOLMOTOS.zfill(13) + "000" + "2205010000" + "0000000000000" + 
            fecha + str(cc).zfill(4) + "000" + "INCOLMOTOS SAS".ljust(50)[:50] + 
            "C" + str(int(round(total_fac * 100))).zfill(15) + "000000000000000" + 
            "0000" + "0000" + "000" + str(cc).zfill(4) + "000" + "000000000000000" + 
            "P" + str(doc).zfill(3) + num_doc.zfill(11) + "001" + fecha_vto + "0000" + "00"
        )
        sec += 1

        iva = float(fac.get("iva_total", 0))
        if iva > 0:
            lines.append(fmt_line(sec, "2408020100", "0000000000000", "INCOLMOTOS SAS", "D", iva, 1))

        content = "\r\n".join(lines) + "\r\n"
        archivos_prn.append((f"INT{num_doc}.prn", content.encode("latin-1", errors="replace")))

    if len(archivos_prn) == 1:
        headers = {"Content-Disposition": f"attachment; filename={archivos_prn[0][0]}"}
        return StreamingResponse(io.BytesIO(archivos_prn[0][1]), headers=headers, media_type="application/octet-stream")
    else:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for nombre, datos_prn in archivos_prn:
                zf.writestr(nombre, datos_prn)
        zip_buf.seek(0)
        headers = {"Content-Disposition": "attachment; filename=Lote_ContaFlow.zip"}
        return StreamingResponse(zip_buf, headers=headers, media_type="application/zip")
