# S8 decision: compact in place, retain the full packages

Status: implemented candidates for maintainer review; no merge, tag, release, or publication.
Date: 2026-10-10. Parent: [UTF8 #103](https://github.com/voku/portable-utf8/issues/103).

## Decision and scope

Keep all mapping functionality and existing Composer requirements in `portable-ascii` and
`portable-utf8`. Store dense ASCII banks as delimiter-separated PHP strings decoded lazily
per bank; retain the sparse `x1f1.php` unchanged. Generate byte arrays compactly, preserving
all original keys, ordering, and the ordinal maps' extra `'' => 0`. Keep the files at their
original paths. Store emoji as ordered UTF8 name/value rows with the shared `CHARACTER_`
prefix reconstructed on load. No zlib/JSON/compressor dependency is introduced.

An unrelated support query defers loading transliterator metadata. Debug support output also materializes deferred data while preserving
its existing echo and reference/cache semantics. The historical slot in
the support array is reserved; requesting the complete result or the list materializes the
same array at the same key position. A complete query before any keyed query keeps its old
shape. This saves cold loading, **not installed bytes**; the loader code itself is slightly
larger. Locale operations still have their own existing lazy metadata initialization.

S4 is NO-GO for replacing the non-strict table engine with ICU. S8 is NO-GO for mandatory
mapping packages. An optional slim distribution would change the API/support contract and
is outside this full-package compatibility work. No extension-conditional dependency,
Composer plugin, synthetic production requirement, or new remote repository was added.

## Immutable inputs and candidate revisions

| Library | master baseline | published stable | measured runtime candidate |
| --- | --- | --- | --- |
| ASCII | `180a8d12055eb350859b628c64066a90a895bd10` | 2.1.1, `8e1051fe39379367aecf014f41744ce7539a856f` | `5133a66` (full SHA in Composer evidence) |
| UTF8 | `28cb685c22cd829aba819406295c0763204c5c09` | 6.1.1, `837e32cd4b166320cc3e70e3ffe1ba413e81ee46` | `796f909` (full SHA in Composer evidence) |

Evidence/documentation commits follow these runtime candidates. Their build/test files are
excluded from Dist; Source installs of a later evidence revision can include additional
review material. Exact refs and package versions are recorded in `composer-measurements.json`
and the pinned consumer locks. All third-party package versions/references are held constant
across each before/after comparison. The 2.1.99/6.1.99 consumer aliases are not published versions.

## Actual Composer footprints

Logical bytes include every file in the production vendor tree. Allocated bytes use
`st_blocks * 512` on this filesystem. Source installs include tests and Git metadata;
they are not used as a substitute for Dist measurements. File count does not count directories.

| Consumer / method | Before logical | After logical | Delta | Before allocated | After allocated | Files before → after |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ASCII / Dist | 601,631 | 455,690 | −145,941 (−24.26%) | 1,077,248 | 1,077,248 | 214 → 214 |
| UTF8 full closure / Dist | 3,535,169 | 3,299,640 | −235,529 (−6.66%) | 4,186,112 | 4,100,096 | 330 → 330 |
| ASCII / Source | 2,475,320 | 2,364,289 | −111,031 (−4.49%) | 3,964,928 | 4,009,984 | 503 → 508 |
| UTF8 full closure / Source | 31,348,412 | 31,157,515 | −190,897 (−0.61%) | 34,078,720 | 34,058,240 | 977 → 987 |

The allocated ASCII footprint does **not** improve: many per-bank files already consume one
filesystem block. The full UTF8 Dist closure saves 86,016 allocated bytes (2.05%). Source file
counts/allocated size can rise because characterization tests and Git history are retained.
Do not advertise those as physical source-checkout savings.

ASCII package ZIP: 166,582 → 162,770 bytes (−3,812).
UTF8 package ZIP: 167,787 → 164,362 bytes (−3,425).
These are local deterministic Git-export ZIP measurements, not observed CDN transfer sizes.
ZIP compression already removes much of the PHP textual redundancy; logical installed-byte
savings are larger than ZIP/download savings.

The selection criteria are exact compatibility, measurable full-closure savings, retained
PHP floor, no extra required package, and honest cold/warm measurements. No retrospective
numeric threshold is used to turn a failed experiment into a pass. Maintainers can assess
the significance using all four size dimensions and the runtime trade-offs.

## Alternatives measured

| Option | Evidence | Decision |
| --- | --- | --- |
| In-place representation | Full UTF8 Dist closure saves 235,529 logical / 86,016 allocated bytes; exact mappings and all 8 extension profiles match | Selected candidate |
| Replace banks with native ICU | ICU 76.1: 48,248 keys in 189 banks, 37,654 raw-ICU/table mismatches and 29,370 strict/table mismatches; 51 language maps also examined | NO-GO; retain strict/native and non-strict/table policies |
| Mandatory ASCII + emoji mapping packages | Actual Composer Dist prototype: 3,299,640 → 3,301,201 logical bytes, 4,100,096 → 4,116,480 allocated bytes, 330 → 332 files | NO-GO; moves 315,421 mapping bytes and adds overhead |
| Optional slim/core alternative | Would remove existing guaranteed full-package functionality; not a compatible install mode for the current API | Not selected; needs separate support contract and project approval |

The split prototype installs required children and verifies consumer transliteration/emoji
calls; its copied data is unchanged. It is rejected on footprint before any publication or
claim of exhaustive split compatibility. Temporary manifests and rewritten loader paths are
confined to the prototype archives. Current Composer cannot conditionally `require` by intl.
Missing extensions still require complete table/emoji functionality.

## Compatibility and runtime evidence

All 193 ASCII data files and all 8 UTF8 files match their baseline serialized-array SHA256,
including key types, order, empty values, sparse keys, and unknown markers. Generators have a
non-mutating check mode and are idempotent after generation. Public reflection signatures
also match the published stable releases; no public method was added, removed or changed.

On PHP 8.4.26, all 8 combinations of native intl/mbstring/iconv were tested against the same
polyfills. Each profile compares 11,500 ASCII and 7,437 UTF8 scenarios with zero output,
warning, exception or signature differences. Tests cover byte values, invalid/large codepoints,
encodings, malformed UTF8, all Unicode banks, locale behavior, unknown replacements, emoji
names/concatenations/sentinels, manual validation, and support result ordering. They are
behavioral comparisons, not another general public-API smoke test with swallowed warnings.

Native suites: final ASCII 336 tests / 3,370 assertions (two opt-in performance skips);
UTF8 2,004 tests / 429,266 assertions. Four existing
PHPUnit deprecations and the legacy UTF8 XML/coverage-driver warning remain distinct from
failures. No zero-test run is counted as validation.

Runtime medians are in `runtime-matrix.json`: 7 fresh processes, 5 warm rounds per process,
identical output hashes and captured warnings. Native support-query cold time decreases
from ~124 µs to ~5 µs and avoids retaining ~46,760 bytes. Byte-table decode/repair cold loading
also improves. Emoji retained memory rises by ~49,648 bytes (ordered row parsing creates
non-interned strings), and its native cold median is ~3.83 → ~4.20 ms; its recorded warm
median is ~94 → ~96 µs. This is a footprint trade-off, not a promised emoji CPU improvement.
Per-bank decoding remains lazy and warm public operations use the same memoization.

Existing ASCII performance thresholds are unchanged. An alternating three-run comparison
passes the baseline 3/3 and candidate 1/3: two candidate runs trip the short-Latin ratio
threshold. Those runs include scheduling noise (one candidate's entire short-path measurements
are roughly doubled); the final pair is green and the absolute target latency is close to
baseline. **Do not conceal the intermittent failures or claim a uniformly green performance
gate.** All raw logs are attached. New mapping-load samples show substantial dense-table
parse improvements; the sparse retained bank behaves as before. Maintainer review should
rerun the opt-in profile on a quiet representative runner before release.

PHP 7.1, 7.4 and 8.5 runtimes were unavailable locally. The coordinator CI workflow configures
those versions and native-on/off runs, but has not been executed. It needs the pinned candidate
commits to be available remotely. OPcache CLI was measured; no persistent web-worker OPcache
claim is made. Exact data definitions and production syntax retain PHP 7.1 compatibility.

## S9 release / migration gate (no tag)

No data paths move and included files still return the same arrays. This work therefore does
not require a major release or mapping-file migration. Scope S9 to review of a compatible
patch/minor candidate. If a later separate project moves internal data paths, that project
must explicitly warn direct-file consumers and obtain its own major-release review.

Rollback is a normal revert of the compact representations and support getter; no dependency
migration, generated runtime artifact, external service or data update is required. Do not
change package versions, tags, Packagist publication, existing release PRs or unrelated APIs.

Release is **not approved** by this evidence:

- ASCII PHPStan at configured level 8 passes both current and PHP-7-targeted configs.
- Current UTF8 PHPStan reports 6 errors (`decimal_to_chr`, `string`, four `mb_convert_encoding`
  argument types). The identical six errors occur on untouched master; no suppression or
  unrelated behavior fix was introduced. Treat that as an inherited release-check limitation.
- Both existing `phpcs.php_cs` files require PHP-CS-Fixer's retired `Config::create()` API.
  Current fixer 3 cannot directly run them. A temporary v3 rule-name adapter confirms the new
  UTF8 tests' formatting; full-source adapted checks show inherited formatting drift and do
  not establish the old formatter gate as green. The legacy style toolchain needs review.
- The native full suites, Composer validation, all 8 extension-profile differential checks,
  generators, production Dist/Source install smokes and published-stable signature comparison
  pass. Full suites on other PHP runtimes and remote CI remain unrun, explicitly.
- U+FFA0 already differs between ASCII 2.1.1 and master: non-strict `to_transliterate` returns
  a space on stable and empty string on master. The candidate retains master's behavior;
  `to_ascii`, `clean`, and slug results also retain master. See `uffa0.json`. This work does
  not fix, shadow or certify the separate [PR #164](https://github.com/voku/portable-ascii/pull/164)
  / [#166](https://github.com/voku/portable-ascii/issues/166) release contract.
- [ASCII #162](https://github.com/voku/portable-ascii/issues/162) and
  [PR #167](https://github.com/voku/portable-ascii/pull/167) remain separate TransliteratorPolyfill
  work. No extraction/API/requirement from that PR is included here.

Maintainers can review the measured candidates and all evidence. No release tag, GitHub
release, package publication or automatic merge has been performed.
