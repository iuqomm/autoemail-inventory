/**
 * Stock Checker - Defontana API
 * Lee SKUs desde columna A, consulta stock por bodega, escribe en B y C.
 *
 * SETUP:
 * 1. Extensiones > Apps Script > pegar este código
 * 2. Configurar API_KEY abajo
 * 3. Insertar > Dibujo > forma > asignar macro "actualizarStock"
 *
 * ESTRUCTURA DE LA PLANILLA:
 *   Columna A: SKU del producto (desde fila 2)
 *   Columna B: Stock Uqomm (BODEGACENTRAL)
 *   Columna C: Stock Loginsa (BODEGA2)
 */

// ============================================================
// CONFIGURACIÓN
// ============================================================
const API_BASE_URL = "https://api.defontana.com";
const API_KEY = "TU_API_KEY_AQUI";

// Mapeo: storageID → índice de columna relativo a B (0 = B, 1 = C)
const BODEGAS = [
  { storageID: "BODEGACENTRAL", colOffset: 0, label: "Uqomm" },   // Col B
  { storageID: "BODEGA2", colOffset: 1, label: "Loginsa" }         // Col C
];

const MS_POR_PRODUCTO = 500; // estimado por llamada

// ============================================================
// FUNCIÓN PRINCIPAL (asignar al botón)
// ============================================================
function actualizarStock() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert("No hay datos. Agregá SKUs desde la fila 2, columna A.");
    return;
  }

  // Leer SKUs (columna A, fila 2 en adelante)
  const skus = sheet.getRange(2, 1, lastRow - 1, 1).getValues()
    .flat()
    .map(s => s ? String(s).trim() : "")
    .filter(s => s !== "");

  if (skus.length === 0) {
    SpreadsheetApp.getUi().alert("No se encontraron SKUs válidos en columna A.");
    return;
  }

  const ui = SpreadsheetApp.getUi();

  // Array de resultados: cada fila = [stockUqomm, stockLoginsa]
  const resultados = [];
  let errores = 0;

  for (let i = 0; i < skus.length; i++) {
    const sku = skus[i];
    const fila = new Array(BODEGAS.length).fill(0);

    try {
      const stockDetail = fetchProductStock(sku);

      if (!stockDetail || stockDetail.length === 0) {
        fila[0] = "No encontrado";
        fila[1] = "";
        errores++;
      } else {
        // Construir mapa storageID → stock
        const stockMap = {};
        stockDetail.forEach(d => {
          stockMap[d.storageID] = d.stock || 0;
        });

        // Llenar cada bodega
        for (let j = 0; j < BODEGAS.length; j++) {
          const bodega = BODEGAS[j];
          fila[j] = stockMap[bodega.storageID] !== undefined
            ? stockMap[bodega.storageID]
            : 0;
        }
      }
    } catch (e) {
      fila[0] = "Error";
      fila[1] = e.message;
      errores++;
    }

    resultados.push(fila);

    // Pausa entre llamadas
    Utilities.sleep(MS_POR_PRODUCTO);
  }

  // ESCRITURA ÚNICA: todo de una vez al sheet
  sheet.getRange(2, 2, resultados.length, BODEGAS.length).setValues(resultados);

  const tiempoEstimado = ((skus.length * MS_POR_PRODUCTO) / 1000).toFixed(0);
  ui.alert(
    "Actualización completa",
    `⏱️ Tiempo estimado: ~${tiempoEstimado}s\n✅ ${skus.length - errores} productos actualizados\n❌ ${errores} errores`,
    ui.ButtonSet.OK
  );
}

// ============================================================
// API CALL
// ============================================================
function fetchProductStock(sku) {
  const url = `${API_BASE_URL}/api/Sale/Getproducts?status=0&itemsPerPage=1&pageNumber=1&code=${encodeURIComponent(sku)}`;

  const response = UrlFetchApp.fetch(url, {
    method: "get",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json"
    },
    muteHttpExceptions: true
  });

  const statusCode = response.getResponseCode();
  if (statusCode !== 200) {
    throw new Error(`HTTP ${statusCode}`);
  }

  const data = JSON.parse(response.getContentText());
  const products = data.productList || [];

  if (products.length === 0) return null;

  return products[0].stockDetail || [];
}
