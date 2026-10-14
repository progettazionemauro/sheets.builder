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

  // Legge tutte le righe successive all'intestazione.
  const allRows = sheet
    .getRange(2, 1, lastRow - 1, lastCol)
    .getValues();

  // Conserva soltanto le righe con un ID intero positivo.
  const validRows = allRows.filter(function (row) {
    const rawId = row[0];
    const id = Number(rawId);

    return rawId !== "" &&
      rawId !== null &&
      String(rawId).trim() !== "" &&
      Number.isInteger(id) &&
      id > 0;
  });

  // Applica il limite ai record validi, non alle righe fisiche.
  const rows = validRows.slice(-requestedLimit);

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

  // Individua la prima riga senza ID.
  const maxRows = sheet.getMaxRows();
  let rowNumber = maxRows + 1;

  if (maxRows >= 2) {
    const idValues = sheet
      .getRange(2, 1, maxRows - 1, 1)
      .getValues();

    const firstFreeIndex = idValues.findIndex(function (row) {
      return row[0] === "" || row[0] === null;
    });

    if (firstFreeIndex !== -1) {
      rowNumber = firstFreeIndex + 2;
    }
  }

  // Se tutte le righe sono occupate, espande la griglia.
  if (rowNumber > maxRows) {
  sheet.insertRowsAfter(maxRows, 1);

  if (maxRows >= 2) {
    const sourceRange = sheet.getRange(
      maxRows, 1, 1, lastCol
    );

    const targetRange = sheet.getRange(
      rowNumber, 1, 1, lastCol
    );

    // Copia formule, formattazione e convalide.
    sourceRange.copyTo(targetRange);

    // Elimina i valori statici copiati, preservando le formule.
    const formulas = targetRange.getFormulas()[0];

    for (let col = 1; col <= lastCol; col++) {
      if (formulas[col - 1] === "") {
        targetRange.getCell(1, col).clearContent();
      }
    }
  }
}
  const targetRange = sheet.getRange(rowNumber, 1, 1, lastCol);
  const existingValues = targetRange.getValues()[0];
  const existingFormulas = targetRange.getFormulas()[0];

  // Impedisce di sovrascrivere dati non associati a un ID.
  for (let i = 1; i < lastCol; i++) {
    if (
      existingFormulas[i] === "" &&
      existingValues[i] !== "" &&
      existingValues[i] !== null
    ) {
      throw new Error(
        "Row " + rowNumber +
        " contains data without a stable ID"
      );
    }
  }

  const rowValues = [id];

  for (let i = 1; i < headers.length; i++) {
    const key = headers[i].toLowerCase();

    if (existingFormulas[i] !== "") {
      // Mantiene la formula originale.
      rowValues.push(existingFormulas[i]);
    } else {
      rowValues.push(
        Object.prototype.hasOwnProperty.call(normalizedData, key)
          ? normalizedData[key]
          : ""
      );
    }
  }

  // Scrive il record preservando le formule delle colonne calcolate.
  targetRange.setValues([rowValues]);

  // Aggiorna il contatore soltanto dopo la scrittura.
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
  const updates = [];

  /*
   * B3.5 - FASE 1
   * Verifica tutti i campi prima di modificare il foglio.
   */
  for (let col = 2; col <= lastCol; col++) {
    const header = headers[col - 1];
    const key = header.toLowerCase();

    if (!Object.prototype.hasOwnProperty.call(normalizedData, key)) {
      continue;
    }

    const cell = sheet.getRange(row, col);
    const newValue = normalizedData[key];

    // Non sovrascrivere formule.
    if (cell.getFormula() !== "") {
      throw new Error(
        "UPDATE blocked: formula protected in column " + header
      );
    }

    const rule = cell.getDataValidation();

    if (rule !== null) {
      const type = rule.getCriteriaType();

      // B3.5: supporto alle convalide da intervallo.
      if (type !== SpreadsheetApp.DataValidationCriteria.VALUE_IN_RANGE) {
        throw new Error(
          "UPDATE blocked: unsupported validation in column " + header
        );
      }

      const allowedRange = rule.getCriteriaValues()[0];

      const allowedValues = allowedRange
        .getDisplayValues()
        .flat()
        .filter(function (value) {
          return value !== "";
        });

      // Un valore vuoto è consentito in questa prima versione.
      if (newValue !== "" && newValue !== null) {
        const valid = allowedValues.some(function (value) {
          return String(value) === String(newValue);
        });

        if (!valid) {
          throw new Error(
            "UPDATE blocked: invalid value for column " + header
          );
        }
      }
    }

    // Memorizza la modifica, senza ancora applicarla.
    updates.push({
      cell: cell,
      value: newValue
    });
  }

  /*
   * B3.5 - FASE 2
   * Tutti i controlli sono superati: applica le modifiche.
   */
  updates.forEach(function (update) {
    update.cell.setValue(update.value);
  });

  return {
    ok: true,
    id: Number(id),
    updatedRow: row,
    updatedFields: updates.length
  };
}


