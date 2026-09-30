const DJUNGO_BACKEND_VERSION = "B2.1";

/**
 * Restituisce il foglio identificato dal suo sheetId.
 *
 * Non usa getActiveSheet().
 * Non usa getSheetByName().
 */
function djungoGetSheetById_(sheetId) {
  const id = Number(sheetId);

  if (!Number.isInteger(id) || id < 0) {
    throw new Error("Invalid sheetId: " + sheetId);
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const sheet = ss.getSheets().find(function (sh) {
    return sh.getSheetId() === id;
  });

  if (!sheet) {
    throw new Error(
      "Sheet not found for sheetId " + id +
      " in spreadsheet " + ss.getId()
    );
  }

  return sheet;
}


/**
 * Primo test B2.
 *
 * Legge un foglio ESPLICITAMENTE tramite sheetId
 * e restituisce solo informazioni diagnostiche.
 *
 * Non modifica nulla.
 */
function djungoTestPersistentRead(sheetId) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = djungoGetSheetById_(sheetId);

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();

  let headers = [];

  if (lastColumn > 0) {
    headers = sheet
      .getRange(1, 1, 1, lastColumn)
      .getValues()[0]
      .map(function (value) {
        return String(value == null ? "" : value).trim();
      });
  }

  return {
    ok: true,
    backendVersion: DJUNGO_BACKEND_VERSION,

    spreadsheetId: ss.getId(),

    sheetId: sheet.getSheetId(),
    sheetName: sheet.getName(),

    lastRow: lastRow,
    lastColumn: lastColumn,

    headers: headers
  };
}



/**
 * B2.2 — interpreta il routing tecnico ricevuto da Flask.
 *
 */
function djungoPersistentRequest_(p) {
  p = p || {};

  /*
   * 1. PARAMETRI DI ROUTING
   */
  const appSlug = String(p.appSlug || "").trim();
  const spreadsheetId = String(p.spreadsheetId || "").trim();
  const sheetId = Number(p.sheetId);
  const mode = String(p.mode || "meta").trim();

  /*
   * 2. VALIDAZIONE DEL ROUTING
   */
  if (!appSlug) {
    throw new Error("Missing appSlug");
  }

  if (!spreadsheetId) {
    throw new Error("Missing spreadsheetId");
  }

  if (!Number.isInteger(sheetId) || sheetId < 0) {
    throw new Error("Missing/invalid sheetId");
  }

  /*
   * 3. SPREADSHEET COLLEGATO AL GAS
   */
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  /*
   * 4. VERIFICA DELLO SPREADSHEET
   *
   * Flask determina il routing persistente.
   * Il GAS verifica che la richiesta sia destinata
   * allo Spreadsheet al quale è effettivamente collegato.
   */
  if (ss.getId() !== spreadsheetId) {
    throw new Error(
      "Spreadsheet mismatch. Expected " +
      ss.getId() +
      ", received " +
      spreadsheetId
    );
  }

  /*
   * 5. RISOLUZIONE DEL FOGLIO TRAMITE sheetId
   */
  const sheet = djungoGetSheetById_(sheetId);

  /*
   * 6A. META
   *
   * Restituisce informazioni diagnostiche sul backend
   * e sulla destinazione della richiesta.
   */
  if (mode === "meta") {
    return {
      ok: true,
      backendVersion: DJUNGO_BACKEND_VERSION,
      appSlug: appSlug,
      spreadsheetId: ss.getId(),
      sheetId: sheet.getSheetId(),
      sheetName: sheet.getName()
    };
  }

  /*
   * 6B. VIEW
   *
   * Restituisce un insieme di record del foglio.
   */
  if (mode === "view") {
    return djungoView_(sheet, p.limit);
  }

  /*
   * 6C. GET BY ID
   */
  if (mode === "getById") {
    const id = Number(p.id);

    if (!Number.isInteger(id) || id < 1) {
      throw new Error("Missing/invalid id");
    }

    return djungoGetById_(sheet, id);
  }

  /*
   * 6D. INSERT
   */
  if (mode === "insert") {
    return djungoInsert_(sheet, p);
  }

  /*
   * 6E. UPDATE
   */
  if (mode === "update") {
    const id = Number(p.id);

    if (!Number.isInteger(id) || id < 1) {
      throw new Error("Missing/invalid id");
    }

    return djungoUpdate_(sheet, id, p);
  }

  /*
   * 6F. DELETE
   */
  if (mode === "delete") {
    const id = Number(p.id);

    if (!Number.isInteger(id) || id < 1) {
      throw new Error("Missing/invalid id");
    }

    return djungoDelete_(sheet, id);
  }

  /*
   * 7. MODE NON SUPPORTATO
   */
  throw new Error("Unsupported persistent mode: " + mode);
}


function djungoView_(sheet, limit) {
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();

  if (lastCol < 1) {
    return {
      ok: true,
      headers: [],
      rows: []
    };
  }

  const headers = sheet
    .getRange(1, 1, 1, lastCol)
    .getValues()[0]
    .map(function (value) {
      return String(value == null ? "" : value).trim();
    });

  if (lastRow < 2) {
    return {
      ok: true,
      headers: headers,
      rows: []
    };
  }

  let requestedLimit = Number(limit);

  if (!Number.isInteger(requestedLimit) || requestedLimit < 1) {
    requestedLimit = 50;
  }

  requestedLimit = Math.min(requestedLimit, 500);

  const dataRows = lastRow - 1;
  const take = Math.min(requestedLimit, dataRows);
  const startRow = lastRow - take + 1;

  const rows = sheet
    .getRange(startRow, 1, take, lastCol)
    .getValues();

  return {
    ok: true,
    headers: headers,
    rows: rows
  };
}


