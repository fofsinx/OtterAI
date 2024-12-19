import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from cori_ai.review import (
    clean_json_string, 
    review_code, 
    CodeReviewComment, 
    CodeReviewResponse,
    validate_comment_position
)
from langchain.output_parsers import PydanticOutputParser

class TestCleanJsonString(unittest.TestCase):
    def test_clean_basic_json(self):
        input_json = '{"comments": [], "comments_to_delete": []}'
        result = clean_json_string(input_json)
        self.assertEqual(json.loads(result), {"comments": [], "comments_to_delete": []})

    def test_clean_markdown_blocks(self):
        input_json = '```json\n{"comments": [], "comments_to_delete": []}\n```'
        result = clean_json_string(input_json)
        self.assertEqual(json.loads(result), {"comments": [], "comments_to_delete": []})

    def test_clean_incomplete_json(self):
        input_json = '"comments": []'
        result = clean_json_string(input_json)
        self.assertEqual(json.loads(result), {"comments": [], "comments_to_delete": []})

    def test_clean_newline_json(self):
        input_json = '\n    "comments": []'
        result = clean_json_string(input_json)
        self.assertEqual(json.loads(result), {"comments": [], "comments_to_delete": []})

    def test_clean_unbalanced_braces(self):
        input_json = '{"comments": [], "comments_to_delete": ['
        result = clean_json_string(input_json)
        self.assertEqual(json.loads(result), {"comments": []})

class TestValidateCommentPosition(unittest.TestCase):
    def test_valid_line_number(self):
        patch = '@@ -1,3 +1,4 @@\n def test():\n+    print("test")\n     return True'
        self.assertTrue(validate_comment_position(patch, 2))

    def test_invalid_line_number(self):
        patch = '@@ -1,3 +1,4 @@\n def test():\n+    print("test")\n     return True'
        self.assertFalse(validate_comment_position(patch, 999))

    def test_empty_patch(self):
        self.assertFalse(validate_comment_position("", 1))

class TestReviewCode(unittest.TestCase):
    def setUp(self):
        self.patcher1 = patch('cori_ai.main.LLMClient')
        self.patcher2 = patch('langchain.output_parsers.PydanticOutputParser')
        
        self.mock_llm_client = self.patcher1.start()
        self.mock_parser_class = self.patcher2.start()
        
        self.mock_llm = Mock()
        self.mock_parser = Mock()
        self.mock_llm_client.return_value.get_client.return_value = self.mock_llm
        self.mock_parser_class.return_value = self.mock_parser
        self.mock_parser.get_format_instructions.return_value = "format instructions"
        
        # Sample test data
        self.test_file = {
            'file': 'test.py',
            'patch': '@@ -1,3 +1,4 @@\n def test():\n+    print("test")\n     return True',
            'line_mapping': {2: {'content': '    print("test")', 'line': 2}},
            'existing_comments': []
        }
        
    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()

    def test_review_code_success(self):
        # Mock LLM and parser responses
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "comments": [{
                "path": "test.py",
                "line": 2,
                "body": "✅ Test comment"
            }],
            "comments_to_delete": []
        })
        self.mock_llm.invoke.return_value = mock_response
        
        parsed_response = CodeReviewResponse(
            comments=[CodeReviewComment(path="test.py", line=2, body="✅ Test comment")],
            comments_to_delete=[]
        )
        self.mock_parser.parse.return_value = parsed_response

        # Call review_code
        comments, comments_to_delete = review_code(
            [self.test_file],
            "Test context",
            ""
        )

        # Assertions
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].path, "test.py")
        self.assertEqual(comments[0].line, 2)
        self.assertEqual(comments[0].body, "✅ Test comment")
        self.assertEqual(len(comments_to_delete), 0)

    def test_review_code_invalid_json(self):
        # Mock LLM response and parser error
        mock_response = MagicMock()
        mock_response.content = 'Invalid JSON'
        self.mock_llm.invoke.return_value = mock_response
        self.mock_parser.parse.side_effect = ValueError("Invalid JSON")

        # Call review_code
        comments, comments_to_delete = review_code(
            [self.test_file],
            "Test context",
            ""
        )

        # Assertions
        self.assertEqual(len(comments), 0)
        self.assertEqual(len(comments_to_delete), 0)

    def test_review_code_invalid_line_number(self):
        # Mock LLM and parser responses
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "comments": [{
                "path": "test.py",
                "line": 999,
                "body": "✅ Test comment"
            }],
            "comments_to_delete": []
        })
        self.mock_llm.invoke.return_value = mock_response
        
        parsed_response = CodeReviewResponse(
            comments=[CodeReviewComment(path="test.py", line=999, body="✅ Test comment")],
            comments_to_delete=[]
        )
        self.mock_parser.parse.return_value = parsed_response

        # Call review_code
        comments, comments_to_delete = review_code(
            [self.test_file],
            "Test context",
            ""
        )

        # Assertions
        self.assertEqual(len(comments), 0)
        self.assertEqual(len(comments_to_delete), 0)

    def test_review_code_with_existing_comments(self):
        # Add existing comment to test file
        self.test_file['existing_comments'] = [{
            'id': 1,
            'line': 2,
            'body': "Old comment",
            'user': "test_user",
            'created_at': "2024-01-01T00:00:00Z"
        }]

        # Mock LLM and parser responses
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "comments": [{
                "path": "test.py",
                "line": 2,
                "body": "✅ New comment"
            }],
            "comments_to_delete": [1]
        })
        self.mock_llm.invoke.return_value = mock_response
        
        parsed_response = CodeReviewResponse(
            comments=[CodeReviewComment(path="test.py", line=2, body="✅ New comment")],
            comments_to_delete=[1]
        )
        self.mock_parser.parse.return_value = parsed_response

        # Call review_code
        comments, comments_to_delete = review_code(
            [self.test_file],
            "Test context",
            ""
        )

        # Assertions
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].body, "✅ New comment")
        self.assertEqual(len(comments_to_delete), 1)
        self.assertEqual(comments_to_delete[0], 1)

    def test_review_code_empty_response(self):
        # Mock LLM and parser responses
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "comments": [],
            "comments_to_delete": []
        })
        self.mock_llm.invoke.return_value = mock_response
        
        parsed_response = CodeReviewResponse(comments=[], comments_to_delete=[])
        self.mock_parser.parse.return_value = parsed_response

        # Call review_code
        comments, comments_to_delete = review_code(
            [self.test_file],
            "Test context",
            ""
        )

        # Assertions
        self.assertEqual(len(comments), 0)
        self.assertEqual(len(comments_to_delete), 0)

    def test_review_code_missing_path(self):
        # Mock LLM and parser responses
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "comments": [{
                "path": "test.py",
                "line": 2,
                "body": "✅ Test comment"
            }],
            "comments_to_delete": []
        })
        self.mock_llm.invoke.return_value = mock_response
        
        parsed_response = CodeReviewResponse(
            comments=[CodeReviewComment(path="test.py", line=2, body="✅ Test comment")],
            comments_to_delete=[]
        )
        self.mock_parser.parse.return_value = parsed_response

        # Call review_code
        comments, comments_to_delete = review_code(
            [self.test_file],
            "Test context",
            ""
        )

        # Assertions
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].path, "test.py")
        self.assertEqual(comments[0].line, 2)
        self.assertEqual(comments[0].body, "✅ Test comment")

if __name__ == '__main__':
    unittest.main() 