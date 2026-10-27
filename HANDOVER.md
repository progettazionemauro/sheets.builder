# DJUNGO SHEET BUILDER — HANDOVER OPERATIVO

## REGOLA FONDAMENTALE

QUESTO È L'UNICO PUNTO DI INGRESSO DEL PROGETTO.

Prima di riprendere qualsiasi attività su Djungo:
1. Leggere questo documento.
2. Consultare i documenti collegati solo quando necessario.
3. Non ripetere verifiche già documentate, salvo modifiche che ne invalidino i risultati.
4. Al termine di ogni capitolo aggiornare stato, decisioni, test e prossimo passo.

## INDICE DOCUMENTALE

- HANDOVER.md — fonte autorevole dello stato operativo e delle decisioni.
- README.md — presentazione generale del progetto.
- docs/MANUALE_TECNICO.md — manuale tecnico da predisporre.
- PROJECT_STATE_DUMP.md — inventario tecnico generato da tools/project_state_dump.py.
- google/persistent/README.md — architettura del backend persistente Level B.

ATTENZIONE: PROJECT_STATE_DUMP.md può contenere informazioni riservate.
Non rigenerarlo o pubblicarlo senza verificare i filtri per i segreti.

## AMBIENTI

Repository locale: ~/Scrivania/sheet-builder
Branch di sviluppo: level-b-persistent-backend
Repository GitHub: progettazionemauro/sheets.builder

Hetzner STAGING:
- Host: 65.21.176.227
- Directory: /opt/sheets.builder
- Dominio: https://builder.sgbh.org
- Nginx -> Gunicorn: 127.0.0.1:8000
- Servizio: sheets-builder

PRODUZIONE: 157.180.16.0
NON MODIFICARE LA PRODUZIONE.

## STATO DELLO SVILUPPO

B34-03 — COMPLETATO
Pannello dettaglio record del Viewer.
Verificati sullo staging caricamento record, Update e Delete.
Commit di riferimento: 1492bda.

B34-01 — IMPLEMENTATO E COLLAUDATO SU STAGING
Ordinamento configurabile per singola colonna nella Customization.
Tipi previsti: numerico, alfabetico, data italiana e data estesa.
Distinguere ordinamento iniziale dei record e ordinamento Tabulator.
La scelta deve essere persistente.

## TRISINCRONIA

Strumento storico: publish.sh.
Flusso originale: Ubuntu -> GitHub -> Hetzner.

NON ESEGUIRE publish.sh NELLA VERSIONE ATTUALE:
- usa il branch main;
- esegue git add .;
- esegue git reset --hard sul server;
- reinstalla sempre le dipendenze.

Obiettivo: deploy sicuro sul solo staging, branch esplicito,
protezione dei dati persistenti, verifiche essenziali automatiche.

NON ESEGUIRE generators/rollback_to_commit.sh:
contiene reset distruttivi e force push su main.

## DATI DA PROTEGGERE

- codice.gs
- data/apps_registry.json
- data/persistent_apps.json
- backup esistenti
- sessioni e dati runtime

Verificare sempre lo stato Git prima di distribuire.

## STATO LOCALE AL 21/10/2026

Branch: level-b-persistent-backend, allineato a origin.

File modificati preesistenti:
- codice.gs
- data/apps_registry.json
- docs/index.html
- docs/viewer.html

Sono inoltre presenti backup locali non tracciati.
Non eliminarli né includerli automaticamente nei commit.

## METODO DI LAVORO

- Un comando terminale alla volta.
- Preferire verifiche mirate e non ripetitive.
- Non confondere test statici, HTTP e funzionali nel browser.
- Documentare le decisioni progettuali.
- Aggiornare questo handover alla chiusura di ogni capitolo.

## PROSSIMO PASSO OPERATIVO

1. Predisporre docs/MANUALE_TECNICO.md.
2. Adeguare publish.sh alla trisincronia sicura dello staging.
3. B34-01 implementato; completare i test specifici date_it e datetime_it.

## PRIORITÀ COLLAUDO FINALE — 21/10/2026

Obiettivo: arrivare rapidamente al collaudo integrato di Djungo.

Funzionalità ancora da completare con priorità:
- B34-01: completato su staging; test specifici date_it e datetime_it ancora aperti.
- Anchor link: collegamenti cliccabili nel Viewer e nel dettaglio.
- Immagini: visualizzazione corretta nel Viewer e nel dettaglio.

B34-03: già collaudato, non ripetere senza motivo tecnico.

La documentazione e la trisincronia sono attività di supporto:
non devono ritardare inutilmente il collaudo finale.

