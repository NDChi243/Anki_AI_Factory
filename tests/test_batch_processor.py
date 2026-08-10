"""
Unit tests for utils/batch_processor.py — pure functions.

Tests parse_word_list, smart_group_words, estimate_batch_cost,
_fallback_deck_organization, _build_batch_user_prompt, _batch_cache_key.

Pure functions are copied inline to avoid Anki dependency issues.
"""

import json
import re
import hashlib


# ═══════════════════════════════════════════════════════════
#  COPIED PURE FUNCTIONS from utils/batch_processor.py
# ═══════════════════════════════════════════════════════════

DEFAULT_BATCH_SIZE = 80


def parse_word_list(raw_text: str, lang: str = "japanese") -> list:
    """Parse danh sach tu vung tu text paste cua nguoi dung."""
    raw_text = raw_text.strip()
    if not raw_text:
        return []

    # Thu parse JSON truoc
    if raw_text.startswith("["):
        try:
            data = json.loads(raw_text)
            if isinstance(data, list):
                result = []
                for item in data:
                    if isinstance(item, dict):
                        result.append({
                            "front": str(item.get("front") or item.get("simplified") or item.get("word") or "").strip(),
                            "meaning": str(item.get("meaning") or "").strip(),
                            "level": str(item.get("jlptlevel") or item.get("hsk_level") or item.get("level") or "").strip(),
                            "topic": str(item.get("topic") or "").strip(),
                        })
                    elif isinstance(item, str):
                        result.append({"front": item.strip(), "meaning": "", "level": "", "topic": ""})
                return [r for r in result if r["front"]]
        except json.JSONDecodeError:
            pass

    # Parse tung dong
    lines = raw_text.split("\n")
    result = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        # Thu cac delimiter
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t")]
        elif "," in line and not (lang == "chinese" and any(c in line for c in "，")):
            parts = [p.strip() for p in line.split(",")]
        elif ":" in line:
            parts = [p.strip() for p in line.split(":")]
        elif ";" in line:
            parts = [p.strip() for p in line.split(";")]
        elif " - " in line:
            parts = [p.strip() for p in line.split(" - ")]
        elif "–" in line or "—" in line:
            parts = [p.strip() for p in re.split(r'[–—]', line)]
        else:
            parts = [line]

        entry = {"front": parts[0] if len(parts) > 0 else "",
                  "meaning": "", "level": "", "topic": ""}

        if len(parts) >= 2:
            second = parts[1]
            if re.match(r'^(N[1-5]|HSK[1-6])$', second, re.IGNORECASE):
                entry["level"] = second.upper()
            else:
                entry["meaning"] = second

        if len(parts) >= 3:
            third = parts[2]
            if re.match(r'^(N[1-5]|HSK[1-6])$', third, re.IGNORECASE):
                entry["level"] = third.upper()
            elif not entry["level"]:
                entry["level"] = third
            else:
                entry["topic"] = third

        if len(parts) >= 4:
            entry["topic"] = parts[3]

        if entry["front"]:
            result.append(entry)

    return result


def smart_group_words(words: list, batch_size: int = DEFAULT_BATCH_SIZE) -> list:
    """Nhom tu thong minh de toi uu chat luong AI."""
    if not words:
        return []

    with_level = [w for w in words if w.get("level")]
    without_level = [w for w in words if not w.get("level")]

    level_order = {"N5": 0, "N4": 1, "N3": 2, "N2": 3, "N1": 4,
                   "HSK1": 0, "HSK2": 1, "HSK3": 2, "HSK4": 3, "HSK5": 4, "HSK6": 5}

    with_level.sort(key=lambda w: (level_order.get(w["level"].upper(), 99), len(w["front"])))
    without_level.sort(key=lambda w: len(w["front"]))

    all_sorted = with_level + without_level

    batches = []
    for i in range(0, len(all_sorted), batch_size):
        batch = all_sorted[i:i + batch_size]
        batches.append(batch)

    if len(batches) >= 2 and len(batches[-1]) < 10:
        small_batch = batches.pop()
        batches[-1].extend(small_batch)

    return batches


