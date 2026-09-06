/**
 * DJUNGO BUILDER — GOOGLE SHEET HELPER
 *
 * Level A
 *
 * A4.1b:
 * test export XLSX tramite endpoint documentale
 * docs.google.com/spreadsheets
 *
 * NON utilizza direttamente:
 * https://www.googleapis.com/drive/v3/...
 */


/**
 * Crea il menu Djungo Builder all'apertura dello Spreadsheet.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Djungo Builder')
    .addItem('Mostra informazioni foglio', 'showDjungoSheetInfo')
    .addSeparator()
    .addItem('Crea app dal foglio corrente', 'openDjungoBuilder')
    .addSeparator()
    .addItem('TEST — Esporta XLSX', 'testDjungoXlsxExport')
    .addItem('TEST — Esporta HTML ZIP', 'testDjungoHtmlExport')
    .addItem('TEST — Mostra contenuto ZIP', 'testDjungoZipContents')
    .addItem('TEST — Hosted import', 'testDjungoHostedImport')
    .addToUi();
}


/**
 * Mostra le informazioni dello Spreadsheet e del foglio attivo.
 */
function showDjungoSheetInfo() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();

  const info =
    'Spreadsheet: ' + spreadsheet.getName() + '\n\n' +
    'Spreadsheet ID:\n' + spreadsheet.getId() + '\n\n' +
    'Foglio attivo: ' + sheet.getName() + '\n\n' +
    'Sheet ID: ' + sheet.getSheetId();

  SpreadsheetApp.getUi().alert(
    'Djungo Builder',
    info,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


/**
 * Apre Djungo Builder passando il contesto
 * dello Spreadsheet e del foglio attivo.
 *
 * In questa fase non vengono ancora trasferiti i dati.
 */
function openDjungoBuilder() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();

  const baseUrl = 'https://builder.sgbh.org/generate.html';

  const params = [
    'spreadsheetId=' + encodeURIComponent(spreadsheet.getId()),
    'spreadsheetName=' + encodeURIComponent(spreadsheet.getName()),
    'sheetName=' + encodeURIComponent(sheet.getName()),
    'sheetId=' + encodeURIComponent(sheet.getSheetId())
  ].join('&');

  const builderUrl = baseUrl + '?' + params;

  const html = HtmlService.createHtmlOutput(
    '<p>Il foglio corrente è pronto per Djungo Builder.</p>' +
    '<p><a href="' + builderUrl + '" target="_blank">Apri Djungo Builder</a></p>'
  )
    .setWidth(420)
    .setHeight(150);

  SpreadsheetApp.getUi().showModalDialog(
    html,
    'Djungo Builder'
  );
}


/**
 * A4.1b — TEST XLSX
 *
 * Prova l'export usando l'endpoint documentale
 * di Google Sheets anziché Drive API v3.
 *
 * Il file resta in memoria come Blob.
 * Non viene ancora inviato a Djungo.
 */