function testB32SwotView() {
  const sheet = djungoGetSheetById_(784597021);
  const result = djungoView_(sheet, 50);

  console.log("Scheda: " + sheet.getName());
  console.log("Record restituiti: " + result.rows.length);

  const ids = result.rows.map(function (row) {
    return row[0];
  });

  console.log("ID trovati: " + ids.join(", "));
}

function testB33InsertPosition() {
  const sheet = djungoGetSheetById_(784597021);

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  const candidate = sheet.getRange(17, 1, 1, 19);
  const idValues = sheet.getRange(2, 1, sheet.getMaxRows() - 1, 1).getValues();

const firstFreeIndex = idValues.findIndex(function (row) {
  return row[0] === "" || row[0] === null;
});

console.log("Prima riga candidata: " + (firstFreeIndex + 2));

console.log("Valori riga 17: " +
  JSON.stringify(candidate.getValues()[0]));

console.log("Formule riga 17: " +
  JSON.stringify(candidate.getFormulas()[0]));
  console.log("Righe fisiche totali: " + sheet.getMaxRows());

  console.log("Scheda: " + sheet.getName());
  console.log("Ultima riga con contenuto: " + lastRow);
  console.log("Ultima colonna con contenuto: " + lastCol);
  console.log("Riga prevista per INSERT: " + (lastRow + 1));
  console.log("ID A2:A17:", JSON.stringify(sheet.getRange(2, 1, 16, 1).getFormulas()));
  console.log("Riga 17 disponibile: " + candidate.getValues()[0].every(value => value === "" || value === null));
}

function testB33RealInsert() {
  const sheet = SpreadsheetApp
    .getActiveSpreadsheet()
    .getSheetByName("SWOT_B33_TEST");

  if (!sheet) {
    throw new Error("Scheda SWOT_B33_TEST non trovata");
  }

  const targetRow = 17;
  const lastCol = sheet.getLastColumn();

  const before = sheet.getRange(targetRow, 1, 1, lastCol);
  const formulasBefore = before.getFormulas()[0];
  const validationsBefore = before.getDataValidations()[0];

  // Protezione: il test non deve sovrascrivere un record esistente.
  if (before.getValues()[0][0] !== "") {
    throw new Error("Riga 17 già occupata: test annullato");
  }

  const data = {
  "Anno": 2025,
  "Contesto": "QUALITÀ E PROCESSI",
  "Attività": "TEST B3.3 - Inserimento Djungo",
  "Parti interessate": "CLIENTI",
  "Obiettivo (Ante)": "Verifica ID statico, formule e convalide"
};

  const result = djungoInsert_(sheet, data);

  const insertedRow = result.insertedRow;
  const after = sheet.getRange(insertedRow, 1, 1, lastCol);
  const formulasAfter = after.getFormulas()[0];
  const validationsAfter = after.getDataValidations()[0];

  const formulaColumns = [8, 11, 16, 17];

  const formulasPreserved = formulaColumns.every(function (i) {
    return formulasBefore[i] === formulasAfter[i];
  });

  const validationsPreserved = validationsBefore.every(function (rule, i) {
    return Boolean(rule) === Boolean(validationsAfter[i]);
  });

  console.log("=== TEST B3.3 ===");
  console.log("ID assegnato: " + result.id);
  console.log("Riga inserita: " + insertedRow);
  console.log("Contesto: " + after.getValues()[0][2]);
  console.log("Formule conservate: " + formulasPreserved);
  console.log("Convalide conservate: " + validationsPreserved);

  if (
    insertedRow !== 17 ||
    !formulasPreserved ||
    !validationsPreserved
  ) {
    throw new Error("TEST B3.3 NON SUPERATO");
  }

  console.log("TEST B3.3 SUPERATO");
}

