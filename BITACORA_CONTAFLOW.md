# BITÁCORA CONTAFLOW YAMAHA

## 2026-08-14 — Aceites excluidos 003/0001 e IVA como mayor costo

**Problema:** Siigo rechazó el producto `0030001000116` porque ContaFlow le
asignaba `1435010201`. Además, el IVA cobrado por Incolmotos a los aceites
excluidos se llevaba completo a `2408020100`, aunque contablemente debe formar
parte del costo del inventario.

**Causa raíz:** La regla histórica suponía que todos los productos pertenecían
a la línea 002. No existía tratamiento tributario por referencia y el generador
solo conocía el IVA total de la factura.

**Regla validada por la contadora:**

- Las 28 referencias aprobadas de línea 003/grupo 0001 usan `1435020101`.
- Su IVA se calcula al 19% sobre la base después de descuentos, redondeado al
  peso, y se suma al costo del inventario.
- En facturas mixtas, el IVA de los repuestos 002 conserva `2408020100`.
- Una referencia 003/0001 futura debe declarar explícitamente si es excluida
  (`IVA_MAYOR_COSTO`) o gravada (`DESCONTABLE`).
- Ejemplo CPFE-790425: base 516.307 + IVA 98.098 = débito 614.405 a
  `1435020101`; crédito 614.405 a `2205010000`; sin línea de IVA descontable.

**Implementación segura:** reglas y generador PRN compartidos, cálculos con
`Decimal`, validación de balance en pesos, previsualización contable, bloqueo
ante datos ambiguos y eliminación del generador legado. Las cuentas se calculan
en el servidor; no se confía en valores enviados por el navegador.

**Migración Google Sheets:** 2 filas existentes corregidas y 26 referencias
agregadas. Verificación final: 28 correctas, 0 pendientes, 0 conflictos. Se
preservaron como texto exacto los códigos `003`/`001`.

**Respaldos previos:**

- `C:\Users\PC\Desktop\contaflow_backups\inventarios-before-excluded-oils-20260814-164128.*`
- `C:\Users\PC\Desktop\contaflow_backups\inventarios-before-excluded-oils-20260814-164317.*`

**Validación técnica:** 40 pruebas Python, compilación Next.js de producción,
ESLint del flujo de repuestos y arranque local de Streamlit.

**Estado:** listo para despliegue; falta la aceptación final importando en
Siigo un PRN real de aceite y uno mixto.

---

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

---

## 2026-04-07 — Reestructuración Frontend UI (Premium V2) y Hotfix Ibagué
**Mejora UI:** Se rediseñó totalmente la plataforma dentro de Streamlit usando inyección de CSS Vanilla (`<style>`). 
- **Cambios Estéticos:** Implementación de Modo Oscuro Corporativo (Yamaha Red & Black), glassmorphism en las métricas, bordes suavizados y botones modernos sin la barra lateral (Sidebar) vieja.
- **Cambios UX:** Se implementó `st.tabs` para evitar el desplazamiento vertical infinito leyendo múltiples facturas. Se agregaron animaciones (balloons) cuando el PRN se descarga correctamente.

**Bug Fix (Hotfix):** El enrutamiento de Ibagué (CC1 SEXTA vs CC7 PRINCIPAL) fallaba y caía por default a `P1 / CC1`.
- **Causa Raíz:** Durante una optimización agresiva del prompt JSON esa mañana, se borró involuntariamente de la instrucción la orden de extraer el campo `"direccion_entrega"`. Al no tener la dirección exacta, la función matemática `_resolver_tienda_ibague` carecía del texto (`CR 5` / `CR 6`) para decidir.
- **Solución:** Se reconstruyó el esquema en `yamaha_app.py` forzando de nuevo la extracción de `direccion_entrega` y se corrobora en pruebas exhaustivas locales simulando las direcciones de ambas sucursales.
- **Estado:** ✅ Todo operativo; Streamlit Cloud Auto-sincronizado.
