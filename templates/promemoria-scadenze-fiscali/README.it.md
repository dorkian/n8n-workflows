# Promemoria Scadenze Fiscali

> Invia ogni giorno un promemoria a 7 giorni e uno urgente a 2 giorni a ogni cliente prima della scadenza fiscale, senza controlli manuali.

[English version](README.md)

## Cosa fa

Gira **ogni giorno alle 08:00 (Europe/Rome)**. Per ogni riga del foglio Google `Scadenze`:

| Quando | Azione |
|---|---|
| 7-3 giorni prima della scadenza, se il promemoria a 7gg non è ancora stato inviato | Invia al cliente un'email di promemoria (blu) |
| 0-2 giorni prima della scadenza, se il promemoria a 2gg non è ancora stato inviato | Invia un'email urgente (rossa) |
| Riga senza ID, senza email o con data non valida | Scrive nella scheda `Errori`, nessuna email inviata |
| Scadenza a più di 7 giorni | Saltata, ricontrollata il giorno dopo |

Se un cliente ha più scadenze nello stesso giorno riceve **una sola email** con l'elenco. Dopo ogni invio il flusso scrive data e stato nella riga, così sai sempre cosa è stato inviato e quando.

## Cosa serve

- n8n 1.0.0 o successivo (self-hosted o cloud)
- Un account Google per Google Sheets e Gmail (basta il piano gratuito)

## Struttura del foglio

Una scheda chiamata esattamente `Scadenze` (maiuscole/minuscole contano). Intestazioni nella riga 1: vedi [`sheets/scadenze.csv`](sheets/scadenze.csv).

| Colonna | Intestazione | Note |
|---|---|---|
| A | ID Scadenza | ID univoco per riga (es. `ROSSI-IVA-2026-Q2`). Obbligatorio: il flusso aggiorna le righe tramite questo ID |
| B | Cliente | Nome del cliente |
| C | Email | Email del cliente |
| D | Tipo Scadenza | Es. IVA, F24, Unico PF, INPS |
| E | Data Scadenza | `GG/MM/AAAA` oppure `AAAA-MM-GG` |
| F | Reminder 7gg Inviato | Lascia vuoto: il flusso scrive `SI` |
| G | Data Invio 7gg | Lascia vuoto: il flusso scrive la data |
| H | Reminder 2gg Inviato | Lascia vuoto: il flusso scrive `SI` |
| I | Data Invio 2gg | Lascia vuoto: il flusso scrive la data |
| J | Stato | Lascia vuoto: `promemoria-7gg` o `promemoria-2gg` |
| K | Ultimo Errore | Lascia vuoto: descrizione dell'errore se una riga fallisce |

Serve anche una scheda `Errori`: vedi [`sheets/errori.csv`](sheets/errori.csv).

## Installazione

1. In n8n: **+ → Import from file** e carica [`workflow.json`](workflow.json). Salva.
2. Crea due credenziali con lo stesso account Google: **Google Sheets OAuth2** e **Gmail OAuth2**, poi assegnale ai nodi corrispondenti.
3. Apri il nodo **Workflow Config** e compila:

| Campo | Valore |
|---|---|
| `SHEET_ID` | ID del foglio (nell'URL: `/d/QUESTA_PARTE/edit`) |
| `STUDIO_EMAIL` | Email dello studio, usata per test ed errori |
| `STUDIO_NAME` | Nome dello studio nella firma delle email |
| `TEST_MODE` | `false` in produzione. `true` reindirizza tutte le email a `STUDIO_EMAIL` |

4. **Prova in TEST_MODE:** imposta `TEST_MODE = true`, aggiungi una riga con scadenza tra 5 giorni, premi **Test workflow**. Devi ricevere il promemoria a 7gg sulla tua email e vedere le colonne F-J aggiornate. Poi rimetti `TEST_MODE = false`.
5. Attiva il flusso con l'interruttore in alto a destra.

## Scadenze ricorrenti

All'inizio di ogni anno azzera `Reminder 7gg Inviato`, `Reminder 2gg Inviato` e `Stato` (e, se vuoi, le date di invio) sulle righe dell'anno nuovo, oppure aggiungi righe nuove con un nuovo `ID Scadenza`.

## Problemi comuni

| Problema | Causa | Soluzione |
|---|---|---|
| Nessuna email inviata | Nessuna riga con scadenza entro 0-7 giorni | Aggiungi una riga di prova con la data giusta |
| "Authentication failed" | Token OAuth scaduto | Settings → Credentials → riconnetti |
| Riga non aggiornata dopo l'invio | `SHEET_ID` o nome scheda errati | Controlla `SHEET_ID`; la scheda deve chiamarsi `Scadenze` |
| La scheda `Errori` si riempie | Righe senza ID, con data non valida o senza email | Correggi i dati e svuota `Ultimo Errore` |
| Il cliente riceve promemoria doppi | La colonna `Reminder Xgg Inviato` è stata svuotata a mano | Non cancellare quelle colonne: il flusso reinvia se il flag è vuoto |

Licenza MIT.
