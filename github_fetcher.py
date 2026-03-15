import os
import time
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
github_token = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization" : f"token: {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

REPO = {
    "microsoft/vscode",
    "django/django",
    "facebook/react"
}

def fetch_pull_requests(repo, max_prs=500):
    """
    Fetches merged pull requests from a given GitHub repository.
    Returns a list of raw PR objects.
    """
    print(f"Fetching PRs from {repo}...")
    
    prs = []
    page = 1

    while len(prs) < max_prs:
        url = f"https://api.github.com/repos/{repo}/pulls"
        
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page
        }

        response = requests.get(url, headers=HEADERS, params=params)

        # Stop if rate limit or error hits
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.json()}")
            break

        data = response.json()

        # No more pages left
        if not data:
            break

        # Only keep MERGED PRs (closed != always merged)
        merged = [pr for pr in data if pr.get("merged_at") is not None]
        prs.extend(merged)

        print(f"  Page {page} → {len(merged)} merged PRs found")

        page += 1
        time.sleep(1)  # Be respectful to GitHub API

    print(f"Total PRs collected from {repo}: {len(prs)}")
    return prs[:max_prs]

def extract_pr_features(pr, repo):
    """
    Extracts relevant features from a single PR object.
    Returns a dictionary of features.
    """
    
    # Calculate review time in hours
    created_at = pd.to_datetime(pr["created_at"])
    merged_at = pd.to_datetime(pr["merged_at"])
    review_time_hours = (merged_at - created_at).total_seconds() / 3600

    return {
        "repo": repo,
        "pr_number": pr["number"],
        "title": pr["title"],
        "lines_added": pr.get("additions", 0),
        "lines_deleted": pr.get("deletions", 0),
        "lines_changed": pr.get("additions", 0) + pr.get("deletions", 0),
        "files_modified": pr.get("changed_files", 0),
        "commit_count": pr.get("commits", 0),
        "review_comments": pr.get("review_comments", 0),
        "num_reviewers": len(pr.get("requested_reviewers", [])),
        "review_time_hours": round(review_time_hours, 2),
        "merged_at": pr["merged_at"],
    }
    
    
def fetch_pr_reviews(repo, pr_number):
    """
    Fetches review details for a single PR.
    Returns approval count and total reviewers who actually reviewed.
    """
    
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        return {"approval_count": 0, "actual_reviewers": 0}
    
    reviews = response.json()
    
    # Count approvals
    approvals = [r for r in reviews if r["state"] == "APPROVED"]
    
    # Count unique reviewers who actually left a review
    unique_reviewers = set(r["user"]["login"] for r in reviews)
    
    return {
        "approval_count": len(approvals),
        "actual_reviewers": len(unique_reviewers)
    }
    
