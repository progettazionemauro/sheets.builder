# DJUNGO SHEET BUILDER — MANUALE TECNICO

> Punto di ingresso ufficiale: [HANDOVER.md](../HANDOVER.md).
> Per conoscere lo stato corrente, i test conclusi e il prossimo intervento, consultare sempre HANDOVER.md.

## 1. Scopo

Djungo Sheet Builder genera applicazioni web a partire da dati e schemi di Google Sheets.

Il progetto integra Python/Flask, generatori HTML/JavaScript, Tabulator e Google Apps Script.

## 2. Architettura

### Ambiente locale
- Repository: ~/Scrivania/sheet-builder
- Branch di sviluppo: level-b-persistent-backend
- Server applicativo: Flask
- Generatori: generators/builder_generators.py

### Staging Hetzner
- Host: 65.21.176.227
- Directory: /opt/sheets.builder
- Dominio: https://builder.sgbh.org
- Reverse proxy: Nginx
- Server WSGI: Gunicorn su 127.0.0.1:8000
- Servizio systemd: sheets-builder

La produzione è separata e non deve essere modificata durante lo sviluppo.

## 3. Componenti applicativi

### Builder
Acquisisce lo schema e le impostazioni dell'applicazione.

### Generatori
Producono i file HTML e JavaScript del frontend.

### Viewer
Visualizza i record mediante Tabulator e gestisce le interazioni con il pannello di dettaglio.

### Backend persistente Level B
Utilizza Google Apps Script per il motore CRUD condiviso.

I registri principali sono:
- data/apps_registry.json: routing applicazioni e credenziali di accesso al backend.
- data/persistent_apps.json: configurazioni persistenti di Spreadsheet, Sheet e schema.

Per il contratto dettagliato consultare:
[Backend persistente](../google/persistent/README.md).

## 4. Distribuzione

Il sistema storico di trisincronia utilizza publish.sh.

Il flusso previsto è:
Ubuntu locale -> GitHub -> Hetzner staging.

ATTENZIONE: la versione attuale di publish.sh non è approvata per l'esecuzione.
Deve essere adeguata al branch di sviluppo e alla protezione dei dati persistenti.

Non utilizzare generators/rollback_to_commit.sh senza revisione:
contiene operazioni Git potenzialmente distruttive.

## 5. Protezione dei dati

Durante il deploy distinguere:
- codice sorgente versionato;
- configurazioni operative;
- dati persistenti;
- sessioni runtime;
- backup.

Non includere password, token o API key nella documentazione.

## 6. Verifiche

Distinguere sempre:
- controlli statici del codice;
- verifiche HTTP;
- test funzionali nel browser;
- verifiche di persistenza.

Le evidenze dei test e i relativi commit sono registrati in HANDOVER.md.

## 7. Documentazione tecnica automatica

Lo script tools/project_state_dump.py genera PROJECT_STATE_DUMP.md.

ATTENZIONE: il generatore attuale non applica filtri sufficienti
per impedire l'inclusione di informazioni riservate.

Non rigenerare o pubblicare il dump senza una revisione preventiva.

## 8. Gestione delle modifiche

Ogni capitolo di sviluppo deve concludersi con:
1. Modifica del codice.
2. Verifiche pertinenti.
3. Registrazione delle decisioni e delle evidenze.
4. Aggiornamento di HANDOVER.md.
5. Aggiornamento del manuale se cambia l'architettura o una procedura.

## 9. Riferimenti

- [Handover operativo](../HANDOVER.md)
- [README generale](../README.md)
- [Backend persistente](../google/persistent/README.md)
- [Inventario tecnico](../PROJECT_STATE_DUMP.md)

## B34-01 — Ordinamento configurabile delle colonne

Nel Builder, la pagina `docs/review.html` consente di scegliere il criterio
Sorting per ciascun campo: `auto`, `string`, `number`, `date_it`, `datetime_it`.

La proprietà `sortType` è associata al campo nella configurazione del Builder.
Il generatore `generators/builder_generators.py` la acquisisce attraverso
`FieldDef.sort_type` e produce la configurazione JavaScript
`COLUMN_SORT_CONFIG` nel Viewer.

Il Viewer utilizza Tabulator e la funzione `getColumnSorter()` per scegliere
il comparatore. Il confronto delle intestazioni è case-insensitive, per
gestire differenze come `ID` e `id`.

Collaudo locale del 21/10/2026: verificato l'ordinamento numerico della
colonna ID nel Viewer reale, con valori a una e due cifre. Osservato il
mantenimento della selezione Sorting dopo la rigenerazione.

Limiti del collaudo: non ancora verificati sistematicamente tutti i tipi
Sorting e le intestazioni che differiscono per accenti o altri caratteri.
La verifica sul server Hetzner staging è ancora da eseguire.

Il deploy deve preservare `codice.gs`, `data/apps_registry.json` e gli
altri dati operativi esistenti. Non utilizzare `git reset --hard`.
Non intervenire sul server di produzione.
