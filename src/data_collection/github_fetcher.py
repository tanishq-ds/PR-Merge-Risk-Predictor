import os
import time
import requests
from dotenv import load_dotenv
import pandas as pd
import dotenv

load_dotenv(dotenv.find_dotenv())
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization" : f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

REPOS = {
    "microsoft/vscode",
    "facebook/react",
    "expressjs/express"
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

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.json()}")
            break

        data = response.json()

        if not data:
            break

        merged = [pr for pr in data if pr.get("merged_at") is not None]
        prs.extend(merged)

        print(f"  Page {page} → {len(merged)} merged PRs found")

        page += 1
        time.sleep(1)  

    print(f"Total PRs collected from {repo}: {len(prs)}")
    return prs[:max_prs]

def extract_pr_features(pr, repo):
    """
    Extracts relevant features from a single PR object.
    Returns a dictionary of features.
    """

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
    
    approvals = [r for r in reviews if r["state"] == "APPROVED"]

    unique_reviewers = set(r["user"]["login"] for r in reviews)
    
    return {
        "approval_count": len(approvals),
        "actual_reviewers": len(unique_reviewers)
    }
    

def fetch_ci_status(repo, pr):
    """
    Fetches the CI pipeline status for a pull request.
    Returns 'passed', 'failed', or 'none'.
    """

    head_sha = pr["head"]["sha"]
    
    url = f"https://api.github.com/repos/{repo}/commits/{head_sha}/check-runs"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        return "none"
    
    data = response.json()
    check_runs = data.get("check_runs", [])
    
    if not check_runs:
        return "none"

    statuses = [run["conclusion"] for run in check_runs]
    
    if "failure" in statuses:
        return "failed"
    elif all(s == "success" for s in statuses):
        return "passed"
    else:
        return "none"
    
    
def fetch_developer_stats(repo, pr):
    """
    Fetches statistics about the PR author.
    Returns total commits and previous PR failures.
    """
    
    author = pr["user"]["login"]

    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"author": author, "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        return {"developer_total_commits": 0, "previous_pr_failures": 0}
    
    commits = response.json()
    developer_total_commits = len(commits)

    url = f"https://api.github.com/repos/{repo}/pulls"
    params = {
        "state": "closed",
        "per_page": 100
    }
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        return {"developer_total_commits": developer_total_commits, "previous_pr_failures": 0}
    
    all_prs = response.json()

    author_prs = [p for p in all_prs if p["user"]["login"] == author]

    previous_pr_failures = len([
        p for p in author_prs 
        if p["merged_at"] is None
    ])
    
    return {
        "developer_total_commits": developer_total_commits,
        "previous_pr_failures": previous_pr_failures
    }
    

