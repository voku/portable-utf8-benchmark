# S8 follow-up: full by default, explicit slim consumers

Historical spike evidence. The [real provider integration](PROVIDER-INTEGRATION.md) now
implements this model on separate development branches with successful remote CI.
No new remote repositories, production requirements, versions, tags or releases were created.
The in-place compression stays intact. The mandatory split's full-install overhead remains a
valid result; its earlier NO-GO did not measure an application choosing to omit functionality.

## Experiment and contracts

`opt-out-spike.py` builds deterministic, checksum-protected local Dist archives. It moves the
already compressed emoji and ASCII banks into illustrative data packages at version `1.0.0`,
and rewrites loaders only inside the scratch core archives:

- `voku/portable-utf8-emoji-data`: PSR-4 `Voku\PortableUtf8EmojiData\EmojiMap::load(): array`.
- `voku/portable-ascii-mapping-data`: PSR-4 `Voku\PortableAsciiMappingData\BankMap::load(string $bank): array`.

The providers return exact original arrays; an absent bank in an installed provider still
returns `[]`, preserving the existing unknown-codepoint behavior. An absent provider throws
`RuntimeException` before any include, naming the missing package and instructing the caller
to install it and remove its root replacement declaration. Bootstrap and unrelated operations
do not autoload either provider. No installer hook, Composer plugin or runtime download is used.

Full installation requires both data packages. The tested slim root declares, for example:

```json
{
  "replace": {
    "voku/portable-utf8-emoji-data": "1.0.0"
  }
}
```

These are unpublished experimental names. The 2.1.99/6.1.99 core aliases are local consumer
fixtures, not proposed release versions. `replace` ordinarily claims equivalent functionality;
here it is an intentional application-controlled suppression with reduced guarantees. Keep
an exact reviewed replacement version and a committed application lockfile. Tests show that
`1.0.0` cannot satisfy a new `1.1.0` data requirement, while an unsafe `"*"` can silently do so.
That wildcard case is a negative control, not a recommendation.

## Measured installed footprints

All values cover the full production UTF8 vendor closure, including Composer metadata and
polyfills. Eight real installs (four initial resolves, four clean lock reinstalls) passed.
Every vendor file's content hash, package metadata and footprint matches its lock reinstall;
all extracted installed mappings are byte-identical to the input archives.

| Mode | Logical bytes | Allocated bytes | Files | Logical saving vs compressed in-place | Allocated saving vs compressed in-place |
| --- | ---: | ---: | ---: | ---: | ---: |
| Compressed in-place baseline | 3,299,679 | 4,100,096 | 330 | — | — |
| Full split | 3,303,940 | 4,124,672 | 334 | −4,261 | −24,576 |
| Omit emoji | 3,212,106 | 4,022,272 | 331 | 87,573 | 77,824 |
| Omit ASCII banks | 3,076,738 | 3,338,240 | 143 | 222,941 | 761,856 |
| Omit both | 2,984,861 | 3,235,840 | 140 | 314,818 (9.54%) | 864,256 (21.08%) |

Allocated bytes are filesystem-specific `st_blocks * 512`. Local archive URLs embedded in
Composer metadata affect logical counts by a few bytes when a different output path is used.
Full split adds overhead; optional removal provides real savings, especially physical bank
blocks. This is evidence for reviewing the optional model, not an unconditional CPU or
maintenance-cost improvement.

## Behavior and extension matrix

On PHP 8.4.26, every actual intl/mbstring/iconv combination compares full installation against
the compressed in-place baseline: 11,500 ASCII and 7,437 UTF8 cases per profile, with identical
public signatures, outputs, warnings, exceptions and buffered echo. An independent original
mapping corpus supplies test inputs; no missing data is restored to the extracted core.

Additionally, 20 fresh-process path probes × four modes × eight profiles verify supported
paths, missing-provider exceptions and deferred loading. Important indirect callers:

