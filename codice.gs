/***************
 * HORROR BACKEND — Standalone Web App (JSONP) for sheet: HorrorMovie
 *
 * Modes:
 * - meta
 * - schema
 * - view        (public read)
 * - insert      (write, requires apiKey)
 * - getById     (write-key protected)
 * - update      (write-key protected)
 * - delete      (write-key protected)
 ***************/

// ===== CONFIG =====
const SHEET_NAME = "HorrorMovie";

// Se vuoi usare un file Sheet diverso da quello bound/attivo, metti qui l'ID.
// Se lo lasci vuoto, usa lo Spreadsheet attivo del progetto Apps Script.
const SPREADSHEET_ID = ""; // es: "1AbC...XyZ"

// Chiave privata per write
const API_KEY = "CHANGE_ME_WRITE_KEY_2026";

// Marker build per capire subito quale deploy stai chiamando
const BUILD_MARKER = "HORROR_BACKEND_DUPCHECK_V1";
const BUILD_TIME = "2026-03-07 22:45";

const RATING_ALLOWED = [
  "Pessimo",
  "Mediocre",
  "Medio",
  "Buono",
  "Ottimo",
  "Capolavoro"
];

// Ordine colonne nel foglio
const HEADERS = ["id", "year", "title", "url", "link", "nation", "rating"];

// Required vs optional
const REQUIRED_ON_INSERT = ["year", "title"];
const OPTIONAL_ON_INSERT = ["url", "nation", "rating"];
const COMPUTED = ["id", "link"];

/***************
 * ENTRY POINT — UNICO
 ***************/
function doGet(e) {
  const p = (e && e.parameter) ? e.parameter : {};
  const cb = String(p.cb || "").trim();

  if (!cb) return ContentService.createTextOutput("Missing cb (JSONP)");

  try {
    const mode = String(p.mode || "meta").trim();
    const debug = String(p.debug || "") === "1";

    // PUBLIC
    if (mode === "meta")   return jsonp_(cb, meta_());
    if (mode === "schema") return jsonp_(cb, schema_());
    if (mode === "view") {
      const limit = clampInt_(p.limit, 1, 500, 50);
      return jsonp_(cb, view_(limit));
    }

    // PROTECTED
    const apiKey = String(p.apiKey || "");
    if (apiKey !== API_KEY) {
      const out = { ok: false, error: "Invalid apiKey" };
      if (debug) out.debug = { receivedApiKey: apiKey ? "(provided)" : "(missing)" };
      return jsonp_(cb, out);
    }

    if (mode === "insert") return jsonp_(cb, insert_(p, debug));

    if (mode === "getById") {
      const id = clampInt_(p.id, 1, 999999999, 0);
      if (!id) return jsonp_(cb, { ok: false, error: "Missing/invalid id" });
      return jsonp_(cb, getById_(id));
    }

    if (mode === "update") {
      const id = clampInt_(p.id, 1, 999999999, 0);
      if (!id) return jsonp_(cb, { ok: false, error: "Missing/invalid id" });
      return jsonp_(cb, update_(id, p, debug));
    }

    if (mode === "delete") {
      const id = clampInt_(p.id, 1, 999999999, 0);
      if (!id) return jsonp_(cb, { ok: false, error: "Missing/invalid id" });
      return jsonp_(cb, del_(id));
    }

    return jsonp_(cb, { ok: false, error: "Unknown mode", mode });

  } catch (err) {
    return jsonp_(cb, {
      ok: false,
      error: String(err && err.message ? err.message : err)
    });
  }
}

/***************
 * META + SCHEMA
 ***************/
function meta_() {
  return {
    ok: true,
    backend: "horror-backend",
    sheet: SHEET_NAME,
    marker: BUILD_MARKER,
    build: BUILD_TIME,
    publicModes: ["meta", "schema", "view"],
    protectedModes: ["insert", "getById", "update", "delete"]
  };
}

function schema_() {
  return {
    ok: true,
    entity: "HorrorMovie",
    headers: HEADERS,
    requiredOnInsert: REQUIRED_ON_INSERT,
    optionalOnInsert: OPTIONAL_ON_INSERT,
    computed: COMPUTED,
    ratingAllowed: RATING_ALLOWED,
    constraints: {
      year:   { type: "int", min: 1890, max: 2100, required: true },
      title:  { type: "string", minLen: 1, maxLen: 120, required: true },
      url:    { type: "string", maxLen: 600, required: false },
      nation: { type: "string", maxLen: 80, required: false },
      rating: { type: "enum", values: RATING_ALLOWED, required: false }
    }
  };
}

