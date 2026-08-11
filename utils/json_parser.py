"""
🔍 Safe JSON Parser — Parse JSON an toàn, hỗ trợ object và array.
V16.0: Sử dụng json.JSONDecoder.raw_decode() (C implementation) thay vì stack loop.
"""

import json


# Khởi tạo decoder một lần (reusable)
_decoder = json.JSONDecoder()


def safe_parse_json(text: str) -> list:
    """Parse JSON an toàn, hỗ trợ cả object và array.

    Sử dụng raw_decode() để tận dụng native C parser (~25x nhanh hơn stack loop).
    """
    results = []
    text = text.strip()
    if not text:
        return results

    def _skip_ws(s: str, i: int) -> int:
        """Bỏ qua whitespace/dấu phẩy để raw_decode không bị lệch vị trí."""
        n = len(s)
        while i < n and s[i] in ' \t\n\r,':
            i += 1
        return i

    # Thử parse cả chuỗi như một JSON array/object
    try:
        data, end = _decoder.raw_decode(text)
        if isinstance(data, list):
            # Kiểm tra còn object nào sau array không
            idx = _skip_ws(text, end)
            while idx < len(text):
                try:
                    obj, end2 = _decoder.raw_decode(text, idx)
                    if isinstance(obj, dict):
                        data.append(obj)
                    idx = _skip_ws(text, end2)
                except json.JSONDecodeError:
                    break
            results.extend(data)
        elif isinstance(data, dict):
            results.append(data)
            # Kiểm tra còn object nào sau object đầu tiên không
            idx = _skip_ws(text, end)
            while idx < len(text):
                try:
                    obj, end2 = _decoder.raw_decode(text, idx)
                    if isinstance(obj, dict):
                        results.append(obj)
                    idx = _skip_ws(text, end2)
                except json.JSONDecodeError:
                    break
        return results
    except json.JSONDecodeError:
        pass

    # Fallback: parse từng object rời rạc bằng raw_decode
    idx = 0
    text_len = len(text)
    while idx < text_len:
        idx = _skip_ws(text, idx)
        if idx >= text_len:
            break

        try:
            obj, end = _decoder.raw_decode(text, idx)
            if isinstance(obj, dict):
                results.append(obj)
            idx = end
        except json.JSONDecodeError:
            # Bỏ qua ký tự không parse được, thử tiếp
            idx += 1

    return results