| Path | Omitted data behavior |
| --- | --- |
| UTF8 `emoji_encode`, `emoji_decode`, nonempty `strrev`, nonempty `is_html` | Require emoji data, even plain ASCII `strrev('hello')` and `is_html('<b>hello</b>') |
| UTF8 `is_html('')` | Early return works without emoji |
| ASCII non-strict `to_transliterate`, UTF8 `to_ascii`, ASCII `to_filename` | Non-ASCII bank-dependent input throws without bank provider |
| UTF8 `to_filename` | Default `use_transliterate=false` works; explicit `true` with bank-dependent input throws |
| Strict ASCII transliteration | Tested input works without banks when native intl is present; without intl the fallback requires banks |
| ASCII passthrough, retained language-only mapping, UTF8 length/repair/ord, support queries | Tested paths work without either extracted family and do not load providers |

This table describes tested paths, inputs and options, not a universal whitelist for every
method, locale or caller. Native intl does not substitute for the non-strict bank contract.
Transliterator metadata, byte tables and language tables remain in core; this spike establishes
no opt-out contract for those families. Applications must audit their entire call graph and
test their real workloads before claiming data is unused.

Thirty-two Composer solver checks use explicit `config.platform` absence overrides, without
`--ignore-platform-reqs`. The pinned existing polyfill-mbstring 1.43 requires ext-iconv, so all
four modes resolve when iconv is available and all four reject its absence. Runtime fallback
comparisons still pass in all eight profiles. **Runtime fallback behavior does not prove that
this particular locked dependency closure installs on an iconv-free application.** That
inherited platform requirement needs a separate dependency-support decision. Actual installs
and lock reinstalls run under the native extension profile.

## Reproduce

First run the existing `measure.py` in a fresh output directory to obtain the compressed
consumers and archives. It needs both checked-out library histories and a resolved UTF8
production lock; CI supplies the committed evidence lock as its pinned package inventory.
Then use the actual PHP binary (a wrapper that forces a php.ini would invalidate `-n`):

```sh
python3 tools/footprint/opt-out-spike.py \
  --consumers /tmp/mapping-consumers \
  --output /tmp/mapping-opt-out \
  --php "$(command -v php)" \
  --extension-dir "$(php -r 'echo ini_get("extension_dir");')"
```

The native Composer command must be available, and the three shared PHP modules must be
loadable from that directory. Output must be empty. `results.json`, four manifests/locks,
resolve/reinstall logs and all solver manifests/logs/available locks are retained under
[`evidence/opt-out`](evidence/opt-out). Full input refs and archive hashes are recorded there.
Local matrix verification ran successfully. The added GitHub Actions job has not run.
PHP 7.1/7.4/8.5 provider compatibility remains a gate, distinct from the existing core matrix.

## Next steps and publication gate

1. Push the two existing library candidate branches, then the benchmark evidence branch.
   Its workflow pins the library commits, so those commits must be remotely accessible first.
   A push to `mapping-footprint/evidence` or a PR starts the prepared workflow, including the
   opt-out integration job. Review actual results; local evidence is not remote CI success.
2. Review the provider contract, names, data versioning/compatibility policy, licenses,
   generator ownership and an application migration/opt-out guide. Check direct-file
   consumers, broader indirect paths and older PHP versions. Treat changed data paths and
   reduced guarantees as a separate release/design review from the in-place candidate.
3. If that review accepts extraction, create the data repositories with retained provenance,
   licenses, deterministic generation and independent provider tests. Integrate dev revisions
   through explicit Composer repositories and pinned commits before publication.
4. Register Packagist only once package manifests and repository ownership are settled and
   the chosen release plan is approved. Registration alone does not require tagging, but it
   is unnecessary for this spike and should not prematurely reserve experimental contracts.

Recommendation: proceed to CI and design review of the optional model. Do not publish data
packages merely because Composer accepts `replace`; full-default parity and reduced-mode
support obligations must be maintained independently. No production extraction or release
has been approved or performed by this experiment.
