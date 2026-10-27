# Paper A — consolidated first experimental execution

Run from Anaconda PowerShell:

```powershell
cd D:\GW\GW_State4_Experiments
python run.py
```

Requires pandas and numpy. Reads the five existing Gate 4 CSVs, verifies their SHA-256 checksums, and writes `outputs/` without modifying originals. Runtime depends on machine and large telemetry files.

**Outputs:** report.json, station_month_provisional.csv, station_coverage.csv, forecast_predictions.csv, forecast_metrics.csv, paired_errors.csv (last three only if eligible samples exist).

**Scientific scope:** exploratory monthly aggregation, observed-month coverage, and rolling one-step persistence versus seasonal-naive forecasting. Telemetry and manual data are kept separate. Exclusions of `-999`, `-999.999`, `-9999`, `9999`, and `958` are *provisional*, not agency-confirmed. `958` must undergo sensitivity analysis and source confirmation. These results cannot yet establish actual monitoring completeness, effects of missingness, unseen-station generalization, rainfall impacts, GEC-2015 impacts, or interval calibration. They are deliberately not labeled as those experiments.

**Next step:** upload `report.json`, `forecast_metrics.csv`, and `station_coverage.csv`; optionally `paired_errors.csv`. Do not upload multi-gigabyte raw datasets.
