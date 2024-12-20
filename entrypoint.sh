#!/bin/bash
set -e

# Check if review should be skipped
if echo "$PR_TITLE $PR_DESCRIPTION" | grep -iE "(no|skip)(-|\\s)?(review|cori|coriai)|cori(-|\\s)?(no|bye|restricted)" || \
   echo "$PR_STATE" | grep -iE "\b(merged|closed)\b"; then
    echo "🦦 Otter taking a coffee break - no review needed! ☕"
    
    # Add skip comment if not already present
    COMMENT="Hey @$PR_AUTHOR! 🦦 Looks like you've requested a vacation from code review! I'll be chilling with my fish friends instead! 🐠 Have a splashing good day! 🌊"
    
    # Use GitHub API to add comment (only if it doesn't exist)
    check_comment=$(curl -L -s -H "Authorization: Bearer $INPUT_GITHUB_TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments" | jq -r '.[] | select(.body == "'$COMMENT'") | .id')
    
    if [ -z "$check_comment" ]; then
        curl -L -s -X POST -H "Authorization: Bearer $INPUT_GITHUB_TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" -d "{\"body\":\"$COMMENT\"}" "https://api.github.com/repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments"
    fi
    
    exit 0
fi

# Install cori-ai and all its dependencies
pip install --no-cache-dir cori-ai --upgrade pip

# Install and run ollama if provider is ollama
if [ "$INPUT_PROVIDER" = "ollama-local" ]; then \
    curl -fsSL https://ollama.com/install.sh | sh && \
    ollama serve & ollama run "$INPUT_MODEL"; \
fi

echo "🔍 Detective Otter on the case! Time to review some code! 🕵️‍♂️"
echo "Working directory: $GITHUB_WORKSPACE"

# Run the code review
python -m cori_ai.review