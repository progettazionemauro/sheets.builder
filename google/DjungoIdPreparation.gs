/**
 * DJUNGO — B0.3 ID PREPARATION
 * Anteprima in sola lettura.
 * Nessuna modifica al foglio.
 */

function djungoAnalyzeCurrentSheetIds() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();

  if (lastRow < 1 || lastColumn < 1) {
    return {
      status: 'missing',
      reason: 'empty_sheet',
      spreadsheetId: spreadsheet.getId(),
      sheetId: sheet.getSheetId(),
      sheetName: sheet.getName()
    };
  }

  const headers = sheet.getRange(1, 1, 1, lastColumn)
    .getValues()[0]
    .map(value => String(value == null ? '' : value).trim().toLowerCase());

  const idColumns = [];
  const dataColumns = [];

  headers.forEach((name, index) => {
    if (name) dataColumns.push(index);
    if (name === 'id') idColumns.push(index);
  });

  if (idColumns.length !== 1) {
    return {
      status: idColumns.length === 0 ? 'missing' : 'invalid',
      reason: idColumns.length === 0 ? 'missing_id_column' : 'multiple_id_columns',
      spreadsheetId: spreadsheet.getId(),
      sheetId: sheet.getSheetId(),
      sheetName: sheet.getName(),
      idColumns: idColumns.map(index => index + 1)
    };
  }

  const idIndex = idColumns[0];
  const values = sheet.getRange(1, 1, lastRow, lastColumn).getValues();
  const formulas = sheet.getRange(1, 1, lastRow, lastColumn).getFormulas();

  const occupiedRows = [];
  const missingRows = [];
  const invalidRows = [];
  const formulaRows = [];
  const staticRows = [];
  const proposedChanges = [];
  const duplicateMap = {};
  const seen = {};

  for (let index = 1; index < values.length; index++) {
    const rowValues = values[index];

    const occupied = dataColumns.some(col => {
      const value = rowValues[col];
      return value !== null && value !== '' &&
        String(value).trim() !== '';
    });

    if (!occupied) continue;

    const rowNumber = index + 1;
    occupiedRows.push(rowNumber);

    const value = rowValues[idIndex];
    const formula = formulas[index][idIndex];

    if (value === null || value === '' || String(value).trim() === '') {
      missingRows.push(rowNumber);
      continue;
    }

    const number = Number(value);

    if (!Number.isSafeInteger(number) || number < 1 ||
        (typeof value !== 'number' && !/^[0-9]+$/.test(String(value).trim()))) {
      invalidRows.push(rowNumber);
      continue;
    }

    const key = String(number);

    if (!seen[key]) seen[key] = [];
    seen[key].push(rowNumber);

    if (formula) {
      formulaRows.push(rowNumber);
      proposedChanges.push({
        row: rowNumber,
        column: idIndex + 1,
        currentValue: number,
        proposedValue: number,
        formula: formula
      });
    } else {
      staticRows.push(rowNumber);
    }
  }

  Object.keys(seen).forEach(id => {
    if (seen[id].length > 1) {
      duplicateMap[id] = seen[id];
    }
  });

  const duplicateIds = Object.keys(duplicateMap).map(Number)
    .sort((a, b) => a - b);

  let status = 'valid';

  if (missingRows.length || invalidRows.length || duplicateIds.length) {
    status = 'invalid';
  } else if (formulaRows.length) {
    status = 'formula_based';
  }

  const isolatedRows = [];

  for (let i = 1; i < occupiedRows.length; i++) {
    if (occupiedRows[i] - occupiedRows[i - 1] > 1) {
      isolatedRows.push(occupiedRows[i]);
    }
  }

  return {
    status: status,
    spreadsheetId: spreadsheet.getId(),
    spreadsheetName: spreadsheet.getName(),
    sheetId: sheet.getSheetId(),
    sheetName: sheet.getName(),
    idColumn: idIndex + 1,
    dataRows: occupiedRows.length,
    occupiedRows: occupiedRows,
    isolatedRows: isolatedRows,
    missingRows: missingRows,
    invalidRows: invalidRows,
    duplicateIds: duplicateIds,
    duplicateRows: duplicateMap,
    formulaRows: formulaRows,
    staticRows: staticRows,
    proposedChanges: proposedChanges
  };
}


/**
 * Test manuale: mostra il rapporto senza modificare il foglio.
 */
