# CONTAFLOW YAMAHA — DOCUMENTO CEREBRO
**Última actualización: 2026-08-14**
**Para usar con cualquier IA: Claude Code, Antigravity, o Claude.ai**

---

## ¿QUÉ ES ESTE ARCHIVO?

Este es el contexto completo del proyecto ContaFlow Yamaha. Cualquier IA que trabaje en este proyecto debe leerlo completo antes de tocar cualquier línea de código. Contiene la historia, la arquitectura, los bugs resueltos, las reglas de negocio y el estado actual.

---

## SECCIÓN 1 — QUÉ ES CONTAFLOW YAMAHA

ContaFlow Yamaha es una app Streamlit que automatiza el proceso de causación de facturas de compra para Yamaha Yamamotos S.A.S. La app extrae datos de facturas PDF de Incolmotos usando Claude Haiku y genera archivos `.PRN` que Siigo importa directamente, eliminando la digitación manual.

**Cliente:** Yamaha Yamamotos S.A.S — NIT: 900.974.547
**Proveedor procesado:** Industria Colombiana de Motocicletas Yamaha S.A.S — NIT: 890.916.911-6 (en Siigo: "INCOLMOTOS SAS")
**Contadora/usuaria piloto:** Mamá de Alejo (valida todo en Siigo)
**Software contable:** Siigo (NO Alegra)
**Volumen:** ~1.200 facturas al mes, entre 4 y 126+ ítems cada una

---

## SECCIÓN 2 — STACK TÉCNICO

- **Lenguaje:** Python (validado localmente con 3.12.13)
- **Frontend:** Streamlit
- **IA extracción PDF:** claude-haiku-4-5-20251001 via Anthropic API
- **Deploy activo:** Streamlit Community Cloud → https://contaflow-yamaha.streamlit.app
- **Repo:** github.com/alejoMoreno28/contaflow (rama: main)
- **Local:** C:\Users\PC\Desktop\contaflow
- **Google Sheets ID:** 1JzKIDiMmjqVD-iYXTAjxk4wqPvdassNMZJjsNP_UtQI
- **Service account:** contaflow-yamaha@contaflow-489019.iam.gserviceaccount.com

**Archivo principal:** `yamaha_app.py`. Reglas compartidas en `yamaha_rules.py`,
`yamaha_catalog.py` y `yamaha_prn.py`.
**NO tocar:** `app.py` (ContaFlow general, bugs activos)

---

## SECCIÓN 3 — FLUJO COMPLETO DE LA APP

```
1. Usuaria sube PDF de factura Incolmotos
2. Claude Haiku extrae en JSON:
   - Header: numero_factura, fecha, fecha_vencimiento, fecha_pronto_pago,
             ciudad, direccion_entrega, subtotal, iva_total
   - Items: referencia, descripcion, cantidad, valor_total, tiene_iva
3. App determina tienda según ciudad + dirección
4. App busca cada referencia en Google Sheets hoja INVENARIOS
5. App genera archivo .PRN de 220 chars por línea
6. Usuaria descarga .PRN y lo sube manualmente a Siigo
```

---

## SECCIÓN 4 — GOOGLE SHEETS (FUENTE DE DATOS)

**Hoja INVENARIOS** — catálogo de ~22.718 referencias:
- Col B = REFERENCIA (clave de búsqueda, código Incolmotos)
- Col C = PRODUCTO (código Siigo, 13 chars, ej: "0020038000183")
- Col D = DESCRIPCION
- Col E = CTA-INV (cuenta contable, 10 chars, ej: "1435010238")
- Col G = LINEA (texto de 3 dígitos)
- Col H = GRUPO (texto de 3 dígitos en la hoja; el producto usa 4 dígitos)
- Col I = TRATAMIENTO_IVA (`DESCONTABLE` o `IVA_MAYOR_COSTO`)
- Datos desde fila 6 (primeras 5 son encabezados/vacías)

### Regla especial aceites excluidos (validada 2026-08-14)

- Solo las 28 referencias aprobadas y futuras referencias confirmadas de
  producto línea `003`, grupo `0001`, usan cuenta `1435020101`.
- Para `IVA_MAYOR_COSTO`, el 19% de la base después de descuentos se redondea
  al peso y se suma al movimiento de inventario.
