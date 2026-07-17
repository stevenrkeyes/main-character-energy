# Steven's Common Character Table

Tables showing the most common characters for each valid syllable in Mandarin Chinese.

## Data

Character frequencies come from [SUBTLEX-CH](https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexch) (Cai & Brysbaert, 2010). Readings are taken primarily from [`kMandarin_8105`](https://github.com/mozillazg/pinyin-data) (通用规范汉字表). See [`data/README.md`](data/README.md) for file-level icensing notes.

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

The original project code is available under the [MIT License](LICENSE).
Third-party datasets in `data/` remain subject to their respective terms and
are not relicensed by this project.