def fetch_revert_commits(repo):
    """
    Fetches all revert commits from the repo.
    Returns a list of (message, date) tuples.
    """
    print(f"  Fetching revert commits for {repo}...")
    
    url = f"https://api.github.com/repos/{repo}/commits"
    params = {"per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"  Error fetching commits: {response.status_code}")
        return []
    
    commits = response.json()
    revert_commits = []
    
    for commit in commits:
        message = commit["commit"]["message"].lower()
        date = pd.to_datetime(commit["commit"]["committer"]["date"])
        
        if any(word in message for word in ["revert", "rollback"]):
            revert_commits.append({
                "message": message,
                "date": date
            })
    
    print(f"  Found {len(revert_commits)} revert commits")
    return revert_commits


def fetch_hotfix_prs(repo):
    """
    Fetches all hotfix PRs from the repo.
    Returns a list of hotfix PR objects.
    """
    print(f"  Fetching hotfix PRs for {repo}...")
    
    url = f"https://api.github.com/repos/{repo}/pulls"
    params = {"state": "all", "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"  Error fetching PRs: {response.status_code}")
        return []
    
    pulls = response.json()
    hotfix_prs = []
    
    for pr in pulls:
        title = pr["title"].lower()
        if any(word in title for word in ["hotfix", "fix", "patch", "revert"]):
            hotfix_prs.append({
                "title": title,
                "body": (pr.get("body") or "").lower(),
                "created_at": pd.to_datetime(pr["created_at"])
            })
    
    print(f"  Found {len(hotfix_prs)} hotfix PRs")
    return hotfix_prs


def fetch_bug_issues(repo):
    """
    Fetches all bug issues from the repo.
    Returns a list of bug issue objects.
    """
    print(f"  Fetching bug issues for {repo}...")
    
    url = f"https://api.github.com/repos/{repo}/issues"
    params = {"state": "all", "per_page": 100, "labels": "bug"}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    
    if response.status_code != 200:
        print(f"  Error fetching issues: {response.status_code}")
        return []
    
    issues = response.json()
    bug_issues = []
    
    for issue in issues:
        bug_issues.append({
            "body": (issue.get("body") or "").lower(),
            "title": issue["title"].lower(),
            "created_at": pd.to_datetime(issue["created_at"])
        })
    
    print(f"  Found {len(bug_issues)} bug issues")
    return bug_issues


def label_pr(pr, revert_commits, hotfix_prs, bug_issues):
    """
    Labels a PR as risky (1) or clean (0) using pre-fetched data.
    """
    
    pr_number = pr["number"]
    pr_title = pr["title"].lower()
    merged_at = pd.to_datetime(pr["merged_at"])
    window = pd.Timedelta(days=30)
      
    # ① Check revert commits
    for commit in revert_commits:
        if (
            (f"#{pr_number}" in commit["message"] or 
             any(word in commit["message"] for word in pr_title.split())) and
            commit["date"] > merged_at and
            commit["date"] <= merged_at + window
        ):
            return 1
    
    # ② Check hotfix PRs
    for hotfix in hotfix_prs:
        if (
            (f"#{pr_number}" in hotfix["title"] or 
             f"#{pr_number}" in hotfix["body"]) and
            hotfix["created_at"] > merged_at and
            hotfix["created_at"] <= merged_at + window
        ):
            return 1
    
    # ③ Check bug issues
    for issue in bug_issues:
        if (
            f"#{pr_number}" in issue["body"] and
            issue["created_at"] > merged_at and
            issue["created_at"] <= merged_at + window
        ):
            return 1
    
    return 0


def collect_dataset():
    """
    Main pipeline function that ties everything together.
    Collects PR data from all repos and saves to CSV.
    """
    
    all_rows = []
    
    for repo in REPOS:
        # Pre-fetch once per repo
        revert_commits = fetch_revert_commits(repo)
        hotfix_prs = fetch_hotfix_prs(repo)
        bug_issues = fetch_bug_issues(repo)
        
        prs = fetch_pull_requests(repo, max_prs=500)
        
        for pr in prs:
            try:
                # Step 1 — Extract basic features FIRST
                row = extract_pr_features(pr, repo)
                
                # Step 2 — Fetch review details
                reviews = fetch_pr_reviews(repo, pr["number"])
                row.update(reviews)
                
                # Step 3 — Fetch CI status
                row["ci_status"] = fetch_ci_status(repo, pr)
                
                # Step 4 — Fetch developer stats
                dev_stats = fetch_developer_stats(repo, pr)
                row.update(dev_stats)
                
                # Step 5 — Label the PR (only once!)
                risk = label_pr(pr, revert_commits, hotfix_prs, bug_issues)
                row["merge_risk"] = risk
                
                # Step 6 — Show progress
                label = "🔴 RISKY" if risk == 1 else "✅ CLEAN"
                print(f"  PR #{pr['number']} → {label}")
                
                all_rows.append(row)
                time.sleep(1)
                
            except Exception as e:
                print(f"  Skipping PR #{pr['number']} due to error: {e}")
                continue

    # Save to CSV
    df = pd.DataFrame(all_rows)
    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/pr_data.csv", index=False)

    print(f"\n✅ Dataset saved to data/raw/pr_data.csv")
    print(f"✅ Total PRs collected: {len(df)}")

    if len(df) > 0:
        print(f"✅ Risky PRs: {df['merge_risk'].sum()}")
        print(f"✅ Clean PRs: {len(df) - df['merge_risk'].sum()}")
    else:
        print("⚠️ No PRs collected — check errors above")


# Entry point
if __name__ == "__main__":
    collect_dataset()