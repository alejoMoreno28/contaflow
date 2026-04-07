# BITÁCORA CONTAFLOW YAMAHA

## 2026-04-01 — Reconstrucción completa yamaha_app
**Problema:** Múltiples bugs acumulados desde el 20 de marzo rompieron
la generación de PRNs. Errores reportados por la contadora:
- Neiva generaba cc=0015 en vez de cc=0008
- Girardot generaba doc=010 con cc=010 en vez de cc=0005
- Ibagué Principal generaba P001 en vez de P014
- Facturas grandes (100+ ítems) truncaban el JSON

**Causa raíz:** El commit e85d1ea invirtió las columnas C y D de la
hoja DATOS del Google Sheets para todas las tiendas al intentar
arreglar Girardot.

**Solución:** Reconstrucción desde commit f972ec7 (20 marzo, último
bueno) con 3 mejoras aplicadas correctamente:
1. Columnas DATOS verificadas: cc=col C, doc=col D, bodega=col E
2. _resolver_tienda_ibague con keywords CR 5/CR 6 verificados con PDFs reales
3. _extraer_iterativa para facturas de 100+ ítems (chunking 50 ítems/llamada)

**Valores validados por contadora (Google Sheets hoja DATOS):**
| Tienda | CC | Doc P | Bodega |
|--------|----|-------|--------|
| SEXTA | 1 | 1 | 1 |
| PURIFICACION | 2 | 2 | 2 |
| GUAMO | 3 | 3 | 3 |
| SALDANA | 4 | 4 | 4 |
| GIRARDOT | 5 | 10 | 5 |
| MELGAR | 6 | 12 | 6 |
| IBAGUE Principal | 7 | 14 | 7 |
| NEIVA | 8 | 15 | 8 |

**PRN verificado:** INT759006__2_.prn (Girardot, aceptado por Siigo)
**Commit:** 4e4476a
**Estado:** ✅ Simulaciones pasadas, pendiente validación en Siigo

---

## 2026-03-20 — Anti-deduplicación referencias repetidas (f972ec7)
Prompt mejorado para que Haiku no fusione ítems repetidos.
Verificado contra 9 escenarios. Solo tocó yamaha_app.py.

---

## Reglas de trabajo establecidas
- NUNCA hacer push sin simulaciones internas que pasen primero
- NUNCA leer empresa/cc/doc desde Excel — esos valores son fijos en hoja DATOS
- Columnas hoja DATOS: A=Dirección, B=Tienda, C=CC, D=Doc P, E=Bodega
- Cada cambio = un commit descriptivo separado
- Validar con la contadora en Siigo antes de cerrar cualquier bug


### 2026-04-06  Migración a Streamlit Community Cloud (Pendiente 2 completado)
**Problema:** Railway pausó el contenedor principal al terminar la capa gratuita de USD  (Trial Ended).
**Solución:** Se abandonó Railway de inmediato y se hizo el despliegue directo sobre Streamlit Community Cloud (100% gratis). Se reconstruyó el .env con TOML formatting (usando multi-line literals para el JSON service account key) y se actualizó yamaha_app.py para usar st.secrets como fallback a os.environ.

---

## 2026-04-07 — Estabilización profunda en Streamlit (JSON y Watchdog)
**Problema 1:** Fallos de `Expecting value:` debido a que el modelo (Claude) ocasionalmente retornaba un bloque markdown en lugar de puro JSON, el cual el Cloud no procesaba amigablemente.
**Solución 1:** Se configuró el `prompt` en un esquema JSON plano root-level estricto y se implementó un parser exhaustivo dentro de `_extraer_iterativa`.

**Problema 2:** Caídas de Streamlit (`OSError: inotify instance limit reached`) durante el cargue pesado de PDFs.
**Solución 2:** Se introdujo `.streamlit/config.toml` con `fileWatcherType = "none"`.

**Problema 3:** El `Subtotal` y las métricas de pie quedaban en $0 al mostrarse y en el PRN.
**Solución 3:** Reajuste del mapeo de extracción en `iteracion == 1` para que capturara las variables base (`numero_factura`, `subtotal`, `iva_total`, etc.) desde la raíz del objeto modificado (`data.get`) en vez de la subcarpeta deprecada `"header"`.
**Estado:** ✅ Plataforma 100% estable; en producción. Los PRNs recogen los montos fieles de la factura y evitan el error de estado residual haciendo refresh (F5).