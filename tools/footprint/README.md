# Mapping footprint and compatibility evidence (S0–S9)

This harness coordinates [UTF8 #103](https://github.com/voku/portable-utf8/issues/103),
[UTF8 #270–275](https://github.com/voku/portable-utf8/issues/270) and
[ASCII #168–171](https://github.com/voku/portable-ascii/issues/168).
It never changes production dependency declarations, tags releases, or publishes packages.
The production changes are in the existing ASCII and UTF8 repositories.

## Reproduce

Use existing checkouts; do not create a worktree. PHP 7.1 remains the runtime floor.
`python3`, Git, Composer 2, and a working PHP CLI are needed. Resolve library development
or isolated consumer dependencies for the PHP version actually under test.
The checked-in evidence was obtained on PHP 8.4.26, ICU 76.1, Linux, Composer 2.8.8.

From the parent directory containing all three repositories:

```sh
export PATH=/workspace/.onboarding/bin:$PATH  # Cloud instance's retained local PHP/Composer
mkdir -p /tmp/mapping-baselines/portable-ascii-baseline /tmp/mapping-baselines/portable-utf8-baseline
git -C portable-ascii archive 180a8d12055eb350859b628c64066a90a895bd10 | tar -x -C /tmp/mapping-baselines/portable-ascii-baseline
git -C portable-utf8 archive 28cb685c22cd829aba819406295c0763204c5c09 | tar -x -C /tmp/mapping-baselines/portable-utf8-baseline
python3 portable-utf8-benchmark/tools/footprint/verify.py --workspace "$PWD" --baselines /tmp/mapping-baselines --output /tmp/mapping-contract
python3 portable-utf8-benchmark/tools/footprint/measure.py --workspace "$PWD" --output /tmp/mapping-consumers
python3 portable-utf8-benchmark/tools/footprint/split-prototype.py --consumers /tmp/mapping-consumers --output /tmp/mapping-split
php portable-ascii/build/footprint/icu-parity.php > /tmp/icu-parity.json
php portable-ascii/build/footprint/compact.php
php portable-utf8/build/footprint/compact.php
```

Choose **fresh output directories** for installation experiments. `measure.py` deliberately
rejects an existing consumer vendor tree instead of silently reusing Dist for a Source run.
It uses the checkout's production Composer lock for dependency versions and references;
no dev dependencies are installed in consumers. Local ZIPs are `git archive` exports, which
respect the repositories' existing export-ignore rules. Codeload URLs address the original
locked Git commits; TLS, artifact hashes, and verification are not disabled. Local temporary
`2.1.99`/`6.1.99` aliases satisfy the existing `~2.1.0` dependency, and are **not release numbers**.

`evidence/locks/` contains all four pinned consumer manifests/locks from the measured run.
Their file URLs refer to the measured local archives; generate those with `measure.py` at the
recorded output path or regenerate the harness at a new path. Do not publish these manifests.
Source URLs reference actual checkout commits. Source measurements include `.git` and tests.
The complete vendor closure is measured, not just mapping files.

`verify.py` compares before/after roots in separate PHP processes in the active extension
profile. `contract.php` captures outputs, warning levels/messages and exception types/messages;
it normalizes only the caller's path/line in exception text. It checks every byte, Unicode and
invalid-input edges, all banks, encoding/repair, locales, emoji concatenations and sentinel
collisions, support result ordering, and public reflection signatures. It also exercises the
manual UTF8 validator normally bypassed by PCRE. All output data is serialized/base64 to
preserve binary strings and PHP types. Failures produce a nonzero exit; warnings are evidence,
not a success heuristic. It does not suppress warnings without recording them.

## Cold/warm runtime

Use `runtime.php ROOT ASCII|UTF8 AUTOLOAD SCENARIO` in a fresh PHP process for each cold sample.
Scenarios are `ascii`, `chr`, `ord`, `repair`, `emoji`, `support`, and `locale`.
Collect seven fresh-process samples per variant; report medians of cold microseconds,
five-round warm medians (1,000 calls/round, 100 for emoji), retained and peak bytes, and output
hashes. Run baseline and candidate on the same PHP/extension profile. Every call's recorded
warnings and output checksum must match. No process-start or class-autoload time is included
in the cold-call timer. OPcache CLI was also exercised; independent CLI processes do not
share a persistent warmed OPcache, so these are not web-server OPcache-throughput claims.

ASCII warm/representation metrics reuse the existing test infrastructure:

```sh
cd portable-ascii
PORTABLE_ASCII_RUN_PERFORMANCE_TESTS=1 php vendor/bin/phpunit --filter PerformanceRegressionTest
PORTABLE_ASCII_RUN_PERFORMANCE_TESTS=1 PORTABLE_ASCII_MAPPING_ROOT=/tmp/mapping-baselines/portable-ascii-baseline/src/voku/helper/data php vendor/bin/phpunit --filter testMappingDecodeProfile
```

For a baseline of the existing public performance scenarios, invoke the test runner with
`-d auto_prepend_file=/tmp/mapping-baselines/portable-ascii-baseline/src/voku/helper/ASCII.php`.
No working source file needs temporary restoration. The unchanged ratio thresholds can be
sensitive to scheduling for sub-microsecond paths: see the raw alternating-run logs and ADR.

## Extension/PHP coverage

All eight intl/mbstring/iconv on/off combinations were compared on PHP 8.4.26 using its real
shared modules and the same Composer polyfills: 11,500 ASCII and 7,437 UTF8 cases per profile,
zero output/diagnostic/signature differences. Full native suites also passed. The PHP 7.1,
7.4 and 8.5 runtime jobs are configured in `mapping-contract.yml`, **not run locally**.
Those jobs resolve production polyfills against their actual PHP version (the 8.4 lock's
newest polyfills need not support 7.1). Candidate refs must be pushed before GitHub can fetch
them. Workflow preparation does not constitute a successful remote CI run.

The matrix JSONs list every mapping file and direct/transitive public consumers. Transitive
consumer lists come from conservative static call tracing, not per-method execution coverage.
The legacy `ascii_language_max_key.php` has no current runtime consumer and is retained.
No native replacement is proven: strict ICU and non-strict banks have distinct policies,
emoji is required independently of extensions, and byte tables have an extra empty-string
entry / array warning contract that raw primitive substitution would erase.

See [ADR.md](ADR.md) for the measured architecture decision and release review.
