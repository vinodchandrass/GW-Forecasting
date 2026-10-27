# Paper A — Local reproduction verification (2026-10-27)

## Verification basis
Investigator-provided PowerShell terminal outputs and explicit PASS confirmations, using original inputs on `D:\GW`. This record documents investigator-reported local reproduction; the repository maintainer did not execute the experiments independently in a separate environment.

## Confirmed checks
- Original input SHA-256 checks: **3/3 PASS**, for the four-state station-month input and Maharashtra manual/telemetry source files.
- Python syntax parsing: **5/5 PASS** for the five published `run.py` modules.
- Python 3.14.6, NumPy 2.4.6, pandas 3.0.3, scikit-learn 1.9.0 were reported in the local environment.
- `GW_Common_Protocol_Experiment/outputs/common_protocol_report.json`: investigator confirmed **byte-for-byte SHA-256 match** after running the script.
- `GW_Common_Unseen_Station/outputs/common_unseen_report.json`: investigator confirmed **byte-for-byte SHA-256 match** after running the script.

## Scope and limits
The historical Maharashtra completion, five-state consolidation and targeted diagnostics modules were not independently rerun in this verification. Source-specific data conventions, telemetry sign/datum, manual observation schedules, station identities and exchangeability assumptions retain their documented limitations. The two successful local report reproductions do not demonstrate cross-machine reproducibility or independent data authentication.

No input datasets, processed observations, manuscript files or figures are included in this record.

**Status: PRINCIPAL_REPORTS_LOCALLY_REPRODUCED; FULL_RELEASE_REPRODUCIBILITY_NOT_CERTIFIED.**
