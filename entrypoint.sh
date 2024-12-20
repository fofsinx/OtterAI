#!/bin/bash
set -e

pip install requests==2.32.3

ls -la /github/workspace

# Run Python script to check if review should be skipped
python3 << 'EOF'
import os
import re
import requests

def should_skip_review():
    # Get PR details from environment variables
    pr_title = os.getenv("PR_TITLE", "")
    pr_description = os.getenv("PR_DESCRIPTION", "")
    pr_state = os.getenv("PR_STATE", "")
    
    # Skip patterns
    skip_patterns = [
        r"\b((?:no|skip)-(?:review|cori|coriai)|cori-(?:no|bye|restricted))(?:,((?:no|skip)-(?:review|cori|coriai)|cori-(?:no|bye|restricted)))*\b"
    ]
    state_patterns = [r"\b(?:merged|closed)\b"]
    
    # Check title and description
    text_to_check = f"{pr_title} {pr_description}"
    for pattern in skip_patterns:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return True
            
    # Check PR state
    for pattern in state_patterns:
        if re.search(pattern, pr_state, re.IGNORECASE):
            return True
            
    return False

def post_skip_comment():
    github_token = os.getenv("INPUT_GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")
    pr_author = os.getenv("PR_AUTHOR")
    
    comment = f"Hey @{pr_author}! 🦦 Looks like you've requested a vacation from code review! I'll be chilling with my fish friends instead! 🐠 Have a splashing good day! 🌊"
    
    # Check for existing comments
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    existing_comments = requests.get(comments_url, headers=headers).json()
    
    # Only post if comment doesn't already exist
    if not any(comment["body"] == comment for comment in existing_comments):
        requests.post(
            comments_url,
            headers=headers,
            json={"body": comment}
        )
        print("💬 Posted skip comment")
    else:
        print("🦜 Looks like I already left my mark here! No need to repeat myself! 🤐")

if should_skip_review():
    print("🦦 Otter taking a coffee break - no review needed! ☕")
    post_skip_comment()
    exit(0)
EOF

# Install cori-ai and all its dependencies
pip install --no-cache-dir cori-ai --upgrade pip

# Install and run ollama if provider is ollama
if [ "$INPUT_PROVIDER" = "ollama-local" ]; then
    curl -fsSL https://ollama.com/install.sh | sh && \
    ollama serve & ollama run "$INPUT_MODEL"
fi

echo "🔍 Detective Otter on the case! Time to review some code! 🕵️‍♂️"
echo "Working directory: $GITHUB_WORKSPACE"

# Run the code review
python -m cori_ai.review