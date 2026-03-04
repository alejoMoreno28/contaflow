"""
app.py — ContaFlow (Streamlit)
Flujo: Login → Upload múltiple → Procesar lote → Editar → Parametrizar → Excel
"""

import json
import os
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from extractor import process_pdf, process_image, IMAGE_MEDIA_TYPES

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTENTICACIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_VALID_EMAIL    = "demo@contaflow.co"
_VALID_PASSWORD = "ContaFlow2024"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.set_page_config(
    page_title="ContaFlow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROFESSIONAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }

    :root {
        --blue:        #0066FF;
        --blue-dark:   #0052CC;
        --blue-light:  #E8F0FF;
        --blue-mid:    #4D94FF;
        --green:       #10B981;
        --green-light: #ECFDF5;
        --text:        #0F172A;
        --text-soft:   #475569;
        --text-xsoft:  #94A3B8;
        --bg:          #FFFFFF;
        --bg-soft:     #F8FAFF;
        --border:      #E2E8F0;
        --shadow-sm:   0 1px 3px rgba(0,0,0,0.08);
        --shadow-md:   0 4px 16px rgba(0,102,255,0.10);
        --radius:      14px;
        --radius-sm:   8px;
        --radius-pill: 999px;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stBaseViewContainer"] {
        background: var(--bg) !important;
        color: var(--text) !important;
    }

    [data-testid="stToolbar"],
    [data-testid="stMainMenu"],
    footer { display: none !important; }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--blue) 0%, var(--blue-mid) 100%);
        z-index: 999;
        pointer-events: none;
    }

    [data-testid="stMainBlockContainer"] {
        padding: 0 24px !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebarContent"] { padding: 32px 24px !important; }

    button[kind="primary"] {
        background: linear-gradient(135deg, var(--blue) 0%, var(--blue-dark) 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 16px rgba(0,102,255,0.35) !important;
        transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
        letter-spacing: -0.01em !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--blue-dark) 0%, #003D99 100%) !important;
        box-shadow: 0 8px 28px rgba(0,102,255,0.45) !important;
        transform: translateY(-2px) !important;
    }

    button[kind="secondary"] {
        background: transparent !important;
        border: 2px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: var(--radius-pill) !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
    }
    button[kind="secondary"]:hover {
        border-color: var(--blue) !important;
        color: var(--blue) !important;
        background: var(--blue-light) !important;
    }

    .download-btn button {
        background: linear-gradient(135deg, var(--green) 0%, #059669 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        padding: 16px 32px !important;
        font-weight: 700 !important;
        font-size: 1.0625rem !important;
        box-shadow: 0 4px 16px rgba(16,185,129,0.35) !important;
        transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
    }
    .download-btn button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 8px 28px rgba(16,185,129,0.45) !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed var(--blue) !important;
        border-radius: var(--radius) !important;
        background: var(--blue-light) !important;
        padding: 48px 32px !important;
    }

    h1 {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1.15 !important;
        color: var(--text) !important;
        margin: 32px 0 8px !important;
    }
    h2 {
        font-size: 1.875rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        color: var(--text) !important;
        margin: 0 !important;
    }
    h3 {
        font-size: 1.125rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
        margin: 24px 0 12px !important;
    }

    .step-header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 36px 0 18px;
    }
    .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px; height: 42px;
        border-radius: 50%;
        background: var(--blue);
        color: #fff;
        font-weight: 800;
        font-size: 1.125rem;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0,102,255,0.28);
    }

    .bloque-card {
        background: var(--bg-soft);
        border: 1.5px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 22px;
        margin-bottom: 14px;
    }
    .bloque-title {
        font-size: 0.8125rem !important;
        font-weight: 700 !important;
        color: var(--blue) !important;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 14px !important;
    }

    [data-testid="stMetricContainer"] {
        background: var(--bg) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 24px !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
    }
    [data-testid="stMetricContainer"]:hover {
        border-color: var(--blue) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-4px) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: var(--blue) !important;
        letter-spacing: -0.04em !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8125rem !important;
        color: var(--text-soft) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stDataFrameContainer"] {
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stAlert"] {
        border-radius: var(--radius) !important;
        border-left: 4px solid !important;
        padding: 14px 18px !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 32px 0 !important;
    }

    @media (max-width: 900px) {
        h1 { font-size: 1.875rem !important; }
        h2 { font-size: 1.5rem !important; }
    }