function testDjungoXlsxExport() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const spreadsheetId = spreadsheet.getId();

  /*
   * ATTENZIONE:
   * questo NON è:
   *
   * https://www.googleapis.com/drive/v3/files/...
   *
   * Stiamo usando l'endpoint di export
   * del documento Google Sheets.
   */
  const url =
    'https://docs.google.com/spreadsheets/d/' +
    encodeURIComponent(spreadsheetId) +
    '/export?format=xlsx';

  try {

    const response = UrlFetchApp.fetch(url, {
      headers: {
        Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
      },

      /*
       * Non generare subito un'eccezione in caso
       * di HTTP 403/401 ecc.
       *
       * Vogliamo leggere la risposta di Google.
       */
      muteHttpExceptions: true,

      /*
       * Segui eventuali redirect di Google.
       */
      followRedirects: true
    });

    const statusCode = response.getResponseCode();
    const blob = response.getBlob();

    const contentType = blob.getContentType();
    const sizeBytes = blob.getBytes().length;
    const sizeKB = (sizeBytes / 1024).toFixed(2);

    let result =
      'Spreadsheet: ' + spreadsheet.getName() + '\n\n' +
      'HTTP status: ' + statusCode + '\n\n' +
      'Content type:\n' + contentType + '\n\n' +
      'Size: ' + sizeBytes + ' bytes\n' +
      'Size: ' + sizeKB + ' KB';

    /*
     * Se l'export fallisce, mostriamo anche
     * il contenuto restituito da Google.
     */
    if (statusCode !== 200) {
      result +=
        '\n\n--- GOOGLE RESPONSE ---\n\n' +
        response.getContentText().substring(0, 3000);
    }

    SpreadsheetApp.getUi().alert(
      'Djungo XLSX export test',
      result,
      SpreadsheetApp.getUi().ButtonSet.OK
    );

  } catch (error) {

    SpreadsheetApp.getUi().alert(
      'Djungo XLSX export test — ERRORE',
      String(error),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

/**
 * A4.2 — TEST HTML ZIP
 *
 * Prova a ottenere l'equivalente di:
 *
 * File → Scarica → Pagina web (.html)
 *
 * Non salva e non invia ancora nulla.
 * Verifica solamente la risposta ricevuta da Google.
 */
function testDjungoHtmlExport() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const spreadsheetId = spreadsheet.getId();

  const url =
    'https://docs.google.com/spreadsheets/d/' +
    encodeURIComponent(spreadsheetId) +
    '/export?format=zip';

  try {

    const response = UrlFetchApp.fetch(url, {
      headers: {
        Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
      },
      muteHttpExceptions: true,
      followRedirects: true
    });

    const statusCode = response.getResponseCode();
    const blob = response.getBlob();

    const contentType = blob.getContentType();
    const sizeBytes = blob.getBytes().length;
    const sizeKB = (sizeBytes / 1024).toFixed(2);

    let result =
      'Spreadsheet: ' + spreadsheet.getName() + '\n\n' +
      'HTTP status: ' + statusCode + '\n\n' +
      'Content type:\n' + contentType + '\n\n' +
      'Size: ' + sizeBytes + ' bytes\n' +
      'Size: ' + sizeKB + ' KB';

    if (statusCode !== 200) {
      result +=
        '\n\n--- GOOGLE RESPONSE ---\n\n' +
        response.getContentText().substring(0, 3000);
    }

    SpreadsheetApp.getUi().alert(
      'Djungo HTML export test',
      result,
      SpreadsheetApp.getUi().ButtonSet.OK
    );

  } catch (error) {

    SpreadsheetApp.getUi().alert(
      'Djungo HTML export test — ERRORE',
      String(error),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

/**
 * A4.2b — ISPEZIONE CONTENUTO ZIP
 *
 * Scarica in memoria l'export Web dello Spreadsheet,
 * apre lo ZIP e mostra l'elenco dei file contenuti.
 *
 * Non salva nulla su Drive.
 * Non scarica nulla sul PC.
 * Non invia ancora nulla a Djungo Builder.
 */
function testDjungoZipContents() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const spreadsheetId = spreadsheet.getId();

  const url =
    'https://docs.google.com/spreadsheets/d/' +
    encodeURIComponent(spreadsheetId) +
    '/export?format=zip';

  try {

    const response = UrlFetchApp.fetch(url, {
      headers: {
        Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
      },
      muteHttpExceptions: true,
      followRedirects: true
    });

    const statusCode = response.getResponseCode();

    if (statusCode !== 200) {
      SpreadsheetApp.getUi().alert(
        'Djungo ZIP inspection — ERRORE',
        'HTTP status: ' + statusCode + '\n\n' +
        response.getContentText().substring(0, 3000),
        SpreadsheetApp.getUi().ButtonSet.OK
      );

      return;
    }

    const zipBlob = response.getBlob();

    // Decomprime lo ZIP direttamente in memoria.
    const files = Utilities.unzip(zipBlob);

    let result =
      'Spreadsheet: ' + spreadsheet.getName() + '\n\n' +
      'File trovati nello ZIP: ' + files.length + '\n\n';

    files.forEach(function(file, index) {
      result +=
        (index + 1) + '. ' +
        file.getName() +
        '\n   ' +
        file.getContentType() +
        ' — ' +
        file.getBytes().length +
        ' bytes\n\n';
    });

    SpreadsheetApp.getUi().alert(
      'Djungo ZIP contents',
      result.substring(0, 7000),
      SpreadsheetApp.getUi().ButtonSet.OK
    );

  } catch (error) {

    SpreadsheetApp.getUi().alert(
      'Djungo ZIP inspection — ERRORE',
      String(error),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}


/**
 * A4.4a — TEST HOSTED IMPORT
 *
 * Esporta automaticamente:
 * - Spreadsheet completo in XLSX
 * - Web export completo in ZIP
 *
 * e li invia a Djungo Builder tramite HTTPS multipart/form-data.
 *
 * Non modifica ancora il flusso principale del menu.
 */
function djungoHostedImportCurrentSheet() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = spreadsheet.getActiveSheet();

  const spreadsheetId = spreadsheet.getId();
  const spreadsheetName = spreadsheet.getName();
  const sheetId = String(sheet.getSheetId());
  const sheetName = sheet.getName();

  const xlsxUrl =
    'https://docs.google.com/spreadsheets/d/' +
    encodeURIComponent(spreadsheetId) +
    '/export?format=xlsx';

  const zipUrl =
    'https://docs.google.com/spreadsheets/d/' +
    encodeURIComponent(spreadsheetId) +
    '/export?format=zip';

  const authHeaders = {
    Authorization: 'Bearer ' + ScriptApp.getOAuthToken()
  };

  const xlsxResponse = UrlFetchApp.fetch(xlsxUrl, {
    headers: authHeaders,
    muteHttpExceptions: true,
    followRedirects: true
  });

  const xlsxStatus = xlsxResponse.getResponseCode();

  if (xlsxStatus !== 200) {
    throw new Error(
      'XLSX export failed. HTTP ' +
      xlsxStatus +
      '\n\n' +
      xlsxResponse.getContentText().substring(0, 2000)
    );
  }

  const xlsxBlob = xlsxResponse
    .getBlob()
    .setName(spreadsheetName + '.xlsx');

  const zipResponse = UrlFetchApp.fetch(zipUrl, {
    headers: authHeaders,
    muteHttpExceptions: true,
    followRedirects: true
  });

  const zipStatus = zipResponse.getResponseCode();

  if (zipStatus !== 200) {
    throw new Error(
      'Web ZIP export failed. HTTP ' +
      zipStatus +
      '\n\n' +
      zipResponse.getContentText().substring(0, 2000)
    );
  }

  const zipBlob = zipResponse
    .getBlob()
    .setName(spreadsheetName + '.zip');

  const builderResponse = UrlFetchApp.fetch(
    'https://builder.sgbh.org/api/google-sheet/import',
    {
      method: 'post',
      payload: {
        spreadsheet_id: spreadsheetId,
        spreadsheet_name: spreadsheetName,
        sheet_id: sheetId,
        sheet_name: sheetName,
        xlsx: xlsxBlob,
        web_export: zipBlob
      },
      muteHttpExceptions: true,
      followRedirects: true
    }
  );

  const builderStatus = builderResponse.getResponseCode();
  const builderBody = builderResponse.getContentText();

  let builderData = null;

  try {
    builderData = JSON.parse(builderBody);
  } catch (error) {
    throw new Error(
      'Invalid Djungo response. HTTP ' +
      builderStatus +
      '\n\n' +
      builderBody.substring(0, 2000)
    );
  }

  if (builderStatus !== 200 || !builderData.ok) {
    throw new Error(
      builderData.error ||
      ('Djungo import failed. HTTP ' + builderStatus)
    );
  }

  return {
    spreadsheetId: spreadsheetId,
    spreadsheetName: spreadsheetName,
    sheetId: sheetId,
    sheetName: sheetName,
    xlsxBytes: xlsxBlob.getBytes().length,
    zipBytes: zipBlob.getBytes().length,
    builderStatus: builderStatus,
    builderData: builderData
  };
}


function testDjungoHostedImport() {
  try {
    const result = djungoHostedImportCurrentSheet();

    SpreadsheetApp.getUi().alert(
      'Djungo hosted import test',
      'Spreadsheet: ' + result.spreadsheetName + '\n' +
      'Foglio: ' + result.sheetName + '\n' +
      'Sheet ID: ' + result.sheetId + '\n\n' +
      'XLSX: ' + result.xlsxBytes + ' bytes\n' +
      'ZIP: ' + result.zipBytes + ' bytes\n\n' +
      'Djungo HTTP status: ' + result.builderStatus + '\n\n' +
      'Session ID: ' + result.builderData.session_id,
      SpreadsheetApp.getUi().ButtonSet.OK
    );

  } catch (error) {
    SpreadsheetApp.getUi().alert(
      'Djungo hosted import test — ERRORE',
      String(error),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}


function createDjungoAppFromCurrentSheet() {
  try {
    const result = djungoHostedImportCurrentSheet();

    const sessionId = result.builderData.session_id;

    if (!sessionId) {
      throw new Error('Djungo did not return a session_id.');
    }

    const builderUrl =
      'https://builder.sgbh.org/generate.html?session=' +
      encodeURIComponent(sessionId);

    const html = HtmlService
      .createHtmlOutput(
        '<div style="font-family:Arial,sans-serif;padding:18px;">' +
          '<h3>Djungo Builder</h3>' +
          '<p>Il foglio <strong>' +
          escapeDjungoHtml(result.sheetName) +
          '</strong> è stato importato correttamente.</p>' +
          '<p><a href="' +
          builderUrl +
          '" target="_blank" style="' +
          'display:inline-block;padding:10px 14px;' +
          'background:#111;color:#fff;text-decoration:none;' +
          'border-radius:6px;font-weight:bold;">' +
          'Apri Djungo Builder' +
          '</a></p>' +
          '<p style="color:#666;font-size:12px;">' +
          'Sessione: ' +
          escapeDjungoHtml(sessionId) +
          '</p>' +
        '</div>'
      )
      .setWidth(420)
      .setHeight(220);

    SpreadsheetApp.getUi().showModalDialog(
      html,
      'Djungo Builder'
    );

  } catch (error) {
    SpreadsheetApp.getUi().alert(
      'Djungo Builder — ERRORE',
      String(error),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}


function escapeDjungoHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
