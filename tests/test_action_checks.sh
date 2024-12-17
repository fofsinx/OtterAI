#!/bin/bash

# Initialize error counter
errors=0

# Function to simulate the "Check if review is requested" step
check_review_requested() {
  PR_TITLE="$1"
  
  if [[ "$PR_TITLE" =~ ^(no|skip)(-|\s)?review|skip(-|\s)?code(-|\s)?review|otter(ai)?(-|\s)?skip|otter(-|\s)?restricted ]]; then
    echo "🦦 No review requested, skipping code review"
    return 0
  else
    echo "🔍 Code review requested"
    return 0
  fi
}

# Function to simulate the "Check if PR is merged" step
check_pr_merged() {
  PR_STATE="$1"
  
  if [[ "$PR_STATE" == "merged" ]]; then
    echo "🦦 PR is merged, skipping code review"
    return 0
  else
    echo "🔍 PR is not merged, proceeding with code review"
    return 0
  fi
}

# Test Cases for Review Requested
review_descriptions=(
  "Test1_no_review"
  "Test2_skip_review"
  "Test3_otterai_skip"
  "Test4_otter_restricted"
  "Test5_feature"
)

review_titles=(
  "no-review needed"
  "skip code review"
  "otterai-skip"
  "otter-restricted"
  "feature enhancement"
)

# Test Cases for PR Merged
pr_descriptions=(
  "TestA_merged"
  "TestB_open"
  "TestC_closed"
)

pr_states=(
  "merged"
  "open"
  "closed"
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
  
  if [[ "$description" =~ Test[1-4]* ]]; then
    if [[ $result -eq 0 ]]; then
      echo "✅ Passed"
    else
      echo "❌ Failed"
      ((errors++))
    fi
  elif [[ "$description" =~ Test5* ]]; then
    if [[ $result -ne 0 ]]; then
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

# Execute PR Merged Test Cases
for i in "${!pr_descriptions[@]}"; do
  description="${pr_descriptions[$i]}"
  state="${pr_states[$i]}"
  echo "Running $description with state: '$state'"
  check_pr_merged "$state"
  result=$?
  
  if [[ "$description" =~ TestA* ]]; then
    if [[ $result -eq 0 ]]; then
      echo "✅ Passed"
    else
      echo "❌ Failed"
      ((errors++))
    fi
  else
    if [[ $result -ne 0 ]]; then
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