/*********************************
 * LEVEL B2.3 — STABLE RECORD ID
 *********************************/

function djungoFindRowById_(sheet, id) {
  const targetId = Number(id);

  if (!Number.isInteger(targetId) || targetId < 1) {
    throw new Error("Invalid record ID: " + id);
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return 0;

  const ids = sheet
    .getRange(2, 1, lastRow - 1, 1)
    .getValues();

  for (let i = 0; i < ids.length; i++) {
    if (Number(ids[i][0]) === targetId) {
      return i + 2;
    }
  }

  return 0;
}


function djungoComputeNextId_(sheet) {
  const propertyKey = "DJUNGO_LAST_ID_" + sheet.getSheetId();
  const properties = PropertiesService.getDocumentProperties();

  const storedValue = Number(properties.getProperty(propertyKey));

  // Legge il massimo ID realmente presente nel foglio.
  const lastRow = sheet.getLastRow();
  let maxSheetId = 0;

  if (lastRow >= 2) {
    const ids = sheet
      .getRange(2, 1, lastRow - 1, 1)
      .getValues();

    ids.forEach(function (row) {
      const id = Number(row[0]);

      if (Number.isInteger(id) && id > maxSheetId) {
        maxSheetId = id;
      }
    });
  }

  /*
   * Il contatore persistente e il foglio vengono confrontati.
   * Questo consente anche di inizializzare B2 su fogli già esistenti.
   */
  const lastAssignedId = Math.max(
    Number.isInteger(storedValue) ? storedValue : 0,
    maxSheetId
  );

  return lastAssignedId + 1;
}



function djungoGetById_(sheet, id) {
  const row = djungoFindRowById_(sheet, id);

  if (!row) {
    return {
      ok: false,
      error: "ID not found",
      id: Number(id)
    };
  }

  const lastCol = sheet.getLastColumn();

  const headers = sheet
    .getRange(1, 1, 1, lastCol)
    .getValues()[0]
    .map(function (value) {
      return String(value || "").trim();
    });

  const values = sheet
    .getRange(row, 1, 1, lastCol)
    .getValues()[0];

  const record = {};

  headers.forEach(function (header, index) {
    record[header] = values[index];
  });

  return {
    ok: true,
    id: Number(id),
    row: row,
    record: record
  };
}



function djungoInsert_(sheet, data) {
  const lastCol = sheet.getLastColumn();

  const headers = sheet
    .getRange(1, 1, 1, lastCol)
    .getValues()[0]
    .map(function (value) {
      return String(value || "").trim();
    });

  if (headers.length < 1 || headers[0].toLowerCase() !== "id") {
    throw new Error("First column must be the stable ID column");
  }

  const normalizedData = djungoNormalizeDataKeys_(data);

  const id = djungoComputeNextId_(sheet);
  const rowNumber = sheet.getLastRow() + 1;

  const rowValues = [id];

  for (let i = 1; i < headers.length; i++) {
    const key = headers[i].toLowerCase();

    rowValues.push(
      Object.prototype.hasOwnProperty.call(normalizedData, key)
        ? normalizedData[key]
        : ""
    );
  }

  // Prima scriviamo realmente il record.
  sheet
    .getRange(rowNumber, 1, 1, rowValues.length)
    .setValues([rowValues]);

  // Solo dopo una scrittura riuscita l'ID viene considerato consumato.
  const propertyKey = "DJUNGO_LAST_ID_" + sheet.getSheetId();

  PropertiesService
    .getDocumentProperties()
    .setProperty(propertyKey, String(id));

  return {
    ok: true,
    id: id,
    insertedRow: rowNumber
  };
}

function djungoNormalizeDataKeys_(data) {
  const normalized = {};

  Object.keys(data || {}).forEach(function (key) {
    normalized[String(key).trim().toLowerCase()] = data[key];
  });

  return normalized;
}


function djungoDelete_(sheet, id) {
  const row = djungoFindRowById_(sheet, id);

  if (!row) {
    return {
      ok: false,
      error: "ID not found",
      id: Number(id)
    };
  }

  sheet.deleteRow(row);

  return {
    ok: true,
    id: Number(id),
    deletedRow: row
  };
}


function djungoUpdate_(sheet, id, data) {
  const row = djungoFindRowById_(sheet, id);

  if (!row) {
    return {
      ok: false,
      error: "ID not found",
      id: Number(id)
    };
  }

  const lastCol = sheet.getLastColumn();

  const headers = sheet
    .getRange(1, 1, 1, lastCol)
    .getValues()[0]
    .map(function (value) {
      return String(value || "").trim();
    });

  const normalizedData = djungoNormalizeDataKeys_(data);

  /*
   * Colonna 1 esclusa intenzionalmente:
   * l'ID è immutabile.
   */
  for (let col = 2; col <= lastCol; col++) {
    const key = headers[col - 1].toLowerCase();

    if (Object.prototype.hasOwnProperty.call(normalizedData, key)) {
      sheet.getRange(row, col).setValue(normalizedData[key]);
    }
  }

  return {
    ok: true,
    id: Number(id),
    updatedRow: row
  };
}
