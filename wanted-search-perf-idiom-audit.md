# Wanted Search Perf Idiom Audit

Scope: `mjc/wanted-search-integration..HEAD` on `mjc/wanted-search-perf`.

Current scope evidence:

```text
13 commits
36 changed files
2753 insertions, 957 deletions
```

This audit looks for non-idiomatic Python, pytest, SQLAlchemy, and branch-local maintainability issues. It is not a bug-only review; some items are deliberate performance tradeoffs, but they are still listed because they are less idiomatic or raise maintenance cost.

## Findings

### I01. Three independent repr-list parsers now exist

Evidence:

- `bazarr/subtitles/serialization.py:6` defines `_parse_repr_list`.
- `bazarr/app/config.py:951` defines `_parse_text_array`.
- `bazarr/app/database.py:575` defines `_parse_audio_languages_text`.
- `migrations/versions/e6cbb0f6f9b1_.py:48` defines `_parse_missing_text_tuple`.

Why it is non-idiomatic:

The branch replaces `ast.literal_eval` in hot paths with hand-written parsers, which is reasonable for performance, but the parser logic is copied instead of centralized. That creates several subtly different grammars and error behaviors for the same legacy representation.

Suggested direction:

Use one shared parser for runtime code, for example `subtitles.serialization.parse_text_list_or_default`, and keep the migration copy only if Alembic/import isolation requires it. If the migration needs its own copy, add a note saying it intentionally mirrors the runtime parser.

Status: complete in code. `app.config`, `app.database`, and the migration now all use the shared text-list parser or shared attempt-window helper instead of separate local repr-list parsers.

### I02. Legacy repr serialization is still emitted from new normalized state code

Status: complete

Evidence:

- `bazarr/subtitles/wanted_state.py:62` serializes normalized attempt rows back to `str(sorted(...))`.
- `bazarr/subtitles/adaptive_searching.py:342` returns `str(updated_attempts)`.
- `tests/bazarr/wanted_search_fixtures.py:167` and `tests/bazarr/wanted_search_fixtures.py:175` duplicate that representation in test helpers.

Why it is non-idiomatic:

The normalized tables are the new source of truth, but new code still emits Python repr strings for legacy column compatibility. That is understandable for compatibility, but the serialization format is spread across modules instead of being isolated behind a named legacy adapter.

Suggested direction:

Move legacy write-through helpers into one module with names that say `legacy`, for example `serialize_legacy_failed_attempts` and `serialize_legacy_missing_subtitles`, then make production and tests call those helpers.

### I03. `missing_subtitle_to_language_tuple` loses combined flags

Evidence:

- `bazarr/subtitles/serialization.py:103` checks `language.endswith(':hi')` and `language.endswith(':forced')`.
- `tests/bazarr/test_wanted_search_language_unit.py:72` passes `"en:hi:forced"` but expects `("en", "False", "True")`.

Why it is non-idiomatic:

The parser silently treats a combined `hi` + `forced` token as only forced if `forced` is the last suffix. The older `parse_language_token` in `bazarr/subtitles/language_utils.py:8` handles flags as a set. Having two language parsers with different semantics is surprising and test-encoded.

Suggested direction:

Reuse `parse_language_token` or move flag parsing into a single helper that handles order-independent flags. If combined flags are intentionally unsupported, tests and helper names should say so directly.

Status: complete in code. `missing_subtitle_to_language_tuple` now reuses `parse_language_token`, and the unit coverage was updated to expect combined `hi` + `forced` flags.

### I04. `language_utils.safe_missing_languages` still uses `ast.literal_eval`

Evidence:

- `bazarr/subtitles/language_utils.py:30` calls `ast.literal_eval`.
- `bazarr/subtitles/language_utils.py:76` still exposes `build_search_payload`, which uses `safe_missing_languages`.

Why it is non-idiomatic for this branch:

