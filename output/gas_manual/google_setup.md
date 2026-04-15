# Google Apps Script setup guide

## Project summary
- Project name: Prova_film
- Project slug: prova-film
- Backend logical name: prova-film-backend
- Sheet name: ProvaFilmData

## Files prepared
- codice.gs
- fields.schema.json
- project.config.json
- deploy.manifest.json
- sample_rows.json
- sample_rows.csv

## Suggested Google flow

### 1. Create the Google Sheet
Create a new Google Sheet and rename the main tab exactly as:

    ProvaFilmData

### 2. Create the header row
Insert these headers in row 1, from column A onward:

    id, Titolo, Data Produzione

### 3. Insert example rows
You have two prepared files:

- sample_rows.json
- sample_rows.csv

Suggested use:
- use `sample_rows.csv` if you want a quick import structure
- use `sample_rows.json` if you want to inspect the data clearly first

### 4. Create a new Apps Script project
Suggested project name:

    Prova_film Backend

### 5. Replace script content
Open:

    codice.gs

Copy everything into the Apps Script editor.

### 6. Deploy as Web App
Use the Apps Script deploy flow:

- Deploy → New deployment
- Type: Web app
- Execute as: Me
- Access: Anyone

Then copy the /exec URL.

### 7. Connect frontend
Paste the /exec URL into your frontend configuration.

## Notes
- No clasp required
- No Google API required
- Fully manual but controlled setup
