# Djungo Persistent Backend — Level B

## Obiettivo
Un solo backend Apps Script persistente per più applicazioni
generate da fogli dello stesso Spreadsheet.

## Identità
- appSlug: identificatore dell'app nel Builder.
- spreadsheetId + sheetId: identità tecnica stabile del foglio.
- sheetName: nome descrittivo e modificabile, non identificatore primario.

## Separazione
- Motore CRUD comune.
- Configurazione specifica per app/Sheet.
- Schema acquisito dal parser del Builder.
- Routing Flask separato dalla configurazione persistente.

## Registri
- data/apps_registry.json:
  routing appSlug -> Web App URL + API key.
- data/persistent_apps.json:
  configurazione appSlug -> Spreadsheet + Sheet + schema.

Più app dello stesso Spreadsheet possono condividere lo stesso
backend Apps Script pur mantenendo sheetId e schema distinti.

## Compatibilità
Il generatore GAS attuale generate_gas_backend() resta invariato
durante il primo prototipo Level B.

## Stato B1
Definito il contratto minimo della configurazione:
- configVersion
- appSlug
- spreadsheetId
- sheetId
- sheetName
- schema

La configurazione viene derivata dal builder_state approvato.
