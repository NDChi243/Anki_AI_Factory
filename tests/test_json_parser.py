"""
Unit tests for safe_parse_json (utils/json_parser.py)

Tests a pure function — no Anki dependency needed.
"""

import json as _json

# === Copy of safe_parse_json from utils/json_parser.py (pure function) ===
def safe_parse_json(text: str) -> list:
    """Parse JSON an toan, ho tro ca object va array"""
    results = []
    text = text.strip()

    # Thu parse ca chuoi nhu mot JSON array
    try:
        data = _json.loads(text)
        if isinstance(data, list):
            results.extend(data)
        elif isinstance(data, dict):
            results.append(data)
        return results
    except Exception:
        pass

    # Parse tung object rieng le voi stack-based approach
    objects = []
    depth = 0
    start_idx = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == '{':
            if depth == 0:
                start_idx = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                obj_str = text[start_idx:i + 1]
                try:
                    obj = _json.loads(obj_str)
                    if isinstance(obj, dict):
                        objects.append(obj)
                except Exception:
                    continue

    return objects


# === TESTS ===

class TestSafeParseJson:
    """Tests for safe_parse_json function."""

    def test_empty_string(self):
        assert safe_parse_json("") == []
        assert safe_parse_json("   ") == []

    def test_single_object(self):
        result = safe_parse_json('{"front": "taberu", "meaning": "an"}')
        assert len(result) == 1
        assert result[0]["front"] == "taberu"
        assert result[0]["meaning"] == "an"

    def test_array_of_objects(self):
        result = safe_parse_json('[{"a":1},{"b":2}]')
        assert len(result) == 2
        assert result[0] == {"a": 1}
        assert result[1] == {"b": 2}

    def test_unicode(self):
        result = safe_parse_json('{"word": "nihongo", "meaning": "tieng Nhat"}')
        assert result[0]["word"] == "nihongo"
        assert result[0]["meaning"] == "tieng Nhat"

    def test_multiple_objects_no_array(self):
        result = safe_parse_json('{"a":1}{"b":2}')
        assert len(result) == 2

    def test_nested_objects(self):
        result = safe_parse_json('{"outer": {"inner": "value"}}')
        assert len(result) == 1
        assert result[0]["outer"]["inner"] == "value"

    def test_objects_with_newlines(self):
        result = safe_parse_json('{\n"a": 1\n}\n{\n"b": 2\n}')
        assert len(result) == 2

    def test_invalid_json(self):
        result = safe_parse_json("not json at all")
        assert result == []

    def test_mixed_valid_invalid(self):
        result = safe_parse_json('{"ok":1} garbage {"also_ok":2}')
        assert len(result) == 2


class TestSafeParseJsonEdgeCases:
    """Edge case tests."""

    def test_strings_with_braces(self):
        result = safe_parse_json('{"text": "hello {world}"}')
        assert len(result) == 1
        assert result[0]["text"] == "hello {world}"

    def test_escaped_quotes(self):
        result = safe_parse_json('{"text": "he said \\"hello\\""}')
        assert len(result) == 1
        assert 'hello' in result[0]["text"]

    def test_empty_object(self):
        result = safe_parse_json('{}')
        assert len(result) == 1
        assert result[0] == {}

    def test_large_array(self):
        items = [{"id": i} for i in range(100)]
        text = _json.dumps(items)
        result = safe_parse_json(text)
        assert len(result) == 100

    def test_single_item_array(self):
        result = safe_parse_json('[{"only": "one"}]')
        assert len(result) == 1
        assert result[0]["only"] == "one"
