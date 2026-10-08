from datetime import datetime, timezone
import os
import sys
import requests
from dotenv import load_dotenv 
import logging

logging.basicConfig(
    level=logging.INFO,  # show INFO and anything more serious
    format="%(asctime)s %(levelname)s %(message)s",  # each line starts with time and level
    handlers=[
        logging.FileHandler("sheet_sync.log"),  # write lines to a file
        logging.StreamHandler(),         # also show them on screen
    ],
)

#Load variables from the local .env file
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

#Prevent a silent fail: Validate the token immediately
if not GITHUB_TOKEN:
    logging.error("Error: 'GITHUB_TOKEN' not found in your environment variables!")
    logging.info("Please verify that your local '.env' file exists and contains: GITHUB_TOKEN=your_token_here")
    sys.exit(1)  # Stop execution immediately with an error exit code


REPO = "python/cpytho"
url = f"https://api.github.com/repos/{REPO}"

#Package the token securely into the HTTP request headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"  
}

try:
    #Pass the headers dictionary into the get request
    response = requests.get(url, headers=headers, timeout=10)
    
    logging.info(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        snapshot_date = datetime.now(timezone.utc).date().isoformat()
        print("\n--- Repository Metrics ---")
        logging.info(f"Fetched {REPO}: Snapshot date={snapshot_date}, stars={data.get('stargazers_count')}, Forks={data.get('forks_count')}, Watchers={data.get('subscribers_count')}, Open issues + PRs={data.get('open_issues_count')}")
        
        
        
    else:    
        logging.error(f"Failed: {response.status_code} {response.reason}")
        sys.exit(1)  # non-zero exit code = "this run failed"

except requests.exceptions.Timeout:
    logging.error("Error: The request timed out! The network connection took longer than 10 seconds.")
    sys.exit(1)

except requests.exceptions.RequestException as e:
    logging.error(f"An error occurred: {e}")
    sys.exit(1)
