import os
import requests
import smtplib
import schedule
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# ==========================================
# CONFIGURACIÓN DE LA API DE DEFONTANA
# ==========================================
API_BASE_URL = "https://api.defontana.com" 
API_KEY = os.getenv("API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Parámetros Globales de Bodegas
BODEGAS_INFO = [
    {
        "code": "BODEGA2",
        "description": "LOGINSA",
        "saleAvailable": "S",
        "active": "S"
    },
    {
        "code": "BODEGACENTRAL",
        "description": "BODEGA CONCON",
        "saleAvailable": "S",
        "active": "S"
    }
]

# ==========================================
# CONFIGURACIÓN DE CORREO
# ==========================================
# Leyendo desde .env para mayor seguridad
EMAIL_EMISOR = os.getenv("EMAIL_EMISOR", "astrid@uqomm.com")
EMAIL_RECEPTOR = os.getenv("EMAIL_RECEPTOR", "ignacio@uqomm.com")
PASSWORD_CORREO = os.getenv("EMAIL_PASSWORD", "tu_contraseña_de_aplicacion")

def enviar_correo_alerta_multiple(productos_bajo_stock):
    """Envía un solo correo consolidado con todos los productos que tienen stock bajo (Fase Final)."""
    if not productos_bajo_stock:
        return
        
    try:
        if PASSWORD_CORREO == "tu_contraseña_de_aplicacion":
            print("ADVERTENCIA: No se ha configurado 'EMAIL_PASSWORD' en .env. El envío de correo fallará.")
            
        msg = MIMEMultipart()
        msg['From'] = EMAIL_EMISOR
        msg['To'] = EMAIL_RECEPTOR
        #msg['Subject'] = "TEST: Alerta de Inventario: Productos con Stock Bajo"
        msg['Subject'] = "Alerta de Inventario: Productos con Stock Bajo"

        total_productos = len(productos_bajo_stock)
        cuerpo_html = f"""
        <html>
        <body>
            <h2 style="color: #d9534f;">Alerta: Productos con Stock Bajo</h2>
            <p>Se encontraron <strong>{total_productos}</strong> productos que han bajado de su límite de stock mínimo establecido:</p>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 800px;">
                <tr style="background-color: #f2f2f2;">
                    <th>External Code</th>
                    <th>Name</th>
                    <th>Stock Actual</th>
                    <th>Stock Mínimo</th>
                </tr>
        """
        
        for p in productos_bajo_stock:
            cuerpo_html += f"""
                <tr>
                    <td>{p.get('external_code', p.get('code'))}</td>
                    <td>{p.get('name', 'N/A')}</td>
                    <td style="color: red; font-weight: bold; text-align: center;">{p.get('stock', 0)}</td>
                    <td style="text-align: center;">{p.get('minimo', 0)}</td>
                </tr>
            """
            
        cuerpo_html += """
            </table>
            <p>Revisar el inventario en sistema.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(cuerpo_html, 'html'))

        # Configuración para SMTP (por ej. Gmail)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, PASSWORD_CORREO)
        server.sendmail(EMAIL_EMISOR, EMAIL_RECEPTOR, msg.as_string())
        server.quit()
        print(f"Correo consolidado enviado exitosamente a {EMAIL_RECEPTOR}.")
    except Exception as e:
        print(f"Error al enviar el correo consolidado: {e}")

def enviar_correo_alerta(producto_codigo, stock_actual):
    """Envía un correo electrónico notificando el bajo stock de un solo producto (Usado en pruebas anteriores)."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_EMISOR
        msg['To'] = EMAIL_RECEPTOR
        msg['Subject'] = f"Alerta de Stock Bajo: {producto_codigo}"

        cuerpo = f"Hola,\n\nEl producto con código {producto_codigo} ha bajado del stock mínimo establecido.\nStock actual: {stock_actual}\n\nPor favor, revisar inventario.\n"
        msg.attach(MIMEText(cuerpo, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EMISOR, PASSWORD_CORREO)
        server.sendmail(EMAIL_EMISOR, EMAIL_RECEPTOR, msg.as_string())
        server.quit()
        print(f"Correo de alerta individual enviado exitosamente a {EMAIL_RECEPTOR} para el producto {producto_codigo}.")
    except Exception as e:
        print(f"Error al enviar el correo individual: {e}")

# ==========================================
# FUNCIONES DE LAS FASES ANTERIORES
# ==========================================
def buscar_stock_primera_prueba():
    """Realiza una primera prueba para obtener el stock de algún producto."""
    print("Iniciando prueba de conexión y búsqueda de stock...\n")
    url_bodegas = f"{API_BASE_URL}/api/Sale/GetStorages?itemsPerPage=100&pageNumber=1"
    print(f"Consultando bodegas en: {url_bodegas}")
    
    try:
        res_bodegas = requests.get(url_bodegas, headers=HEADERS)
        res_bodegas.raise_for_status()
        bodegas = res_bodegas.json()
        lista_bodegas = bodegas.get('storageList', []) if isinstance(bodegas, dict) else bodegas
        
        if not lista_bodegas: return
        bodega_id = lista_bodegas[0].get('id', lista_bodegas[0].get('code'))
        
        url_stock = f"{API_BASE_URL}/api/Sale/GetStorageStock?storageID={bodega_id}&itemsPerPage=5&pageNumber=1"
        res_stock = requests.get(url_stock, headers=HEADERS)
        res_stock.raise_for_status()
        productos = res_stock.json().get('productList', [])
        
        print("\n--- PRODUCTOS ENCONTRADOS (MUESTRA) ---")
        for p in productos[:5]:
            print(f"Producto Código: {p.get('productID', 'N/A')} | Stock Actual: {p.get('stock', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")

def buscar_stock_prueba_dos(producto_id="VLAD"):
    """Realiza una segunda prueba buscando un producto específico y mostrando su stock en todas las bodegas."""
    print(f"\n--- INICIANDO PRUEBA DOS ---")
    url_producto = f"{API_BASE_URL}/api/Sale/Getproducts?code={producto_id}&status=0&itemsPerPage=1&pageNumber=1"
    
    try:
        res = requests.get(url_producto, headers=HEADERS)
        res.raise_for_status()
        productos = res.json().get('productList', [])
        
        if not productos: return
        producto_encontrado = productos[0]
        detalles_stock = producto_encontrado.get('stockDetail', [])
        
        if detalles_stock:
            print("\n--- STOCK POR BODEGA ---")
            for detalle in detalles_stock:
                bodega_id = detalle.get('storageID', 'Desconocida')
                description = 'Sin descripción'
                for b_info in BODEGAS_INFO:
                    if b_info.get('code') == bodega_id:
                        description = b_info.get('description', 'Sin descripción')
                        break
                print(f"Bodega: {bodega_id} - {description} | Stock: {detalle.get('stock', 0)}")
    except Exception as e:
        print(f"Error: {e}")

def buscar_stock_prueba_tres(producto_id="VLAD"):
    """Prueba semi final 3: Verifica stock de un producto y envía correo si es menor a STOCK_MINIMO."""
    print(f"\n--- INICIANDO PRUEBA TRES (SEMI FINAL) ---")
    url_producto = f"{API_BASE_URL}/api/Sale/Getproducts?code={producto_id}&status=0&itemsPerPage=1&pageNumber=1"
    
    try:
        res = requests.get(url_producto, headers=HEADERS)
        res.raise_for_status()
        productos = res.json().get('productList', [])
        if not productos: return
        
        stock_total = productos[0].get('stock', 0)
        STOCK_MINIMO_TEST = 10
        if stock_total < STOCK_MINIMO_TEST:
            enviar_correo_alerta(producto_id, stock_total)
    except Exception as e:
        print(f"Error: {e}")

# ==========================================
# FASE FINAL
# ==========================================
def revision_fase_final():
    """Fase Final: Consulta hasta 1000 productos, compara con stock_minimo.json y envía un correo consolidado."""
    print("\n--- INICIANDO FASE FINAL ---")
    print("1. Cargando configuraciones de stock mínimo...")
    
    # Leer el archivo de stock mínimo
    ruta_json = os.path.join(os.path.dirname(__file__), "stock_minimo.json")
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            stock_minimo_data = json.load(f)
    except Exception as e:
        print(f"Error al leer stock_minimo.json: {e}")
        return
        
    # Convertir a un diccionario para búsqueda rápida (código -> stock mínimo)
    dict_stock_minimo = {item['code']: item['stock'] for item in stock_minimo_data}
    
    print("2. Consultando productos a la API de Defontana...")
    
    productos_bajo_stock = []
    page_number = 1
    total_evaluados = 0
    
    try:
        while True:
            print(f"-> Obteniendo página {page_number} (250 productos por página)...")
            url_productos = f"{API_BASE_URL}/api/Sale/Getproducts?status=1&itemsPerPage=250&pageNumber={page_number}"
            
            res = requests.get(url_productos, headers=HEADERS)
            res.raise_for_status()
            data = res.json()
            
            productos = data.get('productList', [])
            
            if productos == []:
                break # Si la página está vacía, no hay más productos
                
            for p in productos:
                # Filtro: Solo procesar si availableSale es true (o su equivalente)
                available = p.get('availableSale')
                if str(available).lower() not in ['true', 's', '1'] and available is not True:
                    continue
                    
                codigo = p.get('code', 'N/A')
                # Obtenemos externalCode, si es None o vacío usamos el código normal
                external_code = p.get('externalCode')
                if not external_code:
                    external_code = codigo
                    
                nombre = p.get('name', 'Sin nombre')
                stock_total = p.get('stock', 0)
                
                # Filtro: Solo evaluar los productos que estén definidos en stock_minimo.json
                if codigo not in dict_stock_minimo:
                    continue
                    
                minimo_configurado = dict_stock_minimo[codigo]
                
                # Validamos si está por debajo de su límite
                if stock_total < minimo_configurado:
                    productos_bajo_stock.append({
                        'code': codigo,
                        'external_code': external_code,
                        'name': nombre,
                        'stock': stock_total,
                        'minimo': minimo_configurado
                    })
                
                total_evaluados += 1
                
            page_number += 1
            
        print(f"\nSe evaluaron un total de {total_evaluados} productos disponibles para venta.")
        print(f"-> Se encontraron {len(productos_bajo_stock)} productos con stock bajo.")
        
        # 4. Enviar correo consolidado
        if productos_bajo_stock:
            print("4. Enviando correo consolidado con tabla HTML...")
            enviar_correo_alerta_multiple(productos_bajo_stock)
        else:
            print("4. Todos los productos evaluados tienen stock suficiente. No se requiere enviar alerta.")
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión o validación de la API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalle del error devuelto por la API: {e.response.text}")
    except Exception as e:
        print(f"Error inesperado procesando la fase final: {e}")

def tarea_programada():
    """Esta es la tarea que se programará en el cron/schedule."""
    revision_fase_final()

# ==========================================
# EJECUCIÓN DEL SCRIPT
# ==========================================
if __name__ == "__main__":
    # Ejecuta directamente la fase final
    revision_fase_final()

    # Si quisieras dejarlo corriendo constantemente con schedule en lugar de un cron de Linux/Windows:
    # hora_revision = "08:00"
    # schedule.every().day.at(hora_revision).do(tarea_programada)
    # print(f"Script iniciado. Esperando para revisar el stock a las {hora_revision} todos los días...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
