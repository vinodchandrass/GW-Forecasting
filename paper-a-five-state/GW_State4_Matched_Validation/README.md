# Groundwater Paper A: focused matched-sample validation

Purpose: Verify missingness effect on identical station/month/replicate/model target records, fixing comparability limitations of aggregated scenario metrics. This is NOT a new acquisition or broad audit phase.

Requirements: Python 3, pandas, numpy (existing Anaconda environment).

Run in PowerShell:
```
cd D:\GW\GW_State4_Matched_Validation
python run.py
```

Reads existing `D:\GW\GW_State4_Final_Experiments\outputs\gap_predictions.csv` (10.7m rows) without changing it. The program partitions input by source in a temporary folder, so disk space and RAM are needed (several GB of free disk recommended; the largest source may require >1GB RAM). It joins baseline and masked results on source/station/month/replicate/model, checks matching target truth, computes paired MAE differences and station-cluster bootstrap CIs, and reports extreme values as diagnostics only. A zero effect for some models may reflect that masking removes predictions rather than increasing errors; compare counts.

Upload `outputs/matched_gap_results.csv`, `outputs/matching_checks.csv`, `outputs/validation_report.json`. No earlier phases need rerunning.
