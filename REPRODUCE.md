# Paper A — Reproduction guide

## Scope and evidence status
Five-state groundwater forecasting (Karnataka, Punjab, Rajasthan, Maharashtra, Tamil Nadu). This repository contains original experimental code and selected aggregate reference results, **not** the underlying datasets or observation-level predictions. Historical four-state and Maharashtra analyses are not fully protocol-harmonized. No independent clean-machine end-to-end reproduction is claimed.

The scripts were reviewed from the repository snapshot supplied by the project owner. The commands below are a reconstruction plan, **not a successfully executed end-to-end test**.

## Environment
Use Python 3.14.6 (the locally reported environment) and install `python -m pip install -r requirements.txt` from the repository root. The pins reflect locally reported versions, not an independently validated clean installation. Record `python --version` and `python -m pip freeze` for each reproduction.

## Data preparation (not committed)
All input files must be obtained from their authorized public sources and placed locally; original/processed datasets and prediction-level outputs must not be committed. The repository does not yet supply complete verified official acquisition URLs or an executable upstream `GW_State4_Gate4` preprocessing workflow. Thus raw-to-results reproducibility remains **blocked** pending those instructions/code.

Expected four-state input directory (pass to `--data-dir`):
- `data_0_44aeb7689d.csv` (KA manual)
- `data_7_0f2da7ec6d.csv` (RJ manual, used by the exploratory script)
- one file each matching `data_35_*.csv` (PB telemetry), `data_33_*.csv` (TN telemetry), `data_41_*.csv` (RJ telemetry).

The script validates expected input hashes internally. Source provenance, redistribution rights, exact filenames, and hashes must be reconciled before claiming full reconstruction. Check the `GW_State4_Experiments/run.py` `SOURCES` and `expected_hashes` definitions.

Maharashtra files must be placed locally at:
`paper-a-five-state/Maharashtra_GW_Download/downloads/manual.csv`
`paper-a-five-state/Maharashtra_GW_Download/downloads/telemetry.csv`

Expected SHA-256:
- `manual.csv`: `5003c9030b34df310f0bdd0527df022b9b0e73aa780b5bbacc88cc49d1be0eb6`
- `telemetry.csv`: `b4bf746c09eae07b7998328a5699ddc22989f7ec829509919b60421e7a366822`
- `GW_State4_Experiments/outputs/station_month_provisional.csv`: `ecc20c22fa0b52b4ab8295856b35121d0a62bcfdbf138fbbf7e6a757f16f85de` (previously verified locally; only valid for the corresponding frozen input).

## Execution sequence
Run from repository root, with input directories outside Git when possible. On Windows, use PowerShell and replace `<FOUR_STATE_CSV_DIR>` with a local directory. Some scripts use fixed relative paths; the Maharashtra directory above must exist.

```powershell
python paper-a-five-state/GW_State4_Experiments/run.py --data-dir "<FOUR_STATE_CSV_DIR>"
python paper-a-five-state/GW_State4_Final_Experiments/run.py --monthly "paper-a-five-state/GW_State4_Experiments/outputs/station_month_provisional.csv"
python paper-a-five-state/GW_State4_Matched_Validation/run.py --input "paper-a-five-state/GW_State4_Final_Experiments/outputs/gap_predictions.csv"
python paper-a-five-state/GW_State4_Sensitivity_Final/run.py --input "paper-a-five-state/GW_State4_Final_Experiments/outputs/gap_predictions.csv"
python paper-a-five-state/Maharashtra_Experiment/run.py
python paper-a-five-state/Maharashtra_Completion/run.py
python paper-a-five-state/GW_Common_Protocol_Experiment/run.py
python paper-a-five-state/GW_Common_Unseen_Station/run.py
python paper-a-five-state/GW_Targeted_Final_Diagnostics/run.py
```

`GW_Five_State_Consolidation/run.py` expects these *locally copied* filenames in `GW_Five_State_Consolidation/inputs/`:
`matched_gap_results.csv`, `extreme_value_sensitivity.csv`, `unseen_station_metrics.csv`, `matched_metrics.csv`, `station_bootstrap.csv`, `extreme_value_sensitivity(1).csv`, `unseen_station_metrics(1).csv`.
The first three originate from the four-state matched/sensitivity/final experiments; the remaining four are Maharashtra completion outputs. Copy and rename only where necessary, preserving provenance; do not publish these intermediate files. Then run:
```powershell
python paper-a-five-state/GW_Five_State_Consolidation/run.py
```

`GW_Five_State_Final_Gate/run.py` expects four locally staged CSVs in its `inputs/` directory: `source_specific_matched_effects.csv`, `four_sensitivity.csv`, `mh_sensitivity.csv`, `source_specific_unseen_station.csv`. Obtain them from consolidation outputs (the first and fourth, and the two source-specific sensitivity exports), then run:
```powershell
python paper-a-five-state/GW_Five_State_Final_Gate/run.py
```

**Important:** Never overwrite committed reference outputs before capturing a clean reference copy. Prefer a fresh clone for testing, and inspect `git status` afterward.

## Verification
`verify_results.py` compares numeric and textual values in generated aggregate CSV files against a **separate clean reference checkout**; it does not treat a generated file as its own reference. Use:
```powershell
python verify_results.py --reference "<PATH_TO_FROZEN_REFERENCE_CHECKOUT>" --generated "<PATH_TO_REPRODUCTION_CHECKOUT>"
```
The verifier checks only CSVs that exist in the frozen reference and reports missing generated files. It does not verify raw data acquisition, all reports, all intermediate outputs, or scientific validity. A passing comparison is therefore **aggregate-output agreement**, not complete independent reproducibility.

## Known limits
- Input acquisition and upstream preprocessing are not fully packaged.
- Some code contains fixed paths and must be run using the documented overrides or required directory layout.
- Reference CSV coverage is partial; many observation-level outputs are intentionally excluded.
- Numeric results from historical modules are not pooled as if fully protocol-harmonized.
- Local reproduction of two reports was user-confirmed previously, but a clean external reproduction is pending.
