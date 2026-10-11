# Registered-provider experiment

The owner registered both packages on Packagist. The coordinator's `--packagist-data`
experiment resolves their reviewed `dev-main` commits through that registry, without VCS,
path or fixture-package overrides for either data package. The core and polyfill closure
remain pinned fixtures for the matrix; the examples additionally use ordinary GitHub VCS
resolution for the real core branches.

`example-full` and `example-slim` retain the public manifests and actual resolved lockfiles.
`example-path-results.json` records 20 fresh-process calls for each example, compared with
the matrix consumers under the same PHP configuration. Both installs and all 40 comparisons
passed locally on PHP 8.4.26. The installed full data packages use Packagist's GitHub Dist
URLs and exact reviewed source references; the slim consumer contains neither package.

Remote matrix results and the CI summary are retained alongside this file. Complete
application manifests, lockfiles, registry metadata, clean-reinstall checks and solver logs
are available in the matching `packagist-providers-php-*` CI artifacts.

The older scratch spike had a duplicate core alias inherited from its inventory. That alias
could bypass the rewritten provider requirement; its version-guard failure was then caused
by an inaccessible stale archive URL. The corrected spike removes duplicate core entries,
checks future-version rejection before installation, and requires the solver's diagnostic
to name the intended future emoji contract. This supersedes the old spike's version-guard
claim. Real repository/Packagist modes already replaced all duplicate core metadata.

No release tags, releases, core merges or stable package versions were created. Development
aliases are application test allowances, not stable releases. Full splitting adds overhead;
only deliberately restricted consumers save space. Existing static-analysis, formatter and
performance release gates described in PROVIDER-INTEGRATION.md remain separate.