The branch is explicitly moving wanted search away from `literal_eval` and toward a faster parser/normalized table path. Leaving a nearby helper on `literal_eval` makes the parsing story inconsistent, and future callers may accidentally reintroduce the hot-path cost.

Suggested direction:

Either remove dead wanted-search call paths if `build_search_payload` is no longer needed, or make `safe_missing_languages` delegate to the shared parser.

Status: complete in code. `safe_missing_languages` now uses the shared text-list parser instead of `ast.literal_eval`.

### I05. Migration parser does not share runtime parser tests

Evidence:

- `migrations/versions/e6cbb0f6f9b1_.py:48` through `migrations/versions/e6cbb0f6f9b1_.py:177` contains migration-specific parsing.
- There is no migration-specific parser test file in the branch diff.

Why it is non-idiomatic:

The migration carries a high-risk copy of parsing code, but tests exercise the runtime helpers more than the migration grammar itself. Since this parser backfills user data, its malformed-input behavior should be locked down separately.

Suggested direction:

Add direct tests around the migration parser/backfill helpers or refactor the parser into an importable helper that both runtime tests and migration tests can exercise.

Status: complete in code. The migration now uses the shared runtime parsers and has dedicated tests for the backfill append helpers.

### I06. Migration mixes Alembic operations, SQLAlchemy Core, and raw DB-API cursor paths

Evidence:

- `migrations/versions/e6cbb0f6f9b1_.py:180` uses SQLAlchemy inserts.
- `migrations/versions/e6cbb0f6f9b1_.py:217` and `migrations/versions/e6cbb0f6f9b1_.py:224` use cursor `executemany`.
- `migrations/versions/e6cbb0f6f9b1_.py:249` uses `exec_driver_sql`.

Why it is non-idiomatic:

This is a performance-oriented migration, but three data-access styles in one migration makes it harder to reason about transaction boundaries, error handling, and dialect behavior.

Suggested direction:

Keep the SQLite fast path if benchmarked, but split it into clearly named dialect-specific functions and add comments documenting why raw DB-API is used.

### I07. Migration SQL interpolates table and column names with f-strings

Evidence:

- `migrations/versions/e6cbb0f6f9b1_.py:250` and `migrations/versions/e6cbb0f6f9b1_.py:280` build SQL with `id_column` and `table_name`.

Why it is non-idiomatic:

The values are currently internal constants, so this is not user input, but SQLAlchemy/Alembic code usually models identifiers structurally rather than interpolating them. It makes future edits easier to misuse.

Suggested direction:

Use `sa.table` metadata for both source tables or centralize the allowed source table mapping so only whitelisted identifiers can be used.

### I08. Wanted movie and series modules duplicate large blocks of logic

Evidence:

- `bazarr/subtitles/wanted/movies.py:90` mirrors `bazarr/subtitles/wanted/series.py:73`.
- `bazarr/subtitles/wanted/movies.py:109` mirrors `bazarr/subtitles/wanted/series.py:93`.
- `bazarr/subtitles/wanted/movies.py:262` mirrors `bazarr/subtitles/wanted/series.py:246`.
- `bazarr/subtitles/wanted/movies.py:315` mirrors `bazarr/subtitles/wanted/series.py:299`.

Why it is non-idiomatic:

The branch added normalized due filtering, refresh handling, provider throttling, deferred failed-attempt writes, and temp-table updates twice. The two copies are close but not identical, which makes future bug fixes prone to only landing on one side.

Suggested direction:

Extract shared primitives around count/query due media, deferred failed-attempt flushing, and provider-loop orchestration while leaving media-specific history/indexing calls in the two modules.

### I09. Private module-level SQL statements are rebound by tests

Evidence:

- Production statements are defined at import time in `bazarr/subtitles/wanted/movies.py:39` and `bazarr/subtitles/wanted/series.py:40`.
- Tests mutate them in `tests/bazarr/wanted_search_fixtures.py:214` and `tests/bazarr/wanted_search_fixtures.py:267`.