</style>
"""

st.markdown(PROFESSIONAL_CSS, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGIN — verificar autenticación antes de mostrar la app
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style="max-width:420px;margin:80px auto 0;padding:40px 36px;
                background:#fff;border:1.5px solid #E2E8F0;border-radius:20px;
                box-shadow:0 8px 40px rgba(0,102,255,0.10);">
        <div style="text-align:center;margin-bottom:32px;">
            <div style="display:inline-flex;align-items:center;justify-content:center;
                        width:56px;height:56px;background:linear-gradient(135deg,#0066FF,#0052CC);
                        border-radius:16px;box-shadow:0 4px 16px rgba(0,102,255,0.3);margin-bottom:16px;">
                <span style="font-size:28px;">⚡</span>
            </div>
            <div style="font-size:1.75rem;font-weight:800;color:#0F172A;letter-spacing:-0.04em;">
                Conta<span style="color:#0066FF;">Flow</span>
            </div>
            <div style="font-size:0.875rem;color:#94A3B8;font-weight:500;margin-top:4px;">
                Plataforma de facturación electrónica
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Correo electrónico", placeholder="usuario@empresa.co")
        password = st.text_input("Contraseña", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

    if submitted:
        if email == _VALID_EMAIL and password == _VALID_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SESSION STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_defaults = {
    "batch_results":  [],   # list[dict] extraídos por Claude, uno por archivo
    "batch_names":    [],   # list[str] nombres de archivos procesados
    "historial":      [],   # list[dict] facturas confirmadas
    "config_por_nit": {},   # dict[nit → config] memoria por proveedor
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:28px;">
        <div style="width:44px;height:44px;background:linear-gradient(135deg,#0066FF,#0052CC);
                    border-radius:12px;display:flex;align-items:center;justify-content:center;
                    box-shadow:0 4px 12px rgba(0,102,255,0.3);">
            <span style="font-size:22px;">⚡</span>
        </div>
        <div>
            <div style="font-size:1.25rem;font-weight:800;color:#0F172A;letter-spacing:-0.03em;">
                Conta<span style="color:#0066FF;">Flow</span>
            </div>
            <div style="font-size:0.75rem;color:#94A3B8;font-weight:600;">Colombia 🇨🇴</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔧 Estado")
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error("⚠️ ANTHROPIC_API_KEY no configurada")
    else:
        st.success("✅ API Key activa")

    st.divider()
    st.markdown("### 📊 Sesión")
    st.metric("Facturas en lote",     len(st.session_state.batch_results))
    st.metric("Facturas en historial", len(st.session_state.historial))

    if st.session_state.historial:
        if st.button("🗑️ Limpiar historial", use_container_width=True):
            st.session_state.historial = []
            st.rerun()
    else:
        st.caption("Sube tus facturas para comenzar.")

    st.divider()
    st.markdown(f"👤 **Demo ContaFlow**")
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    st.caption("**ContaFlow © 2026** • Colombia 🇨🇴")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div style="margin-bottom:40px;padding-top:16px;">
    <h1>⚡ ContaFlow</h1>
    <p style="font-size:1.0625rem;color:#475569;margin:0;line-height:1.6;">
        Sube hasta 50 facturas → Extrae con IA → Parametriza → Descarga Excel
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PASO 1 — UPLOAD MÚLTIPLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="step-header">
    <div class="step-num">1</div>
    <h2>📄 Sube tus facturas</h2>
</div>
""", unsafe_allow_html=True)
st.caption("PDF, PNG, JPG, JPEG o WEBP · Hasta 50 archivos a la vez")

