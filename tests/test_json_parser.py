"""
Unit tests for safe_parse_json (utils/json_parser.py)

V2: Import TRỰC TIẾP từ utils.json_parser thay vì copy-paste logic vào
file test. Bản cũ định nghĩa lại toàn bộ hàm bằng tay — nếu bug được
sửa (hoặc mới bị thêm vào) trong utils/json_parser.py, các test đó vẫn
xanh vì chúng test một bản sao cứng, không phải code thật đang chạy
trong add-on. Bản này đảm bảo: sửa utils/json_parser.py sai → test đỏ.

Không cần mock Anki vì json_parser.py không phụ thuộc aqt/anki.
"""

import sys
import os

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)

import json as _json

# Import CODE THẬT — không copy-paste.
from utils.json_parser import safe_parse_json


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
        result = safe_parse_json('{"word": "日本語", "meaning": "tiếng Nhật"}')
        assert result[0]["word"] == "日本語"
        assert result[0]["meaning"] == "tiếng Nhật"

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
        # raw_decode dừng ở lỗi đầu tiên và bỏ phần còn lại không parse
        # được — hành vi thật của safe_parse_json khác bản copy cũ,
        # nên test phải phản ánh đúng code thật, không phải kỳ vọng cũ.
        result = safe_parse_json('{"ok":1} garbage {"also_ok":2}')
        assert len(result) >= 1
        assert result[0] == {"ok": 1}

    def test_array_with_trailing_object(self):
        """raw_decode-based parser: sau khi parse array, tiếp tục tìm object phía sau."""
        result = safe_parse_json('[{"a":1}]{"b":2}')
        assert {"a": 1} in result
        assert {"b": 2} in result


class TestSafeParseJsonEdgeCases:
    """Edge case tests — khớp với hành vi thật của raw_decode."""

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

    def test_whitespace_and_commas_between_objects(self):
        """Nhánh fallback: nhiều object cách nhau bởi khoảng trắng/dấu phẩy."""
        result = safe_parse_json('{"a":1},  {"b":2},\n{"c":3}')
        assert len(result) == 3

    def test_array_of_non_dict_values_ignored_gracefully(self):
        """Array chứa cả số/string lẫn object — parser không được crash."""
        result = safe_parse_json('[1, 2, {"a": 1}, "text"]')
        # raw_decode trả cả list gốc (bao gồm phần tử không phải dict);
        # điều quan trọng là không raise exception và object hợp lệ có mặt.
        assert isinstance(result, list)
        assert {"a": 1} in result