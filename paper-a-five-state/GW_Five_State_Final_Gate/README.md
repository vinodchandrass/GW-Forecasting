# Five-state final evidence gate — no new experiments

This package audits existing consolidated tables, separates observation-weighted and station-equal estimands, normalizes labels for *target-only* trimming, and records a decision on what can be claimed. It **does not** pretend to run a common five-state experimental protocol or authenticate official monitoring conventions.

## PowerShell — paste all lines together

```powershell
$base = 'D:\GW'
$dest = "$base\GW_Five_State_Final_Gate\inputs"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$src = "$base\GW_Five_State_Consolidation\outputs"
Copy-Item "$src\source_specific_matched_effects.csv" "$dest\source_specific_matched_effects.csv" -Force
Copy-Item "$src\source_specific_unseen_station.csv" "$dest\source_specific_unseen_station.csv" -Force
Copy-Item "$src\four_sensitivity.csv" "$dest\four_sensitivity.csv" -Force
Copy-Item "$src\mh_sensitivity.csv" "$dest\mh_sensitivity.csv" -Force
python "$base\GW_Five_State_Final_Gate\run.py"
```

## Outputs

- `outputs/final_gate_report.json`
- `outputs/matched_estimands_audit.csv`
- `outputs/sensitivity_harmonized_labels.csv`
- `outputs/sensitivity_summary.csv`

The audit may support a **descriptive-only evidence freeze**; true protocol harmonization requires access to underlying station-month series and a new common evaluation design. This kit makes no such claim. No manuscript is generated.
