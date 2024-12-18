#!/bin/bash

# Initialize error counter
errors=0
pattern="\b(?:(?:no|skip)-(?:review|otter|otterai)|otter-(?:no|bye|restricted))(?:,(?:(?:no|skip)-(?:review|otter|otterai)|otter-(?:no|bye|restricted)))*\b"

# Function to simulate the "Check if review is requested" step
check_review_requested() {
  PR_TITLE="$1"
  if echo "$PR_TITLE" | grep -Eiq "$pattern"; then
    echo "🦦 No review requested, skipping code review"
    return 1
  else
    echo "🔍 Code review requested"
    return 0
  fi
}

# Function to simulate the "Check if PR is merged" step
check_pr_merged() {
  PR_STATE="$1"
  pattern="\b(?:merged|closed)\b"
  
  if echo "$PR_STATE" | grep -Eiq "$pattern"; then
    echo "🦦 PR is merged, skipping code review"
    return 1
  else
    echo "🔍 PR is not merged, proceeding with code review"
    return 0
  fi
}

# Array of test descriptions and their expected outcomes
review_descriptions=(
  "Test1_NoReview"
  "Test2_SkipReview"
  "Test3_SkipOtter"
  "Test4_NoOtterAI"
  "Test5_OtterRestricted"
  "Test6_OtterBye"
  "Test7_MultipleFlags"
  "Test8_StandardFeature"
  "Test9_ConventionalCommit"
  "Test10_BugFix"
  "Test11_Documentation"
  "Test12_Maintenance"
  "Test13_Testing"
  "Test14_CodeRefactor"
  "Test15_Formatting"
  "Test16_Performance"
  "Test17_NoSkipFlags"
)

review_titles=(
  "no-review: Update authentication system :false"
  "Important security patch but skip-review please :false" 
  "Refactor database layer with skip-otter flag :false"
  "Backend optimization with no-otterai needed :false"
  "Frontend changes otter-restricted due to sensitivity :false"
  "Critical hotfix otter-bye emergency deploy :false"
  "Infrastructure update no-review,skip-otter,otter-restricted :false"
  "Add user management features and improve UI :true"
  "feat: implement new logging system :true"
  "fix: resolve authentication bug :true"
  "docs: update API documentation :true"
  "chore: upgrade dependencies :true"
  "test: add integration tests :true"
  "refactor: optimize database queries :true"
  "style: format code according to standards :true"
  "perf: improve loading times :true"
  "This PR skips nothing :true"
)

# Test Cases for PR Merged
pr_descriptions=(
  "TestA_merged"
  "TestB_open"
  "TestC_closed"
)

pr_states=(
  "merged :false"
  "open :true"
  "closed :false"
)

echo "=============================="
echo "Running PR Title Check Tests"
echo "=============================="

# Execute Review Requested Test Cases
for i in "${!review_descriptions[@]}"; do
  description="${review_descriptions[$i]}"
  title="${review_titles[$i]}"
  echo "Running $description with title: '$title'"
  check_review_requested "$title"
  result=$?
  
  # Extract expected result from title (":true" or ":false")
  expected_result=$(echo "$title" | grep -o ':\(true\|false\)$' | cut -d':' -f2)

  echo "Expected result: $expected_result for $description"
  
  if [[ "$expected_result" == "true" ]]; then
    # For titles that should trigger review
    if [[ $result -eq 0 ]]; then
      echo "✅ Passed"
    else
      echo "❌ Failed"
      ((errors++))
    fi
  else
    # For titles that should skip review
    if [[ $result -eq 1 ]]; then
      echo "✅ Passed"
    else
      echo "❌ Failed"
      ((errors++))
    fi
  fi
  echo "---------------------------"
done

echo "=============================="
echo "Running PR State Check Tests"
echo "=============================="

# regex pattern for to match merged, open, closed
pattern="\b(?:merged|closed)\b"

# Execute PR Merged Test Cases
for i in "${!pr_descriptions[@]}"; do
  description="${pr_descriptions[$i]}"
  state="${pr_states[$i]}"
  echo "Running $description with state: '$state'"
  check_pr_merged "$state"
  result=$?
  
  # Extract expected result from state (":true" or ":false")
  expected_result=$(echo "$state" | grep -o ':\(true\|false\)$' | cut -d':' -f2)
  
  if [[ "$expected_result" == "true" ]]; then
    # For states that should trigger review
    if [[ $result -eq 0 ]]; then
      echo "✅ Passed"
    else
      echo "❌ Failed"
      ((errors++))
    fi
  else
    # For states that should skip review
    if [[ $result -eq 1 ]]; then
      echo "✅ Passed"
    else
      echo "❌ Failed"
      ((errors++))
    fi
  fi
  echo "---------------------------"
done

echo "=============================="
echo "All Tests Completed"
if [ $errors -gt 0 ]; then
  echo "❌ $errors test(s) failed"
  exit 1
else
  echo "✅ All tests passed"
  exit 0
fi
echo "=============================="