function testDjungoIdPreparation() {
  const report = djungoAnalyzeCurrentSheetIds();

  Logger.log(JSON.stringify(report, null, 2));

  const summary =
    'Stato: ' + report.status + '\n' +
    'Foglio: ' + report.sheetName + '\n' +
    'Righe occupate: ' + (report.dataRows || 0) + '\n' +
    'ID formula: ' + (report.formulaRows || []).length + '\n' +
    'ID mancanti: ' + (report.missingRows || []).length + '\n' +
    'ID invalidi: ' + (report.invalidRows || []).length + '\n' +
    'ID duplicati: ' + (report.duplicateIds || []).length + '\n' +
    'Righe isolate: ' + (report.isolatedRows || []).join(', ');

  SpreadsheetApp.getUi().alert(
    'Djungo — Anteprima ID',
    summary,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * B0.3 — Verifica che un'anteprima ID sia ancora attuale.
 * Nessuna scrittura.
 */
function djungoValidateIdPreparationSnapshot(snapshot) {
  if (!snapshot || !snapshot.spreadsheetId || !snapshot.sheetId) {
    throw new Error('Anteprima ID non valida.');
  }

  const current = djungoAnalyzeCurrentSheetIds();

  if (
    String(current.spreadsheetId) !== String(snapshot.spreadsheetId) ||
    String(current.sheetId) !== String(snapshot.sheetId)
  ) {
    throw new Error('Il foglio corrente non corrisponde all’anteprima.');
  }

  const fields = [
    'status',
    'idColumn',
    'dataRows',
    'occupiedRows',
    'missingRows',
    'invalidRows',
    'duplicateIds',
    'formulaRows',
    'staticRows',
    'proposedChanges'
  ];

  for (const field of fields) {
    if (JSON.stringify(current[field]) !== JSON.stringify(snapshot[field])) {
      throw new Error(
        'Il foglio è cambiato rispetto all’anteprima: ' + field
      );
    }
  }

  return {
    ok: true,
    spreadsheetId: current.spreadsheetId,
    sheetId: current.sheetId,
    proposedChanges: current.proposedChanges.length
  };
}


/**
 * Test B0.3 — analisi e verifica immediata.
 * Non modifica il foglio.
 */
function testDjungoIdPreparationSnapshot() {
  const snapshot = djungoAnalyzeCurrentSheetIds();
  const result = djungoValidateIdPreparationSnapshot(snapshot);

  Logger.log(JSON.stringify(result, null, 2));

  SpreadsheetApp.getUi().alert(
    'Djungo — Verifica anteprima',
    'Anteprima valida.\n' +
    'Modifiche proposte: ' + result.proposedChanges + '\n' +
    'Nessuna modifica effettuata.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

function testDjungoIdPreparationSnapshotLog() {
  const snapshot = djungoAnalyzeCurrentSheetIds();
  const result = djungoValidateIdPreparationSnapshot(snapshot);
  Logger.log(JSON.stringify(result, null, 2));
}

function djungoCreateSpreadsheetBackup() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const file = DriveApp.getFileById(spreadsheet.getId());

  const timestamp = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    'yyyyMMdd_HHmmss'
  );

  const backupName =
    spreadsheet.getName() +
    '_DJUNGO_BACKUP_' +
    timestamp;

  const backup = file.makeCopy(backupName);

  return {
    ok: true,
    originalSpreadsheetId: spreadsheet.getId(),
    backupId: backup.getId(),
    backupName: backup.getName()
  };
}

function testDjungoCreateSpreadsheetBackup() {
  const result = djungoCreateSpreadsheetBackup();
  Logger.log(JSON.stringify(result, null, 2));

  SpreadsheetApp.getUi().alert(
    'Djungo — Backup',
    'Backup creato correttamente.\n\n' +
    result.backupName,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * B0.3 — Snapshot completo del foglio.
 * Legge valori e formule senza effettuare scritture.
 */
function djungoCaptureSheetSnapshot() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();

  const lastRow = sheet.getLastRow();
  const lastColumn = sheet.getLastColumn();

  if (lastRow < 1 || lastColumn < 1) {
    throw new Error('Il foglio è vuoto.');
  }

  const range = sheet.getRange(1, 1, lastRow, lastColumn);

  return {
    spreadsheetId: spreadsheet.getId(),
    sheetId: sheet.getSheetId(),
    sheetName: sheet.getName(),
    lastRow: lastRow,
    lastColumn: lastColumn,
    values: range.getValues(),
    formulas: range.getFormulas()
  };
}

/**
 * Verifica che valori e formule siano identici allo snapshot.
 * Nessuna scrittura.
 */
function djungoValidateSheetSnapshot(snapshot) {
  if (!snapshot || !snapshot.spreadsheetId || !snapshot.sheetId) {
    throw new Error('Snapshot del foglio non valido.');
  }

  const current = djungoCaptureSheetSnapshot();

  const fields = [
    'spreadsheetId',
    'sheetId',
    'lastRow',
    'lastColumn',
    'values',
    'formulas'
  ];

  for (const field of fields) {
    if (JSON.stringify(current[field]) !== JSON.stringify(snapshot[field])) {
      throw new Error(
        'Il foglio è cambiato rispetto allo snapshot: ' + field
      );
    }
  }

  return {
    ok: true,
    spreadsheetId: current.spreadsheetId,
    sheetId: current.sheetId,
    lastRow: current.lastRow,
    lastColumn: current.lastColumn
  };
}

/**
 * Test B0.3 — acquisizione e verifica immediata.
 * Non modifica il foglio.
 */
function testDjungoSheetSnapshot() {
  const snapshot = djungoCaptureSheetSnapshot();
  const result = djungoValidateSheetSnapshot(snapshot);

  Logger.log(JSON.stringify(result, null, 2));
}
