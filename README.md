# ContaFlow

Extractor automático de facturas electrónicas colombianas (PDF → JSON → CSV) usando Claude AI.

## Campos extraídos

| Campo | Descripción |
|---|---|
| `numero_factura` | Código de la factura (ej: `FE-0001234`) |
| `proveedor_nombre` | Razón social del emisor |
| `proveedor_nit` | NIT del emisor con dígito verificador |
| `comprador_nombre` | Razón social del receptor |
| `comprador_nit` | NIT o cédula del comprador |
| `fecha_emision` | Fecha de emisión (`YYYY-MM-DD`) |
| `fecha_vencimiento` | Fecha de vencimiento (`YYYY-MM-DD`) |
| `forma_pago` | Ej: `Contado`, `Crédito 30 días` |
| `subtotal` | Valor antes de IVA |
| `porcentaje_iva` | Tasa de IVA (ej: `19`) |
| `valor_iva` | Monto del IVA |
| `total_factura` | Total a pagar |
| `es_autorretenedor` | `true/false` |
| `aplica_retefuente` | `true/false` |

---

## Instalación

### 1. Requisitos previos
- Python 3.11 o superior
- Una clave de API de Anthropic → https://console.anthropic.com

### 2. Instalar dependencias

Abre una terminal en la carpeta `contaflow` y ejecuta:

```bash
pip install -r requirements.txt
```

### 3. Configurar la API key

Copia el archivo de ejemplo y edítalo:

```bash
# Windows
copy .env.example .env
```

Abre `.env` con cualquier editor de texto y reemplaza el valor:

```
ANTHROPIC_API_KEY=sk-ant-aqui-va-tu-clave-real
```

---

## Uso

### Procesar una sola factura

```bash
python main.py FE-0001234.pdf
```

### Procesar una carpeta completa de facturas

```bash
python main.py facturas/
```

### Cambiar el archivo CSV de salida

```bash
python main.py facturas/ --output reportes/mayo-2025.csv
```

### Ver el JSON extraído en consola

```bash
python main.py FE-0001234.pdf --json
```

### Ver todas las opciones

```bash
python main.py --help
```

---

## Estructura del proyecto

```
contaflow/
├── main.py          ← punto de entrada (CLI)
├── extractor.py     ← lógica: leer PDF + llamar Claude + guardar CSV
├── requirements.txt
├── .env             ← tu API key (NO subir a git)
├── .env.example     ← plantilla de configuración
└── output/
    └── facturas.csv ← resultados acumulados (se crea automáticamente)
```

---

## Notas

- El CSV es **acumulativo**: cada ejecución agrega filas sin borrar las anteriores.
- Los PDFs escaneados sin capa de texto no son compatibles (se requiere OCR previo).
- Los campos que no se encuentran en el PDF quedan como `null` en el JSON y vacíos en el CSV.
