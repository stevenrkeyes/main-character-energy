#!/usr/bin/env python3
"""Build onset/final character tables from SUBTLEX-CH frequencies."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

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


def main() -> None:
    pinyin_map = load_pinyin_map()
    subtlex = load_subtlex()
    unihan_glosses = load_unihan_glosses()
    cedict_glosses = load_cedict_glosses()

    # best[(tone, onset, final)] = (count, char, syllable)
    best: dict[tuple[int, str, str], tuple[int, str, str]] = {}
    missing_pinyin = 0
    bad_split = 0

    for char, count in subtlex:
        reading = pinyin_map.get(char)
        if not reading:
            missing_pinyin += 1
            continue
        toneless, tone = strip_tone(reading)
        if tone not in (1, 2, 3, 4):
            # skip neutral tone for the four main tables
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
        prev = best.get(key)
        if prev is None or count > prev[0]:
            best[key] = (count, char, f"{toneless}{tone}")

    tones: dict[str, dict[str, dict[str, dict]]] = {}
    for tone in (1, 2, 3, 4):
        grid: dict[str, dict[str, dict]] = {}
        for onset in ONSETS:
            row: dict[str, dict] = {}
            for final in FINALS:
                hit = best.get((tone, onset, final))
                if hit:
                    count, char, syl = hit
                    row[final] = {
                        "char": char,
                        "count": count,
                        "pinyin": syl,
                        "gloss": {
                            "unihan": unihan_glosses.get(char, ""),
                            "cedict": cedict_glosses.get(char, ""),
                        },
                    }
            if row:
                grid[onset] = row
        tones[str(tone)] = grid

    filled = [cell for grid in tones.values() for row in grid.values() for cell in row.values()]

    out = {
        "corpus": "SUBTLEX-CH",
        "citation": "Cai, Q., & Brysbaert, M. (2010). SUBTLEX-CH: Chinese Word and Character Frequencies Based on Film Subtitles. PLoS ONE.",
        "analysis": "pinyin",
        "gloss_sources": {
            "unihan": "Unihan Database (kDefinition)",
            "cedict": "CC-CEDICT (CC BY-SA 4.0)",
        },
        "onsets": ONSETS,
        "finals": FINALS,
        "tones": tones,
        "stats": {
            "characters_in_corpus": len(subtlex),
            "filled_cells": len(best),
            "missing_pinyin": missing_pinyin,
            "bad_split": bad_split,
            "missing_gloss_unihan": sum(1 for c in filled if not c["gloss"]["unihan"]),
            "missing_gloss_cedict": sum(1 for c in filled if not c["gloss"]["cedict"]),
        },
    }

    out_path = DATA / "tables.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps(out["stats"], indent=2))


if __name__ == "__main__":
    main()
