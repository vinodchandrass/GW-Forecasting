# Five-state evidence reconciliation (no new experiments)

This package **does not claim that protocols have been harmonized**. It consolidates existing matched-gap and unseen-station outputs with source-specific provenance and retains original extreme-value sensitivity outputs separately. It does not alter raw data, re-run experiments, pool monitoring types, or generate manuscript text.

## PowerShell

Extract to `D:\GW\GW_Five_State_Consolidation`. Create `inputs` and copy the existing CSV exports into it. If Windows renamed duplicates, preserve the names below exactly.

```powershell
$dest = 'D:\GW\GW_Five_State_Consolidation\inputs'
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item 'D:\GW\GW_State4_Matched_Validation\outputs\matched_gap_results.csv' $dest
Copy-Item 'D:\GW\GW_State4_Sensitivity_Final\outputs\extreme_value_sensitivity.csv' $dest
Copy-Item 'D:\GW\GW_State4_Final_Experiments\outputs\unseen_station_metrics.csv' $dest
Copy-Item 'D:\GW\Maharashtra_Completion\outputs\matched_metrics.csv' $dest
Copy-Item 'D:\GW\Maharashtra_Completion\outputs\station_bootstrap.csv' $dest
Copy-Item 'D:\GW\Maharashtra_Completion\outputs\extreme_value_sensitivity.csv' "$dest\extreme_value_sensitivity(1).csv"
Copy-Item 'D:\GW\Maharashtra_Completion\outputs\unseen_station_metrics.csv' "$dest\unseen_station_metrics(1).csv"
python -m pip install pandas
python 'D:\GW\GW_Five_State_Consolidation\run.py'
```

If the local directory names differ, adjust only the Copy-Item source paths. Do not substitute unrelated outputs.

## Outputs
- `outputs/source_specific_matched_effects.csv`
- `outputs/source_specific_unseen_station.csv`
- `outputs/four_sensitivity.csv`
- `outputs/mh_sensitivity.csv`
- `outputs/consolidation_report.json`

**Important:** The earlier four-state data may have different model implementations, evaluation windows, and gap construction from Maharashtra. The table is descriptive. No pooled effect, comparative ranking, or common inferential conclusion is justified without an explicit harmonization experiment. In particular, official schedule validation, IMD rainfall, and GEC-2015 input data remain open scientific objectives.