function testB33Validation() {
  const sheet = SpreadsheetApp
    .getActiveSpreadsheet()
    .getSheetByName("SWOT_B33_TEST");

  const rule = sheet.getRange("C17").getDataValidation();

  if (!rule) {
    console.log("Nessuna convalida in C17");
    return;
  }

  console.log("Tipo: " + rule.getCriteriaType());
  console.log("Valori non validi ammessi: " + rule.getAllowInvalid());

  try {
    const criteria = rule.getCriteriaValues();

    console.log("Numero parametri: " + criteria.length);

    const sourceRange = criteria[0];

    console.log("Tipo parametro: " + typeof sourceRange);
    console.log("Foglio sorgente: " + sourceRange.getSheet().getName());
    console.log("Intervallo: " + sourceRange.getA1Notation());
    console.log("Valori: " + JSON.stringify(sourceRange.getDisplayValues()));

  } catch (error) {
    console.log("Errore riferimento convalida: " + error.message);
  }
}

function testB34RowExpansion() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName("SWOT_B33_TEST");

  if (!source) {
    throw new Error("SWOT_B33_TEST non trovato");
  }

  const testName = "SWOT_B34_EXPANSION_TEST";

  if (ss.getSheetByName(testName)) {
    throw new Error("Il foglio di test esiste già");
  }

  const sheet = source.copyTo(ss).setName(testName);

  const lastRow = sheet.getMaxRows();
  const lastCol = sheet.getLastColumn();

  const original = sheet.getRange(lastRow, 1, 1, lastCol);

  const formulasBefore = original.getFormulas()[0];
  const validationsBefore = original.getDataValidations()[0];

  sheet.insertRowsAfter(lastRow, 1);

  const newRow = sheet.getRange(lastRow + 1, 1, 1, lastCol);

  const formulasAfter = newRow.getFormulas()[0];
  const validationsAfter = newRow.getDataValidations()[0];

  console.log("=== B3.4 ESPANSIONE ===");
  console.log("Ultima riga originale: " + lastRow);
  console.log("Nuova riga: " + (lastRow + 1));

  console.log(
    "Formule originali: " +
    formulasBefore.filter(Boolean).length
  );

  console.log(
    "Formule nuova riga: " +
    formulasAfter.filter(Boolean).length
  );

  console.log(
    "Convalide originali: " +
    validationsBefore.filter(Boolean).length
  );

  console.log(
    "Convalide nuova riga: " +
    validationsAfter.filter(Boolean).length
  );
}
function testB34InsertWithExpansion() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName("SWOT_B34_EXPANSION_TEST");
  const testName = "SWOT_B34_INSERT_TEST";

  if (!source) {
    throw new Error("Foglio sorgente non trovato");
  }

  if (ss.getSheetByName(testName)) {
    throw new Error("Foglio di test già esistente");
  }

  // Crea una copia isolata per il collaudo.
  const sheet = source.copyTo(ss).setName(testName);

  const lastCol = sheet.getLastColumn();

  // Conserva intestazioni e una riga modello.
  const maxRows = sheet.getMaxRows();

  if (maxRows > 2) {
    sheet.deleteRows(3, maxRows - 2);
  }

  // Prepara la riga 2 come modello senza dati statici.
  const modelRange = sheet.getRange(2, 1, 1, lastCol);
  const formulas = modelRange.getFormulas()[0];

  for (let col = 1; col <= lastCol; col++) {
    if (formulas[col - 1] === "") {
      modelRange.getCell(1, col).clearContent();
    }
  }

  // Occupa la riga 2 per obbligare Djungo a espandere.
  sheet.getRange("A2").setValue(1);

  const result = djungoInsert_(sheet, {});

  const insertedRow = result.insertedRow;
  const newRange = sheet.getRange(insertedRow, 1, 1, lastCol);

  const formulasNew = newRange.getFormulas()[0];
  const validationsNew = newRange.getDataValidations()[0];

  console.log("=== B3.4 TEST INSERIMENTO ===");
  console.log("ID assegnato: " + result.id);
  console.log("Riga inserita: " + insertedRow);
  console.log("Formule nuova riga: " + formulasNew.filter(Boolean).length);
  console.log("Convalide nuova riga: " + validationsNew.filter(Boolean).length);

  if (insertedRow !== 3) {
    throw new Error("Espansione non avvenuta alla riga attesa");
  }

  console.log("TEST B3.4 COMPLETATO");
}