- En facturas mixtas, únicamente el IVA atribuible a esos aceites se capitaliza;
  el IVA restante continúa en `2408020100`.
- El crédito `2205010000` siempre conserva subtotal + IVA total de la factura.
- Si una referencia 003/0001 nueva no tiene tratamiento explícito, el PRN se
  bloquea. Nunca adivinar ni generalizar la regla a otros grupos.
- Caso patrón CPFE-790425: `516307 + 98098 = 614405` a `1435020101`.
- La hoja quedó migrada con 28/28 referencias correctas el 2026-08-14.

**Hoja DATOS** — mapeo de tiendas:
- Col A = Dirección física de la tienda
- Col B = Nombre tienda
- Col C = CC (Centro de Costo)
- Col D = DOCUMENTO P (número del comprobante en Siigo)
- Col E = BODEGA

**REGLA CRÍTICA:** Las columnas SIEMPRE son C=CC, D=Doc P, E=Bodega.
Nunca invertir. Verificado contra PRNs aceptados por Siigo.

---

## SECCIÓN 5 — TABLA DE TIENDAS (VALORES EXACTOS VALIDADOS)

Estos valores fueron validados por la contadora y verificados contra PRNs que Siigo aceptó. Son la fuente de verdad absoluta.

| Tienda | Dirección PDF | CC | Doc P | Bodega |
|--------|--------------|-----|-------|--------|
| SEXTA | CR 6 25 40 BRR BELALCAZAR | 1 | 1 | 1 |
| PURIFICACION | CR 6 5 - 58 | 2 | 2 | 2 |
| GUAMO | CL 9A 9 - 98 | 3 | 3 | 3 |
| SALDANA | CL 14 16 16 | 4 | 4 | 4 |
| GIRARDOT | CR 10 28 73 | 5 | 10 | 5 |
| MELGAR | CR 25 CL 8 A 24 52 | 6 | 12 | 6 |
| IBAGUE Principal | CR 5 20 39 B 1 CARMEN | 7 | 14 | 7 |
| NEIVA | CRR 7 22 66 | 8 | 15 | 8 |

**En el PRN:**
- Campo [1:4] = Doc P → str(doc).zfill(3) → ej: Girardot='010', Neiva='015'
- Campo [67:71] = CC → str(cc).zfill(4) → ej: Girardot='0005', Neiva='0008'
- Campo bodega = mismo valor que CC → str(cc).zfill(4)

**Ibagué tiene DOS tiendas** con la misma ciudad en el PDF. Se distinguen por dirección:
- `_resolver_tienda_ibague(direccion)` evalúa keywords:
  - Principal: CR 5, CRR 5, CARRERA 5, 20 39, 20-39, B 1 CARMEN → cc=7, doc=14
  - Sexta: CR 6, CRR 6, CARRERA 6, BELALCAZAR, BRR BELALCAZAR, 25 40 → cc=1, doc=1
  - Fallback: Sexta con st.warning()

---

## SECCIÓN 6 — FORMATO PRN (CRÍTICO — NUNCA MODIFICAR)

Cada línea: exactamente 220 caracteres. Encoding: latin-1. Separador: \r\n (CRLF).

**Líneas de ítems:**
```
[0:1]    'P'
[1:4]    Doc P zfill(3)
[4:9]    '00000'
[9:15]   num_factura zfill(6) — solo dígitos sin 'CPFE-'
[15:20]  secuencia ítem zfill(5) — 00001, 00002...
[20:26]  '000089'
[26:36]  '0916911000'
[36:46]  cuenta contable ljust(10)
[46:59]  código producto Siigo ljust(13)
[59:67]  fecha YYYYMMDD
[67:71]  CC zfill(4)
[71:74]  '000'
[74:124] referencia Incolmotos ljust(50)
[124]    'D'
[125:140] valor_total × 100 zfill(15)
[140:155] cantidad × 100 zfill(15)
[155:170] precio_unitario × 100 zfill(15)
[170:220] '000000000000100000 000000000000000000000000000000'
```

