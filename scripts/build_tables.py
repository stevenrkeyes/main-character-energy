#!/usr/bin/env python3
"""Build onset/final character tables from SUBTLEX-CH frequencies."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

HSK_FILTERS = ("1", "2", "3", "4", "5", "6", "7-9")

ONSETS = [
    "b",
    "p",
    "m",
    "f",
    "d",
    "t",
    "n",
    "l",
    "g",
    "k",
    "h",
    "j",
    "q",
    "x",
    "zh",
    "ch",
    "sh",
    "r",
    "z",
    "c",
    "s",
    "",
]

# Canonical finals after merging o into uo, and j/q/x + uan into üan.
FINALS = [
    "a",
    "e",
    "ai",
    "ei",
    "ao",
    "ou",
    "an",
    "en",
    "ang",
    "eng",
    "i",
    "ia",
    "ie",
    "iao",
    "iu",
    "ian",
    "in",
    "iang",
    "ing",
    "iong",
    "u",
    "ua",
    "uo",
    "uai",
    "ui",
    "uan",
    "un",
    "uang",
    "ong",
    "ü",
    "üe",
    "üan",
    "ün",
    "er",
]

TONE_MARKS = {
    "ā": ("a", 1),
    "á": ("a", 2),
    "ǎ": ("a", 3),
    "à": ("a", 4),
    "ē": ("e", 1),
    "é": ("e", 2),
    "ě": ("e", 3),
    "è": ("e", 4),
    "ī": ("i", 1),
    "í": ("i", 2),
    "ǐ": ("i", 3),
    "ì": ("i", 4),
    "ō": ("o", 1),
    "ó": ("o", 2),
    "ǒ": ("o", 3),
    "ò": ("o", 4),
    "ū": ("u", 1),
    "ú": ("u", 2),
    "ǔ": ("u", 3),
    "ù": ("u", 4),
    "ǖ": ("ü", 1),
    "ǘ": ("ü", 2),
    "ǚ": ("ü", 3),
    "ǜ": ("ü", 4),
    "ń": ("n", 2),
    "ň": ("n", 3),
    "ǹ": ("n", 4),
    "ḿ": ("m", 2),
}

ZERO_INITIAL_SPELLINGS = {
    "yi": ("", "i"),
    "ya": ("", "ia"),
    "ye": ("", "ie"),
    "yao": ("", "iao"),
    "you": ("", "iu"),
    "yan": ("", "ian"),
    "yin": ("", "in"),
    "yang": ("", "iang"),
    "ying": ("", "ing"),
    "yong": ("", "iong"),
    "yu": ("", "ü"),
    "yue": ("", "üe"),
    "yuan": ("", "üan"),
    "yun": ("", "ün"),
    "wu": ("", "u"),
    "wa": ("", "ua"),
    "wo": ("", "uo"),
    "wai": ("", "uai"),
    "wei": ("", "ui"),
    "wan": ("", "uan"),
    "wen": ("", "un"),
    "wang": ("", "uang"),
    "weng": ("", "eng"),
}


def strip_tone(syllable: str) -> tuple[str, int]:
    """Return (toneless_syllable, tone). Tone 5 = neutral."""
    tone = 5
    chars = []
    for ch in syllable:
        if ch in TONE_MARKS:
            base, tone = TONE_MARKS[ch]
            chars.append(base)
        elif ch.isdigit():
            tone = int(ch)
        else:
            chars.append(ch)
    # Normalize combining marks if any slipped through.
    flat = unicodedata.normalize("NFD", "".join(chars))
    flat = "".join(c for c in flat if unicodedata.category(c) != "Mn")
    flat = flat.replace("v", "ü").replace("u:", "ü")
    return flat, tone


def split_onset_final(toneless: str) -> tuple[str, str] | None:
    """Split a toneless pinyin syllable into (onset, final)."""
    s = toneless.lower().replace("u:", "ü").replace("v", "ü")

    if s in ZERO_INITIAL_SPELLINGS:
        return ZERO_INITIAL_SPELLINGS[s]

    # Bare "o" merges into the uo row
    if s == "o":
        return "", "uo"

    # Bare finals (a, e, er, ai, ...)
    if s in FINALS:
        return "", s

    # y/w should already be handled; leftovers after y/w rules above
    if s.startswith("y") or s.startswith("w"):
        return None

    for onset in ("zh", "ch", "sh"):
        if s.startswith(onset):
            final = s[len(onset) :]
            return onset, normalize_final(onset, final)

    for onset in (
        "b",
        "p",
        "m",
        "f",
        "d",
        "t",
        "n",
        "l",
        "g",
        "k",
        "h",
        "j",
        "q",
        "x",
        "r",
        "z",
        "c",
        "s",
    ):
        if s.startswith(onset):
            final = s[len(onset) :]
            return onset, normalize_final(onset, final)

    return None


def normalize_final(onset: str, final: str) -> str:
    """Normalize spelling quirks to canonical finals."""
    if not final:
        return final

    # After j/q/x, written "u" stands for ü (ju, jue, juan, jun)
    if onset in {"j", "q", "x"}:
        jqx_u = {
            "u": "ü",
            "ue": "üe",
            "uan": "üan",
            "un": "ün",
        }
        if final in jqx_u:
            return jqx_u[final]

    # After n/l, "ü" may appear as "v" already handled; "ue" → üe
    if onset in {"n", "l"} and final == "ue":
        return "üe"

    # bo/po/mo/fo are written -o but merge into the uo row
    if final == "o":
        return "uo"

    return final


def parse_unicode_line(line: str) -> tuple[str, list[str]] | None:
    """Parse 'U+XXXX: pīn,yīn  # 字' lines."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = re.match(r"U\+([0-9A-Fa-f]+):\s*([^\s#]+)", line)
    if not m:
        return None
    char = chr(int(m.group(1), 16))
    readings = [p.strip() for p in m.group(2).split(",") if p.strip()]
    return char, readings


def load_pinyin_map() -> dict[str, str]:
    """Map character → primary toned pinyin."""
    mapping: dict[str, str] = {}

    # Prefer official common readings for 通用规范汉字表
    for path in (DATA / "kMandarin_8105.txt", DATA / "pinyin.txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = parse_unicode_line(line)
            if not parsed:
                continue
            char, readings = parsed
            if char not in mapping and readings:
                mapping[char] = readings[0]
    return mapping


def load_unihan_glosses() -> dict[str, str]:
    """Map character → short English gloss from Unihan kDefinition (first sense)."""
    mapping: dict[str, str] = {}
    path = DATA / "Unihan_kDefinition.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3 or parts[1] != "kDefinition":
            continue
        code, _, definition = parts
        try:
            char = chr(int(code[2:], 16))
        except ValueError:
            continue
        # Take the first sense; kDefinition separates senses with ";".
        gloss = definition.split(";")[0].strip()
        if gloss:
            mapping[char] = gloss
    return mapping


def load_cedict_glosses() -> dict[str, str]:
    """Map single character → first English definition from CC-CEDICT."""
    mapping: dict[str, str] = {}
    path = DATA / "cedict_ts.u8"
    entry_re = re.compile(r"^(\S+)\s+(\S+)\s+\[[^\]]*\]\s+/(.+)/\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        m = entry_re.match(line)
        if not m:
            continue
        simplified = m.group(2)
        if len(simplified) != 1:
            continue
        first_def = m.group(3).split("/")[0].strip()
        # Keep the first entry seen for each character.
        if simplified not in mapping and first_def:
            mapping[simplified] = first_def
    return mapping


def load_custom_glosses() -> dict[str, str]:
    """Map character to gloss from data/simple-glosses.json."""
    path = DATA / "simple-glosses.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    glosses = payload.get("glosses", payload)
    if not isinstance(glosses, dict):
        return {}
    return {
        str(char): str(text).strip()
        for char, text in glosses.items()
        if isinstance(char, str) and len(char) == 1
    }


def load_hsk_levels() -> dict[str, int]:
    """Map character → first HSK 3.0 band (7 represents combined 7–9)."""
    mapping: dict[str, int] = {}
    path = DATA / "hsk30-chars.csv"
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            char = row.get("Hanzi", "").strip()
            level_text = row.get("Level", "").strip()
            if len(char) != 1:
                continue
            try:
                level = 7 if level_text == "7-9" else int(level_text)
            except ValueError:
                continue
            mapping[char] = level
    return mapping


def load_subtlex() -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for line in (DATA / "SUBTLEX-CH-CHR.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith('"') or line.startswith("Character"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        char, count_s = parts[0], parts[1]
        if len(char) != 1:
            continue
        try:
            count = int(count_s)
        except ValueError:
            continue
        rows.append((char, count))
    return rows


def load_subtlex_words() -> list[tuple[str, int]]:
    """Load multi-character word counts from SUBTLEX-CH-WF."""
    rows: list[tuple[str, int]] = []
    path = DATA / "SUBTLEX-CH-WF.txt"
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith('"') or line.startswith("Word"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        word, count_s = parts[0], parts[1]
        if len(word) < 2:
            continue
        try:
            count = int(count_s)
        except ValueError:
            continue
        rows.append((word, count))
    return rows


def load_simple_word_glosses() -> dict[str, str]:
    """Load concise glosses for dominant words shown in simple-gloss mode."""
    path = DATA / "simple-word-glosses.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    glosses = payload.get("glosses", payload)
    if not isinstance(glosses, dict):
        return {}
    return {
        str(word): str(text).strip()
        for word, text in glosses.items()
        if isinstance(word, str) and isinstance(text, str) and text.strip()
    }


def find_top_words(
    words: list[tuple[str, int]],
    character_counts: dict[str, int],
    word_glosses: dict[str, str],
) -> dict[str, dict]:
    """Find the word accounting for the most corpus uses of each character."""
    top_words: dict[str, dict] = {}
    for word, word_count in words:
        for char in set(word):
            character_count = character_counts.get(char)
            if not character_count:
                continue
            character_uses = word_count * word.count(char)
            previous = top_words.get(char)
            if previous and previous["character_uses"] >= character_uses:
                continue
            top_words[char] = {
                "word": word,
                "gloss": word_glosses.get(word, ""),
                "word_count": word_count,
                "character_uses": character_uses,
                "share": character_uses / character_count,
            }
    return top_words


def build_tones(
    best: dict[tuple[int, str, str], tuple[int, str, str]],
    unihan_glosses: dict[str, str],
    cedict_glosses: dict[str, str],
    custom_glosses: dict[str, str],
    top_words: dict[str, dict],
) -> dict[str, dict[str, dict[str, dict]]]:
    """Convert best-hit tuples into the JSON-ready four-tone structure."""
    tones: dict[str, dict[str, dict[str, dict]]] = {}
    for tone in (1, 2, 3, 4):
        grid: dict[str, dict[str, dict]] = {}
        for onset in ONSETS:
            row: dict[str, dict] = {}
            for final in FINALS:
                hit = best.get((tone, onset, final))
                if not hit:
                    continue
                count, char, syllable = hit
                row[final] = {
                    "char": char,
                    "count": count,
                    "pinyin": syllable,
                    "gloss": {
                        "unihan": unihan_glosses.get(char, ""),
                        "cedict": cedict_glosses.get(char, ""),
                        "custom": custom_glosses.get(char, ""),
                    },
                    "top_word": top_words.get(char),
                }
            if row:
                grid[onset] = row
        tones[str(tone)] = grid
    return tones


def main() -> None:
    pinyin_map = load_pinyin_map()
    subtlex = load_subtlex()
    simple_word_glosses = load_simple_word_glosses()
    top_words = find_top_words(
        load_subtlex_words(),
        dict(subtlex),
        simple_word_glosses,
    )
    hsk_levels = load_hsk_levels()
    unihan_glosses = load_unihan_glosses()
    cedict_glosses = load_cedict_glosses()
    custom_glosses = load_custom_glosses()

    # Each HSK cutoff gets its own winner per (tone, onset, final).
    best_by_filter: dict[
        str, dict[tuple[int, str, str], tuple[int, str, str]]
    ] = {"all": {}, **{level: {} for level in HSK_FILTERS}}
    missing_pinyin = 0
    bad_split = 0

    for char, count in subtlex:
        reading = pinyin_map.get(char)
        if not reading:
            missing_pinyin += 1
            continue
        toneless, tone = strip_tone(reading)
        if tone not in (1, 2, 3, 4):
            # Skip neutral tone for the four main tables.
            continue
        split = split_onset_final(toneless)
        if not split:
            bad_split += 1
            continue
        onset, final = split
        if final not in FINALS or onset not in ONSETS:
            bad_split += 1
            continue

        key = (tone, onset, final)
        hit = (count, char, f"{toneless}{tone}")
        targets = ["all"]
        char_level = hsk_levels.get(char)
        if char_level is not None:
            targets.extend(
                label
                for label in HSK_FILTERS
                if char_level <= (7 if label == "7-9" else int(label))
            )

        for target in targets:
            previous = best_by_filter[target].get(key)
            if previous is None or count > previous[0]:
                best_by_filter[target][key] = hit

    tones = build_tones(
        best_by_filter["all"],
        unihan_glosses,
        cedict_glosses,
        custom_glosses,
        top_words,
    )
    hsk_tones = {
        level: build_tones(
            best_by_filter[level],
            unihan_glosses,
            cedict_glosses,
            custom_glosses,
            top_words,
        )
        for level in HSK_FILTERS
    }
    filled = [
        cell
        for grid in tones.values()
        for row in grid.values()
        for cell in row.values()
    ]

    out = {
        "corpus": "SUBTLEX-CH",
        "citation": "Cai, Q., & Brysbaert, M. (2010). SUBTLEX-CH: Chinese Word and Character Frequencies Based on Film Subtitles. PLoS ONE.",
        "analysis": "pinyin",
        "gloss_sources": {
            "custom": "simple glosses (data/simple-glosses.json)",
            "unihan": "Unihan Database (kDefinition)",
            "cedict": "CC-CEDICT (CC BY-SA 4.0)",
        },
        "hsk_source": "HSK 3.0 (2025 character syllabus)",
        "hsk_filter_options": [*HSK_FILTERS, "all"],
        "onsets": ONSETS,
        "finals": FINALS,
        "tones": tones,
        "hsk_tones": hsk_tones,
        "stats": {
            "characters_in_corpus": len(subtlex),
            "characters_in_hsk": len(hsk_levels),
            "filled_cells": len(best_by_filter["all"]),
            "filled_cells_by_hsk": {
                level: len(best_by_filter[level]) for level in HSK_FILTERS
            },
            "missing_pinyin": missing_pinyin,
            "bad_split": bad_split,
            "missing_gloss_custom": sum(
                1 for cell in filled if not cell["gloss"]["custom"]
            ),
            "missing_gloss_unihan": sum(
                1 for cell in filled if not cell["gloss"]["unihan"]
            ),
            "missing_gloss_cedict": sum(
                1 for cell in filled if not cell["gloss"]["cedict"]
            ),
        },
    }

    out_path = DATA / "tables.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps(out["stats"], indent=2))


if __name__ == "__main__":
    main()
