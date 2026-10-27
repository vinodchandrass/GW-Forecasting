# Five-state common-protocol unseen-station experiment

Extract the folder to `D:\GW\GW_Common_Unseen_Station` (the script automatically resolves the `D:\GW` parent). Run:

```powershell
python -m pip install numpy
python "D:\GW\GW_Common_Unseen_Station\run.py"
```

Inputs already on disk: `D:\GW\GW_State4_Experiments\outputs\station_month_provisional.csv`, `D:\GW\Maharashtra_GW_Download\downloads\manual.csv`, and `telemetry.csv`. No manual copying or new download.

Outputs: `outputs/common_unseen_report.json`, `outputs/common_unseen_station_metrics.csv`, `outputs/common_unseen_year_diagnostics.csv`. Upload the first two.

This is a new common-method experiment, not an assertion that source conventions are validated. Station-disjoint train/calibration/test groups, time-restricted training, history-only lag features and 90% empirical interval calibration. No formal conformal coverage guarantee is claimed under clustered/time-dependent data.
