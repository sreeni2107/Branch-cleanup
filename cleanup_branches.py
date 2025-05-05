Here is the updated version of your cleanup_branches.py script with Azure DevOps pipeline-compatible logging commands added via print() statements:


---

import os
import requests
from datetime import datetime, timedelta
import base64
import json

# Configuration from environment variables
organization = os.getenv("ORGANIZATION")
project = os.getenv("PROJECT")
pat = os.getenv("PAT")
repo_filter = os.getenv("REPO_NAME")  # Optional repo name
teams_webhook_url = os.getenv("TEAMS_WEBHOOK_URL")  # Optional
is_dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

excluded_branches = ["main", "master", "develop"]
days_threshold = 30
log_file = "deleted_branches.log"

# Authentication header
auth = base64.b64encode(f":{pat}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/json"
}

# Base URL
base_url = f"https://dev.azure.com/{organization}/{project}/_apis"

with open(log_file, "w") as log:
    start_msg = f"Branch cleanup started: {datetime.now()}"
    print(f"##[section]{start_msg}")
    log.write(start_msg + "\n")
    log.write("=" * 50 + "\n")

    # Get all repositories
    repos_url = f"{base_url}/git/repositories?api-version=7.0"
    all_repos = requests.get(repos_url, headers=headers).json().get('value', [])

    if repo_filter:
        repos = [r for r in all_repos if r['name'].lower() == repo_filter.lower()]
        if not repos:
            error_msg = f"Repository '{repo_filter}' not found in project '{project}'"
            print(f"##[error]{error_msg}")
            log.write(error_msg + "\n")
            exit(1)
    else:
        repos = all_repos

    for repo in repos:
        repo_id = repo['id']
        repo_name = repo['name']
        print(f"##[section]Repository: {repo_name}")
        log.write(f"\nRepository: {repo_name}\n")

        branches_url = f"{base_url}/git/repositories/{repo_id}/refs?filter=heads/&api-version=7.0"
        branches = requests.get(branches_url, headers=headers).json().get('value', [])

        for branch in branches:
            branch_name = branch['name'].replace('refs/heads/', '')
            if branch_name in excluded_branches:
                continue

            commits_url = f"{base_url}/git/repositories/{repo_id}/commits?searchCriteria.itemVersion.version={branch_name}&$top=1&api-version=7.0"
            commits = requests.get(commits_url, headers=headers).json().get('value', [])

            if not commits:
                msg = f"Skipping '{branch_name}' (no commits found)"
                print(msg)
                log.write(f"  {msg}\n")
                continue

            last_commit_date = datetime.strptime(commits[0]['author']['date'], "%Y-%m-%dT%H:%M:%S%z")
            if last_commit_date < datetime.now(last_commit_date.tzinfo) - timedelta(days=days_threshold):
                msg = f"[DRY RUN] Would delete '{branch_name}'" if is_dry_run else f"Deleting '{branch_name}'"
                print(f"{msg} - last commit: {last_commit_date}")
                log.write(f"  {msg} - last commit: {last_commit_date}\n")

                if not is_dry_run:
                    delete_url = f"{base_url}/git/repositories/{repo_id}/refs?filter=heads/{branch_name}&api-version=7.0"
                    response = requests.delete(delete_url, headers=headers)
                    if response.status_code == 204:
                        print(f"##[command]Deleted branch '{branch_name}' successfully.")
                        log.write("    Deleted successfully\n")
                    else:
                        print(f"##[error]Failed to delete branch '{branch_name}': {response.status_code} {response.text}")
                        log.write(f"    Failed to delete: {response.status_code} {response.text}\n")
            else:
                print(f"Keeping '{branch_name}' - last commit: {last_commit_date}")
                log.write(f"  Keeping '{branch_name}' - last commit: {last_commit_date}\n")

# Optional Teams webhook notification
if teams_webhook_url:
    with open(log_file, "r") as log:
        content = log.read()
    payload = {
        "text": f"**Azure DevOps Branch Cleanup Completed:**\n```\n{content[-4000:]}\n```"
    }
    try:
        response = requests.post(
            teams_webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        if response.status_code == 200:
            print("Notification sent to Microsoft Teams.")
        else:
            print(f"##[error]Failed to send Teams notification: {response.status_code}")
    except Exception as e:
        print(f"##[error]Error sending Teams notification: {e}")


---

Key Azure DevOps logging features added:

##[section] for visual log separation per repo or stage.

##[command] to highlight operations like deletions.

##[error] for failures to make them stand out and be captured in pipeline error reports.


Let me know if you want to also:

Upload this updated script file.

Add unit tests or dry-run test commands.

Send a summary to Teams only when real deletions happen.


