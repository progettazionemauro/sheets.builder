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
 * Test manuale temporaneo B2.1.
 *
 * volcano_db:
 * sheetId = 843771997
 */
function TEST_djungoPersistentVolcano() {
  const result = djungoTestPersistentRead(843771997);

  Logger.log(JSON.stringify(result, null, 2));

  return result;
}

function TEST_djungoPersistentRS101() {
  const result = djungoTestPersistentRead(977951306);

  Logger.log(JSON.stringify(result, null, 2));

  return result;
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


/**
 * Test B2.2 — simula esattamente il routing
 * che Flask invierà per volcano-db.
 */
function TEST_djungoPersistentRoutingVolcano() {
  const result = djungoPersistentRequest_({
    appSlug: "volcano-db",
    spreadsheetId: "1W9GWokNp6PSsPNCU35lMx2AAVeFvBqirw22ABT7_cUU",
    sheetId: "843771997"
  });

  Logger.log(JSON.stringify(result, null, 2));

  return result;
}