## Version 6.2.0 (March 16, 2024)

- Fixed a case where an en-dash and a space near other mojibake would be
  interpreted (probably incorrectly) as MacRoman mojibake.
- Added [project.urls] metadata to pyproject.toml.
- README contains license clarifications for entitled jerks.

## Version 6.1.3 (November 21, 2023)

- Updated wcwidth.
- Switched to the Apache 2.0 license.
- Dropped support for Python 3.7.

## Version 6.1.2 (February 17, 2022)

- Added type information for `guess_bytes`.

## Version 6.1.1 (February 9, 2022)

- Updated the heuristic to fix the letter ß in UTF-8/MacRoman mojibake,
  which had regressed since version 5.6.

- Packaging fixes to pyproject.toml.

## Version 6.1 (February 9, 2022)

- Updated the heuristic to fix the letter Ñ with more confidence.

- Fixed type annotations and added py.typed.

- ftfy is packaged using Poetry now, and wheels are created and uploaded to
  PyPI.

## Version 6.0.3 (May 14, 2021)

- Allow the keyword argument `fix_entities` as a deprecated alias for
  `unescape_html`, raising a warning.

- `ftfy.formatting` functions now disregard ANSI terminal escapes when
  calculating text width.


## Version 6.0.2 (May 4, 2021)

This version is purely a cosmetic change, updating the maintainer's e-mail
address and the project's canonical location on GitHub.


## Version 6.0.1 (April 12, 2021)

- The `remove_terminal_escapes` step was accidentally not being used. This
  version restores it.

- Specified in setup.py that ftfy 6 requires Python 3.6 or later.

- Use a lighter link color when the docs are viewed in dark mode.

## Version 6.0 (April 2, 2021)

- New function: `ftfy.fix_and_explain()` can describe all the transformations
  that happen when fixing a string. This is similar to what
  `ftfy.fixes.fix_encoding_and_explain()` did in previous versions, but it
  can fix more than the encoding.

- `fix_and_explain()` and `fix_encoding_and_explain()` are now in the top-level
  ftfy module.

- Changed the heuristic entirely. ftfy no longer needs to categorize every
  Unicode character, but only characters that are expected to appear in
  mojibake.

- Because of the new heuristic, ftfy will no longer have to release a new
  version for every new version of Unicode. It should also run faster and
  use less RAM when imported.

- The heuristic `ftfy.badness.is_bad(text)` can be used to determine whether
  there appears to be mojibake in a string. Some users were already using
  the old function `sequence_weirdness()` for that, but this one is actually
  designed for that purpose.

- Instead of a pile of named keyword arguments, ftfy functions now take in
  a TextFixerConfig object. The keyword arguments still work, and become
  settings that override the defaults in TextFixerConfig.

- Added support for UTF-8 mixups with Windows-1253 and Windows-1254.

- Overhauled the documentation: https://ftfy.readthedocs.org

## Version 5.9 (February 10, 2021)

This version is brought to you by the letter à and the number 0xC3.

- Tweaked the heuristic to decode, for example, "Ã&nbsp;" as the letter "à"
  more often.

- This combines with the non-breaking-space fixer to decode "Ã " as "à" as
  well. However, in many cases, the text " Ã " was intended to be " à ",
  preserving the space -- the underlying mojibake had two spaces after it, but
  the Web coalesced them into one. We detect this case based on common French
  and Portuguese words, and preserve the space when it appears intended.

Thanks to @zehavoc for bringing to my attention how common this case is.

- Updated the data file of Unicode character categories to Unicode 13, as
  used in Python 3.9. (No matter what version of Python you're on, ftfy uses
  the same data.)

## Version 5.8 (July 17, 2020)

- Improved detection of UTF-8 mojibake of Greek, Cyrillic, Hebrew, and Arabic
  scripts.

- Fixed the undeclared dependency on setuptools by removing the use of
  `pkg_resources`.

## Version 5.7 (February 18, 2020)

- Updated the data file of Unicode character categories to Unicode 12.1, as
  used in Python 3.8. (No matter what version of Python you're on, ftfy uses
  the same data.)

- Corrected an omission where short sequences involving the ACUTE ACCENT
  character were not being fixed.

## Version 5.6 (August 7, 2019)

