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

    # Thử parse cả chuỗi như một JSON array/object
    try:
        data, _ = _decoder.raw_decode(text)
        if isinstance(data, list):
            # Kiểm tra còn object nào sau array không
            idx = _
            while idx < len(text):
                try:
                    obj, end = _decoder.raw_decode(text, idx)
                    if isinstance(obj, dict):
                        data.append(obj)
                    idx = end
                except json.JSONDecodeError:
                    break
            results.extend(data)
        elif isinstance(data, dict):
            results.append(data)
            # Kiểm tra còn object nào sau object đầu tiên không
            idx = _
            while idx < len(text):
                try:
                    obj, end = _decoder.raw_decode(text, idx)
                    if isinstance(obj, dict):
                        results.append(obj)
                    idx = end
                except json.JSONDecodeError:
                    break
        return results
    except json.JSONDecodeError:
        pass

    # Fallback: parse từng object rời rạc bằng raw_decode
    idx = 0
    text_len = len(text)
    while idx < text_len:
        # Bỏ qua whitespace
        while idx < text_len and text[idx] in ' \t\n\r,':
            idx += 1
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
