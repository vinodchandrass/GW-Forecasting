# Five-state common-protocol missingness experiment

Extract ZIP to `D:\GW` (ZIP contains one `GW_Common_Protocol_Experiment` folder). Run:

```powershell
python D:\GW\GW_Common_Protocol_Experiment\run.py
```

Requires `numpy` (Anaconda normally includes it). Inputs are the existing `D:\GW\GW_State4_Experiments\outputs\station_month_provisional.csv` and two Maharashtra raw files in `D:\GW\Maharashtra_GW_Download\downloads`. The Maharashtra files are SHA-256 verified. This is a **new common computational protocol** on existing monthly source-specific values; it does not claim harmonized official monitoring schedules, common measurement conventions, unseen-station model parity, or new rainfall/GEC analyses.

Outputs: `outputs/common_protocol_report.json`, `outputs/common_matched_effects.csv`, `outputs/common_sensitivity.csv`. Upload these three small files for interpretation.

The experiment applies one deterministic synthetic intervention per target (not ten historical replicates), uses a six-calendar-month latest-observed carry-forward baseline and compares on exactly matched target months. Random masking is deterministic per station and historical month; three-month masking is deterministic per station and target. Bootstrap confidence intervals refer to station-equal effects, not observation-weighted point estimates. No model rankings or state superiority claims are justified.