Why it is non-idiomatic pytest/SQLAlchemy:

The tests have to reach inside private globals because the statements bind to production table objects at import time. This makes import order and fixture setup part of correctness.

Suggested direction:

Prefer statement builder functions that read current table objects when called, or pass table/session dependencies explicitly in tests. That removes the need to reassign private `_WANTED_*` globals.

### I10. Test table proxies imitate ORM models instead of using one consistent model/table shape

Evidence:

- `tests/bazarr/wanted_search_fixtures.py:147` defines `_TableProxy`.
- `tests/bazarr/wanted_search_fixtures.py:657` through `tests/bazarr/wanted_search_fixtures.py:688` monkeypatch many production module globals to proxies.

Why it is non-idiomatic:

The proxy only implements the small surface area current tests need. Production code uses a mix of ORM-like models, SQLAlchemy table columns, and `__table__` access, so proxies can diverge from real behavior.

Suggested direction:

Either use real declarative test models or refactor production helpers to accept SQLAlchemy `Table` objects/session dependencies in a way tests can provide directly.

### I11. Test fixture routing depends on test names and fixture names

Evidence:

- `tests/bazarr/wanted_search_fixtures.py:304` infers `"movies"` or `"series"` from `request.node.name` and fixture names.

Why it is non-idiomatic pytest:

Implicit routing by test name makes renames behavior-changing. It is clever, but hidden.

Suggested direction:

Use explicit `kind` parametrization everywhere or split movie/series fixtures (`movie_wanted_module`, `series_wanted_module`) so dependency selection is visible in the test signature.

### I12. Row factories return `SimpleNamespace` snapshots, not persisted rows

Evidence:

- `tests/bazarr/wanted_search_fixtures.py:161` inserts into SQLAlchemy tables and returns `SimpleNamespace(**values)`.
- Tests mutate returned rows, for example `tests/bazarr/test_wanted_search_paths.py:117`.

Why it is non-idiomatic:

The object looks row-like but is detached from the database. Mutating it changes only the in-memory object, which is fine for worker-unit tests but misleading when the same factories also seed DB state.

Suggested direction:

Return actual selected rows/mappings from the transactional session, or introduce small dataclasses with names that make the snapshot nature explicit.

### I13. Test fixtures serialize legacy values instead of reading production serializers

Evidence:

- `tests/bazarr/wanted_search_fixtures.py:167` serializes missing languages.
- `tests/bazarr/wanted_search_fixtures.py:175` serializes failed attempts.

Why it is non-idiomatic:

The tests now encode a separate copy of legacy serialization rules. If production serialization changes, tests can keep passing against their own local format rather than the app's format.

Suggested direction:

Use production serialization helpers where possible. If tests intentionally bypass production serialization, name the helpers as legacy test fixtures and add focused tests proving they match production.

### I14. Wanted search still asks providers once per candidate

Evidence:

- `bazarr/subtitles/wanted/movies.py:356` calls `get_providers()` inside the movie loop.
- `bazarr/subtitles/wanted/series.py:346` calls `get_providers()` inside the episode loop.

Why it is non-idiomatic/performance-adjacent:

The per-candidate refresh fixed throttling correctness, but it also hardwires provider polling into the inner loop. A provider-availability service or iterator could make the correctness rule explicit without scattering the call.

Suggested direction:

Wrap provider refresh in a small helper/iterator that documents "refresh each candidate because providers can throttle mid-run." That would also make tests less dependent on monkeypatching `get_providers` directly.

### I15. Deferred failed-attempt flushing uses mutable dict accumulation and manual flush points

Evidence:

