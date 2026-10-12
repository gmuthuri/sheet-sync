from datetime import datetime, timezone
import time
import os
import sys
import requests
from dotenv import load_dotenv 
import logging
import gspread
load_dotenv()

SHEET_NAME = os.getenv("SHEET_NAME")
def open_sheet():
    gc = gspread.service_account(filename="service_account.json")  # log in as the robot using the key file
    return gc.open(SHEET_NAME).sheet1                     # open the spreadsheet by name, take its first tab


def fetch_repo():
    for attempt in range(1, MAX_ATTEMPTS + 1):              
        try:
            response = requests.get(url, headers=headers, timeout=10)
            break                            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt == MAX_ATTEMPTS:                 
                raise                        
            logging.warning(f"Attempt {attempt} of {MAX_ATTEMPTS} failed: {e}")
            time.sleep(2 * attempt)         
    return response  # hand the result back to whoever called fetch_repo()

logging.basicConfig(
    level=logging.INFO,  # show INFO and anything more serious
    format="%(asctime)s %(levelname)s %(message)s",  # each line starts with time and level
    handlers=[
        logging.FileHandler("sheet_sync.log"),  # write lines to a file
        logging.StreamHandler(),         # also show them on screen
    ],
)

#Load variables from the local .env file

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

#Prevent a silent fail: Validate the token immediately
if not GITHUB_TOKEN:
    logging.error("Error: 'GITHUB_TOKEN' not found in your environment variables!")
    logging.info("Please verify that your local '.env' file exists and contains: GITHUB_TOKEN=your_token_here")
    sys.exit(1)  # Stop execution immediately with an error exit code


REPO = "python/cpython"
MAX_ATTEMPTS = 3
url = f"https://api.github.com/repos/{REPO}"

#Package the token securely into the HTTP request headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"  
}

try:
    #Pass the headers dictionary into the get request
    response = fetch_repo()
    
    logging.info(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        snapshot_date = datetime.now(timezone.utc).date().isoformat()

        row = [snapshot_date, REPO, data.get('stargazers_count'), data.get('forks_count'), data.get('subscribers_count'), data.get('open_issues_count')]                      # you fill in the four metrics, in header order
        sheet = open_sheet()                                  # get the tab
        sheet.append_row(row, value_input_option="RAW")       # add the row, stored exactly as sent
        
        logging.info("Row added")
        logging.info(f"Fetched {REPO}: Snapshot date={snapshot_date}, stars={data.get('stargazers_count')}, Forks={data.get('forks_count')}, Watchers={data.get('subscribers_count')}, Open issues + PRs={data.get('open_issues_count')}")
        
        
        
    else:    
        logging.error(f"Failed: {response.status_code} {response.reason}")
        sys.exit(1)  # non-zero exit code = "this run failed"

except requests.exceptions.Timeout:
    logging.error("Error: The request timed out! The network connection took longer than 10 seconds.")
    sys.exit(1)

except gspread.exceptions.APIError as e:                      # Google rejected a request (e.g. sheet not shared)
    logging.error(f"Google Sheets error: {e}")
    sys.exit(1)

except requests.exceptions.RequestException as e:
    logging.error(f"An error occurred: {e}")
    sys.exit(1)
