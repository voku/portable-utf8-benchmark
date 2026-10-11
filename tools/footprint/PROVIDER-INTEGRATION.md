# Real data repositories and development integration

The explicit opt-out architecture is implemented on separate development branches. The earlier
in-place candidates remain available. No library default branch was merged, no version was
released, and no tags or Packagist registrations were created.

## Repositories and immutable inputs

| Repository | Branch | Verified commit |
| --- | --- | --- |
| [ASCII data](https://github.com/voku/portable-ascii-mapping-data) | main | `3a5ae61` |
| [Emoji data](https://github.com/voku/portable-utf8-emoji-data) | main | `74c440f` |
| [ASCII core integration](https://github.com/voku/portable-ascii/tree/mapping-footprint/providers) | mapping-footprint/providers | `e6eaa3c` |
| [UTF8 core integration](https://github.com/voku/portable-utf8/tree/mapping-footprint/providers) | mapping-footprint/providers | `819c7eb` |

Complete SHAs are recorded in the examples, lockfiles and CI evidence. The data repositories
retain original licenses, attribution, exact ordered-array/hash fixtures, provenance and
reproducible imports. Build/tests/CI are excluded from their Dist archives. Providers are
PSR-4 autoloaded and load data only when called; no plugin or runtime download is involved.

The core candidates require their data providers at `^1.0`. Full default behavior matches
the in-place baseline. A missing provider throws an actionable RuntimeException. Unknown
valid banks retain the old empty-array behavior, whereas damaged known files and malformed
provider bank identifiers fail explicitly. Data and policy versioning are independent;
raise the core's minimum data version whenever new behavior actually requires newer data.

Byte/language/support metadata stays in core. This does not introduce an extension-driven
Composer switch or treat intl as a replacement for the non-strict ASCII engine. Internal
mapping files move in this candidate; direct-file consumers need migration. Each core branch
ships `MAPPING-MIGRATION.md`. This requires separate release/migration review rather than
silently replacing the compatible in-place candidate with a patch release.

## Actual remote CI

- [ASCII provider CI](https://github.com/voku/portable-ascii-mapping-data/actions/runs/38099326156): successful PHP 7.1, 7.4, 8.4 and 8.5 provider contracts and exported-archive checks.
- [Emoji provider CI](https://github.com/voku/portable-utf8-emoji-data/actions/runs/38099350133): successful on the same four PHP versions.
- [Coordinator CI](https://github.com/voku/portable-utf8-benchmark/actions/runs/38099868434): all 13 jobs successful, benchmark runtime commit `2ba7d31`.

Four real-provider jobs each test all eight native intl/mbstring/iconv combinations. Each
profile compares 11,500 ASCII and 7,437 UTF8 scenarios with no signature, result, warning,
exception or echo differences. Additionally, 20 fresh-process path probes × four install
modes × eight profiles verify retained paths, lazy loading and missing-data failures per
PHP version. These are comparisons against the unchanged in-place revision under the same
PHP/polyfill profile, not claims that every behavior matches a published older release.

Full, no-emoji, no-banks and both-omitted consumers resolve pinned locks and pass two clean
Dist reinstalls with equal package metadata, footprint and every vendor file's content hash.
Composer 2.2 normally randomizes a fresh autoloader's class suffix; test consumers explicitly
set a manifest-derived `config.autoloader-suffix` so byte-level reproducibility is meaningful
on that Composer version too. No files are excluded from the vendor-content comparison.
The PHP 7 fallback harness loads its JSON serializer while keeping the three tested text
extensions absent. The probe avoids deprecated reflection setup on newer PHP versions.

The test registry's 2.1.99/6.1.99/1.0.0 aliases are local test versions, not published releases.
Separate normal VCS consumers also resolve the real branches with SHA-pinned development
aliases and validate both full and both-omitted paths. They use local Git URLs to avoid
registry/API variability; the public examples use the corresponding GitHub repository URLs.
The local library development helpers installed the data providers from their actual GitHub
VCS repositories without Packagist or tags.

Evidence is retained under [evidence/providers](evidence/providers): remote job summaries,
all four PHP matrix results, application manifests/locks, reinstall reports/logs and local
full-suite/static-analysis/performance logs. Complete solver logs remain in the linked CI
artifacts. Expected missing-iconv solver rejections are recorded independently of successful
runtime fallback checks; those dependency platform requirements are inherited.

## Footprint of the licensed real packages

The minimal spike omitted the eventual repositories' provenance, licensing and migration
material. The real full split therefore adds more overhead. Use these measured values rather
than promoting the spike's earlier savings as the final package result.

PHP 8.4 remote Dist results, covering the full production UTF8 vendor closure:

| Installation | Logical bytes | Allocated bytes | Files | Logical saving vs in-place | Allocated saving vs in-place |
| --- | ---: | ---: | ---: | ---: | ---: |
| In-place baseline | 3,300,497 | 4,100,096 | 330 | — | — |
| Full split | 3,353,074 | 4,198,400 | 345 | −52,577 | −98,304 |
| Omit emoji | 3,227,722 | 4,046,848 | 337 | 72,775 | 53,248 |
| Omit banks | 3,118,338 | 3,391,488 | 150 | 182,159 | 708,608 |
| Omit both | 2,992,944 | 3,248,128 | 142 | 307,553 | 851,968 |

Allocated bytes depend on the filesystem. Composer version, installation URLs and inventory
metadata can change logical counts slightly. Original mappings remain identical. Full-default
installation is larger; the optional footprint saving is real and conditional on consumers
accepting reduced functionality. No uniform CPU improvement is claimed for extraction.

## Try the development branches without tags or Packagist

Use [examples/providers-full.composer.json](examples/providers-full.composer.json) for full
functionality or [examples/providers-slim.composer.json](examples/providers-slim.composer.json)
for the deliberately restricted application. Copy the selected file to a new application's
`composer.json`, run `composer update --no-dev`, then commit its generated lockfile. The
examples pin the four reviewed commits with explicit development aliases and VCS repositories.
Composer reads branch metadata, so retain the reviewed manifests and lock in addition to
commit pins. Aliases do not turn a development branch into a stable published version.

For a selective opt-out, omit that provider from the application's explicit require list and
add a version-pinned root replacement declaration. Never use `"*"`. Audit indirect calls:
nonempty `strrev` and `is_html` reach emoji even for ASCII text; UTF8 `to_ascii` and filenames
with transliteration can need ASCII banks. Existing [opt-out path evidence](OPT-OUT.md)
remains applicable. The table describes tested paths/options, not a universal application
whitelist. Full and incorrectly reduced installs must be tested separately.

## Remaining publication and release gates

Packagist returned 404 for both names when checked. This environment has no Packagist account
credentials or authenticated publishing connector. The account owner must submit the two
existing repository URLs through [Packagist's submit form](https://packagist.org/packages/submit).
Registration can index development branches without creating release tags. It does not make
`^1.0` satisfiable for ordinary stable consumers until an approved stable data version exists;
the VCS/development examples remain the current integration route.

The local core suites pass: ASCII 336 tests / 3,370 assertions (two opt-in skips, four existing
PHPUnit deprecations); UTF8 2,004 tests / 429,268 assertions. ASCII PHPStan passes both configs.
UTF8 PHPStan still reports the same six inherited errors. The opt-in ASCII performance ratio
fails once at 1.2619 versus a 1.25 threshold; it remains an explicit gate, with thresholds
unchanged and its raw log retained. The legacy formatter limitation in the original ADR also
remains. These issues are not represented as a green full release gate by successful
compatibility/integration CI. No core versions, release tags, releases or merges were made.