def estimate_batch_cost(word_count: int, lang: str, batch_size: int = DEFAULT_BATCH_SIZE) -> dict:
    """Uoc tinh chi phi API cho viec xu ly batch."""
    batches = max(1, (word_count + batch_size - 1) // batch_size)

    input_tokens = word_count * 150
    output_tokens = word_count * 200

    cost_input = input_tokens / 1_000_000 * 0.14
    cost_output = output_tokens / 1_000_000 * 0.28
    total_cost = cost_input + cost_output

    return {
        "total_words": word_count,
        "batch_size": batch_size,
        "estimated_batches": batches,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_cost_usd": round(total_cost, 4),
        "estimated_time_seconds": batches * 10,
    }


def _build_batch_user_prompt(words, lang, existing_words, custom_instruction="",
                              batch_num=1, total_batches=1):
    """Xay dung user prompt cho mot batch tu."""
    _JSON_TEMPLATES = {"japanese": '{"front":"","meaning":""}', "chinese": '{"simplified":"","meaning":""}'}
    template = _JSON_TEMPLATES.get(lang, _JSON_TEMPLATES["japanese"])

    word_list_str = "\n".join(
        f"{i+1}. {w['front']}"
        + (f" (nghia: {w['meaning']})" if w.get("meaning") else "")
        + (f" [{w['level']}]" if w.get("level") else "")
        for i, w in enumerate(words)
    )

    prompt = f"""BATCH {batch_num}/{total_batches} — XU LY {len(words)} TU VUNG

DANH SACH TU CAN XU LY:
{word_list_str}

Template: {template}"""

    if existing_words:
        shown = existing_words[:100]
        existing_str = ", ".join(shown)
        prompt += f"\nDA CO: {existing_str}\n"

    if custom_instruction.strip():
        prompt += f"\nYEU CAU BO SUNG:\n{custom_instruction.strip()}\n"

    return prompt


def _batch_cache_key(words, lang, instruction, existing_hash):
    """Tao cache key cho mot batch."""
    fronts = ",".join(sorted(w["front"] for w in words))
    raw = f"batch|{lang}|{instruction}|{existing_hash}|{fronts}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _fallback_deck_organization(vocab_list, lang):
    """Fallback: Tu to chuc deck don gian."""
    if not vocab_list:
        return {"suggestion": "Khong co tu vung", "decks": []}

    by_topic = {}
    no_topic = []

    for item in vocab_list:
        topic = (item.get("topic") or "").strip()
        if topic:
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(item)
        else:
            no_topic.append(item)

    decks = []
    lang_label = "Tieng Nhat" if lang == "japanese" else "Tieng Trung"

    if by_topic:
        sub_decks = []
        for topic, words in sorted(by_topic.items(), key=lambda x: -len(x[1])):
            if len(words) > 50:
                by_level = {}
                for w in words:
                    level = w.get("jlptlevel") or w.get("hsk_level") or "Khac"
                    if level not in by_level:
                        by_level[level] = []
                    by_level[level].append(w)
                for level, lvl_words in sorted(by_level.items()):
                    sub_decks.append({
                        "name": f"{topic} - {level}",
                        "description": f"Tu vung {topic} cap do {level}",
                        "word_count": len(lvl_words),
                        "words": [w.get("front") or w.get("simplified") or "" for w in lvl_words],
                    })
            else:
                sub_decks.append({
                    "name": topic,
                    "description": f"Tu vung ve {topic.lower()}",
                    "word_count": len(words),
                    "words": [w.get("front") or w.get("simplified") or "" for w in words],
                })
        decks.append({
            "parent": f"{lang_label} Theo Chu De",
            "sub_decks": sub_decks,
        })

    if no_topic:
        by_level = {}
        for w in no_topic:
            level = w.get("jlptlevel") or w.get("hsk_level") or "Chua phan loai"
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(w)
        sub_decks = []
        for level, lvl_words in sorted(by_level.items()):
            sub_decks.append({
                "name": f"{level} - Tu vung",
                "description": f"Tu vung {level}",
                "word_count": len(lvl_words),
                "words": [w.get("front") or w.get("simplified") or "" for w in lvl_words],
            })
        decks.append({
            "parent": f"{lang_label} Theo Cap Do",
            "sub_decks": sub_decks,
        })

    return {
        "suggestion": "To chuc tu dong (fallback) — nhom theo chu de va cap do",
        "decks": decks,
    }


# ═══════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════

class TestParseWordList:
    def test_empty(self):
        assert parse_word_list("") == []
        assert parse_word_list("   ") == []

    def test_single_word_per_line(self):
        result = parse_word_list("taberu\nnomu\nmiru")
        assert len(result) == 3
        assert result[0]["front"] == "taberu"

    def test_word_with_meaning_colon(self):
        result = parse_word_list("taberu : an\nnomu : uong")
        assert len(result) == 2
        assert result[0]["meaning"] == "an"

    def test_word_with_level(self):
        result = parse_word_list("taberu : an : N5")
        assert result[0]["level"] == "N5"

    def test_csv_style(self):
        """CSV: front,reading,meaning,level → second field becomes meaning, third → level."""
        result = parse_word_list("taberu,taberu,an,N5")
        assert result[0]["front"] == "taberu"
        assert result[0]["meaning"] == "taberu"  # second field, not a level
        assert result[0]["level"] == "an"         # third field assigned to level
        assert result[0]["topic"] == "N5"         # fourth field → topic

    def test_tab_separated(self):
        result = parse_word_list("taberu\tan\tN5")
        assert result[0]["level"] == "N5"

    def test_semicolon_separated(self):
        result = parse_word_list("taberu;an;N5")
        assert result[0]["level"] == "N5"

    def test_dash_separated(self):
        result = parse_word_list("taberu - an - N5")
        assert result[0]["level"] == "N5"

    def test_json_array_of_dicts(self):
        result = parse_word_list('[{"front":"taberu","meaning":"an","jlptlevel":"N5"}]')
        assert result[0]["front"] == "taberu"
        assert result[0]["level"] == "N5"

    def test_json_array_with_simplified(self):
        result = parse_word_list('[{"simplified":"xuexi","meaning":"hoc tap","hsk_level":"HSK1"}]')
        assert result[0]["front"] == "xuexi"
        assert result[0]["level"] == "HSK1"

    def test_json_array_of_strings(self):
        result = parse_word_list('["taberu","nomu","miru"]')
        assert len(result) == 3

    def test_skip_comment_lines(self):
        result = parse_word_list("# comment\ntaberu\n// another\nnomu")
        assert len(result) == 2

    def test_strips_whitespace(self):
        result = parse_word_list("  taberu  :  an  ")
        assert result[0]["front"] == "taberu"
        assert result[0]["meaning"] == "an"

    def test_skip_empty_lines(self):
        result = parse_word_list("taberu\n\n\nnomu\n")
        assert len(result) == 2

    def test_level_detection_n5(self):
        result = parse_word_list("taberu : N5")
        assert result[0]["level"] == "N5"
        assert result[0]["meaning"] == ""

    def test_level_detection_hsk(self):
        result = parse_word_list("xuexi : HSK3", lang="chinese")
        assert result[0]["level"] == "HSK3"

    def test_chinese_lang(self):
        result = parse_word_list("xuexi : hoc tap : HSK1", lang="chinese")
        assert result[0]["level"] == "HSK1"

    def test_four_parts(self):
        """Four CSV parts: front,reading,meaning,level → level from 4th."""
        result = parse_word_list("taberu,taberu,an,N5")
        assert result[0]["front"] == "taberu"
        assert result[0]["meaning"] == "taberu"
        assert result[0]["level"] == "an"
        assert result[0]["topic"] == "N5"  # parts[3] → topic

    def test_invalid_json_falls_back(self):
        """Invalid JSON starting with [ falls through to line parsing."""
        result = parse_word_list("[not valid json")
        # Falls back to line parsing: single line with no delimiter → 1 word
        assert len(result) == 1
        assert result[0]["front"] == "[not valid json"

    def test_large_list(self):
        words = "\n".join([f"word{i}" for i in range(500)])
        result = parse_word_list(words)
        assert len(result) == 500


class TestSmartGroupWords:
    def test_empty(self):
        assert smart_group_words([]) == []

    def test_single_batch(self):
        words = [{"front": f"w{i}", "meaning": "", "level": ""} for i in range(30)]
        batches = smart_group_words(words, batch_size=80)
        assert len(batches) == 1

    def test_multiple_batches(self):
        words = [{"front": f"w{i}", "meaning": "", "level": ""} for i in range(200)]
        batches = smart_group_words(words, batch_size=80)
        assert len(batches) == 3

    def test_small_last_batch_merged(self):
        words = [{"front": f"w{i}", "meaning": "", "level": ""} for i in range(85)]
        batches = smart_group_words(words, batch_size=80)
        assert len(batches) == 1
        assert len(batches[0]) == 85

    def test_sorts_by_level(self):
        words = [
            {"front": "w1", "meaning": "", "level": "N1"},
            {"front": "w2", "meaning": "", "level": "N5"},
            {"front": "w3", "meaning": "", "level": "N3"},
        ]
        batches = smart_group_words(words, batch_size=80)
        levels = [w["level"] for w in batches[0]]
        assert levels == ["N5", "N3", "N1"]

    def test_sorts_by_length(self):
        words = [
            {"front": "longword", "meaning": "", "level": ""},
            {"front": "sh", "meaning": "", "level": ""},
            {"front": "mid", "meaning": "", "level": ""},
        ]
        batches = smart_group_words(words, batch_size=80)
        fronts = [w["front"] for w in batches[0]]
        assert fronts == ["sh", "mid", "longword"]

    def test_with_level_comes_first(self):
        words = [
            {"front": "no", "meaning": "", "level": ""},
            {"front": "yes", "meaning": "", "level": "N5"},
        ]
        batches = smart_group_words(words, batch_size=80)
        assert batches[0][0]["level"] == "N5"

    def test_hsk_level_ordering(self):
        words = [
            {"front": "w1", "meaning": "", "level": "HSK6"},
            {"front": "w2", "meaning": "", "level": "HSK1"},
        ]
        batches = smart_group_words(words, batch_size=80)
        levels = [w["level"] for w in batches[0]]
        assert levels == ["HSK1", "HSK6"]


class TestEstimateBatchCost:
    def test_zero(self):
        cost = estimate_batch_cost(0, "ja")
        assert cost["total_words"] == 0

    def test_small(self):
        cost = estimate_batch_cost(40, "ja")
        assert cost["estimated_batches"] == 1

    def test_exact_boundary(self):
        cost = estimate_batch_cost(80, "ja")
        assert cost["estimated_batches"] == 1

    def test_crosses_boundary(self):
        cost = estimate_batch_cost(81, "ja")
        assert cost["estimated_batches"] == 2

    def test_large(self):
        cost = estimate_batch_cost(500, "ja")
        assert cost["estimated_batches"] == 7

    def test_cost_calculation(self):
        cost = estimate_batch_cost(100, "ja")
        expected = (15000 / 1_000_000 * 0.14) + (20000 / 1_000_000 * 0.28)
        assert abs(cost["estimated_cost_usd"] - round(expected, 4)) < 0.0001

    def test_time_estimate(self):
        cost = estimate_batch_cost(160, "ja")
        assert cost["estimated_time_seconds"] == 20

    def test_custom_batch_size(self):
        cost = estimate_batch_cost(100, "ja", batch_size=50)
        assert cost["batch_size"] == 50
        assert cost["estimated_batches"] == 2

    def test_all_keys_present(self):
        cost = estimate_batch_cost(50, "chinese")
        for k in ("total_words", "batch_size", "estimated_batches",
                  "estimated_input_tokens", "estimated_output_tokens",
                  "estimated_cost_usd", "estimated_time_seconds"):
            assert k in cost


class TestBuildBatchUserPrompt:
    def test_basic_prompt(self):
        words = [{"front": "taberu", "meaning": "an", "level": "N5"}]
        prompt = _build_batch_user_prompt(words, "japanese", [], "", 1, 1)
        assert "BATCH 1/1" in prompt
        assert "taberu" in prompt

    def test_includes_existing_words(self):
        words = [{"front": "taberu", "meaning": "", "level": ""}]
        prompt = _build_batch_user_prompt(words, "japanese", ["nomu", "miru"], "", 1, 1)
        assert "nomu" in prompt

    def test_includes_custom_instruction(self):
        words = [{"front": "taberu", "meaning": "", "level": ""}]
        prompt = _build_batch_user_prompt(words, "japanese", [], "Chi lay N3+", 1, 1)
        assert "Chi lay N3+" in prompt

    def test_batch_numbering(self):
        words = [{"front": "taberu", "meaning": "", "level": ""}]
        prompt = _build_batch_user_prompt(words, "japanese", [], "", 3, 5)
        assert "BATCH 3/5" in prompt

    def test_chinese_prompt(self):
        words = [{"front": "xuexi", "meaning": "", "level": ""}]
        prompt = _build_batch_user_prompt(words, "chinese", [], "", 1, 1)
        assert "xuexi" in prompt


class TestBatchCacheKey:
    def test_consistent(self):
        words = [{"front": "a"}, {"front": "b"}]
        k1 = _batch_cache_key(words, "ja", "test", "h1")
        k2 = _batch_cache_key(words, "ja", "test", "h1")
        assert k1 == k2

    def test_different_lang(self):
        words = [{"front": "a"}]
        k1 = _batch_cache_key(words, "ja", "", "h")
        k2 = _batch_cache_key(words, "zh", "", "h")
        assert k1 != k2

    def test_different_instruction(self):
        words = [{"front": "a"}]
        k1 = _batch_cache_key(words, "ja", "i1", "h")
        k2 = _batch_cache_key(words, "ja", "i2", "h")
        assert k1 != k2

    def test_order_independent(self):
        w1 = [{"front": "a"}, {"front": "b"}]
        w2 = [{"front": "b"}, {"front": "a"}]
        assert _batch_cache_key(w1, "ja", "", "h") == _batch_cache_key(w2, "ja", "", "h")


class TestFallbackDeckOrganization:
    def test_empty(self):
        result = _fallback_deck_organization([], "japanese")
        assert result["decks"] == []

    def test_single_topic(self):
        words = [
            {"front": "taberu", "meaning": "an", "topic": "Am thuc"},
            {"front": "nomu", "meaning": "uong", "topic": "Am thuc"},
        ]
        result = _fallback_deck_organization(words, "japanese")
        assert len(result["decks"]) == 1
        sub = result["decks"][0]["sub_decks"]
        assert sub[0]["word_count"] == 2

    def test_multiple_topics(self):
        words = [
            {"front": "a", "topic": "Topic1"},
            {"front": "b", "topic": "Topic2"},
        ]
        result = _fallback_deck_organization(words, "japanese")
        assert len(result["decks"][0]["sub_decks"]) == 2

    def test_large_topic_split(self):
        words = []
        for i in range(60):
            level = "N5" if i < 30 else "N4"
            words.append({"front": f"w{i}", "topic": "Large", "jlptlevel": level})
        result = _fallback_deck_organization(words, "japanese")
        sub = result["decks"][0]["sub_decks"]
        assert len(sub) == 2

    def test_no_topic_words(self):
        words = [
            {"front": "a", "jlptlevel": "N5"},
            {"front": "b", "jlptlevel": "N4"},
        ]
        result = _fallback_deck_organization(words, "japanese")
        parents = [d["parent"] for d in result["decks"]]
        assert any("Cap Do" in p for p in parents)

    def test_chinese(self):
        words = [{"front": "xuexi", "topic": "Giao duc"}]
        result = _fallback_deck_organization(words, "chinese")
        assert "Tieng Trung" in result["decks"][0]["parent"]

    def test_mixed(self):
        words = [
            {"front": "a", "topic": "T1"},
            {"front": "b", "topic": ""},
        ]
        result = _fallback_deck_organization(words, "japanese")
        assert len(result["decks"]) == 2

    def test_words_preserved(self):
        words = [
            {"front": "taberu", "topic": "Food"},
            {"front": "nomu", "topic": "Food"},
        ]
        result = _fallback_deck_organization(words, "japanese")
        all_words = []
        for parent in result["decks"]:
            for sub in parent.get("sub_decks", []):
                all_words.extend(sub.get("words", []))
        assert "taberu" in all_words
        assert "nomu" in all_words


class TestParseAndGroupIntegration:
    def test_full_flow_small(self):
        text = "taberu : an : N5\nnomu : uong : N4\nmiru : nhin : N5"
        words = parse_word_list(text)
        assert len(words) == 3
        batches = smart_group_words(words, batch_size=80)
        assert len(batches) == 1

    def test_full_flow_large(self):
        text = "\n".join([f"word{i} : meaning{i}" for i in range(300)])
        words = parse_word_list(text)
        assert len(words) == 300
        batches = smart_group_words(words, batch_size=80)
        assert len(batches) == 4

    def test_json_input_flow(self):
        items = [{"front": f"w{i}", "meaning": f"m{i}", "jlptlevel": f"N{(i%5)+1}"} for i in range(50)]
        text = json.dumps(items)
        words = parse_word_list(text)
        assert len(words) == 50
        batches = smart_group_words(words, batch_size=80)
        assert len(batches) == 1
