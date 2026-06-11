# Autoemail Inventory

Script de Python que revisa automáticamente el inventario de productos en la API de Defontana y envía un correo electrónico de alerta cuando los productos bajan de su stock mínimo configurado.

## Descripción General

El script (`test.py`) realiza las siguientes tareas:

1. **Consulta la API de Defontana**: Obtiene el listado completo de productos disponibles para venta (paginado en 250 productos por página).
2. **Compara con stock mínimo**: Carga los umbrales desde `stock_minimo.json` y verifica si cada producto está por debajo de su límite.
3. **Envía correo consolidado**: Si hay productos con stock bajo, envía un solo correo HTML con una tabla que muestra el código, nombre, stock actual y stock mínimo de cada producto.

## Configuración

### 1. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (ver `.env.example`):

```bash
API_KEY=tu_token_de_defontana
EMAIL_PASSWORD=contraseña_de_aplicacion_de_gmail
EMAIL_EMISOR=correo_remitente@gmail.com
EMAIL_RECEPTOR=correo_destino@gmail.com
```

> **Importante**: `EMAIL_PASSWORD` debe ser una **contraseña de aplicación** de Gmail, no tu contraseña regular. Para generarla ve a: https://myaccount.google.com/apppasswords

### 2. Stock mínimo

Edita `stock_minimo.json` con los productos y sus umbrales mínimos:

```json
[
    {"code": "VLAD", "stock": 350},
    {"code": "VBU1", "stock": 200}
]
```

Solo los productos listados aquí serán evaluados.

### 3. Dependencias

```bash
pip install requests python-dotenv schedule
```

## Ejecución

```bash
python test.py
```

### Salida esperada

```
--- INICIANDO FASE FINAL ---
1. Cargando configuraciones de stock mínimo...
2. Consultando productos a la API de Defontana...
-> Obteniendo página 1 (250 productos por página)...
-> Obteniendo página 2 (250 productos por página)...
...

Se evaluaron un total de X productos disponibles para venta.
-> Se encontraron Y productos con stock bajo.

4. Enviando correo consolidado con tabla HTML...
Correo consolidado enviado exitosamente a destino@correo.com
```

Si no hay productos bajo stock mínimo, no se envía correo.

## Flujo del Script

```
┌─────────────────────────────┐
│   Leer stock_minimo.json    │
│   (umbrales por producto)   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Consultar API Defontana    │
│  GET /api/Sale/Getproducts  │
│  (paginado, 250 por página) │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Filtrar productos:         │
│  - availableSale = true     │
│  - existente en stock_min   │
│  - stock < mínimo           │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  ¿Hay productos bajo stock? │
│  SÍ → Enviar correo HTML    │
│  NO → No hacer nada         │
└─────────────────────────────┘
```

## Automatización con Cron (Linux/Mac)

Para que el correo se envíe automáticamente **cada lunes a las 7:30 AM**:

### 1. Abrir el crontab

```bash
crontab -e
```

### 2. Agregar la siguiente línea

```bash
30 7 * * 1 cd /home/ignacio/Others/autoemail-inventory && /usr/bin/python3 test.py >> /tmp/inventory_log.txt 2>&1
```

**Explicación:**

| Campo | Valor | Significado |
|-------|-------|-------------|
| `30`  | Minuto | 30 minutos |
| `7`   | Hora | 7:00 AM |
| `*`   | Día del mes | Cualquier día |
| `*`   | Mes | Cualquier mes |
| `1`   | Día de la semana | Lunes |

### 3. Verificar que el cron está activo

```bash
crontab -l
```

### 4. Logs

La salida se guarda en `/tmp/inventory_log.txt`. Para revisar los logs:

```bash
cat /tmp/inventory_log.txt
```

### Notas sobre Cron

- Asegúrate de que `python3` apunta a la versión correcta. Puedes verificar con `which python3`.
- El directorio de trabajo (`cd /...`) es necesario porque el script carga `stock_minimo.json` relativo a su ubicación.
- Si usas virtualenv, usa la ruta completa al intérprete Python del entorno virtual, por ejemplo:
  ```bash
  30 7 * * 1 cd /home/ignacio/Others/autoemail-inventory && /home/ignacio/Others/autoemail-inventory/venv/bin/python test.py >> /tmp/inventory_log.txt 2>&1
  ```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `test.py` | Script principal |
| `stock_minimo.json` | Umbrales de stock mínimo por producto |
| `.env` | Variables de entorno (API key, correo) |
| `api.json` | Especificación OpenAPI de la API de Defontana (referencia) |
| `test.csv` | Exportación CSV de stock_minimo.json (referencia, no se usa en el script) |
