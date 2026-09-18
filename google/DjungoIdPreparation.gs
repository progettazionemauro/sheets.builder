/**
 * DJUNGO — B0.3 ID PREPARATION
 * Anteprima in sola lettura.
 * Nessuna modifica al foglio.
 */

function djungoAnalyzeCurrentSheetIds(targetSheetId) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();

  let sheet;

  if (targetSheetId !== undefined && targetSheetId !== null) {
    const numericSheetId = Number(targetSheetId);

    sheet = spreadsheet.getSheets().find(
      candidate => candidate.getSheetId() === numericSheetId
    );

    if (!sheet) {
      throw new Error(
        'Foglio Djungo non trovato. sheetId=' + targetSheetId
      );
    }
  } else {
    sheet = spreadsheet.getActiveSheet();
  }

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
  const result = {
    status: idColumns.length === 0 ? 'missing' : 'invalid',
    reason: idColumns.length === 0 ? 'missing_id_column' : 'multiple_id_columns',
    spreadsheetId: spreadsheet.getId(),
    spreadsheetName: spreadsheet.getName(),
    sheetId: sheet.getSheetId(),
    sheetName: sheet.getName(),
    idColumns: idColumns.map(index => index + 1)
  };

  if (idColumns.length === 0) {
    const values = sheet.getRange(1, 1, lastRow, lastColumn).getValues();
    const occupiedRows = [];

    for (let index = 1; index < values.length; index++) {
      const occupied = dataColumns.some(col => {
        const value = values[index][col];
        return value !== null &&
          value !== '' &&
          String(value).trim() !== '';
      });

      if (occupied) {
        occupiedRows.push(index + 1);
      }
    }

   const proposedChanges = occupiedRows.map((rowNumber, index) => ({
    row: rowNumber,
  proposedId: index + 1
  }));

  result.dataRows = occupiedRows.length;
  result.occupiedRows = occupiedRows;
  result.proposedAction = 'create_static_id_column';
  result.proposedIdColumn = 1;
  result.proposedIdHeader = 'ID';
  result.proposedChanges = proposedChanges;
  }

  return result;
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

  const validIds = Object.keys(seen)
  .map(Number)
  .sort((a, b) => a - b);

const maxExistingId = validIds.length
  ? validIds[validIds.length - 1]
  : 0;

const proposedMissingIdChanges = missingRows.map(
  (rowNumber, index) => ({
    row: rowNumber,
    proposedId: maxExistingId + index + 1
  })
);
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
    proposedChanges: proposedChanges,
    maxExistingId: maxExistingId,
proposedMissingIdChanges: proposedMissingIdChanges
  };
}