function testB34VerifyFormulas() {
  const sheet = SpreadsheetApp
    .getActiveSpreadsheet()
    .getSheetByName("SWOT_B34_INSERT_TEST");

  if (!sheet) {
    throw new Error("Foglio di test non trovato");
  }

  const lastCol = sheet.getLastColumn();

  const source = sheet.getRange(2, 1, 1, lastCol);
  const target = sheet.getRange(3, 1, 1, lastCol);

  const sourceFormulas = source.getFormulasR1C1()[0];
  const targetFormulas = target.getFormulasR1C1()[0];

  let differences = 0;

  for (let i = 0; i < lastCol; i++) {
    if (sourceFormulas[i] !== targetFormulas[i]) {
      differences++;

      console.log(
        "Differenza colonna " + (i + 1) +
        ": origine=" + sourceFormulas[i] +
        " | destinazione=" + targetFormulas[i]
      );
    }
  }

  console.log("=== VERIFICA FORMULE B3.4 ===");
  console.log("Differenze: " + differences);

  if (differences === 0) {
    console.log("FORMULE COERENTI");
  } else {
    console.log("FORMULE DA ESAMINARE");
  }
}

function testB35InspectValidations() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("SWOT_B34_INSERT_TEST");

  if (!sheet) {
    throw new Error("Foglio di test non trovato");
  }

  const row = 2;
  const lastCol = sheet.getLastColumn();

  console.log("=== B3.5 ANALISI CONVALIDE ===");

  for (let col = 1; col <= lastCol; col++) {
    const cell = sheet.getRange(row, col);
    const rule = cell.getDataValidation();

    if (rule !== null) {
      const criterion = rule.getCriteriaType();
      const values = rule.getCriteriaValues();

      console.log(
        "Colonna " + col +
        " | Intestazione: " + sheet.getRange(1, col).getValue() +
        " | Criterio: " + criterion +
        " | Parametri: " + values.map(function (value) {
          if (value && typeof value.getA1Notation === "function") {
            return value.getSheet().getName() +
              "!" + value.getA1Notation();
          }
          return String(value);
        }).join(", ") +
        " | Rifiuta input non valido: " + !rule.getAllowInvalid()
      );
    }
  }

  console.log("=== FINE ANALISI B3.5 ===");
}

