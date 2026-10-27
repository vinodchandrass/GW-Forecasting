# Maharashtra fifth-state exploratory experiments

Extract folder into D:\GW, alongside Maharashtra_GW_Download. Run:

```powershell
cd D:\GW\Maharashtra_Experiment
python run.py
```

Uses standard-library Python; reads the existing downloaded manual.csv and telemetry.csv; verifies their exact SHA-256 values from the supplied download report. Streams the files without loading all raw records into memory. Outputs `outputs/report.json`, `station_coverage.csv`, `forecast_metrics.csv`, and `forecast_predictions.csv`.

This is a **first-stage Maharashtra feasibility and baseline experiment**, not the previously promised complete five-state harmonized missingness, unseen-station and statistical package. The code treats suspected sentinel values as excluded provisionally and keeps manual/telemetry separate. The forecast gap comparisons use different eligible targets and are not paired causal effect estimates. Actual sampling cadence must be inferred from full timestamps and official documentation. We must inspect this output before constructing the fully matched fifth-state analysis.
