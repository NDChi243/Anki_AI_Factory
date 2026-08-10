"""
Unit tests for file text extraction (đọc tài liệu tham khảo cho AI).

Tests extract_text_from_file cho txt/md/csv + extract_text_from_files nhiều file.
Không đụng tới PDF/DOCX/XLSX để tránh phụ thuộc thư viện ngoài (openpyxl, python-docx).
"""

import os
import sys
import tempfile

_addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _addon_root not in sys.path:
    sys.path.insert(0, _addon_root)


class TestExtractTextFromFile:
    def test_read_txt(self):
        from utils.ai_extractor import extract_text_from_file
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "doc.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write("日本語の文法\n第二行")
            text = extract_text_from_file(p)
            assert "日本語" in text
            assert "第二行" in text

    def test_read_md(self):
        from utils.ai_extractor import extract_text_from_file
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "notes.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write("# Title\n- item")
            assert "item" in extract_text_from_file(p)

    def test_read_csv(self):
        from utils.ai_extractor import _extract_csv_text
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "list.csv")
            with open(p, "w", encoding="utf-8") as f:
                f.write("食べる,ăn,N5\n")
            text = _extract_csv_text(p)
            assert "食べる" in text
            assert "N5" in text

    def test_missing_file_returns_empty(self):
        from utils.ai_extractor import extract_text_from_file
        assert extract_text_from_file(os.path.join(tempfile.gettempdir(), "no_such_file.txt")) == ""

    def test_unknown_ext_fallback(self):
        from utils.ai_extractor import extract_text_from_file
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.xyz")
            with open(p, "w", encoding="utf-8") as f:
                f.write("plain text")
            assert "plain text" in extract_text_from_file(p)


class TestExtractTextFromFiles:
    def test_multi_file(self):
        from utils.ai_extractor import extract_text_from_files
        with tempfile.TemporaryDirectory() as d:
            p1 = os.path.join(d, "a.txt")
            p2 = os.path.join(d, "b.txt")
            with open(p1, "w", encoding="utf-8") as f:
                f.write("AAA")
            with open(p2, "w", encoding="utf-8") as f:
                f.write("BBB")
            results = extract_text_from_files([p1, p2])
            assert len(results) == 2
            assert results[0][0] == "a.txt"
            assert results[1][1] == "BBB"

    def test_bad_files_skipped(self):
        from utils.ai_extractor import extract_text_from_files
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write("AAA")
            results = extract_text_from_files([p, os.path.join(d, "missing.txt")])
            assert len(results) == 1
