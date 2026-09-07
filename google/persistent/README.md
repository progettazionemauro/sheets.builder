# Djungo Persistent Backend — Level B

## Obiettivo
Un solo backend Apps Script persistente per più applicazioni
generate da fogli dello stesso Spreadsheet.

## Identità
- appSlug: identificatore dell'app nel Builder.
- spreadsheetId + sheetId: identità tecnica del foglio.
- sheetName: nome descrittivo, non identificatore primario.

## Separazione
- Motore CRUD comune.
- Configurazione specifica per app.
- Schema e stili acquisiti dal parser del Builder.

## Compatibilità
Il generatore legacy generate_gas_backend() resta invariato
durante il primo prototipo.

## Da definire
- Formato completo della configurazione.
- Rappresentazione di validazioni e formule.
- Registrazione e aggiornamento delle app.
- Routing dal proxy Flask.
- Test con volcano-db e il secondo foglio.