- The `unescape_html` function now supports all the HTML5 entities that appear
  in `html.entities.html5`, including those with long names such as
  `&DiacriticalDoubleAcute;`.

- Unescaping of numeric HTML entities now uses the standard library's
  `html.unescape`, making edge cases consistent.

  (The reason we don't run `html.unescape` on all text is that it's not always
  appropriate to apply, and can lead to false positive fixes. The text
  "This&NotThat" should not have "&Not" replaced by a symbol, as
  `html.unescape` would do.)

- On top of Python's support for HTML5 entities, ftfy will also convert HTML
  escapes of common Latin capital letters that are (nonstandardly) written
  in all caps, such as `&NTILDE;` for `Ñ`.


## Version 5.5.1 (September 14, 2018)

- Added Python 3.7 support.

- Updated the data file of Unicode character categories to Unicode 11, as used
  in Python 3.7.0. (No matter what version of Python you're on, ftfy uses the
  same data.)


## Version 5.5 (September 6, 2018)

- Recent versions have emphasized making a reasonable attempt to fix short,
  common mojibake sequences, such as `Ã»`. In this version, we've expanded the
  heuristics to recognize these sequences in MacRoman as well as Windows-125x
  encodings.

- A related rule for fixing isolated Windows-1252/UTF-8 mixups, even when they
  were inconsistent with the rest of the string, claimed to work on Latin-1/UTF-8
  mixups as well, but in practice it didn't. We've made the rule more robust.

- Fixed a failure when testing the CLI on Windows.

- Removed the `pytest-runner` invocation from setup.py, as it created complex
  dependencies that would stop setup.py from working in some environments.
  The `pytest` command still works fine. `pytest-runner` is just too clever.


## Version 5.4.1 (June 14, 2018)

- Fixed a bug in the `setup.py` metadata.

  This bug was causing ftfy, a package that fixes encoding mismatches, to not
  install in some environments due to an encoding mismatch. (We were really
  putting the "meta" in "metadata" here.)


## Version 5.4 (June 1, 2018)

- ftfy was still too conservative about fixing short mojibake sequences,
  such as "aoÃ»t" -> "août", when the broken version contained punctuation
  such as curly or angle quotation marks.

  The new heuristic observes in some cases that, even if quotation marks are
  expected to appear next to letters, it is strange to have an accented capital
  A before the quotation mark and more letters after the quotation mark.

- Provides better metadata for the new PyPI.

- Switched from nosetests to pytest.


## Version 5.3 (January 25, 2018)

- A heuristic has been too conservative since version 4.2, causing a regression
  compared to previous versions: ftfy would fail to fix mojibake of common
  characters such as `á` when seen in isolation. A new heuristic now makes it
  possible to fix more of these common cases with less evidence.


## Version 5.2 (November 27, 2017)

- The command-line tool will not accept the same filename as its input
  and output. (Previously, this would write a zero-length file.)

- The `uncurl_quotes` fixer, which replaces curly quotes with straight quotes,
  now also replaces MODIFIER LETTER APOSTROPHE.

- Codepoints that contain two Latin characters crammed together for legacy
  encoding reasons are replaced by those two separate characters, even in NFC
  mode. We formerly did this just with ligatures such as `ﬁ` and `Ĳ`, but now
  this includes the Afrikaans digraph `ŉ` and Serbian/Croatian digraphs such as
  `ǆ`.


## Version 5.1.1 and 4.4.3 (May 15, 2017)

These releases fix two unrelated problems with the tests, one in each version.

- v5.1.1: fixed the CLI tests (which are new in v5) so that they pass
  on Windows, as long as the Python output encoding is UTF-8.

- v4.4.3: added the `# coding: utf-8` declaration to two files that were
  missing it, so that tests can run on Python 2.

## Version 5.1 (April 7, 2017)

- Removed the dependency on `html5lib` by dropping support for Python 3.2.

  We previously used the dictionary `html5lib.constants.entities` to decode
  HTML entities.  In Python 3.3 and later, that exact dictionary is now in the
  standard library as `html.entities.html5`.

- Moved many test cases about how particular text should be fixed into
  `test_cases.json`, which may ease porting to other languages.

The functionality of this version remains the same as 5.0.2 and 4.4.2.


