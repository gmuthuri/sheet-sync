from datetime import datetime, timezone  # today's date; timezone.utc so "today" is always the UTC day
import time                              # time.sleep() for the pause between retries
import os                                # os.getenv() reads settings from the environment
import sys                               # sys.exit(1) is the "this run failed" signal to the scheduler
import requests                          # makes the HTTP call to the GitHub API
from dotenv import load_dotenv           # loads the local .env file (nothing to load on GitHub's runner)
import logging                           # timestamped log lines, to a file and to the screen
import gspread                           # talks to Google Sheets

# Read .env into the environment. This must run BEFORE any os.getenv() call below.
load_dotenv()
MAX_ATTEMPTS = 3

def open_sheet():
    # Log in as the service account ("the robot") with its key file, open the spreadsheet
    # by its title, and return the first tab.
    gc = gspread.service_account(filename="service_account.json")  
    return gc.open(SHEET_NAME).sheet1                   


def fetch_repo():
    for attempt in range(1, MAX_ATTEMPTS + 1):          # attempt = 1, 2, 3    
        try:
            response = requests.get(url, headers=headers, timeout=10) # timeout: a silent connection can't hang the job
            break                            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt == MAX_ATTEMPTS:        # last try failed, so stop retrying         
                raise                        
            logging.warning(f"Attempt {attempt} of {MAX_ATTEMPTS} failed: {e}")
            time.sleep(2 * attempt)        # backoff: wait 2 s after attempt 1, 4 s after attempt 2 
    return response  # hand the result back to whoever called fetch_repo()

# ---------------------------------------------------------------------------
# LOGGING SETUP
# Every logging.info / warning / error line goes to BOTH sheet_sync.log and the screen.
# On GitHub's runner the log file is thrown away after the run, so the run's console
# output on the Actions tab is the log you read there.
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,  # show INFO and anything more serious
    format="%(asctime)s %(levelname)s %(message)s",  # each line starts with time and level
    handlers=[
        logging.FileHandler("sheet_sync.log"),  # write lines to a file
        logging.StreamHandler(),         # also show them on screen
    ],
)

# ---------------------------------------------------------------------------
# SETTINGS CHECKS (fail fast)
# If a setting is missing, stop now with a clear message instead of failing later
# with a confusing one.
# ---------------------------------------------------------------------------

SHEET_NAME = os.getenv("SHEET_NAME")
#Prevent a silent fail: Validate the Sheet name exist
if not SHEET_NAME:
    logging.error("Error: 'SHEET_NAME' not found in your environment variables!")
    logging.error("Please verify that your local '.env' file exists and contains: SHEET_NAME=your sheet title")
    sys.exit(1)  # stop immediately; the non-zero exit code makes the scheduler show the run as failed

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

#Prevent a silent fail: Validate the token immediately
if not GITHUB_TOKEN:
    logging.error("Error: 'GITHUB_TOKEN' not found in your environment variables!")
    logging.error("Please verify that your local '.env' file exists and contains: GITHUB_TOKEN=your_token_here")
    sys.exit(1)  # Stop execution immediately with an error exit code


REPO = "python/cpython"

url = f"https://api.github.com/repos/{REPO}"

#Package the token securely into the HTTP request headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"  
}

# ---------------------------------------------------------------------------
# MAIN FLOW
# Every error path below logs an ERROR line and calls sys.exit(1).
# ---------------------------------------------------------------------------

try:
    # STEP 1: fetch from GitHub (retries happen inside fetch_repo)
    #Pass the headers dictionary into the get request
    response = fetch_repo()    
    logging.info(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        # STEP 2: build today's row. The date is made here, in UTC; the API does not provide it.
        data = response.json()
        
        snapshot_date = datetime.now(timezone.utc).date().isoformat()
        FIELDS = ["stargazers_count", "forks_count", "subscribers_count", "open_issues_count"]    # the field names this API must give us

        bad = [f for f in FIELDS if not isinstance(data.get(f), (int, float))]  # names that are missing or not numbers
        if bad:
            logging.error(f"API response is missing or invalid fields: {bad}")  # say exactly which ones
            sys.exit(1)                                                         # red run, nothing written

        row = [snapshot_date, REPO, data.get('stargazers_count'), data.get('forks_count'), data.get('subscribers_count'), data.get('open_issues_count')]                      
        
        # STEP 3: open the sheet and read what is already there
        sheet = open_sheet()                                  
        
        existing = sheet.get_all_values()                     # every row currently in the sheet
        seen = {(r[0], r[1]) for r in existing if len(r) >= 2}  # (date, repo) pairs; skips any short or blank rows

        # STEP 4: duplicate check. The key is "date + repo", the pair designed in Step 1.
        # A skip is NOT an error, so the script exits 0.
        if (snapshot_date, REPO) in seen:                     # has this exact pair been recorded already?
            logging.info(f"Skipped: {REPO} already recorded for {snapshot_date}")
        else:
            # RAW = store the text exactly as sent. Otherwise Sheets may turn "2026-10-12" into a
            # real date value and the duplicate check would stop matching.
            sheet.append_row(row, value_input_option="RAW")   # only write when the pair is new and stored exactly as sent                  
            logging.info(f"Row Added: {REPO} on  Snapshot date={snapshot_date}, stars={data.get('stargazers_count')}, Forks={data.get('forks_count')}, Watchers={data.get('subscribers_count')}, Open issues + PRs={data.get('open_issues_count')}")
          
        
    else:    
        logging.error(f"Failed: {response.status_code} {response.reason}")
        sys.exit(1)  # non-zero exit code = "this run failed"

except requests.exceptions.Timeout:
    logging.error("Error: The request timed out! The network connection Timed out after {MAX_ATTEMPTS} attempts.")
    sys.exit(1)

except (gspread.exceptions.GSpreadException, FileNotFoundError) as e:                      # Google rejected a request (e.g. sheet not shared)
    logging.error(f"Google Sheets error: {e}")
    sys.exit(1)

except requests.exceptions.RequestException as e:
    logging.error(f"An error occurred: {e}")
    sys.exit(1)

except Exception as e:
    logging.exception("Unexpected error") # logs the full traceback
    sys.exit(1)
