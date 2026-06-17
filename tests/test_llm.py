"""Tests for _extract_json and _clean_trailing_commas in app.services.llm."""

import json
import unittest

from app.services.llm import _extract_json, _clean_trailing_commas, LLMServiceError


class TestCleanTrailingCommas(unittest.TestCase):
    """_clean_trailing_commas should only remove trailing commas."""

    def test_noop_for_clean_json(self):
        self.assertEqual(_clean_trailing_commas('{"a":1}'), '{"a":1}')

    def test_remove_trailing_comma_in_object(self):
        self.assertEqual(_clean_trailing_commas('{"a":1,}'), '{"a":1}')

    def test_remove_trailing_comma_in_array(self):
        self.assertEqual(_clean_trailing_commas('{"items":["a","b",]}'), '{"items":["a","b"]}')

    def test_remove_multiple(self):
        self.assertEqual(
            _clean_trailing_commas('{"a":1,"b":[1,2,],"c":{"d":"x",}}'),
            '{"a":1,"b":[1,2],"c":{"d":"x"}}',
        )

    def test_trailing_comma_with_spaces(self):
        self.assertEqual(_clean_trailing_commas('{"a":1, }'), '{"a":1 }')

    def test_url_unchanged(self):
        s = '{"url":"https://example.com/a.png"}'
        self.assertEqual(_clean_trailing_commas(s), s)

    def test_url_with_params_unchanged(self):
        s = '{"url":"https://example.com/a.png?foo=1&bar=2"}'
        self.assertEqual(_clean_trailing_commas(s), s)

    def test_empty_object_array_unchanged(self):
        self.assertEqual(_clean_trailing_commas('{"a":{}}'), '{"a":{}}')
        self.assertEqual(_clean_trailing_commas('{"a":[]}'), '{"a":[]}')


class TestExtractJson(unittest.TestCase):
    """_extract_json should parse JSON from LLM responses."""

    def test_normal_json(self):
        self.assertEqual(_extract_json('{"a":1}'), {"a": 1})

    def test_json_with_code_fence(self):
        self.assertEqual(_extract_json('```json\n{"a":1}\n```'), {"a": 1})

    def test_json_with_backticks_only(self):
        self.assertEqual(_extract_json('```\n{"a":1}\n```'), {"a": 1})

    def test_trailing_comma_fallback(self):
        """This would fail without _clean_trailing_commas."""
        self.assertEqual(_extract_json('{"a":1,}'), {"a": 1})

    def test_array_trailing_comma(self):
        self.assertEqual(_extract_json('{"items":["a","b",]}'), {"items": ["a", "b"]})

    def test_nested_trailing_comma(self):
        result = _extract_json('{"a":1,"b":{"c":[1,2,],}}')
        self.assertEqual(result, {"a": 1, "b": {"c": [1, 2]}})

    def test_url_inside_json(self):
        result = _extract_json('{"url":"https://example.com/a.png"}')
        self.assertEqual(result["url"], "https://example.com/a.png")

    def test_non_json_raises(self):
        with self.assertRaises(LLMServiceError):
            _extract_json("hello world")

    def test_no_curly_braces_raises(self):
        with self.assertRaises(LLMServiceError):
            _extract_json("[1,2,3]")

    def test_json_with_extra_text_before(self):
        """Extract JSON from LLM response with explanatory text."""
        text = 'Here is the result:\n```json\n{"a":1}\n```\nHope this helps.'
        self.assertEqual(_extract_json(text), {"a": 1})

    def test_extra_text_no_fence(self):
        """Fallback: find first { and last }."""
        text = 'Result:\n{"a": 1}\nDone.'
        self.assertEqual(_extract_json(text), {"a": 1})


if __name__ == "__main__":
    unittest.main()