## Version 5.0.2 and 4.4.2 (March 21, 2017)

Added a `MANIFEST.in` that puts files such as the license file and this
changelog inside the source distribution.


## Version 5.0.1 and 4.4.1 (March 10, 2017)

Bug fix:

- The `unescape_html` fixer will decode entities between `&#128;` and `&#159;`
  as what they would be in Windows-1252, even without the help of
  `fix_encoding`.

  This better matches what Web browsers do, and fixes a regression that version
  4.4 introduced in an example that uses `&#133;` as an ellipsis.


## Version 5.0 (February 17, 2017)

Breaking changes:

- Dropped support for Python 2. If you need Python 2 support, you should get
  version 4.4, which has the same features as this version.

- The top-level functions require their arguments to be given as keyword
  arguments.

Version 5.0 also now has tests for the command-line invocation of ftfy.


## Version 4.4.0 (February 17, 2017)

Heuristic changes:

- ftfy can now fix mojibake involving the Windows-1250 or ISO-8859-2 encodings.

- The `fix_entities` fixer is now applied after `fix_encoding`. This makes
  more situations resolvable when both fixes are needed.

- With a few exceptions for commonly-used characters such as `^`, it is now
  considered "weird" whenever a diacritic appears in non-combining form,
  such as the diaeresis character `¨`.

- It is also now weird when IPA phonetic letters, besides `ə`, appear next to
  capital letters.

- These changes to the heuristics, and others we've made in recent versions,
  let us lower the "cost" for fixing mojibake in some encodings, causing them
  to be fixed in more cases.


## Version 4.3.1 (January 12, 2017)

Bug fix:

- `remove_control_chars` was removing U+0D ('\r') prematurely. That's the
  job of `fix_line_breaks`.


## Version 4.3.0 (December 29, 2016)

ftfy has gotten by for four years without dependencies on other Python
libraries, but now we can spare ourselves some code and some maintenance burden
by delegating certain tasks to other libraries that already solve them well.
This version now depends on the `html5lib` and `wcwidth` libraries.

Feature changes:

- The `remove_control_chars` fixer will now remove some non-ASCII control
  characters as well, such as deprecated Arabic control characters and
  byte-order marks. Bidirectional controls are still left as is.

  This should have no impact on well-formed text, while cleaning up many
  characters that the Unicode Consortium deems "not suitable for markup"
  (see Unicode Technical Report #20).

- The `unescape_html` fixer uses a more thorough list of HTML entities,
  which it imports from `html5lib`.

- `ftfy.formatting` now uses `wcwidth` to compute the width that a string
  will occupy in a text console.

Heuristic changes:

- Updated the data file of Unicode character categories to Unicode 9, as used
  in Python 3.6.0. (No matter what version of Python you're on, ftfy uses the
  same data.)

Pending deprecations:

- The `remove_bom` option will become deprecated in 5.0, because it has been
  superseded by `remove_control_chars`.

- ftfy 5.0 will remove the previously deprecated name `fix_text_encoding`. It
  was renamed to `fix_encoding` in 4.0.

- ftfy 5.0 will require Python 3.2 or later, as planned. Python 2 users, please
  specify `ftfy < 5` in your dependencies if you haven't already.


## Version 4.2.0 (September 28, 2016)

Heuristic changes:

- Math symbols next to currency symbols are no longer considered 'weird' by the
  heuristic. This fixes a false positive where text that involved the
  multiplication sign and British pounds or euros (as in '5×£35') could turn
  into Hebrew letters.

- A heuristic that used to be a bonus for certain punctuation now also gives a
  bonus to successfully decoding other common codepoints, such as the
  non-breaking space, the degree sign, and the byte order mark.

- In version 4.0, we tried to "future-proof" the categorization of emoji (as a
  kind of symbol) to include codepoints that would likely be assigned to emoji
  later. The future happened, and there are even more emoji than we expected.
  We have expanded the range to include those emoji, too.

  ftfy is still mostly based on information from Unicode 8 (as Python 3.5 is),
  but this expanded range should include the emoji from Unicode 9 and 10.

- Emoji are increasingly being modified by variation selectors and skin-tone
  modifiers. Those codepoints are now grouped with 'symbols' in ftfy, so they
  fit right in with emoji, instead of being considered 'marks' as their Unicode
  category would suggest.

  This enables fixing mojibake that involves iOS's new diverse emoji.

- An old heuristic that wasn't necessary anymore considered Latin text with
  high-numbered codepoints to be 'weird', but this is normal in languages such
  as Vietnamese and Azerbaijani. This does not seem to have caused any false
  positives, but it caused ftfy to be too reluctant to fix some cases of broken
  text in those languages.

  The heuristic has been changed, and all languages that use Latin letters
  should be on even footing now.


## Version 4.1.1 (April 13, 2016)

- Bug fix: in the command-line interface, the `-e` option had no effect on
  Python 3 when using standard input. Now, it correctly lets you specify
  a different encoding for standard input.


## Version 4.1.0 (February 25, 2016)

Heuristic changes:

- ftfy can now deal with "lossy" mojibake. If your text has been run through
  a strict Windows-1252 decoder, such as the one in Python, it may contain
  the replacement character � (U+FFFD) where there were bytes that are
  unassigned in Windows-1252.

  Although ftfy won't recover the lost information, it can now detect this
  situation, replace the entire lossy character with �, and decode the rest of
  the characters. Previous versions would be unable to fix any string that
  contained U+FFFD.

  As an example, text in curly quotes that gets corrupted `â€œ like this â€�`
  now gets fixed to be `“ like this �`.

- Updated the data file of Unicode character categories to Unicode 8.0, as used
  in Python 3.5.0. (No matter what version of Python you're on, ftfy uses the
  same data.)

- Heuristics now count characters such as `~` and `^` as punctuation instead
  of wacky math symbols, improving the detection of mojibake in some edge cases.

New features:

- A new module, `ftfy.formatting`, can be used to justify Unicode text in a
  monospaced terminal. It takes into account that each character can take up
  anywhere from 0 to 2 character cells.

- Internally, the `utf-8-variants` codec was simplified and optimized.


## Version 4.0.0 (April 10, 2015)

Breaking changes:

- The default normalization form is now NFC, not NFKC. NFKC replaces a large
  number of characters with 'equivalent' characters, and some of these
  replacements are useful, but some are not desirable to do by default.

- The `fix_text` function has some new options that perform more targeted
  operations that are part of NFKC normalization, such as
  `fix_character_width`, without requiring hitting all your text with the huge
  mallet that is NFKC.

  - If you were already using NFC normalization, or in general if you want to
    preserve the *spacing* of CJK text, you should be sure to set
    `fix_character_width=False`.

- The `remove_unsafe_private_use` parameter has been removed entirely, after
  two versions of deprecation. The function name `fix_bad_encoding` is also
  gone.

New features:

- Fixers for strange new forms of mojibake, including particularly clear cases
  of mixed UTF-8 and Windows-1252.

- New heuristics, so that ftfy can fix more stuff, while maintaining
  approximately zero false positives.

- The command-line tool trusts you to know what encoding your *input* is in,
  and assumes UTF-8 by default. You can still tell it to guess with the `-g`
  option.

- The command-line tool can be configured with options, and can be used as a
  pipe.

- Recognizes characters that are new in Unicode 7.0, as well as emoji from
  Unicode 8.0+ that may already be in use on iOS.

Deprecations:

- `fix_text_encoding` is being renamed again, for conciseness and consistency.
  It's now simply called `fix_encoding`. The name `fix_text_encoding` is
  available but emits a warning.

Pending deprecations:

- Python 2.6 support is largely coincidental.

- Python 2.7 support is on notice. If you use Python 2, be sure to pin a
  version of ftfy less than 5.0 in your requirements.


## Version 3.4.0 (January 15, 2015)

New features:

- `ftfy.fixes.fix_surrogates` will fix all 16-bit surrogate codepoints,
  which would otherwise break various encoding and output functions.

Deprecations:

- `remove_unsafe_private_use` emits a warning, and will disappear in the
  next minor or major version.


## Version 3.3.1 (December 12, 2014)

This version restores compatibility with Python 2.6.


## Version 3.3.0 (August 16, 2014)

Heuristic changes:

- Certain symbols are marked as "ending punctuation" that may naturally occur
  after letters. When they follow an accented capital letter and look like
  mojibake, they will not be "fixed" without further evidence.
  An example is that "MARQUÉ…" will become "MARQUÉ...", and not "MARQUɅ".

New features:

- `ftfy.explain_unicode` is a diagnostic function that shows you what's going
  on in a Unicode string. It shows you a table with each code point in
  hexadecimal, its glyph, its name, and its Unicode category.

- `ftfy.fixes.decode_escapes` adds a feature missing from the standard library:
  it lets you decode a Unicode string with backslashed escape sequences in it
  (such as "\u2014") the same way that Python itself would.

- `ftfy.streamtester` is a release of the code that I use to test ftfy on
  an endless stream of real-world data from Twitter. With the new heuristics,
  the false positive rate of ftfy is about 1 per 6 million tweets. (See
  the "Accuracy" section of the documentation.)

Deprecations:

- Python 2.6 is no longer supported.

- `remove_unsafe_private_use` is no longer needed in any current version of
  Python. This fixer will disappear in a later version of ftfy.


## Version 3.2.0 (June 27, 2014)

- `fix_line_breaks` fixes three additional characters that are considered line
  breaks in some environments, such as Javascript, and Python's "codecs"
  library. These are all now replaced with \n:

      U+0085   <control>, with alias "NEXT LINE"
      U+2028   LINE SEPARATOR
      U+2029   PARAGRAPH SEPARATOR


## Version 3.1.3 (May 15, 2014)

- Fix `utf-8-variants` so it never outputs surrogate codepoints, even on
  Python 2 where that would otherwise be possible.


## Version 3.1.2 (January 29, 2014)

- Fix bug in 3.1.1 where strings with backslashes in them could never be fixed


## Version 3.1.1 (January 29, 2014)

- Add the `ftfy.bad_codecs` package, which registers new codecs that can
  decoding things that Python may otherwise refuse to decode:

  - `utf-8-variants`, which decodes CESU-8 and its Java lookalike

  - `sloppy-windows-*`, which decodes character-map encodings while treating
    unmapped characters as Latin-1

- Simplify the code using `ftfy.bad_codecs`.


## Version 3.0.6 (November 5, 2013)

- `fix_entities` can now be True, False, or 'auto'. The new case is True, which
  will decode all entities, even in text that already contains angle brackets.
  This may also be faster, because it doesn't have to check.
- `build_data.py` will refuse to run on Python < 3.3, to prevent building
  an inconsistent data file.


## Version 3.0.5 (November 1, 2013)

- Fix the arguments to `fix_file`, because they were totally wrong.


## Version 3.0.4 (October 1, 2013)

- Restore compatibility with Python 2.6.


## Version 3.0.3 (September 9, 2013)

- Fixed an ugly regular expression bug that prevented ftfy from importing on a
  narrow build of Python.


## Version 3.0.2 (September 4, 2013)

- Fixed some false positives.

  - Basically, 3.0.1 was too eager to treat text as MacRoman or cp437 when
    three consecutive characters coincidentally decoded as UTF-8. Increased the
    cost of those encodings so that they have to successfully decode multiple
    UTF-8 characters.

  - See `tests/test_real_tweets.py` for the new test cases that were added as a
    result.


## Version 3.0.1 (August 30, 2013)

- Fix bug in `fix_java_encoding` that led to only the first instance of
  CESU-8 badness per line being fixed
- Add a fixer that removes unassigned characters that can break Python 3.3
  (http://bugs.python.org/issue18183)


## Version 3.0 (August 26, 2013)

- Generally runs faster
- Idempotent
- Simplified decoding logic
- Understands more encodings and more kinds of mistakes
- Takes options that enable or disable particular normalization steps
- Long line handling: now the time-consuming step (`fix_text_encoding`) will be
  consistently skipped on long lines, but all other fixes will apply
- Tested on millions of examples from Twitter, ensuring a near-zero rate of
  false positives


## Version 2.0.2 (June 20, 2013)

- Fix breaking up of long lines, so it can't go into an infinite loop


## Version 2.0.1 (March 19, 2013)

- Restored Python 2.6 support


## Version 2.0 (January 30, 2013)

- Python 3 support
- Use fast Python built-ins to speed up fixes
- Bugfixes


## Version 1.0 (August 24, 2012)

- Made into its own package with no dependencies, instead of a part of
  `metanl`
