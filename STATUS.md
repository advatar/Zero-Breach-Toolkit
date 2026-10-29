# Runtime safety review

- [x] Inspect scan entry points, network access, external commands, evidence reads,
  report writes, temporary storage, and dependency pins.
- [x] Make pre-scan temporary-folder inspection non-destructive and add regression
  coverage for unrelated folders, long-running scans, and source/bundle parity.
- [x] Check pinned dependency versions against published vulnerability records;
  isolate legacy pytest temporary storage in CI.
- [x] Run the unit suite, offline release gate, and reproducible build checks.
- [x] Document the result and remaining limits and prepare validated changes for
  integration into main.

Validation uses synthetic evidence in isolated temporary storage; no personal
device scan or phone acquisition is part of this review. Creating a generic
review-tracking GitHub issue was attempted, but this repository has issues disabled.

## Verification — 2026-10-29

Validated on macOS Apple silicon with Python 3.12.13 and hash-verified test,
encrypted-backup, and YARA-X dependencies in a dedicated virtual environment.

- Unit suite: **1,928 passed, 47 skipped, 1,027 subtests passed**.
- New and related housekeeping regression tests: **29 passed**, including the
  source package and generated single-file build.
- `tools/release_check.py --require-backups --require-patterns`: passed all
  source/bundle fixture comparisons. The audit hooks detected no network or
  subprocess activity during fixture scans; fixture inputs remained unchanged
  and each scan removed its own temporary snapshots.
- `build/build.py --check`: passed; generated indicator artifacts match source.
  Two independent single-file builds were byte-identical. Scanner SHA-256:
  `ac9216a55afbb530bb61e9b9f4d42f3d4667493591da4a63bb8563b6961cbc01`.
- Updated CI workflow YAML parsed successfully. Legacy test jobs now use a fresh
  private temporary parent instead of pytest's shared predictable location.

## Dependency assessment

All 26 distinct pinned package/version pairs in the five requirements files were
queried against the [OSV API](https://google.github.io/osv.dev/post-v1-querybatch/).
Two legacy pins have published advisories; the other pairs returned none at the
time of review. Absence of an advisory is not proof of safety.

- `pytest==8.3.5` is retained for Python 3.8/3.9 test jobs. Its temporary-directory
  issue was fixed in [pytest 9.0.3](https://github.com/pytest-dev/pytest/releases/tag/9.0.3),
  which requires a newer Python. CI now isolates its temporary storage, as the
  local release gate already does. Pytest is not a scanner runtime dependency.
- Intel macOS backup support retains `cryptography==48.0.1`, the last release
  with official Intel Mac wheels. The advisories concern
  [PKCS#7 decryption](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5),
  [certificate path building](https://github.com/pyca/cryptography/security/advisories/GHSA-jwv3-5hgf-82ww),
  and [certificate name constraints](https://github.com/pyca/cryptography/security/advisories/GHSA-m2h6-j472-rp4c).
  Source inspection found only AES-CBC and AES key-unwrapping calls in backup
  decryption; these affected APIs are not used. This is a reachability assessment,
  not a claim that the old library is free of vulnerabilities. Other supported
  platforms pin 50.0.2. Install optional dependencies in a dedicated environment.

## Scope and remaining limits

The review found no remaining blocker for an ordinary local scan from the updated
source, without administrator privileges. It does not certify arbitrary downloaded
executables, an already compromised operating system, or every possible input.
Windows/Linux native behavior and platform-specific skipped tests were not exercised
on this Mac. The separate website source was unavailable, so its check was skipped.
No published release or native executable was replaced by this change.

The Python network guard is not an OS network sandbox: network-mounted filesystems,
native libraries, and concurrent path changes remain outside its guarantees. Use
OS network isolation for strict offline requirements. Indicator updates and Android
acquisition are explicit online operations; acquisition also changes phone state.
Full reports and temporary database copies contain private information. Reports
remain unencrypted, and interrupted scans may leave copies for manual review.