function testB35ProtectedUpdate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName("SWOT_B34_INSERT_TEST");

  if (!source) {
    throw new Error("Foglio sorgente di test non trovato");
  }

  // Copia isolata: nessuna modifica al foglio originale.
  const sheet = source.copyTo(ss);
  sheet.setName("SWOT_B35_UPDATE_TEST_" + Date.now());

  const id = Number(sheet.getRange("A2").getValue());

  if (!Number.isInteger(id) || id <= 0) {
    throw new Error("ID di test non valido");
  }

  // Ricava un valore ammesso dalla convalida di C2.
  const rule = sheet.getRange("C2").getDataValidation();

  if (
    !rule ||
    rule.getCriteriaType() !==
      SpreadsheetApp.DataValidationCriteria.VALUE_IN_RANGE
  ) {
    throw new Error("Convalida C2 non disponibile");
  }

  const allowed = rule.getCriteriaValues()[0]
    .getDisplayValues()
    .flat()
    .filter(function (value) {
      return value !== "";
    });

  if (allowed.length === 0) {
    throw new Error("Nessun valore ammesso per C2");
  }

  const validValue = allowed[0];
  const invalidValue = "__DJUNGO_INVALID_B35__";

  const assert = function (condition, message) {
    if (!condition) {
      throw new Error("TEST FALLITO: " + message);
    }
  };

  console.log("=== B3.5 UPDATE PROTETTO ===");
  console.log("Foglio isolato: " + sheet.getName());
  console.log("ID: " + id);

  // TEST 1: aggiornamento valido.
  const validResult = djungoUpdate_(sheet, id, {
    "Contesto": validValue
  });

  assert(validResult.ok === true, "UPDATE valido non riuscito");
  assert(
    String(sheet.getRange("C2").getDisplayValue()) === validValue,
    "Valore valido non scritto"
  );

  console.log("TEST 1 OK: valore ammesso accettato");

  // TEST 2: aggiornamento non valido.
  const beforeInvalid = sheet.getRange("C2").getValue();
  let rejected = false;

  try {
    djungoUpdate_(sheet, id, {
      "Contesto": invalidValue
    });
  } catch (error) {
    rejected = true;
    console.log("Rifiuto previsto: " + error.message);
  }

  assert(rejected, "Valore non ammesso accettato");
  assert(
    sheet.getRange("C2").getValue() === beforeInvalid,
    "C2 modificata dopo rifiuto"
  );

  console.log("TEST 2 OK: valore non ammesso rifiutato");

  // TEST 3: nessun aggiornamento parziale.
  const beforeD = sheet.getRange("D2").getValue();
  const beforeC = sheet.getRange("C2").getValue();

  rejected = false;

  try {
    djungoUpdate_(sheet, id, {
      "Attività": "__DJUNGO_PARTIAL_TEST__",
      "Contesto": invalidValue
    });
  } catch (error) {
    rejected = true;
  }

  assert(rejected, "Richiesta mista non rifiutata");
  assert(
    sheet.getRange("D2").getValue() === beforeD,
    "D2 modificata nonostante il rifiuto"
  );
  assert(
    sheet.getRange("C2").getValue() === beforeC,
    "C2 modificata nonostante il rifiuto"
  );

  console.log("TEST 3 OK: nessuna modifica parziale");

  // TEST 4: protezione delle formule.
  const lastCol = sheet.getLastColumn();
  const formulas = sheet.getRange(2, 2, 1, lastCol - 1)
    .getFormulas()[0];

  const formulaIndex = formulas.findIndex(function (value) {
    return value !== "";
  });

  assert(formulaIndex >= 0, "Nessuna formula disponibile nella riga 2");

  const formulaCol = formulaIndex + 2;
  const formulaHeader = String(
    sheet.getRange(1, formulaCol).getValue()
  ).trim();

  const originalFormula = sheet.getRange(2, formulaCol).getFormula();

  rejected = false;

  try {
    const payload = {};
    payload[formulaHeader] = "__DJUNGO_FORMULA_TEST__";
    djungoUpdate_(sheet, id, payload);
  } catch (error) {
    rejected = true;
    console.log("Protezione formula: " + error.message);
  }

  assert(rejected, "Sovrascrittura formula accettata");
  assert(
    sheet.getRange(2, formulaCol).getFormula() === originalFormula,
    "Formula originale modificata"
  );

  console.log(
    "TEST 4 OK: formula protetta in colonna " + formulaCol
  );

  console.log("=== B3.5: TUTTI I TEST SUPERATI ===");
}

function testB36DeleteIntegrity() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName("SWOT_B34_INSERT_TEST");

  if (!source) {
    throw new Error("Foglio sorgente non trovato");
  }

  // Copia isolata, senza modificare il foglio originale.
  const sheet = source.copyTo(ss);
  sheet.setName("SWOT_B36_DELETE_TEST_" + Date.now());

  const idToDelete = Number(sheet.getRange("A2").getValue());
  const survivingId = Number(sheet.getRange("A3").getValue());

  if (
    !Number.isInteger(idToDelete) ||
    !Number.isInteger(survivingId) ||
    idToDelete === survivingId
  ) {
    throw new Error("ID di test non validi");
  }

  const survivingRowBefore = djungoFindRowById_(sheet, survivingId);
  const lastCol = sheet.getLastColumn();

  const formulasBefore = sheet
    .getRange(survivingRowBefore, 1, 1, lastCol)
    .getFormulasR1C1()[0];

  const validationsBefore = sheet
    .getRange(survivingRowBefore, 1, 1, lastCol)
    .getDataValidations()[0]
    .map(function (rule) {
      return rule ? String(rule.getCriteriaType()) : "";
    });

  console.log("=== B3.6 DELETE INTEGRITY ===");

  const result = djungoDelete_(sheet, idToDelete);

  if (!result.ok) {
    throw new Error("DELETE non riuscito");
  }
if (djungoFindRowById_(sheet, idToDelete)) {
  throw new Error("ID eliminato ancora presente");
}

  const survivingRowAfter = djungoFindRowById_(sheet, survivingId);

  if (!survivingRowAfter) {
    throw new Error("Record superstite non trovato");
  }

  if (survivingRowAfter !== survivingRowBefore - 1) {
    throw new Error("Spostamento fisico inatteso");
  }

  const formulasAfter = sheet
    .getRange(survivingRowAfter, 1, 1, lastCol)
    .getFormulasR1C1()[0];

  const validationsAfter = sheet
    .getRange(survivingRowAfter, 1, 1, lastCol)
    .getDataValidations()[0]
    .map(function (rule) {
      return rule ? String(rule.getCriteriaType()) : "";
    });

  if (JSON.stringify(formulasBefore) !== JSON.stringify(formulasAfter)) {
    throw new Error("Formule R1C1 alterate");
  }

  if (JSON.stringify(validationsBefore) !== JSON.stringify(validationsAfter)) {
    throw new Error("Tipologie di convalida alterate");
  }

  console.log("TEST 1 OK: record eliminato");
  console.log("TEST 2 OK: ID superstite invariato");
  console.log("TEST 3 OK: spostamento fisico corretto");
  console.log("TEST 4 OK: formule R1C1 conservate");
  console.log("TEST 5 OK: tipologie di convalida conservate");
  console.log("=== B3.6 TEST SUPERATO ===");
}

