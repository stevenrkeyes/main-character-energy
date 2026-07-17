# Data provenance and licensing

The project-level MIT license does not automatically relicense third-party
data in this directory. The notes below record where each file came from and
the licensing information that could be verified.

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
