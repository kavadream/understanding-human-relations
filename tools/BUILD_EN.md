# Build the English preview

From the repository root:

```sh
python3 -m pip install -r tools/requirements_en.txt
python3 tools/build_en.py
python3 tools/validate_en.py
```

Pandoc and the system libraries required by WeasyPrint (including Pango) must also be installed. No account, AI service, private repository, or external manuscript is needed.

The source files are under `translations/en/`; `book.json` controls the reader-facing order independently of stable IDs. Chapters and the separate front/back matter are the authoritative inputs. `book.md` is the combined reading copy. The output is written only to `dist/en/`, and temporary files to `.build/en/`. This does not change the Chinese edition.

The font is a renamed subset of Noto Serif, distributed under SIL Open Font License 1.1. Its independent notice is in `assets/en/fonts/Noto-Serif-LICENSE.txt`. Regular, bold, and italic faces are embedded. The subset covers this edition; a later addition of uncovered characters causes a build error rather than silently dropping text.

The English edition is an AI-assisted translation preview, not a human-approved final translation. The status is visible on its cover and copyright page. Validation is structural and does not replace human language review or certify learning effects. `validate_en.py` is not official EPUBCheck.
