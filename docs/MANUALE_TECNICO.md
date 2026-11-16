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

### 2.1 Accessibilità dei Google Sheets sorgente e API esterne

Djungo privilegia gli endpoint nativi di esportazione di Google Sheets
senza dipendere dalle Google Drive API o Google Sheets API con OAuth.

**Requisito operativo:** il documento sorgente deve essere condiviso
con l'impostazione "Chiunque abbia il link — Visualizzatore",
con esportazione consentita.

**Avvertenza sulla riservatezza:** chiunque ottenga il collegamento
può accedere ai contenuti del documento. La mancata indicizzazione
nei motori di ricerca non costituisce una protezione.
Non utilizzare questa modalità per informazioni riservate o dati
personali che richiedono accesso controllato.

L'autorizzazione necessaria a Google Apps Script per il backend
CRUD persistente è prevista e rimane distinta dall'importazione
dei dati sorgente.

L'automazione dell'importazione XLSX e il recupero degli stili
HTML sono attività progettuali ancora da completare.

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

## Ricerca sperimentale Google Sheets - 05/11/2026

### Obiettivo

Automatizzare il recupero dei metadati delle schede Google Sheets accessibili pubblicamente, senza OAuth e senza esportazioni manuali.

### Principio di manutenzione

Conservare nella documentazione tutto il codice Python consolidato durante gli esperimenti, insieme a:

- Selettori HTML ed endpoint utilizzati.
- Risultati delle verifiche.
- Limiti conosciuti.
- Data dell'ultima verifica.
- Test di regressione e metodi alternativi.

La struttura HTML di Google Sheets non costituisce un'API stabile. Google potrebbe modificarla in futuro.

### GS-01 - Recupero dei nomi delle schede

Codice verificato:

```python
import requests
from bs4 import BeautifulSoup

url = "https://docs.google.com/spreadsheets/d/1W9GWokNp6PSsPNCU35lMx2AAVeFvBqirw22ABT7_cUU/edit?gid=843771997"

response = requests.get(url, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

sheet_names = [
    element.get_text(" ", strip=True)
    for element in soup.select(".docs-sheet-tab-caption")
]

for name in sheet_names:
    print(name)
```

Risultato: individuati correttamente 11 nomi di schede.

Dipendenza HTML: classe CSS `.docs-sheet-tab-caption`.

### GS-02 - Ricerca degli identificativi gid

Codice verificato:

```python
import requests
import re

url = "https://docs.google.com/spreadsheets/d/1W9GWokNp6PSsPNCU35lMx2AAVeFvBqirw22ABT7_cUU/edit?gid=843771997"

html = requests.get(url, timeout=20).text

gids = sorted(set(
    re.findall(r'id="(\d+)-grid-container"', html)
))

print(gids)
```

Risultato: identificato soltanto il gid della scheda attiva, 843771997.

La mappatura completa tra nomi delle schede e relativi gid non è ancora disponibile.

### Prossime attività

1. Individuare tutti i gid e associarli ai nomi.
2. Esaminare i metadati JavaScript incorporati nella pagina.
3. Verificare il recupero automatico delle formattazioni.
4. Integrare il metodo nel backend Djungo.
5. Introdurre test di regressione e fallback.

Stato: ricerca sperimentale, nessuna modifica al codice applicativo.

## CHECKPOINT GS-125 — 16/11/2026

### Importazione Google Sheets

La sorgente può essere acquisita tramite URL pubblico di Google
Sheets e gli endpoint nativi di esportazione, senza OAuth.
Il codice interessato comprende `server.py`,
`generators/google_sheet_source.py` e `docs/generate.html`.
La precedente ricerca GS-01/GS-02 rimane documentazione storica.

### Backend persistente e Viewer

Il backend GAS condiviso implementa `meta`, `view`, `getById`,
`insert`, `update` e `delete`. Il routing persistente è gestito
dal proxy Flask mediante identificativi di applicazione e foglio.

La paginazione considera i record con ID valido, non le righe
fisiche. La ricerca e l'ordinamento globali sono eseguiti
dal backend prima della selezione della pagina.

Il Viewer Tabulator utilizza la paginazione remota quando
riconosce i metadati restituiti dal backend; il generatore
mantiene la compatibilità con il percorso legacy.

### Tipi di dato e rappresentazione

Google Sheets può interpretare celle formattate `h.mm` come
orari. Il backend utilizza `getValues()` per conservare i
valori tipizzati e `getDisplayValues()` per rappresentare
gli oggetti Date nelle risposte `view` e `getById`.

La ricerca confronta i valori visualizzati; l'ordinamento
utilizza i valori tipizzati. La correzione non modifica
il formato né il tipo originale delle celle.

### Aggiornamento e compatibilità

Nel backend persistente, `djungoUpdate_()` controlla formule
e convalide e ignora le celle ricevute con valori invariati.
Il frontend generato continua a poter inviare il modulo intero.
Il backend GAS legacy generato separatamente mantiene
il proprio contratto di aggiornamento.

Il confronto con il valore visualizzato non equivale a una
conversione tipizzata esplicita: tale funzionalità, se richiesta,
dovrà avere un contratto distinto.

### Collaudi e rilascio

- GAS v15: pubblicato sul deployment persistente esistente.
- GS-101, GS-112, GS-120: test JavaScript con simulazioni.
- GS-105 e GS-115: verifiche reali delle letture.
- GS-110: test CRUD reale.
- GS-122: verifica reale della preservazione della cella.
- Dataset di collaudo: 1571 record prima delle prove CRUD,
  32 pagine con dimensione 50.

La trisincronia Ubuntu → GitHub → Hetzner staging deve ancora
essere completata e verificata. La produzione è esclusa.

### GS-138 — Autorità del backend GAS e snapshot Git (16/11/2026)

La fonte autorevole del backend persistente condiviso è il progetto
Google Apps Script. Il comportamento effettivo dell'endpoint /exec
dipende dalla versione associata al deployment GAS attivo.

Il file google/DjungoBackend.gs è uno snapshot locale versionato
per documentazione, confronto e recupero. La sua presenza su Ubuntu,
GitHub o Hetzner non costituisce pubblicazione su Google Apps Script.

Il deployment Git/Hetzner aggiorna Djungo Builder (Flask, generatori,
interfaccia Builder e documentazione), ma non modifica il deployment
GAS né la sua versione pubblicata.

La corrispondenza esatta tra snapshot locale e versione GAS pubblicata
deve essere verificata separatamente; il collaudo funzionale non
dimostra da solo l'identità dei sorgenti.

Le applicazioni HTML generate e le configurazioni persistenti devono
essere gestite separatamente dai sorgenti universali del Builder.
