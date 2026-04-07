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