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


## Aggiornamento tecnico B34-01 — 21/10/2026

Commit d940c03 distribuito su Hetzner staging.

Il Viewer generato include HEADER_ALIASES e resolveFieldKey():
la risoluzione dinamica originalHeader → name viene utilizzata
per visibilità, etichette e configurazione dell'ordinamento.
La soluzione non dipende dai nomi specifici delle colonne SWOT.

Collaudo staging: caricamento di 12 record e ordinamento numerico ID
corretto, inclusi i valori a due cifre.

I precedenti riferimenti al deploy staging ancora da effettuare
sono superati da questo aggiornamento.

Restano aperti i test specifici dei comparatori date_it e datetime_it.
Il problema intermittente HTTP 404 di Apps Script non può considerarsi
definitivamente risolto sulla base di un solo collaudo positivo.

## B34 — Riconoscimento automatico delle immagini (27/10/2026)

Il modulo generators/builder_generators.py è stato aggiornato
per gestire automaticamente le anteprime delle immagini
associate a URL nei campi applicativi.

Le funzionalità introdotte comprendono:
- visualizzazione automatica delle immagini nel CRUD;
- generazione delle miniature nel Viewer;
- compatibilità con la configurazione di visualizzazione esistente.

Il generatore è stato verificato funzionalmente in locale.
La versione presente su Hetzner staging è identica a quella
locale, come confermato dal confronto SHA-256.

Il collaudo completo delle miniature nel Viewer pubblicato
rimane da completare.

## Trisincronia e distribuzione sicura — aggiornamento 30/10/2026

### Architettura e fonti autorevoli

Ubuntu locale è la fonte autorevole per codice Python,
HTML sorgente e documentazione.

Flusso: Ubuntu → GitHub → Hetzner staging.

Branch: level-b-persistent-backend.
Directory staging: /opt/sheets.builder.
Servizio: sheets-builder.
URL: https://builder.sgbh.org.

Il progetto Google Apps Script remoto costituisce
un'eccezione: i file GAS non vengono distribuiti
automaticamente.

### Pubblicazione controllata

Lo script publish.sh supporta:

- ./publish.sh --dry-run
- ./publish.sh --staging

La prima modalità esegue il preflight senza deployment.
La seconda, dopo i controlli, aggiorna staging mediante
merge fast-forward, riavvia il servizio se necessario
e verifica la disponibilità dell'applicazione.

Lo script richiede che il commit locale sia già
presente su GitHub: non esegue commit o push.

Commit comune collaudato: bae6a22.
Il deployment effettivo del 30/10/2026 ha aggiornato
soltanto publish.sh.
Verificati servizio attivo ed endpoint /generate.html
con risposta HTTP 200. Durante il deployment di bae6a22
è stato osservato un HTTP 502 transitorio dopo il riavvio;
la verifica successiva ha restituito HTTP 200.
È stata predisposta localmente una verifica HTTP
con tentativi ripetuti, ancora da distribuire.

Restano da collaudare i diversi casi di conflitto,
la gestione delle migrazioni e i test funzionali completi.

### Protezione dei dati

Non sovrascrivere:
- codice.gs e altri file GAS;
- data/apps_registry.json;
- data/persistent_apps.json;
- data/persistent_backend.json;
- docs/index.html;
- docs/viewer.html;
- output/;
- output_project/;
- workdir/.

Alcuni file operativi risultano già tracciati da Git.
Pertanto .gitignore non costituisce una protezione
sufficiente.

Non utilizzare git add . né git reset --hard.

### Processo di checkpoint

Il processo concordato è:

Implementazione → sintesi tecnica → verifica →
integrazione documentale → checkpoint → trisincronia.

La sintesi viene preparata durante la sessione
di sviluppo e verificata prima della pubblicazione.

checkpoint.sh è operativo nelle modalità --dry-run
e --run. Classifica i file, seleziona soltanto sorgenti
e documentazione autorizzati, controlla l'area di staging
Git, richiede conferma, crea il commit, esegue il push
e richiama publish.sh per la distribuzione.

Il commit bae6a22 ha introdotto il checkpoint.
Il collaudo in anteprima ha confermato la corretta
esclusione dei dati persistenti e degli output generati.

Le modifiche successive per il recupero di push e
deployment interrotti sono ancora in fase di collaudo.
Il recupero deve verificare i singoli commit e rifiutare
merge e percorsi non autorizzati.

La produzione Hetzner rimane esclusa.
La promozione staging → produzione richiederà una
procedura separata, con backup e approvazione.
