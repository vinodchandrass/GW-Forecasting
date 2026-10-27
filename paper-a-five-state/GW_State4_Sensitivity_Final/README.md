# Groundwater Paper A: final targeted sensitivity

Runs the original exact-match validation and **additional empirical tail-trimming sensitivity** using the existing `gap_predictions.csv`. No new data download, no changes to original CSVs.

## Run (Windows PowerShell)

```powershell
cd D:\GW\GW_State4_Sensitivity_Final
python run.py
```

Requires `numpy`, `pandas` and the prior predictions at `D:\GW\GW_State4_Final_Experiments\outputs\gap_predictions.csv`.

Output: `outputs/extreme_value_sensitivity.csv` plus matched-gap results, matching checks and validation report. Upload **only** `extreme_value_sensitivity.csv` and `validation_report.json` (and any error output).

Rules: (a) all matched observations; (b) exclude matched targets above the source-specific absolute-target 99.9th percentile; (c) exclude matched targets above 99th percentile. Thresholds estimated from observed targets, not verified hydrogeological plausibility bounds. Same matched observation is removed from both baseline and gap scenarios. All models and all source datasets are evaluated. Bootstrap resamples stations, 1000 iterations by default. These analyses assess sensitivity to tails, not whether measurements are valid. Note: may require substantial RAM as previous matched-validation run did.