function testB37CrudIntegration() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName("SWOT_B34_INSERT_TEST");

  if (!source) {
    throw new Error("Foglio sorgente non trovato");
  }

  // Ogni esecuzione utilizza una copia isolata.
  const sheet = source.copyTo(ss);
  sheet.setName("SWOT_B37_CRUD_TEST_" + Date.now());

  const assert = function(condition, message) {
    if (!condition) {
      throw new Error("B3.7 FAILED: " + message);
    }
  };

  const propertyKey = "DJUNGO_LAST_ID_" + sheet.getSheetId();

  const originalId = Number(sheet.getRange("A2").getValue());
  const originalRecord = djungoGetById_(sheet, originalId);

  assert(originalRecord.ok, "Record originale non trovato");

  console.log("=== B3.7 CRUD INTEGRATION ===");

  // TEST 1 - INSERT
  const inserted = djungoInsert_(sheet, {
    "Attività": "B37_INSERT_TEST"
  });

  assert(inserted.ok, "INSERT fallito");

  const firstId = inserted.id;

  assert(
    firstId > originalId,
    "Nuovo ID non progressivo rispetto al record originale"
  );

  const created = djungoGetById_(sheet, firstId);

  assert(created.ok, "GET del record inserito fallito");
  assert(
    created.record["Attività"] === "B37_INSERT_TEST",
    "Valore INSERT non corretto"
  );

  console.log("TEST 1 OK: INSERT + GET, ID " + firstId);

  // TEST 2 - UPDATE
  const updated = djungoUpdate_(sheet, firstId, {
    "Attività": "B37_UPDATE_TEST"
  });

  assert(updated.ok, "UPDATE fallito");

  const afterUpdate = djungoGetById_(sheet, firstId);

  assert(
    afterUpdate.record["Attività"] === "B37_UPDATE_TEST",
    "UPDATE non persistito"
  );

  console.log("TEST 2 OK: UPDATE + GET");

  // TEST 3 - DELETE
  const deleted = djungoDelete_(sheet, firstId);

  assert(deleted.ok, "DELETE fallito");

  const afterDelete = djungoGetById_(sheet, firstId);

  assert(
    afterDelete.ok === false,
    "Record eliminato ancora accessibile"
  );

  console.log("TEST 3 OK: DELETE + GET");

  // TEST 4 - Integrità del record superstite
  const surviving = djungoGetById_(sheet, originalId);

  assert(surviving.ok, "Record originale scomparso");

  assert(
    surviving.record["Attività"] ===
      originalRecord.record["Attività"],
    "Record originale modificato"
  );

  console.log("TEST 4 OK: record superstite conservato");

  // TEST 5 - Nuovo INSERT dopo DELETE
  const insertedAgain = djungoInsert_(sheet, {
    "Attività": "B37_SECOND_INSERT"
  });

  assert(insertedAgain.ok, "Secondo INSERT fallito");

  assert(
    insertedAgain.id > firstId,
    "ID eliminato riutilizzato"
  );

  assert(
    djungoGetById_(sheet, insertedAgain.id).ok,
    "Secondo record non recuperabile"
  );

  console.log(
    "TEST 5 OK: nuovo ID " + insertedAgain.id +
    " > ID eliminato " + firstId
  );

  // TEST 6 - Contatore persistente
  const storedId = Number(
    PropertiesService
      .getDocumentProperties()
      .getProperty(propertyKey)
  );

  assert(
    storedId === insertedAgain.id,
    "Contatore persistente non aggiornato"
  );

  console.log("TEST 6 OK: contatore persistente coerente");

  console.log("=== B3.7: TUTTI I TEST SUPERATI ===");
  console.log("Foglio test: " + sheet.getName());
}