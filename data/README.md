# Data provenance and licensing

The project licenses do not relicense third-party data in this directory. The
notes below record where each file came from and the licensing information
that could be verified.

## `SUBTLEX-CH-CHR.txt`

- **Contents:** Chinese character frequencies from SUBTLEX-CH.
- **Original source:** Cai, Q., & Brysbaert, M. (2010). “SUBTLEX-CH:
  Chinese Word and Character Frequencies Based on Film Subtitles.”
  *PLOS ONE*, 5(6), e10729.
- **Official distribution:**
  [Ghent University](https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexch).
- **File used here:** a normalized UTF-8 copy sourced from
  [`SUBTLEX-CH-CHR_converted_to_unicode.txt`](https://github.com/becky82/mteh/blob/4e41abfb5f8322c4326710d689fe6a7ca95da727/sources/SUBTLEX/SUBTLEX-CH-CHR_converted_to_unicode.txt)
  in `becky82/mteh`. Unicode conversion of the original GBK-encoded file.
- **License:** no explicit dataset license was found, but the official page
  makes the data available and requests citation of Cai & Brysbaert (2010).

## `kMandarin_8105.txt`

- **Contents:** the most common pronunciation for each of the 8,105
  characters in the 2013 `通用规范汉字表`.
- **Source:** [`mozillazg/pinyin-data`](https://github.com/mozillazg/pinyin-data),
  pinned to
  [commit `70a4480`](https://github.com/mozillazg/pinyin-data/blob/70a4480b09ff92fbfa884dbc0334cf436bf4f9eb/kMandarin_8105.txt).
- **License:** the `pinyin-data` repository is distributed under the
  [MIT License](https://github.com/mozillazg/pinyin-data/blob/master/LICENSE),
  copyright © 2016 mozillazg.

## `pinyin.txt`

- **Contents:** the merged character-to-pinyin output produced by
  `mozillazg/pinyin-data`; this copy is version `0.15.0`.
- **Source:** [`mozillazg/pinyin-data`](https://github.com/mozillazg/pinyin-data),
  pinned to
  [commit `923b108`](https://github.com/mozillazg/pinyin-data/blob/923b108dc5d45dee061324c011b478fb649f8b73/pinyin.txt).
- **License:** the repository is MIT-licensed, as noted above. Its
  [README](https://github.com/mozillazg/pinyin-data/blob/master/README.md)
  documents the component sources merged into this file, including Unicode
  Unihan data and several dictionaries; those underlying sources may have
  their own terms.

## `Unihan_kDefinition.txt`

- **Contents:** the `kDefinition` lines from the Unihan database, providing a
  short English gloss per character. Used as the "Unihan" gloss option.
- **Source:** [Unihan database](https://www.unicode.org/charts/unihan.html),
  extracted from `Unihan_Readings.txt` in the Unicode Character Database
  (`https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip`). Only the
  `kDefinition` lines are retained here.
- **License:** distributed by Unicode, Inc. under the
  [Unicode License](https://www.unicode.org/license.txt) (also referred to as
  the Unicode Data Files and Software License), which permits redistribution
  with attribution.

## `cedict_ts.u8`

- **Contents:** the full CC-CEDICT Chinese–English dictionary. The first
  definition of each single-character entry is used as the "CC-CEDICT" gloss
  option. The original file (including its license header) is kept intact.
- **Source:** [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict),
  published by MDBG.
- **License:**
  [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/)
  (CC BY-SA 4.0). Note the share-alike obligation: redistributing this data or
  adaptations of it (including glosses derived from it) requires attribution
  and the same license.

## `custom-glosses.json`

- **Contents:** short English glosses original to this repository
- **Source:** original work
- **License:** project content under
  [CC BY-SA 4.0](../LICENSE-CONTENT.md).

## `hsk30-chars.csv`

- **Contents:** the 3,088-character HSK 3.0 (2025) reading syllabus, with the
  first HSK band in which each character appears. The official syllabus has
  separate bands 1–6 and one combined advanced band, 7–9.
- **Source:** level files from
  [`becky82/mteh` `sources/HSK3.1`](https://github.com/becky82/mteh/tree/main/sources/HSK3.1)
  (community name for the 2025 revision of the HSK 3.0 syllabus), combined into
  this CSV. Upstream files include
  `HSK3.1_chars_level1.txt` … `HSK3.1_chars_level6.txt` and
  `HSK3.1_chars_level7-9.txt`.
- **License:** The underlying syllabus is PRC Ministry of Education / CTI material.
