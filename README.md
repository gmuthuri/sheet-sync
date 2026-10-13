# Daily Data to Google Sheets, Automated

**Stop copying numbers into a spreadsheet by hand every morning.**

Many small businesses have someone who opens a web service each day, copies the latest figures, and pastes them into Google Sheets. It is slow, it is boring, and it goes wrong: days get skipped, rows get pasted twice, and nobody notices.

This project replaces that routine. Once a day, on its own, it fetches the latest numbers and adds one new row to your Google Sheet.

> This is a sample project built from a simulated client brief. It uses public GitHub statistics as stand-in data, so anyone can check that it works.

## What it does

- **Runs by itself every day.** No one has to remember or click anything.
- **Adds exactly one row per day.** It checks the sheet first, so running it twice never creates duplicate rows.
- **Keeps a record.** Every run writes plain log lines saying what happened.
- **Fails honestly.** If something breaks, the run is marked as failed. It never pretends to have succeeded.

## What the sheet looks like

docs/sheet.png

## How it protects your data

- **It does not hang.** If the connection is slow or silent, it gives up after 10 seconds instead of waiting forever.
- **It retries.** On temporary network trouble it tries up to 3 times, pausing a little longer each time.
- **No double rows.** A row is identified by its date plus the item tracked. If that pair is already in the sheet, the run skips it.
- **Clear stops.** If a required setting is missing (a token, the sheet name, the key file), it stops straight away with a plain message.
- **Passwords stay private.** Secrets live in environment variables or GitHub Secrets, never in the code.

## Sample log output

```text
2026-10-12 09:30:08,734 ERROR Error: 'SHEET_NAME' not found in your environment variables!
2026-10-12 09:30:08,734 INFO Please verify that your local '.env' file exists and contains: SHEET_NAME=your_token_here
2026-10-12 11:27:47,332 WARNING Attempt 1 of 3 failed: HTTPSConnectionPool(host='api.github.com', port=443): Read timed out. (read timeout=10)
2026-10-12 11:28:13,303 INFO Status Code: 200
2026-10-12 11:28:24,078 INFO Skipped: python/cpython already recorded for 2026-10-12
2026-10-12 14:41:20,151 INFO Status Code: 200
2026-10-12 14:41:27,447 INFO Fetched and Row Added for python/cpython on 2026-10-12 python/cpython: Snapshot date=2026-10-12, stars=77614, Forks=38101, Watchers=1660, Open issues + PRs=9723
```


## Want something like this for your business?

I build small automations that move data from a web service into Google Sheets and keep it there reliably. Message me on [mgibum@gmail.com]

---

# Technical details

## How it works

`fetch.py` calls the GitHub REST API (with retries and a timeout), builds one row, opens the Google Sheet through a service account, checks for an existing row with the same date and repo, and appends only if there is none.

## Run it locally

1. **Clone and set up**
   ```powershell
   git clone https://github.com/gmuthuri/sheet-sync.git
   cd sheet-sync
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Google setup (one time)**
   - Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
   - Create a **service account** and download its JSON key as `service_account.json` in the project folder. Never commit this file.
   - Create a Google Sheet with this header row: `Snapshot Date, Repo, Stars, Forks, Watchers, Open Issues + PRs`.
   - Share the sheet with the service account's `client_email`, with **Editor** access.
3. **Create a `.env` file** (also never committed):
   ```text
   GITHUB_TOKEN=your_fine_grained_token
   SHEET_NAME=your sheet title
   ```
4. **Run**
   ```powershell
   python fetch.py
   ```

Exit code `0` means success or a harmless skip. Exit code `1` means the run failed.

## Scheduling (GitHub Actions)

The workflow in `.github/workflows/sheet-sync.yml` runs once a day and can also be started by hand from the Actions tab. It needs three repository secrets:

| Secret | Contains |
|---|---|
| `GH_API_TOKEN` | the GitHub token |
| `SHEET_NAME` | the sheet title |
| `SERVICE_ACCOUNT_JSON` | the full contents of the service account key file |

Schedules run in UTC, and GitHub may start a run some minutes late.

## Maintenance notes

- The GitHub token expires on the date you set. After that, runs fail with a 401 error until you replace it.
- GitHub pauses scheduled workflows in repositories with no activity for 60 days.
- Log lines appear in each run's output on the Actions tab. The runner is deleted afterwards, so no log file is kept.

## Known limitations

- It tracks one repository per run.
- It retries on timeouts and dropped connections, but not on `429 Too Many Requests` or `503 Service Unavailable` responses.
- The sheet must be shared with the service account's email address.
- If someone retypes a date in the sheet by hand, the duplicate check may not recognize it.
- "Open Issues + PRs" counts both issues and pull requests, because that is how the GitHub API reports it.

## Project origin

Built under a simulated client brief: replace a manual daily copy-and-paste into Google Sheets with a scheduled job that skips duplicates, survives network trouble, and reports failures. No real client or paid work is involved.