- `bazarr/subtitles/wanted/movies.py:333` accumulates `pending_failed_attempts`.
- `bazarr/subtitles/wanted/movies.py:391` and `bazarr/subtitles/wanted/movies.py:396` flush it.
- `bazarr/subtitles/wanted/series.py:317`, `bazarr/subtitles/wanted/series.py:381`, and `bazarr/subtitles/wanted/series.py:386` do the same.

Why it is non-idiomatic:

The manual flush points are easy to get wrong during future early returns or exception handling. The dict mutation is currently local, but the lifecycle is not encapsulated.

Suggested direction:

Use a tiny accumulator object or context manager with `add()` and `flush()` methods, shared by movie and series paths.

### I16. Raw temp-table updates are embedded in wanted modules

Status: complete

Evidence:

- `bazarr/subtitles/wanted/movies.py:275` through `bazarr/subtitles/wanted/movies.py:295`.
- `bazarr/subtitles/wanted/series.py:259` through `bazarr/subtitles/wanted/series.py:279`.

Why it is non-idiomatic SQLAlchemy:

The temp-table optimization is a valid SQLite performance tactic, but embedding raw SQL strings in both wanted modules makes the branch harder to maintain and less portable.

Suggested direction:

Move this into a shared helper, probably in `wanted_state`, with parameters for target table name and ID column. Keep dialect-specific raw SQL isolated.

### I17. `database.bind.engine.dialect.name` assumes session binding shape

Status: complete

Evidence:

- `bazarr/subtitles/wanted/movies.py:273`.
- `bazarr/subtitles/wanted/series.py:257`.

Why it is non-idiomatic SQLAlchemy:

This reaches through Flask-SQLAlchemy/scoped-session internals to infer dialect. It is awkward to test, and it is one reason test fixtures need to imitate more of the production session shape.

Suggested direction:

Resolve dialect through a small database helper, or pass the dialect/connection explicitly into the batch update helper.

### I18. `refresh_wanted_search_state` accepts an unused policy parameter

Evidence:

- `bazarr/subtitles/wanted_state.py:177` accepts `adaptive_search_policy=None`, but the function does not use it.

Why it is non-idiomatic:

Unused parameters invite mistaken assumptions from callers and tests.

Suggested direction:

Remove the parameter unless there is a planned immediate use. If it is forward-looking, add a comment explaining why it exists now.

Status: complete in code. `refresh_wanted_search_state` no longer accepts the unused policy parameter.

### I19. API list endpoints now do two-phase missing-language loading and still call `postprocess` per row

Status: complete in code. The list endpoints now bulk-load subtitles by media id and hand them into `postprocess`, so the per-row subtitle query is gone.

Evidence:

- `bazarr/api/episodes/episodes.py:77` loads normalized missing language maps after loading episodes.
- `bazarr/api/movies/movies.py:90` does the same for movies.
- `bazarr/api/episodes/wanted.py:82` and `bazarr/api/movies/wanted.py:72` do the same for wanted endpoints.
- `api.utils.postprocess` still calls `get_subtitles` for each row at `bazarr/api/utils.py:72`.

Why it is non-idiomatic/performance-adjacent:

The branch removes one serialized-column parsing cost but keeps a two-phase loading pattern and an existing per-row subtitle lookup in `postprocess`. The endpoint shape is common in this codebase, but it is still not ideal SQLAlchemy usage for list views.

Suggested direction:

Consider an API-specific loader that returns all needed subtitles and missing-language rows in bulk, then postprocesses from maps.

### I20. `check_missing_languages` does a DB lookup for each language checked

Status: complete

Evidence:

- `bazarr/subtitles/download.py:70` loops over `language_set`.
- `bazarr/subtitles/download.py:72` calls `check_missing_languages(path, media_type)` inside that loop.
- `bazarr/subtitles/download.py:151` queries normalized missing subtitles.

Why it is non-idiomatic:

The per-language recheck is correctness-preserving for concurrent changes, but it is an N+1 shape inside a download attempt. The function name hides that it now performs database work each time.

Suggested direction:

If correctness requires rechecking before each language, keep it. Otherwise, make the recheck helper explicit about being a DB read and consider a narrowly scoped cache invalidated after each successful save.

### I21. Mass-download paths mix old legacy columns with normalized table reads

Status: complete

Evidence:

- `bazarr/subtitles/mass_download/movies.py:65` checks `movie.missing_subtitles is None`, but `bazarr/subtitles/mass_download/movies.py:81` reads normalized rows.
- `bazarr/subtitles/mass_download/series.py:143` checks `episode.missing_subtitles is None`, but `bazarr/subtitles/mass_download/series.py:160` reads normalized rows.

Why it is non-idiomatic:

The branch keeps legacy columns written, but the read path now mixes old "is cache populated?" signals with normalized table data. That is easy to misread as two sources of truth.

Suggested direction:

Add helper names that make this distinction clear, for example `legacy_missing_cache_needs_rebuild` and `get_normalized_missing_languages`.

### I22. Manual tests rely heavily on lambda monkeypatching

Status: complete

Evidence:

- `tests/bazarr/test_manual_paths.py:14` through `tests/bazarr/test_manual_paths.py:22`.
- `tests/bazarr/test_manual_paths.py:89` through `tests/bazarr/test_manual_paths.py:122`.

Why it is non-idiomatic pytest:

Inline lambdas are compact, but many of them make assertions and setup harder to read. This is especially true where behavior matters more than "do nothing."

Suggested direction:

Use named fakes/fixtures for recurring manual-download dependencies.

### I23. Wrapper/path tests directly exercise private workers

Status: complete

Evidence:

- `tests/bazarr/wanted_search_fixtures.py:709` exposes `_wanted_movie`/`_wanted_episode`.
- `tests/bazarr/test_wanted_search_paths.py:83` and `tests/bazarr/test_wanted_search_language_unit.py:53` call the private worker fixture.

Why it is non-idiomatic:

Testing private workers can be justified for complicated internal state, but here it broadens the public test surface of functions that may need refactoring.

Suggested direction:

Keep a small number of private-worker tests for tight branch behavior and move broader assertions to public wrapper/scheduled-search tests.

### I24. Test assertions sometimes verify loose outcomes instead of specific behavior

Status: complete

Evidence:

- `tests/bazarr/test_wanted_search_paths.py:253` and `tests/bazarr/test_wanted_search_paths.py:256` accept any job name containing broad words like "movie", "series", "search", or "subtitle".

Why it is non-idiomatic pytest:

Loose assertions make tests resilient but less diagnostic. These tests can pass if the wrong final job name is emitted as long as it contains a generic word.

Suggested direction:

Assert the exact expected terminal job name or the exact sequence length/key fields when feasible.

### I25. Attempt timestamps use wall-clock `datetime.now()` directly in tests

Status: complete

Evidence:

- `tests/bazarr/test_wanted_search_paths.py:26`.

Why it is non-idiomatic:

The window is broad, so this is unlikely to flake, but wall-clock tests are harder to reason about. The production code already supports passing `adaptive_search_policy`.

Suggested direction:

Build fixed adaptive policies in tests instead of deriving attempts from current time.

### I26. Some branch changes are incidental style cleanup mixed into behavior commits

Status: complete in code. The cleanup comments now document why the scene-name and upgrade-label tweaks stay with the wanted-search normalization work.

Evidence:

- `bazarr/subtitles/utils.py:37` changes scene-name truthiness.
- `bazarr/subtitles/upgrade.py:88` changes episode label formatting while the branch is mainly wanted-search normalization/performance.
- `bazarr/subtitles/upgrade.py:106` and `bazarr/subtitles/manual.py` changes share audio-language helper behavior.

Why it is non-idiomatic for branch hygiene:

These are reasonable cleanups, but they are not obviously part of the normalized wanted state. Mixed-scope changes increase PR review load.

Suggested direction:

Either document why each is part of the normalization branch or split into a small prerequisite/follow-up commit.

### I27. Table names in tests intentionally differ from production for core media tables

Status: complete

Evidence:

- `tests/bazarr/wanted_search_fixtures.py:20` uses `wanted_movie_rows`.
- `tests/bazarr/wanted_search_fixtures.py:40` uses `wanted_episode_rows`.
- Normalized tables use production names at `tests/bazarr/wanted_search_fixtures.py:126` and `tests/bazarr/wanted_search_fixtures.py:134`.

Why it is non-idiomatic:

Mixing fake names for some tables and real names for normalized tables makes raw SQL paths difficult to test and reason about. It also hides production table-name coupling until a test hits a raw SQL branch.

Suggested direction:

Use production table names consistently in test tables when production code contains raw SQL, or isolate raw SQL behind a helper that can be tested independently.

### I28. Test normalized attempt timestamp columns use `Integer`, production uses `Float`

Evidence:

- `bazarr/app/database.py:309` and `bazarr/app/database.py:310` define `Float`.
- `tests/bazarr/wanted_search_fixtures.py:141` and `tests/bazarr/wanted_search_fixtures.py:142` define `Integer`.

Why it is non-idiomatic:

The test schema does not match production. Current tests may still pass because SQLite is permissive, but the mismatch is easy to trip over when checking precise values.

Suggested direction:

Use `Float` in the test fixture schema.

Status: complete in code. The wanted-search fixture schema now uses `Float` for both attempt timestamp columns, matching production.

### I29. `TableMissingSubtitles` and `TableFailedSubtitleAttempts` lack explicit FK relationships

Status: complete in code. The table definitions now document the polymorphic cleanup tradeoff, and the branch already covers the delete/cleanup paths in wanted-search tests.

Evidence:

- `bazarr/app/database.py:292` through `bazarr/app/database.py:315` define `media_type` and `media_id`, but no FK constraints to movie/episode tables.

Why it is non-idiomatic database design:

Polymorphic references are sometimes necessary, but they trade database-enforced integrity for application cleanup paths. The branch compensates with delete helpers, but missing cleanup remains possible.

Suggested direction:

Keep this shape if upstream prefers it, but document the polymorphic-table tradeoff and make cleanup helper tests cover all delete paths.

### I30. Bulk subtitle API path duplicated single-subtitle formatting and ordering

Status: complete in code. `get_subtitles` and `get_subtitles_map` now share one subtitle payload formatter and sort helper, and the regular movies metadata endpoint now uses the bulk subtitle map.

Evidence:

- `bazarr/app/database.py` had separate dict construction in `get_subtitles` and `get_subtitles_map`.
- `get_subtitles_map` returned rows in database order, while `get_subtitles` sorted by subtitle name and forced flag.
- `bazarr/api/movies/movies.py` still called `postprocess` without preloaded subtitles.

Why it is non-idiomatic:

Duplicated response-shaping code makes the single-row and bulk-row paths easy to drift apart. In this case the bulk path also missed the legacy deterministic ordering.

Suggested direction:

Keep the response payload helper shared between the single and bulk paths, and use the bulk subtitle map anywhere a list endpoint calls `postprocess` per row.

### I31. Wanted-state media id normalization is open-coded

Status: complete in code. Media id normalization now lives in one helper and `delete_wanted_search_state` has direct coverage for scalar ids, string ids, duplicate ids, and cleanup of both normalized tables.

Evidence:

- `bazarr/subtitles/wanted_state.py` normalized ids inline in `get_missing_languages_map`.
- `delete_wanted_search_state` had its own scalar/list handling and integer coercion.

Why it is non-idiomatic:

Both helpers deal with the same public media-id input shape. Keeping normalization inline makes it easier for scalar ids, string ids, and duplicate ids to behave differently across helpers.

Suggested direction:

