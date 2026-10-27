# Paper A — repository reproducibility audit (2026-10-27)

## Scope
Static review of the five uploaded `run.py` scripts and their five JSON reports on `main`. No source data was redistributed, and no independent execution was performed.

## Verified from published files
- Five experiment/consolidation modules are present with their respective JSON reports.
- The common-protocol report identifies six forecasting streams and SHA-256 digests of three local inputs.
- The unseen-station report documents deterministic station-disjoint 70/15/15 train/calibration/test cohorts and source-specific evaluation.
- The targeted-diagnostic report records zero difference between reconstructed and frozen MAE for six streams; this is reported internal reconciliation, not independent replication.
- The five-state consolidation script and report explicitly warn that historical four-state and Maharashtra experimental implementations differ and are not protocol-harmonized.
- The Maharashtra completion report labels its results `COMPUTED_PROVISIONAL`.

## Open checks before release certification
1. Confirm exact input hashes locally against the files referenced by each script; do not upload the inputs.
2. Check runtime dependencies, path portability, execution order, and regenerated-output checksums.
3. Document the distinction between historical consolidation and the later harmonized common-protocol results.
4. Confirm no personally identifying or restricted information is present in the JSON reports.
5. Obtain investigator approval for a tagged experimental release.

## Exclusions
No manuscript, article figure, map, original dataset, processed dataset, or third-party material should be added.

**Status: SOURCE_REVIEW_COMPLETE / REPRODUCTION_NOT_YET_VERIFIED.**
