#!/bin/bash
set -e

ls -la /github/workspace

# Check if review should be skipped based on PR title, description and state
check_skip_patterns() {
    local text="$1"
    local skip_patterns="\b((?:no|skip)-(?:review|cori|coriai)|cori-(?:no|bye|restricted))(?:,((?:no|skip)-(?:review|cori|coriai)|cori-(?:no|bye|restricted)))*\b"
    echo "$text" | grep -iE "$skip_patterns" > /dev/null
    return $?
}

check_state_patterns() {
    local state="$1" 
    local state_patterns="\b(?:merged|closed)\b"
    echo "$state" | grep -iE "$state_patterns" > /dev/null
    return $?
}

should_skip_review() {
    local text_to_check="${PR_TITLE} ${PR_DESCRIPTION}"
    
    if check_skip_patterns "$text_to_check" || check_state_patterns "$PR_STATE"; then
        return 0
    fi
    return 1
}

post_skip_comment() {
    local comment="Hey @${PR_AUTHOR}! 🦦 Looks like you've requested a vacation from code review! I'll be chilling with my fish friends instead! 🐠 Have a splashing good day! 🌊"
    local comments_url="https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments"
    
    # Check for existing comments
    local existing_comments=$(curl -s -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer ${INPUT_GITHUB_TOKEN}" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "$comments_url")
    
    # Only post if comment doesn't already exist
    if ! echo "$existing_comments" | grep -Fq "$comment"; then
        curl -s -X POST \
            -H "Accept: application/vnd.github+json" \
            -H "Authorization: Bearer ${INPUT_GITHUB_TOKEN}" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            -H "Content-Type: application/json" \
            -d "{\"body\": \"$comment\"}" \
            "$comments_url"
        echo "💬 Posted skip comment"
    else
        echo "🦜 Looks like I already left my mark here! No need to repeat myself! 🤐"
    fi
}

if should_skip_review; then
    echo "🦦 Otter taking a coffee break - no review needed! ☕"
    post_skip_comment
    exit 0
fi

printenv | sed 's/^\(.*\)$/\1/' > .env

pip install virtualenv

python -m venv .venv

source .venv/bin/activate

pip install --no-cache-dir cori-ai --upgrade pip

(pip show -f cori-ai | grep Requires: | sed 's/Requires://' | tr ',' ' ' | tr ', ' '\n') > cori-ai-requirements.txt

pip install -r cori-ai-requirements.txt

echo "🔍 Detective Otter on the case! Time to review some code! 🕵️‍♂️"

# Run the code review
python -m cori_ai.review

deactivate