Use one small normalization helper and cover the cleanup helper directly because normalized tables intentionally rely on application-managed cleanup.

## Coverage Checklist

Every file in `git diff --name-only mjc/wanted-search-integration..HEAD` was reviewed. Findings listed below are the primary audit notes for that file; "covered by broad finding" means no separate file-specific issue beyond the referenced pattern.

- `bazarr/api/badges/badges.py`: reviewed; covered by I19-style API bulk/read-shape concerns.
- `bazarr/api/episodes/episodes.py`: reviewed; I19.
- `bazarr/api/episodes/wanted.py`: reviewed; I19.
- `bazarr/api/movies/movies.py`: reviewed; I19, I30.
- `bazarr/api/movies/wanted.py`: reviewed; I19.
- `bazarr/api/series/series.py`: reviewed; normalized count query looked idiomatic enough; no separate finding.
- `bazarr/api/utils.py`: reviewed; I04 context, I19 context.
- `bazarr/app/config.py`: reviewed; I01.
- `bazarr/app/database.py`: reviewed; I01, I29, I30.
- `bazarr/radarr/sync/movies.py`: reviewed; delete cleanup and due lookup are branch-relevant; no separate idiom finding beyond normalized-state coupling.
- `bazarr/sonarr/sync/episodes.py`: reviewed; delete cleanup and due lookup are branch-relevant; no separate idiom finding beyond normalized-state coupling.
- `bazarr/sonarr/sync/series.py`: reviewed; normalized cleanup is straightforward; no separate finding.
- `bazarr/subtitles/adaptive_searching.py`: reviewed; I02, I03 context.
- `bazarr/subtitles/download.py`: reviewed; I20.
- `bazarr/subtitles/indexer/movies.py`: reviewed; normalized refresh integration is straightforward; no separate finding.
- `bazarr/subtitles/indexer/series.py`: reviewed; normalized refresh integration is straightforward; no separate finding.
- `bazarr/subtitles/language_utils.py`: reviewed; I03, I04.
- `bazarr/subtitles/manual.py`: reviewed; I26.
- `bazarr/subtitles/mass_download/movies.py`: reviewed; I21.
- `bazarr/subtitles/mass_download/series.py`: reviewed; I21.
- `bazarr/subtitles/serialization.py`: reviewed; I01, I03.
- `bazarr/subtitles/upgrade.py`: reviewed; I26.
- `bazarr/subtitles/utils.py`: reviewed; I26.
- `bazarr/subtitles/wanted/movies.py`: reviewed; I08, I14, I15, I16, I17, I21 context.
- `bazarr/subtitles/wanted/series.py`: reviewed; I08, I14, I15, I16, I17, I21 context.
- `bazarr/subtitles/wanted/utils.py`: reviewed; wrapper is small; no separate finding beyond I03.
- `bazarr/subtitles/wanted_state.py`: reviewed; I02, I18, I29 context, I31.
- `migrations/versions/e6cbb0f6f9b1_.py`: reviewed; I01, I05, I06, I07.
- `tests/bazarr/test_manual_paths.py`: reviewed; I22.
- `tests/bazarr/test_mass_download_paths.py`: reviewed; mass-download fixtures/assertions covered by I21 and fixture concerns.
- `tests/bazarr/test_upgrade_paths.py`: reviewed; upgrade helper tests covered by I26.
- `tests/bazarr/test_wanted_search_language_unit.py`: reviewed; I03, I23.
- `tests/bazarr/test_wanted_search_paths.py`: reviewed; I23, I24, I25.
- `tests/bazarr/test_wanted_search_scheduler.py`: reviewed; scheduler tests are small; covered by fixture concerns.
- `tests/bazarr/test_wanted_search_wrappers.py`: reviewed; I23 and fixture concerns.
- `tests/bazarr/wanted_search_fixtures.py`: reviewed; I09, I10, I11, I12, I13, I27, I28.
