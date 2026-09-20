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
 * Per ora è una funzione interna/testabile:
 * non sostituisce ancora doGet().
 */
function djungoPersistentRequest_(p) {
  p = p || {};

  const appSlug = String(p.appSlug || "").trim();
  const spreadsheetId = String(p.spreadsheetId || "").trim();
  const sheetId = Number(p.sheetId);

  if (!appSlug) {
    throw new Error("Missing appSlug");
  }

  if (!spreadsheetId) {
    throw new Error("Missing spreadsheetId");
  }

  if (!Number.isInteger(sheetId) || sheetId < 0) {
    throw new Error("Missing/invalid sheetId");
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();

  /*
   * Protezione importante:
   * il backend accetta soltanto richieste destinate
   * allo Spreadsheet al quale questo GAS è collegato.
   */
  if (ss.getId() !== spreadsheetId) {
    throw new Error(
      "Spreadsheet mismatch. Expected " +
      ss.getId() +
      ", received " +
      spreadsheetId
    );
  }

  const sheet = djungoGetSheetById_(sheetId);

  return {
    ok: true,
    backendVersion: DJUNGO_BACKEND_VERSION,
    appSlug: appSlug,
    spreadsheetId: ss.getId(),
    sheetId: sheet.getSheetId(),
    sheetName: sheet.getName()
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

  const id = djungoComputeNextId_(sheet);
  const rowNumber = sheet.getLastRow() + 1;

  const rowValues = [id];

  for (let i = 1; i < headers.length; i++) {
    const header = headers[i];

    rowValues.push(
      Object.prototype.hasOwnProperty.call(data, header)
        ? data[header]
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

  /*
   * Colonna 1 esclusa intenzionalmente:
   * l'ID è immutabile.
   */
  for (let col = 2; col <= lastCol; col++) {
    const header = headers[col - 1];

    if (Object.prototype.hasOwnProperty.call(data, header)) {
      sheet.getRange(row, col).setValue(data[header]);
    }
  }

  return {
    ok: true,
    id: Number(id),
    updatedRow: row
  };
}
