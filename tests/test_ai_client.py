from __future__ import annotations

import unittest

from ai_client import extract_response_text, parse_json_object


class AIClientTests(unittest.TestCase):
    def test_extracts_direct_output_text(self) -> None:
        self.assertEqual(extract_response_text({"output_text": "hello"}), "hello")

    def test_extracts_nested_output_text(self) -> None:
        payload = {"output": [{"content": [{"type": "output_text", "text": "{\"ok\": true}"}]}]}
        self.assertEqual(extract_response_text(payload), '{"ok": true}')

    def test_parses_fenced_json(self) -> None:
        self.assertEqual(parse_json_object("```json\n{\"ok\": true}\n```"), {"ok": True})


if __name__ == "__main__":
    unittest.main()
