# Tratamiento de aceites excluidos 003/0001

## Objetivo

Corregir la generación de PRN para los aceites excluidos de la línea `003`, grupo `0001`, sin alterar el resultado de los repuestos `002` que ya funcionan. La factura CPFE-790425 es el caso patrón: referencia `90793AV50400`, producto `0030001000122`, base `$516.307`, IVA `$98.098` y costo final `$614.405`.

## Reglas contables confirmadas

- Todo producto `003/0001` usa la cuenta de inventario `1435020101`.
- Solo las referencias expresamente clasificadas como excluidas capitalizan IVA. No se inferirá la exclusión para toda la línea.
- Las 28 referencias entregadas en `ACEITE IA.xlsx` son excluidas conocidas.
- Para referencias futuras `003/0001`, la usuaria debe responder obligatoriamente si el producto es `IVA mayor valor del costo` o `IVA descontable`.
- El IVA capitalizado se calcula como `redondear_al_peso(suma de bases excluidas después de descuento × 19%)`.
- Cuando haya varios aceites excluidos, el IVA se calcula sobre la suma del grupo. Se calcula una asignación por ítem y cualquier diferencia de redondeo se aplica al último ítem excluido.
- Cada movimiento de inventario excluido lleva `base + IVA asignado` a `1435020101`.
- El IVA de los demás repuestos permanece en `2408020100`.
- La cuenta por pagar `2205010000` permanece por `subtotal + IVA total`.
- El generador debe bloquear si los movimientos no balancean exactamente o si el IVA capitalizado supera el IVA informado por la factura.

## Arquitectura

### Motor de reglas

`yamaha_rules.py` será la única fuente de verdad para:

- normalizar códigos de producto de 13 dígitos;
- calcular cuentas: regla existente para `002` y `1435020101` para `003/0001`;
- representar `IVA_MAYOR_COSTO` y `DESCONTABLE`;
- contener las 28 referencias excluidas conocidas y sus códigos Siigo;
- enriquecer el catálogo cargado, sin ocultar conflictos entre el código del catálogo y la lista aprobada.

Un código fuera de las familias conocidas fallará de forma explícita; no se generará una cuenta por aproximación.

### Motor PRN

`yamaha_prn.py` separará la planeación contable del formato fijo de 220 caracteres. Usará `Decimal`, redondeo `ROUND_HALF_UP` para el IVA al peso y validaciones de balance antes de serializar.

Streamlit y FastAPI llamarán el mismo generador. El formato, orden, encoding y campos de los PRN `002` se conservarán. El caso 790425 generará dos líneas: débito `1435020101` por `$614.405` y crédito `2205010000` por `$614.405`, sin línea `2408020100`.

### Catálogo y clasificación

La hoja `INVENARIOS` conservará A:H y añadirá la columna I `TRATAMIENTO_IVA`:

- `IVA_MAYOR_COSTO`: capitaliza IVA;
- `DESCONTABLE`: deja el IVA en `2408020100`;
- vacío: permitido para `002` por compatibilidad; bloqueante para un `003/0001` desconocido.

Las altas escribirán también `LINEA` y `GRUPO` en G/H. El servidor calculará la cuenta; nunca confiará en una cuenta enviada por el navegador.

La interfaz Streamlit mostrará una selección obligatoria para nuevos `003/0001`. Las 28 referencias conocidas se reconocerán automáticamente. La validación previa mostrará base, IVA capitalizado, costo de inventario, tratamiento y cuenta.

### Migración segura

Un comando de migración con modo simulación por defecto:

1. leerá la hoja completa y comprobará duplicados y conflictos;
2. guardará un respaldo local con fecha y hora antes de escribir;
3. añadirá el encabezado I sin alterar A:H;
4. actualizará solo E/G/H/I de referencias existentes aprobadas;
5. agregará las referencias aprobadas ausentes con sus datos auditados;
6. volverá a leer y verificará las 28 referencias.

La copia local XLSM no se modificará. El enriquecimiento en memoria de la lista aprobada impedirá que un fallback local desactualizado vuelva a producir la cuenta incorrecta.

## Interfaz y errores

- Ningún `003/0001` nuevo podrá guardarse sin tratamiento tributario.
- Una clasificación desconocida, código distinto al aprobado, IVA insuficiente o PRN descuadrado detendrá la descarga con un mensaje accionable.
- El resumen previo separará `Base`, `IVA mayor costo`, `Costo inventario` e `IVA descontable`.
- El botón `Refrescar DB` seguirá disponible; un despliegue nuevo reiniciará además la memoria del servidor.

## Compatibilidad

- Los casos `002` deben conservar cuentas, importes, orden y bytes de salida.
- No se modifican tienda, centro de costo, documento P, bodega, vencimiento, extracción de referencias ni deduplicación.
- FastAPI y la pantalla Next.js se alinean, aunque el despliegue autorizado en este cambio es la aplicación Streamlit activa.

## Verificación y despliegue

- Pruebas unitarias para cuentas, lista de 28, clasificación y redondeos.
- Snapshot byte a byte de un PRN `002` producido por la versión anterior.
- Caso dorado 790425.
- Facturas mixta, múltiples aceites, IVA cero, clasificación ausente y datos inconsistentes.
- Pruebas de migración contra una hoja falsa antes de ejecutar el modo real.
- Suite Python completa, compilación Python, lint/build de Next.js y prueba local de arranque Streamlit.
- Respaldo y migración real, commit, push a `main`, espera del despliegue automático y comprobación del sitio público.

## Fuera de alcance

- Cambiar el formato PRN de 220 caracteres.
- Modificar `app.py` o los flujos generales de ContaFlow.
- Automatizar la importación a Siigo.
- Reclasificar productos distintos de los 28 aprobados sin intervención de la usuaria.
