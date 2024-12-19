#!/usr/bin/env python3

import unittest
import re
import sys

class TestActionChecks(unittest.TestCase):
    def setUp(self):
        self.review_pattern = r"\b((?:no|skip)-(?:review|cori|coriai)|cori-(?:no|bye|restricted))(?:,((?:no|skip)-(?:review|cori|coriai)|cori-(?:no|bye|restricted)))*\b"
        self.pr_state_pattern = r"\b(?:merged|closed)\b"

    def check_review_requested(self, pr_title):
        """Simulate the 'Check if review is requested' step"""
        if re.search(self.review_pattern, pr_title, re.IGNORECASE):
            print("🦦 No review requested, skipping code review")
            return False
        print("🔍 Code review requested")
        return True

    def check_pr_merged(self, pr_state):
        """Simulate the 'Check if PR is merged' step"""
        if re.search(self.pr_state_pattern, pr_state, re.IGNORECASE):
            print("🦦 PR is merged, skipping code review")
            return False
        print("🔍 PR is not merged, proceeding with code review")
        return True

    def test_review_titles(self):
        test_cases = [
            ("Test0_NoSkipFlags", "Me/the 17 support skippable prs no-review", False),
            ("Test1_NoReview", "no-review: Update authentication system", False),
            ("Test2_SkipReview", "Important security patch but skip-review please", False),
            ("Test3_SkipCori", "Refactor database layer with skip-cori flag", False),
            ("Test4_NoCoriAI", "Backend optimization with no-coriai needed", False),
            ("Test5_CoriRestricted", "Frontend changes cori-restricted due to sensitivity", False),
            ("Test6_CoriBye", "Critical hotfix cori-bye emergency deploy", False),
            ("Test7_MultipleFlags", "Infrastructure update no-review,skip-cori,cori-restricted", False),
            ("Test8_StandardFeature", "Add user management features and improve UI", True),
            ("Test9_ConventionalCommit", "feat: implement new logging system", True),
            ("Test10_BugFix", "fix: resolve authentication bug", True),
            ("Test11_Documentation", "docs: update API documentation", True),
            ("Test12_Maintenance", "chore: upgrade dependencies", True),
            ("Test13_Testing", "test: add integration tests", True),
            ("Test14_CodeRefactor", "refactor: optimize database queries", True),
            ("Test15_Formatting", "style: format code according to standards", True),
            ("Test16_Performance", "perf: improve loading times", True),
            ("Test17_NoSkipFlags", "This PR skips nothing", True),
        ]

        print("==============================")
        print("Running PR Title Check Tests")
        print("==============================")

        for description, title, expected in test_cases:
            with self.subTest(description=description):
                print(f"Running {description} with title: '{title}'")
                result = self.check_review_requested(title)
                print(f"Expected result: {expected}")
                
                try:
                    self.assertEqual(result, expected, 
                        f"{description} failed: expected {expected}, got {result}")
                    print("✅ Passed")
                except AssertionError as e:
                    print("❌ Failed")
                    print(str(e))
                    sys.exit(1)
                print("---------------------------")

    def test_pr_states(self):
        test_cases = [
            ("TestA_merged", "merged", False),
            ("TestB_open", "open", True),
            ("TestC_closed", "closed", False),
        ]

        print("==============================")
        print("Running PR State Check Tests")
        print("==============================")

        for description, state, expected in test_cases:
            with self.subTest(description=description):
                print(f"Running {description} with state: '{state}'")
                result = self.check_pr_merged(state)
                print(f"Expected result: {expected}")
                
                try:
                    self.assertEqual(result, expected,
                        f"{description} failed: expected {expected}, got {result}")
                    print("✅ Passed")
                except AssertionError as e:
                    print("❌ Failed") 
                    print(str(e))
                    sys.exit(1)
                print("---------------------------")

if __name__ == '__main__':
    unittest.main()