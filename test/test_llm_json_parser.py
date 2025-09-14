#!/usr/bin/env python3
"""
Test suite for LLM JSON Parser
Tests the ability to fix invalid JSON using OpenAI GPT models
"""
import json
import logging
import unittest
from pathlib import Path

from tools.llm_json_parser import LLMJSONParser, JSONParseResult

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestLLMJSONParser(unittest.TestCase):
    """Test cases for LLM JSON Parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = LLMJSONParser()

    def test_valid_json_passthrough(self):
        """Test that valid JSON passes through unchanged"""
        valid_json = '{"test": "valid", "number": 123, "boolean": true}'

        result = self.parser.fix_json_string(valid_json)

        self.assertTrue(result.success)
        self.assertEqual(result.original_text, valid_json)
        self.assertEqual(result.fixed_text, valid_json)
        self.assertIsNotNone(result.parsed_json)
        self.assertEqual(result.parsed_json["test"], "valid")
        self.assertEqual(result.parsed_json["number"], 123)
        self.assertTrue(result.parsed_json["boolean"])

    def test_basic_carriage_return_cleanup(self):
        """Test basic cleanup of carriage return characters"""
        json_with_cr = '{"text": "Line 1\\rLine 2\\rLine 3"}'

        result = self.parser.fix_json_string(json_with_cr)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.parsed_json)
        # Should be fixed by basic cleanup or LLM
        self.assertIn("text", result.parsed_json)

    def test_mixed_line_endings(self):
        """Test handling of mixed line endings"""
        mixed_json = '{\n  "description": "Test",\r\n  "content": "Some text"\r}'

        result = self.parser.fix_json_string(mixed_json)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.parsed_json)
        self.assertEqual(result.parsed_json["description"], "Test")
        self.assertEqual(result.parsed_json["content"], "Some text")

    def test_llm_json_fix_required(self):
        """Test case that specifically requires LLM to fix (can't be fixed with basic cleanup)"""
        # This JSON has multiple issues that require LLM intelligence to fix:
        # 1. Missing closing quote
        # 2. Invalid escape sequences
        # 3. Trailing comma
        # 4. Mixed quote styles
        complex_broken_json = '''{
  "description": "Test Document,
  'error': false,
  "errorReason": "",
  "result": "This has \\r invalid escapes \\x and other \\z problems",
  "data": {
    "field1": "value1",
    "field2": 123,
  },
}'''

        result = self.parser.fix_json_string(complex_broken_json)

        # This should trigger LLM fix since basic cleanup won't work
        self.assertTrue(result.success, f"LLM should fix complex JSON issues: {result.error}")
        self.assertIsNotNone(result.parsed_json)

        # Verify the structure was preserved
        self.assertIn("description", result.parsed_json)
        self.assertIn("error", result.parsed_json)
        self.assertIn("result", result.parsed_json)
        self.assertIn("data", result.parsed_json)

        # Verify nested structure
        self.assertIsInstance(result.parsed_json["data"], dict)
        self.assertIn("field1", result.parsed_json["data"])
        self.assertIn("field2", result.parsed_json["data"])

        # Verify content was preserved (not just structure)
        self.assertEqual(result.parsed_json["error"], False)
        self.assertEqual(result.parsed_json["data"]["field2"], 123)

        # The result should be different from original (was actually fixed)
        self.assertNotEqual(result.original_text, result.fixed_text)

        print(f"LLM fix test - Original length: {len(result.original_text)}")
        print(f"LLM fix test - Fixed length: {len(result.fixed_text)}")
        print(f"LLM fix test - Successfully parsed: {len(result.parsed_json)} top-level keys")

def main():
    """Run the test suite"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()