STATO LOCALE: presenti modifiche operative in codice.gs,
data/apps_registry.json, docs/index.html e docs/viewer.html.
Non eseguire git reset --hard, git add . o deploy distruttivi.

## B34-01 — Sorting configurabile (21/10/2026)

Stato: implementato e collaudato funzionalmente in locale; sincronizzazione staging ancora da completare.

La pagina docs/review.html permette di configurare il criterio di ordinamento per ogni campo: Automatico, Testo, Numero, Data italiana e Data/ora.

La configurazione viene conservata nella proprietà sortType di builder_state.fields e trasferita al generatore tramite FieldDef.sort_type.

Il Viewer Tabulator utilizza getColumnSorter() per applicare il comparatore configurato. L'ordinamento numerico è disponibile per qualsiasi colonna, non soltanto per ID.

Durante il collaudo SWOT_B34_EXPANSION_TEST è stata corretta la differenza fra il nome normalizzato id e l'intestazione originale ID restituita dal Google Sheet, utilizzando un confronto case-insensitive.

Esito: ordinamento numerico ID funzionante nel Viewer reale. Osservata anche la conservazione della selezione Sorting dopo la rigenerazione.

Da completare prima della chiusura definitiva: verifica degli altri tipi di ordinamento, aggiornamento del manuale tecnico, commit selettivo, sincronizzazione GitHub e Hetzner staging, verifica funzionale sul server.

Proteggere codice.gs, data/apps_registry.json e gli altri dati operativi. Non utilizzare git add . o git reset --hard. Non intervenire sulla produzione.


## Aggiornamento B34-01 — Hetzner staging, 21/10/2026

Commit generatore: d940c03, sincronizzato Ubuntu → GitHub → Hetzner staging.

Collaudo applicazione SWOT: 12 record caricati correttamente.
Ordinamento numerico ID verificato: 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 17.
La mappatura dinamica HEADER_ALIASES / resolveFieldKey collega
le intestazioni originali del foglio ai nomi interni dei campi,
senza hardcoding di specifiche colonne.

Durante il collaudo mostrato non sono comparsi errori HTTP 404 o JSON.
Non è tuttavia dimostrata la risoluzione definitiva dell'eventuale
problema intermittente Apps Script.

Restano da collaudare specificamente date_it e datetime_it.
Prossima attività funzionale: link cliccabili e immagini nel Viewer.
Produzione non modificata.

## AGGIORNAMENTO 27/10/2026 — IMMAGINI E TRISINCRONIA

### B34 — Anteprime automatiche delle immagini

Il generatore generators/builder_generators.py è stato aggiornato
per riconoscere e visualizzare automaticamente le immagini
associate a URL nei campi applicativi.

Funzionalità introdotte:
- anteprima automatica delle immagini nel CRUD;
- miniature delle immagini nel Viewer;
- mantenimento della configurazione di visualizzazione esistente.

Il generatore aggiornato è stato verificato in locale.
La copia presente su Hetzner staging è identica alla versione locale,
come confermato dal confronto SHA-256:

59d7440ec3495441bd7448e07e541551e4c30bdcfb460f244bd8aac6974fe9fe

GitHub contiene ancora la versione precedente del generatore.
La sincronizzazione GitHub è pertanto da completare.

### Trisincronia Ubuntu → GitHub → Hetzner staging

Branch operativo: level-b-persistent-backend.
Commit comune verificato: aa4e297.

Il precedente publish.sh è stato salvato come:
publish.sh.bak-pre-trisync-20261027

È stata predisposta una prima versione diagnostica di publish.sh,
eseguibile con:

./publish.sh --dry-run

Primo test completato correttamente il 27/10/2026.
Il controllo verifica branch, stato locale, commit GitHub,
commit e modifiche su Hetzner staging e stato documentazione.

La versione corrente NON esegue pubblicazioni.

### Vincoli di sicurezza

Proteggere i file operativi e gli artefatti generati,
in particolare:
- codice.gs;
- data/apps_registry.json;
- data/persistent_apps.json;
- data/persistent_backend.json;
- docs/index.html;
- docs/viewer.html;
- output/current/.

Non utilizzare git add . o git reset --hard.

Google Apps Script resta gestito separatamente:
il progetto GAS remoto è la fonte operativa autorevole.
L'automazione tramite clasp è rinviata.

Non intervenire sulla produzione.

### Prossime attività

1. Completare il nuovo publish.sh con controlli di sicurezza
   e pubblicazione selettiva sul solo staging.
2. Aggiornare docs/MANUALE_TECNICO.md.
3. Eseguire commit selettivo di codice e documentazione.
4. Sincronizzare GitHub e Hetzner staging senza sovrascrivere
   i dati operativi.
5. Riprendere il collaudo funzionale integrato di Djungo.