/***************
 * VIEW (last N rows)
 ***************/
function view_(limit) {
  const sh = getSheet_();
  ensureHeaders_(sh);

  const lastRow = sh.getLastRow();
  const lastCol = sh.getLastColumn();
  if (lastRow < 2 || lastCol < 1) return { ok: true, headers: HEADERS, rows: [] };

  const numCols = Math.min(lastCol, HEADERS.length);
  const dataRows = lastRow - 1;
  const take = Math.min(limit, dataRows);
  const start = lastRow - take + 1;

  const rows = sh.getRange(start, 1, take, numCols).getValues();
  return { ok: true, headers: HEADERS.slice(0, numCols), rows };
}

/***************
 * INSERT
 * title resta testo
 * link (colonna E) è formula
 * duplicati bloccati su year + title
 ***************/
function insert_(p, debug) {
  const sh = getSheet_();
  ensureHeaders_(sh);

  const allowedKeys = new Set([
    "cb", "mode", "apiKey", "debug", "_",
    "year", "title", "url", "nation", "rating"
  ]);

  const unknown = Object.keys(p).filter(k => !allowedKeys.has(k));
  if (unknown.length) return { ok: false, error: "Unknown fields", unknown };

  const year   = clampInt_(p.year, 1890, 2100, 0);
  const title  = norm_(p.title);
  const url    = norm_(p.url);
  const nation = norm_(p.nation);
  const rating = norm_(p.rating);

  const snap = {
    year, title, url, nation, rating,
    keys: Object.keys(p).sort()
  };

  const missing = [];
  if (!year) missing.push("year");
  if (!title) missing.push("title");
  if (missing.length) {
    const out = { ok: false, error: "Missing required fields", missing };
    if (debug) out.debug = snap;
    return out;
  }

  if (title.length > 120) return { ok: false, error: "title too long (max 120)" };
  if (url && url.length > 600) return { ok: false, error: "url too long (max 600)" };
  if (nation && nation.length > 80) return { ok: false, error: "nation too long (max 80)" };

  if (rating && RATING_ALLOWED.indexOf(rating) === -1) {
    return { ok: false, error: "rating not allowed", allowed: RATING_ALLOWED };
  }

  // ===== CONTROLLO DUPLICATI year + title =====
  const dupRow = findDuplicateByYearTitle_(sh, year, title);
  if (dupRow) {
    return {
      ok: false,
      error: "Duplicate record",
      year: year,
      title: title,
      duplicateRow: dupRow
    };
  }

  const id = computeNextId_(sh);
  const rowNumber = sh.getLastRow() + 1;

  // A-D
  sh.getRange(rowNumber, 1, 1, 4).setValues([[id, year, title, url]]);

  // E = link formula
  if (url) {
    sh.getRange(rowNumber, 5).setFormula(`=HYPERLINK(D${rowNumber};C${rowNumber})`);
  } else {
    sh.getRange(rowNumber, 5).setValue("");
  }

  // F-G
  sh.getRange(rowNumber, 6, 1, 2).setValues([[nation, rating]]);

  const out = { ok: true, id, insertedRow: rowNumber };
  if (debug) out.debug = snap;
  return out;
}

/***************
 * GET BY ID
 ***************/
function getById_(id) {
  const sh = getSheet_();
  ensureHeaders_(sh);

  const row = findRowById_(sh, id);
  if (!row) return { ok: false, error: "ID not found", id };

  const values = sh.getRange(row, 1, 1, HEADERS.length).getValues()[0];
  const rec = {};
  HEADERS.forEach((h, i) => rec[h] = values[i]);

  return { ok: true, id, record: rec, row };
}

/***************
 * UPDATE
 * title resta testo
 * link (colonna E) è formula
 ***************/