**Línea CXP (penúltima — una por factura):**
```
[36:46]  '2205010000'
[46:59]  13 espacios
[74:124] 'INCOLMOTOS SAS' ljust(50)
[124]    'C'
[125:140] (subtotal + iva_total) × 100 zfill(15)
[170:220] 'P' + doc(3) + '00000' + factura(6) + '001' + fecha_vto(8) + '000000'
```
fecha_vto: si hay pronto pago "HASTA EL DD-MM-YYYY" → usar esa fecha. Si no → fecha vencimiento.

**Línea IVA (última — una por factura):**
```
[36:46]  '2408020100'
[46:59]  13 espacios
[74:124] 'INCOLMOTOS SAS' ljust(50)
[124]    'D'
[125:140] iva_total × 100 zfill(15)
[170:220] mismo resto fijo que ítems
```

**Total líneas = número de ítems + 2 (CXP + IVA)**

---

## SECCIÓN 7 — REGLAS DE NEGOCIO CRÍTICAS

1. **NUNCA aplicar zfill(13) a códigos de producto** — se escriben exactamente como llegan del Sheets
2. **ANTI-DEDUPLICACIÓN:** si la misma referencia aparece 3 veces en el PDF, son 3 ítems distintos en el PRN. Nunca fusionar.
3. **valor_total en el PRN** = columna "Valor Total" del PDF (ya con descuento aplicado). NUNCA calcular precio × cantidad.
4. **Referencias nuevas** (no en Sheets): bloquear generación del PRN y mostrar tabla editable para que la usuaria asigne producto y cuenta. Guardar en nuevas_refs.json.
5. **Bodega** siempre = mismo valor que CC.

---

## SECCIÓN 8 — EXTRACCIÓN ITERATIVA (CHUNKING)

Para facturas grandes (50+ ítems), Haiku se llama en iteraciones de 50 ítems:

- **Llamada 1:** extrae header + primeros 50 ítems, retorna `hay_mas_items: true/false`
- **Llamadas 2-10:** extrae los siguientes 50 usando los últimos 3 ítems como contexto
- **Merge:** todos los ítems se combinan en una lista plana
- **Límite:** máximo 10 iteraciones. Si hay_mas sigue true → st.warning()
- **Error JSON:** si json.loads() falla → st.error() y detener sin generar PRN

---

## SECCIÓN 9 — BITÁCORA DE CAMBIOS

### 2026-04-01 — Reconstrucción completa (commit actual)
**Problema:** Múltiples bugs acumulados desde el 21 de marzo rompieron la app:
- Neiva generaba cc=0015 en vez de cc=0008
- Girardot generaba doc=010 con cc=010 en vez de cc=0005
- Ibagué Principal generaba P001 en vez de P014
- Facturas grandes (100+ ítems) truncaban el JSON

**Causa raíz:** Commit e85d1ea invirtió columnas C y D de hoja DATOS para todas las tiendas al "arreglar" Girardot.

**Solución:** Reconstrucción desde commit f972ec7 (20 marzo) con 3 mejoras:
1. Columnas DATOS verificadas: cc=col C, doc=col D, bodega=col E
2. `_resolver_tienda_ibague` con keywords CR 5/CR 6 verificados con PDFs reales
3. `_extraer_iterativa` para facturas 100+ ítems (chunking 50 ítems/llamada)

---

### 2026-03-20 — Anti-deduplicación (commit f972ec7)
Prompt mejorado para que Haiku no fusione ítems repetidos.
Verificado contra 9 escenarios. Solo tocó yamaha_app.py.

---

### 2026-03-XX — Chunking inicial (commit db49cff)
Primera implementación de extracción iterativa para facturas grandes.
Resolvía error "La IA alcanzó el límite de tokens".

---

### 2026-03-XX — Distinción Ibagué (commits 9d07303 → 311e86d)
Agregada función `_resolver_tienda_ibague`.
Keywords finales verificadas con PDFs reales:
- Principal: CR 5 20 39 B 1 CARMEN
- Sexta: CR 6 25 40 BRR BELALCAZAR

---

### Bugs históricos resueltos (antes de marzo 20)
- **BUG 1:** API key incorrecta → nueva key en Alejandro's Individual Org
- **BUG 2:** JSON truncado → max_tokens aumentado a 8192
- **BUG 3:** Línea CXP incorrecta → resto[170:220] = 'P'+doc+'00000'+factura+'001'+fecha_vto+'000000'
- **BUG 4:** App buscaba referencias en col A → corregido a col B (row[1])
- **BUG 5:** Ibagué Sexta confundida con Principal → resolver por dirección

