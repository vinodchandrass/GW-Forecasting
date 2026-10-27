# Maharashtra completion experiments

Requires `numpy` and `scikit-learn` in Anaconda. Extract the ZIP into `D:\GW` so `D:\GW\Maharashtra_Completion\run.py` exists. Original downloads and `Maharashtra_Experiment\outputs\forecast_predictions.csv` must remain in place. Run from PowerShell:

```powershell
cd D:\GW\Maharashtra_Completion
python run.py
```

Upload `outputs\completion_report.json`, `matched_metrics.csv`, `station_bootstrap.csv`, `extreme_value_sensitivity.csv`, and `unseen_station_metrics.csv`. No raw datasets need uploading. Existing four-state files are not modified. Telemetry signs and manual observation schedules are not validated. The station-bootstrap estimand is station-equal; matched MAE difference is observation-weighted.
