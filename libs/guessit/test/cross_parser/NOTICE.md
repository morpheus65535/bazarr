# Cross-parser test data — attribution

The `*.json` files in this directory are **generated, derived** test data: each
entry pairs a release name with the metadata that another open-source release-name
parser expects for it, re-expressed in the guessit vocabulary. They are produced by
`scripts/import_cross_parser_tests.py` and consumed by
`guessit/test/test_cross_parser.py` (opt-in, `pytest -m cross_parser`). **Do not
edit them by hand** — re-run the importer.

Each upstream project is redistributed here only as transformed test *data*, under
its own license. License and copyright notices are retained below as required.

| File | Upstream project | License | Copyright |
|------|------------------|---------|-----------|
| `ptt.json` | [dreulavelle/PTT](https://github.com/dreulavelle/PTT) | MIT | © 2024 Spoked |
| `thcolin.json` | [thcolin/scene-release-parser-php](https://github.com/thcolin/scene-release-parser-php) | MIT | © thcolin |
| `go-ptn.json` | [razsteinmetz/go-ptn](https://github.com/razsteinmetz/go-ptn) | MIT | © Raz Steinmetz |
| `ptn.json` | [divijbindlish/parse-torrent-name](https://github.com/divijbindlish/parse-torrent-name) | MIT | © Divij Bindlish |
| `anitomy.json` | [erengy/anitomy](https://github.com/erengy/anitomy) | MPL-2.0 | © Eren Okka |

## Licenses

**MIT** (PTT, scene-release-parser-php, go-ptn, parse-torrent-name): permission is
granted to use, copy, modify, and distribute, provided the copyright notice and
this permission notice are retained. The notices above satisfy that requirement.

**MPL-2.0** (anitomy): the Mozilla Public License 2.0 is a file-level copyleft.
`anitomy.json` is kept as a separate data file carrying its own attribution; it
does not contaminate guessit's own LGPL-licensed source. The full MPL-2.0 text is
at <https://www.mozilla.org/MPL/2.0/>.

> **Not included:** Sonarr and Radarr have very large parser test suites, but both
> are GPLv3 — copyleft incompatible with redistribution inside guessit (LGPLv3) —
> so their fixtures are deliberately excluded.
