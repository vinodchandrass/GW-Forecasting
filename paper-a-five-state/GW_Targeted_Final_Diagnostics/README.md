# Bounded five-state diagnostic

Extract this folder directly into `D:\GW` so `run.py` is at `D:\GW\GW_Targeted_Final_Diagnostics\run.py`.

Run from PowerShell:

```powershell
python "D:\GW\GW_Targeted_Final_Diagnostics\run.py"
```

Requires NumPy. Uses the three frozen inputs from `GW_Common_Unseen_Station`, and verifies Maharashtra source hashes and four-state monthly SHA256. Reconstructs the **same fixed Ridge specification and station cohorts** solely for error-level diagnostics; no hyperparameter search or new model comparisons. Outputs are written only to this package's `outputs` folder. If prior unseen metrics are available, numerical agreement is checked.

Upload `targeted_diagnostic_report.json`, `extreme_error_diagnostics.csv`, `year_distribution_diagnostics.csv`, and `maharashtra_station_composition.csv`.