function testDjungoIdPreparationSnapshotLog() {
  const snapshot = djungoAnalyzeCurrentSheetIds();
  const result = djungoValidateIdPreparationSnapshot(snapshot);
  Logger.log(JSON.stringify(result, null, 2));
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

  const current = djungoAnalyzeCurrentSheetIds(snapshot.sheetId);

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
function djungoCaptureSheetSnapshot(targetSheetId) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();

  let sheet;

  if (targetSheetId !== undefined && targetSheetId !== null) {
    const numericSheetId = Number(targetSheetId);

    sheet = spreadsheet.getSheets().find(
      candidate => candidate.getSheetId() === numericSheetId
    );

    if (!sheet) {
      throw new Error(
        'Foglio Djungo non trovato. sheetId=' + targetSheetId
      );
    }
  } else {
    sheet = spreadsheet.getActiveSheet();
  }

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

  const current = djungoCaptureSheetSnapshot(snapshot.sheetId);

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

function djungoApplyStaticIds(snapshot) {
  if (!snapshot) {
    throw new Error('Snapshot mancante.');
  }

  const validation = djungoValidateIdPreparationSnapshot(snapshot);

  if (!validation.ok) {
    throw new Error('Snapshot non valido.');
  }

  const report = djungoAnalyzeCurrentSheetIds(snapshot.sheetId);

  if (report.status !== 'formula_based') {
    throw new Error(
      'La migrazione richiede uno stato formula_based. Stato attuale: ' +
      report.status
    );
  }

  if (
    report.missingRows.length ||
    report.invalidRows.length ||
    report.duplicateIds.length
  ) {
    throw new Error(
      'Sono presenti anomalie negli ID. Migrazione interrotta.'
    );
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();

  if (String(spreadsheet.getId()) !== String(snapshot.spreadsheetId)) {
    throw new Error(
      'Lo Spreadsheet corrente non corrisponde allo snapshot.'
    );
  }

  const targetSheetId = Number(snapshot.sheetId);

  const sheet = spreadsheet.getSheets().find(
    candidate => candidate.getSheetId() === targetSheetId
  );

  if (!sheet) {
    throw new Error(
      'Foglio target non trovato. sheetId=' + snapshot.sheetId
    );
  }

  const changes = report.proposedChanges || [];

  if (!changes.length) {
    throw new Error(
      'Nessun ID a formula da convertire.'
    );
  }

  /*
   * PRECHECK
   * Prima di effettuare qualsiasi scrittura verifichiamo
   * nuovamente tutte le celle interessate.
   */
  changes.forEach(change => {
    const cell = sheet.getRange(change.row, change.column);

    const currentFormula = cell.getFormula();
    const currentValue = cell.getValue();

    if (currentFormula !== change.formula) {
      throw new Error(
        'Formula ID cambiata alla riga ' + change.row +
        '. Migrazione interrotta.'
      );
    }

    if (Number(currentValue) !== Number(change.currentValue)) {
      throw new Error(
        'Valore ID cambiato alla riga ' + change.row +
        '. Migrazione interrotta.'
      );
    }
  });

  /*
   * SCRITTURA
   * Soltanto dopo che TUTTE le celle hanno superato
   * il precheck convertiamo formula -> valore statico.
   */
  changes.forEach(change => {
    sheet
      .getRange(change.row, change.column)
      .setValue(change.proposedValue);
  });

  SpreadsheetApp.flush();

  /*
   * POSTCHECK
   * Analizziamo esplicitamente lo stesso foglio.
   */
  const after = djungoAnalyzeCurrentSheetIds(snapshot.sheetId);

  if (after.status !== 'valid') {
    throw new Error(
      'Verifica finale fallita. Stato dopo migrazione: ' +
      after.status
    );
  }

  if (after.formulaRows.length !== 0) {
    throw new Error(
      'Verifica finale fallita: risultano ancora ID a formula.'
    );
  }

  return {
    ok: true,
    converted: changes.length,
    spreadsheetId: spreadsheet.getId(),
    sheetId: sheet.getSheetId(),
    sheetName: sheet.getName(),
    statusAfter: after.status,
    formulaRowsAfter: after.formulaRows.length
  };
}


/**
 * B0.5 — Crea una colonna ID statica quando il foglio ne è privo.
 *
 * Richiede:
 * - piano ID precedentemente analizzato;
 * - snapshot completo precedentemente acquisito;
 * - foglio ancora invariato.
 *
 * Inserisce ID come prima colonna e assegna valori statici
 * esclusivamente alle righe occupate individuate dal piano.
 */
function djungoApplyMissingIdColumn(idPlan, sheetSnapshot) {
  if (!idPlan || !sheetSnapshot) {
    throw new Error('Piano ID o snapshot mancanti.');
  }

  if (
    idPlan.status !== 'missing' ||
    idPlan.reason !== 'missing_id_column'
  ) {
    throw new Error(
      'Migrazione non consentita: stato ID non compatibile.'
    );
  }

  if (
    idPlan.spreadsheetId !== sheetSnapshot.spreadsheetId ||
    Number(idPlan.sheetId) !== Number(sheetSnapshot.sheetId)
  ) {
    throw new Error(
      'Piano ID e snapshot appartengono a fogli differenti.'
    );
  }

  // Il foglio deve essere ancora identico allo snapshot.
  djungoValidateSheetSnapshot(sheetSnapshot);

  // Anche il piano ID deve essere ancora identico.
  const currentPlan = djungoAnalyzeCurrentSheetIds(idPlan.sheetId);

  if (JSON.stringify(currentPlan) !== JSON.stringify(idPlan)) {
    throw new Error(
      'Il piano ID è cambiato prima della migrazione.'
    );
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();

  if (spreadsheet.getId() !== idPlan.spreadsheetId) {
    throw new Error('Spreadsheet diverso da quello analizzato.');
  }

  const sheet = spreadsheet.getSheets().find(
    candidate => candidate.getSheetId() === Number(idPlan.sheetId)
  );

  if (!sheet) {
    throw new Error(
      'Foglio Djungo non trovato. sheetId=' + idPlan.sheetId
    );
  }

  const changes = idPlan.proposedChanges || [];

  if (!changes.length) {
    throw new Error('Nessun ID da creare.');
  }

if (
  idPlan.proposedIdColumn !== 1 ||
  idPlan.proposedIdHeader !== 'ID'
) {
  throw new Error(
    'Piano ID non valido: attesa creazione della colonna ID in posizione 1.'
  );
}

changes.forEach((change, index) => {
  if (
    !Number.isSafeInteger(change.row) ||
    change.row < 2 ||
    change.row > sheetSnapshot.lastRow ||
    change.proposedId !== index + 1
  ) {
    throw new Error(
      'Proposta ID non valida alla posizione ' + index + '.'
    );
  }
});

  // Da questo punto iniziano le scritture.
  sheet.insertColumnBefore(1);
  sheet.getRange(1, 1).setValue(idPlan.proposedIdHeader);

  /*
 * Costruiamo l'intera colonna ID in memoria.
 * Le righe non occupate rimangono vuote.
 */
const idValues = Array.from(
  { length: sheetSnapshot.lastRow - 1 },
  () => ['']
);

changes.forEach(change => {
  idValues[change.row - 2][0] = change.proposedId;
});

/*
 * Una sola scrittura batch.
 * Riga 1 = header ID
 * Righe 2:lastRow = ID statici o celle vuote.
 */
sheet
  .getRange(2, 1, idValues.length, 1)
  .setValues(idValues);

  SpreadsheetApp.flush();

  // Verifica finale tramite l'analizzatore generale.
  const after = djungoAnalyzeCurrentSheetIds(idPlan.sheetId);

  if (
    after.status !== 'valid' ||
    after.missingRows.length ||
    after.invalidRows.length ||
    after.duplicateIds.length ||
    after.formulaRows.length
  ) {
    throw new Error(
      'Verifica post-migrazione ID fallita.'
    );
  }

  return {
    ok: true,
    spreadsheetId: after.spreadsheetId,
    sheetId: after.sheetId,
    sheetName: after.sheetName,
    createdIdColumn: after.idColumn,
    assignedIds: changes.length,
    statusAfter: after.status,
    formulaRowsAfter: after.formulaRows.length
  };
}



function djungoApplyMissingIds(idPlan, sheetSnapshot) {
  if (!idPlan || !sheetSnapshot) {
    throw new Error('Piano ID o snapshot mancanti.');
  }

  if (
    idPlan.status !== 'invalid' ||
    !idPlan.missingRows ||
    !idPlan.missingRows.length
  ) {
    throw new Error(
      'Migrazione non consentita: nessun ID mancante da assegnare.'
    );
  }

  // Non ripariamo più categorie di errore contemporaneamente.
  if (
    (idPlan.invalidRows || []).length ||
    (idPlan.duplicateIds || []).length ||
    (idPlan.formulaRows || []).length
  ) {
    throw new Error(
      'Migrazione non consentita: sono presenti anomalie ID aggiuntive.'
    );
  }

  if (
    idPlan.spreadsheetId !== sheetSnapshot.spreadsheetId ||
    Number(idPlan.sheetId) !== Number(sheetSnapshot.sheetId)
  ) {
    throw new Error(
      'Piano ID e snapshot appartengono a fogli differenti.'
    );
  }

  djungoValidateSheetSnapshot(sheetSnapshot);

  const currentPlan = djungoAnalyzeCurrentSheetIds(idPlan.sheetId);

  if (JSON.stringify(currentPlan) !== JSON.stringify(idPlan)) {
    throw new Error(
      'Il piano ID è cambiato prima della migrazione.'
    );
  }

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();

  if (spreadsheet.getId() !== idPlan.spreadsheetId) {
    throw new Error(
      'Spreadsheet diverso da quello analizzato.'
    );
  }

  const sheet = spreadsheet.getSheets().find(
    candidate => candidate.getSheetId() === Number(idPlan.sheetId)
  );

  if (!sheet) {
    throw new Error(
      'Foglio Djungo non trovato. sheetId=' + idPlan.sheetId
    );
  }

  const changes = idPlan.proposedMissingIdChanges || [];

  if (!changes.length) {
    throw new Error(
      'Nessuna proposta di ID mancante.'
    );
  }

  // Ultimi controlli prima di qualsiasi scrittura.
  changes.forEach((change, index) => {
    const expectedId =
      idPlan.maxExistingId + index + 1;

    if (
      !Number.isSafeInteger(change.row) ||
      change.row < 2 ||
      change.row > sheetSnapshot.lastRow ||
      change.proposedId !== expectedId
    ) {
      throw new Error(
        'Proposta ID non valida alla posizione ' + index + '.'
      );
    }

    const currentValue = sheet
      .getRange(change.row, idPlan.idColumn)
      .getValue();

    if (
      currentValue !== null &&
      currentValue !== '' &&
      String(currentValue).trim() !== ''
    ) {
      throw new Error(
        'La cella ID della riga ' +
        change.row +
        ' non è più vuota.'
      );
    }
  });

  // Da questo punto iniziano le scritture.
  changes.forEach(change => {
    sheet
      .getRange(change.row, idPlan.idColumn)
      .setValue(change.proposedId);
  });

  SpreadsheetApp.flush();

  // Verifica indipendente dello stato risultante.
  const after =
    djungoAnalyzeCurrentSheetIds(idPlan.sheetId);

  if (
    after.status !== 'valid' ||
    after.missingRows.length ||
    after.invalidRows.length ||
    after.duplicateIds.length ||
    after.formulaRows.length
  ) {
    throw new Error(
      'Verifica post-migrazione degli ID mancanti fallita.'
    );
  }

  return {
    ok: true,
    spreadsheetId: after.spreadsheetId,
    sheetId: after.sheetId,
    sheetName: after.sheetName,
    assignedIds: changes.length,
    statusAfter: after.status,
    maxExistingIdBefore: idPlan.maxExistingId,
    maxExistingIdAfter: after.maxExistingId
  };
}