function update_(id, p, debug) {
  const sh = getSheet_();
  ensureHeaders_(sh);

  const row = findRowById_(sh, id);
  if (!row) return { ok: false, error: "ID not found", id };

  const year   = clampInt_(p.year, 1890, 2100, 0);
  const title  = norm_(p.title);
  const url    = norm_(p.url);
  const nation = norm_(p.nation);
  const rating = norm_(p.rating);

  const snap = {
    id, year, title, url, nation, rating,
    keys: Object.keys(p).sort()
  };

  const missing = [];
  if (!year) missing.push("year");
  if (!title) missing.push("title");
  if (missing.length) {
    const out = { ok: false, error: "Missing required fields", missing, id };
    if (debug) out.debug = snap;
    return out;
  }

  if (title.length > 120) return { ok: false, error: "title too long (max 120)" };
  if (url && url.length > 600) return { ok: false, error: "url too long (max 600)" };
  if (nation && nation.length > 80) return { ok: false, error: "nation too long (max 80)" };

  if (rating && RATING_ALLOWED.indexOf(rating) === -1) {
    return { ok: false, error: "rating not allowed", allowed: RATING_ALLOWED };
  }

  // A-D
  sh.getRange(row, 1, 1, 4).setValues([[id, year, title, url]]);

  // E = link formula
  if (url) {
    sh.getRange(row, 5).setFormula(`=HYPERLINK(D${row};C${row})`);
  } else {
    sh.getRange(row, 5).setValue("");
  }

  // F-G
  sh.getRange(row, 6, 1, 2).setValues([[nation, rating]]);

  const out = { ok: true, id, updatedRow: row };
  if (debug) out.debug = snap;
  return out;
}

/***************
 * DELETE
 ***************/
function del_(id) {
  const sh = getSheet_();
  ensureHeaders_(sh);

  const row = findRowById_(sh, id);
  if (!row) return { ok: false, error: "ID not found", id };

  sh.deleteRow(row);
  return { ok: true, id, deletedRow: row };
}

/***************
 * INTERNALS
 ***************/
function getSheet_() {
  const ss = SPREADSHEET_ID
    ? SpreadsheetApp.openById(SPREADSHEET_ID)
    : SpreadsheetApp.getActiveSpreadsheet();

  const sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) throw new Error("Sheet not found: " + SHEET_NAME);
  return sh;
}

function ensureHeaders_(sh) {
  const lastCol = Math.max(sh.getLastColumn(), HEADERS.length);
  const row1 = sh.getRange(1, 1, 1, lastCol).getValues()[0].slice(0, HEADERS.length);
  const row1Norm = row1.map(x => String(x || "").trim().toLowerCase());
  const expected = HEADERS.slice();

  const ok = expected.every((h, i) => row1Norm[i] === h);

  if (!ok) {
    const allEmpty = row1Norm.every(x => !x);
    if (allEmpty && sh.getLastRow() === 0) {
      sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
      return;
    }
    throw new Error("Header mismatch in sheet. Expected: " + HEADERS.join(", "));
  }
}

function findRowById_(sh, id) {
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return 0;

  const tf = sh.getRange(2, 1, lastRow - 1, 1)
    .createTextFinder(String(id))
    .matchEntireCell(true);

  const cell = tf.findNext();
  return cell ? cell.getRow() : 0;
}

function findDuplicateByYearTitle_(sh, year, title) {
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return null;

  // B=year, C=title
  const data = sh.getRange(2, 2, lastRow - 1, 2).getValues();
  const titleNorm = String(title ?? "").trim().toLowerCase();

  for (let i = 0; i < data.length; i++) {
    const rowYear = Number(data[i][0]);
    const rowTitle = String(data[i][1] ?? "").trim().toLowerCase();

    if (rowYear === Number(year) && rowTitle === titleNorm) {
      return i + 2; // riga reale nello sheet
    }
  }

  return null;
}

function computeNextId_(sh) {
  const lastRow = sh.getLastRow();
  if (lastRow < 2) return 1;

  const lastId = sh.getRange(lastRow, 1).getValue();
  const n = Number(lastId);
  if (!isNaN(n) && isFinite(n) && n >= 0) return n + 1;

  const ids = sh.getRange(2, 1, lastRow - 1, 1).getValues().flat()
    .map(Number).filter(x => !isNaN(x));
  const maxId = ids.length ? Math.max.apply(null, ids) : 0;
  return maxId + 1;
}

function clampInt_(v, min, max, defVal) {
  const n = parseInt(String(v || ""), 10);
  if (isNaN(n)) return defVal;
  return Math.max(min, Math.min(max, n));
}

function norm_(v) {
  return String(v ?? "").trim();
}

function jsonp_(cb, obj) {
  const out = cb + "(" + JSON.stringify(obj) + ");";
  return ContentService
    .createTextOutput(out)
    .setMimeType(ContentService.MimeType.JAVASCRIPT);
}