---

## SECCIÓN 10 — PRNs VALIDADOS EN SIIGO

| Factura | Tienda | Ítems | Total | Estado |
|---------|--------|-------|-------|--------|
| CPFE-750304 | Neiva | 10 | $384,100 | ✅ VALIDADO en Siigo |
| CPFE-751726 | Purificación | 100 | $5,623,904 | ✅ Generado correcto |
| CPFE-753150 | Neiva | 4 | $289,632 | ✅ Generado correcto |
| CPFE-759006 | Girardot | 126 | $9,417,009 | ✅ PRN bueno disponible |

**PRN de referencia:** `INT759006__2_.prn` — Girardot, verificado que:
- Campo [1:4] = '010' (Doc P de Girardot)
- Campo [67:71] = '0005' (CC de Girardot)

---

## SECCIÓN 11 — FEATURES PENDIENTES

### COMPLETADO — Referencias nuevas
La app bloquea el PRN, solicita producto Siigo de 13 dígitos y, para 003/0001,
solicita el tratamiento tributario antes de escribir en Google Sheets.

### COMPLETADO — Migración a Streamlit Community Cloud
La app activa se despliega desde `main` en `contaflow-yamaha.streamlit.app`.

### PENDIENTE 3 — Login real
Actualmente hardcodeado. Implementar cuando haya más de 1 usuario.

---

## SECCIÓN 12 — REGLAS DE TRABAJO (NO NEGOCIABLES)

1. **NUNCA hacer push sin simulaciones internas que pasen primero**
2. **NUNCA leer empresa/cc/doc desde Excel de inventario** — vienen de hoja DATOS del Sheets
3. **Columnas hoja DATOS:** A=Dirección, B=Tienda, C=CC, D=Doc P, E=Bodega — NUNCA invertir
4. **Cada cambio = un commit descriptivo separado**
5. **Validar con la contadora en Siigo antes de cerrar cualquier bug**
6. **Centralizar reglas Yamaha** en los módulos compartidos; no duplicar fórmulas en UI/API
7. **NO tocar app.py** — tiene bugs activos de ContaFlow general
8. **Diagnóstico antes de código** — nunca escribir código sin entender la causa raíz

---

## SECCIÓN 13 — CÓMO ARRANCAR UNA NUEVA SESIÓN DE IA

Si eres una IA nueva leyendo esto:

1. Lee este documento completo
2. Lee `yamaha_app.py` completo
3. Pregunta al desarrollador qué quiere hacer hoy
4. Diagnostica antes de proponer soluciones
5. Simula internamente antes de hacer push
6. Actualiza la Sección 9 (Bitácora) después de cada cambio exitoso

**Herramientas disponibles:**
- Antigravity (Gemini 3.1 Pro) — IDE principal, ejecuta código
- Claude.ai — diseño, diagnóstico, prompts (gratis)
- Claude Code en VS Code — alternativa a Antigravity
- Railway dashboard — ver logs de deploy

**Credenciales importantes:**
- GitHub: alejoMoreno28 (usar PAT para push)
- Railway: proyecto "calm-bravery" o "profound-essence"
- Google Sheets: service account en credentials.json

---

## SECCIÓN 14 — CONTEXTO DE NEGOCIO

**Por qué existe ContaFlow:**
Yamaha Yamamotos recibe ~1.200 facturas/mes de Incolmotos. El proceso manual tarda 10-25 minutos por factura. ContaFlow lo hace en segundos.

**Competencia:**
- N1 (n1.app): cobra por causación, integra Siigo y Alegra, conecta DIAN
- Cifrato (YC): onboarding 1.5 horas, Excel previo por proveedor

**Ventaja ContaFlow:** sin configuración previa, sin reunión de onboarding, aprende mientras usas.

**Visión:** replicar el modelo "aprende una vez, aplica siempre" de N1 y Cifrato para múltiples contadores colombianos (SaaS multi-tenant con Next.js/FastAPI/Supabase).

---

*Este documento debe actualizarse después de cada sesión de trabajo.*
*Formato: agregar entrada a Sección 9 con fecha, problema, causa y solución.*
