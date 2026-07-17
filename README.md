# Steven's Common Character Table

Tables showing the most common characters for each valid syllable in Mandarin Chinese.

## Data

Character frequencies come from [SUBTLEX-CH](https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexch) (Cai & Brysbaert, 2010). Readings are taken primarily from [`kMandarin_8105`](https://github.com/mozillazg/pinyin-data) (通用规范汉字表). Glosses can be toggled between the [Unihan database](https://www.unicode.org/charts/unihan.html) (`kDefinition`) and [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict) (CC BY-SA 4.0). See [`data/README.md`](data/README.md) for file-level licensing notes.

Rebuild the precomputed tables with:

```bash
python3 scripts/build_tables.py
```

## Deploy on GitHub Pages

1. Push this repository to GitHub.
2. In **Settings → Pages**, set source to **Deploy from a branch**.
3. Choose the `main` branch and `/ (root)`.
4. After deploy, open `https://<user>.github.io/<repo>/`.

## Local preview

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

## License

This is a multi-license project:

- Software code is available under the [MIT License](LICENSE).
- Original website content, visual design, documentation, and generated gloss
  data are available under
  [CC BY-SA 4.0](LICENSE-CONTENT.md).
- Third-party files in `data/` retain their respective terms, documented in
  [`data/README.md`](data/README.md).