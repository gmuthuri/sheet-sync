from datetime import datetime, timezone
import os
import sys
import requests
from dotenv import load_dotenv 

#Load variables from the local .env file
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

#Prevent a silent fail: Validate the token immediately
if not GITHUB_TOKEN:
    print("Error: 'GITHUB_TOKEN' not found in your environment variables!", file=sys.stderr)
    print("Please verify that your local '.env' file exists and contains: GITHUB_TOKEN=your_token_here", file=sys.stderr)
    sys.exit(1)  # Stop execution immediately with an error exit code


REPO = "python/cpython"
url = f"https://api.github.com/repos/{REPO}"

#Package the token securely into the HTTP request headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"  
}

try:
    #Pass the headers dictionary into the get request
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        snapshot_date = datetime.now(timezone.utc).date().isoformat()
        print("\n--- Repository Metrics ---")
        print(f"1. Snapshot Date: {snapshot_date}")
        print(f"2. Repository: {REPO}")
        print(f"3. Stars: {data.get('stargazers_count')}")
        print(f"4. Forks: {data.get('forks_count')}")
        print(f"5. Watchers: {data.get('subscribers_count')}")
        print(f"6. Open issues + PRs: {data.get('open_issues_count')}")
        
        
    else:    
        print(f"Failed: {response.status_code} {response.reason}", file=sys.stderr)
        sys.exit(1)  # non-zero exit code = "this run failed"

except requests.exceptions.Timeout:
    print("Error: The request timed out! The network connection took longer than 10 seconds.", file=sys.stderr)
    sys.exit(1)

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}", file=sys.stderr)
    sys.exit(1)