uploaded_files = st.file_uploader(
    "Arrastra tus archivos aquí o haz clic para seleccionar",
    type=["pdf", "jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    if len(uploaded_files) > 50:
        st.warning("⚠️ Máximo 50 archivos por lote. Solo se procesarán los primeros 50.")
        uploaded_files = uploaded_files[:50]

    # Lista de archivos seleccionados
    st.markdown(f"**{len(uploaded_files)} archivo(s) seleccionado(s):**")
    cols_files = st.columns(min(len(uploaded_files), 4))
    for i, uf in enumerate(uploaded_files):
        with cols_files[i % 4]:
            ext = Path(uf.name).suffix.upper().replace(".", "")
            st.markdown(
                f'<div style="background:#F8FAFF;border:1px solid #E2E8F0;border-radius:8px;'
                f'padding:8px 12px;margin:4px 0;font-size:0.8125rem;">'
                f'<strong style="color:#0066FF;">{ext}</strong> {uf.name}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    current_names = sorted(uf.name for uf in uploaded_files)
    already_processed = current_names == sorted(st.session_state.batch_names)

    col_btn, col_clear = st.columns([3, 1])
    with col_btn:
        btn_label = "🔄 Reprocesar lote" if already_processed else "⚙️ Procesar todos"
        procesar = st.button(btn_label, type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Limpiar lote", use_container_width=True):
            st.session_state.batch_results = []
            st.session_state.batch_names   = []
            st.rerun()

    if already_processed and st.session_state.batch_results:
        st.success(
            f"✅ {len(st.session_state.batch_results)} factura(s) ya procesadas — "
            "revisa y edita los datos abajo."
        )

    # ── Procesamiento ─────────────────────────────────────────────────────────
    if procesar:
        st.session_state.batch_results = []
        st.session_state.batch_names   = []
        errores = []

        progress_bar  = st.progress(0)
        status_holder = st.empty()
        total = len(uploaded_files)

        for idx, uf in enumerate(uploaded_files, start=1):
            status_holder.markdown(
                f"🧠 **Procesando {idx} de {total}:** `{uf.name}`..."
            )
            try:
                suffix = Path(uf.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uf.getbuffer())
                    tmp_path = tmp.name

                suf = suffix.lower()
                datos = process_pdf(tmp_path) if suf == ".pdf" else process_image(tmp_path)
                st.session_state.batch_results.append(datos)
                st.session_state.batch_names.append(uf.name)
            except Exception as e:
                errores.append((uf.name, str(e)))

            progress_bar.progress(idx / total)

        status_holder.empty()
        progress_bar.empty()

        ok = len(st.session_state.batch_results)
        if ok:
            st.success(f"✅ {ok} factura(s) procesadas correctamente.")
        if errores:
            for nombre, err in errores:
                st.error(f"❌ {nombre}: {err}")

        st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PASO 2 — TABLA EDITABLE DE RESULTADOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if st.session_state.batch_results:
    st.divider()
    st.markdown("""
    <div class="step-header">
        <div class="step-num">2</div>
        <h2>✏️ Revisa y corrige los datos extraídos</h2>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Edita cualquier celda directamente en la tabla.")

    filas_editables = []
    for datos in st.session_state.batch_results:
        filas_editables.append({
            "Proveedor":       datos.get("proveedor_nombre", "") or "",
            "NIT Proveedor":   datos.get("proveedor_nit",    "") or "",
            "# Factura":       datos.get("numero_factura",   "") or "",
            "Fecha Emisión":   datos.get("fecha_emision",    "") or "",
            "Fecha Vence":     datos.get("fecha_vencimiento","") or "",
            "Subtotal":        float(datos.get("subtotal")       or 0),
            "% IVA":           float(datos.get("porcentaje_iva") or 0),
            "Valor IVA":       float(datos.get("valor_iva")      or 0),
            "Total a Pagar":   float(datos.get("total_a_pagar")  or 0),
        })

    df_editable = pd.DataFrame(filas_editables)

    df_editado = st.data_editor(
        df_editable,
        use_container_width=True,
        hide_index=False,
        num_rows="fixed",
        column_config={
            "Proveedor":     st.column_config.TextColumn("Proveedor",     width="large"),
            "NIT Proveedor": st.column_config.TextColumn("NIT Proveedor", width="medium"),
            "# Factura":     st.column_config.TextColumn("# Factura",     width="medium"),
            "Fecha Emisión": st.column_config.TextColumn("Fecha Emisión", width="small"),
            "Fecha Vence":   st.column_config.TextColumn("Fecha Vence",   width="small"),
            "Subtotal":      st.column_config.NumberColumn("Subtotal",     format="$ %,.0f", width="medium"),
            "% IVA":         st.column_config.NumberColumn("% IVA",        format="%.0f%%",  width="small"),
            "Valor IVA":     st.column_config.NumberColumn("Valor IVA",    format="$ %,.0f", width="medium"),
            "Total a Pagar": st.column_config.NumberColumn("Total a Pagar",format="$ %,.0f", width="medium"),
        },
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PASO 2.5 — PARAMETRIZACIÓN CONTABLE GLOBAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    st.divider()
    st.markdown("""
    <div class="step-header">
        <div class="step-num">2.5</div>
        <h2>📋 Parametrización Contable</h2>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Se aplicará a **todas** las facturas del lote.")

    # ── BLOQUE 1: COMPROBANTE ─────────────────────────────────────────────
    st.markdown('<div class="bloque-card">', unsafe_allow_html=True)
    st.markdown('<p class="bloque-title">🏷️ Bloque 1 · Comprobante</p>', unsafe_allow_html=True)

    TIPOS = ["Compra de mercancía", "Gasto operacional", "Servicio", "Activo fijo"]
    PAGOS = ["Contado", "Crédito 30 días", "Crédito 60 días", "Crédito 90 días"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("Tipo de comprobante")
        tipo_comprobante = st.selectbox(
            "tipo_comprobante", TIPOS, index=0, label_visibility="collapsed"
        )
    with col2:
        st.caption("Centro de costo")
        centro_costo = st.text_input(
            "centro_costo", value="", placeholder="Ej: CC001",
            label_visibility="collapsed",
        )
    with col3:
        st.caption("Forma de pago")
        forma_pago = st.selectbox(
            "forma_pago", PAGOS, index=0, label_visibility="collapsed"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── BLOQUE 2: RETENCIONES ─────────────────────────────────────────────
    st.markdown('<div class="bloque-card">', unsafe_allow_html=True)
    st.markdown('<p class="bloque-title">💰 Bloque 2 · Retenciones</p>', unsafe_allow_html=True)
    st.caption("Los valores se calcularán individualmente según el subtotal de cada factura.")

    col1, col2 = st.columns(2)
    with col1:
        aplica_rf25 = st.checkbox("ReteFuente 2.5% (PUC 236540)")
        aplica_rf35 = st.checkbox("ReteFuente 3.5% — no declarante (PUC 236540)")
    with col2:
        aplica_riva = st.checkbox("ReteIVA 15% del IVA (PUC 236701)")
        col_check, col_tasa = st.columns([3, 2])
        with col_check:
            aplica_rica = st.checkbox("ReteICA (PUC 236805)")
        with col_tasa:
            st.caption("Tasa ‰")
            tasa_rica = st.number_input(
                "tasa_rica", min_value=0.0, max_value=20.0,
                value=4.14, step=0.01, format="%.2f",
                label_visibility="collapsed",
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── CONFIRMAR LOTE ────────────────────────────────────────────────────
    st.divider()
    col_confirm, col_discard = st.columns([3, 1])
    with col_confirm:
        if st.button(
            f"✅ Confirmar lote — {len(st.session_state.batch_results)} factura(s)",
            type="primary",
            use_container_width=True,
        ):
            registros_editados = df_editado.to_dict("records")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for i, (reg, datos) in enumerate(
                zip(registros_editados, st.session_state.batch_results)
            ):
                sub = float(reg.get("Subtotal") or 0)
                iva = float(reg.get("Valor IVA") or 0)

                # Items desde Claude (sin edición manual en batch)
                items_raw = datos.get("items") or []
                if isinstance(items_raw, str):
                    try:
                        items_raw = json.loads(items_raw)
                    except Exception:
                        items_raw = []
                items_detalle = [
                    {
                        "Descripción": it.get("descripcion", ""),
                        "Tipo":        "Producto",
                        "Cuenta PUC":  "",
                        "Cantidad":    float(it.get("cantidad")    or 1),
                        "Valor Total": float(it.get("valor_total") or 0),
                    }
                    for it in items_raw
                ]

                fila_final = {
                    # Datos editados
                    "proveedor":         reg.get("Proveedor",     ""),
                    "nit_proveedor":     reg.get("NIT Proveedor", ""),
                    "numero_factura":    reg.get("# Factura",     ""),
                    "fecha_emision":     reg.get("Fecha Emisión", ""),
                    "fecha_vencimiento": reg.get("Fecha Vence",   ""),
                    "subtotal":          sub,
                    "pct_iva":           float(reg.get("% IVA")   or 0),
                    "valor_iva":         iva,
                    "total_a_pagar":     float(reg.get("Total a Pagar") or 0),
                    # Datos de Claude no editables
                    "direccion":         datos.get("direccion_proveedor", "") or "",
                    "telefono":          datos.get("telefono_proveedor",  "") or "",
                    "comprador":         datos.get("comprador_nombre",    "") or "",
                    "nit_comprador":     datos.get("comprador_nit",       "") or "",
                    "total_bruto":       float(datos.get("total_bruto")   or 0),
                    # Parametrización global
                    "tipo_comprobante":  tipo_comprobante,
                    "centro_costo":      centro_costo,
                    "forma_pago":        forma_pago,
                    "aplica_rf25":       aplica_rf25,
                    "rf25_valor":        round(sub * 0.025) if aplica_rf25 else 0,
                    "aplica_rf35":       aplica_rf35,
                    "rf35_valor":        round(sub * 0.035) if aplica_rf35 else 0,
                    "aplica_riva":       aplica_riva,
                    "riva_valor":        round(iva * 0.15)  if aplica_riva else 0,
                    "aplica_rica":       aplica_rica,
                    "tasa_rica":         tasa_rica,
                    "rica_valor":        round(sub * (tasa_rica / 1000)) if aplica_rica else 0,
                    # Ítems y metadatos
                    "items_detalle": items_detalle,
                    "_timestamp":    ts,
                    "_archivo":      (
                        st.session_state.batch_names[i]
                        if i < len(st.session_state.batch_names) else ""
                    ),
                }
                st.session_state.historial.append(fila_final)

            st.session_state.batch_results = []
            st.session_state.batch_names   = []
            st.success(f"✅ {len(registros_editados)} factura(s) agregadas al historial.")
            st.rerun()

    with col_discard:
        if st.button("❌ Descartar lote", use_container_width=True):
            st.session_state.batch_results = []
            st.session_state.batch_names   = []
            st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PASO 3 — HISTORIAL Y DESCARGA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if st.session_state.historial:
    st.divider()
    st.markdown("""
    <div class="step-header">
        <div class="step-num">3</div>
        <h2>📊 Historial y Descarga</h2>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("📦 Facturas", len(st.session_state.historial))
    with m2:
        total_pagar = sum(h.get("total_a_pagar", 0) or 0 for h in st.session_state.historial)
        st.metric("💰 Total a pagar", f"${total_pagar:,.0f}")
    with m3:
        total_iva = sum(h.get("valor_iva", 0) or 0 for h in st.session_state.historial)
        st.metric("📋 Total IVA", f"${total_iva:,.0f}")

    st.divider()

    COLS_PREVIEW = [
        "proveedor", "nit_proveedor", "numero_factura",
        "fecha_emision", "subtotal", "total_a_pagar",
        "tipo_comprobante", "forma_pago",
    ]
    df_hist    = pd.DataFrame(st.session_state.historial)
    df_preview = df_hist[[c for c in COLS_PREVIEW if c in df_hist.columns]].copy()
    st.markdown("### Vista previa del historial")
    st.dataframe(df_preview, use_container_width=True, hide_index=True)

    # ── Generar Excel ────────────────────────────────────────────────────────
    def crear_excel(historial: list[dict]) -> BytesIO:
        from openpyxl.styles import Alignment, Font, PatternFill

        COLS_RESUMEN = [
            "proveedor",        "nit_proveedor",    "numero_factura",
            "fecha_emision",    "fecha_vencimiento",
            "direccion",        "telefono",
            "comprador",        "nit_comprador",
            "total_bruto",      "subtotal",          "pct_iva",
            "valor_iva",        "total_a_pagar",
            "tipo_comprobante", "centro_costo",      "forma_pago",
            "aplica_rf25",      "rf25_valor",
            "aplica_rf35",      "rf35_valor",
            "aplica_riva",      "riva_valor",
            "aplica_rica",      "tasa_rica",         "rica_valor",
        ]
        COLS_MONEDA = {
            "total_bruto", "subtotal", "valor_iva", "total_a_pagar",
            "rf25_valor",  "rf35_valor", "riva_valor", "rica_valor",
        }

        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            fill_blue  = PatternFill(start_color="0066FF", end_color="0066FF", fill_type="solid")
            font_white = Font(color="FFFFFF", bold=True, size=11)
            center     = Alignment(horizontal="center", vertical="center")

            # HOJA 1 — RESUMEN
            df_res  = pd.DataFrame(historial)
            cols_ok = [c for c in COLS_RESUMEN if c in df_res.columns]
            df_res[cols_ok].to_excel(writer, sheet_name="Resumen", index=False)

            ws = writer.sheets["Resumen"]
            for cell in ws[1]:
                cell.fill      = fill_blue
                cell.font      = font_white
                cell.alignment = center

            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    col_name = ws.cell(row=1, column=cell.column).value
                    if col_name in COLS_MONEDA:
                        cell.number_format = '$ #,##0'

            for col in ws.columns:
                ancho = max((len(str(c.value or "")) for c in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(ancho + 4, 35)

            # HOJA 2 — ITEMS
            filas_items = []
            for fac in historial:
                for item in fac.get("items_detalle", []):
                    filas_items.append({
                        "# Factura":   fac.get("numero_factura", ""),
                        "Proveedor":   fac.get("proveedor", ""),
                        "Descripción": item.get("Descripción", ""),
                        "Tipo":        item.get("Tipo", ""),
                        "Cuenta PUC":  item.get("Cuenta PUC", ""),
                        "Cantidad":    item.get("Cantidad", ""),
                        "Valor Total": item.get("Valor Total", ""),
                    })

            df_items = pd.DataFrame(
                filas_items if filas_items else [],
                columns=["# Factura", "Proveedor", "Descripción",
                         "Tipo", "Cuenta PUC", "Cantidad", "Valor Total"],
            )
            df_items.to_excel(writer, sheet_name="Items", index=False)

            ws2 = writer.sheets["Items"]
            for cell in ws2[1]:
                cell.fill      = fill_blue
                cell.font      = font_white
                cell.alignment = center

            header_items = {cell.value: cell.column for cell in ws2[1]}
            col_vt = header_items.get("Valor Total")
            if col_vt:
                for row in ws2.iter_rows(min_row=2, min_col=col_vt, max_col=col_vt):
                    for cell in row:
                        cell.number_format = '$ #,##0'

            for col in ws2.columns:
                ancho = max((len(str(c.value or "")) for c in col), default=10)
                ws2.column_dimensions[col[0].column_letter].width = min(ancho + 4, 45)

        buf.seek(0)
        return buf

    d1, d2 = st.columns(2)
    with d1:
        excel_buf = crear_excel(st.session_state.historial)
        st.markdown('<div class="download-btn">', unsafe_allow_html=True)
        st.download_button(
            label="📥 Descargar Excel (Resumen + Items)",
            data=excel_buf,
            file_name=f"ContaFlow_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with d2:
        csv_data = df_preview.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Descargar CSV",
            data=csv_data,
            file_name=f"ContaFlow_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    if st.button("🗑️ Vaciar historial completo", use_container_width=True):
        st.session_state.historial = []
        st.rerun()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if not st.session_state.historial and not st.session_state.batch_results:
    st.divider()
    st.markdown("""
    <div style="text-align:center;padding:40px 0;color:#94A3B8;">
        <p style="font-size:0.9375rem;margin-bottom:8px;">
            <strong>ContaFlow © 2026</strong> · Causación automática con IA
        </p>
        <p style="font-size:0.8125rem;margin:0;">
            Hecho en Colombia 🇨🇴 · <strong>hola@contaflow.co</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
