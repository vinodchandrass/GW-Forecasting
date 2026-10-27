# Paper A — consolidated experimental extension

This is a **research exploratory** pipeline, not a validated operational groundwater predictor. Requires Python packages `pandas`, `numpy`, `scikit-learn` (Anaconda). No downloads or changes to source data.

## Windows PowerShell

```powershell
cd D:\GW\GW_State4_Experiments
python run.py
cd D:\GW\GW_State4_Final_Experiments
python run.py
```

The default input is `D:\GW\GW_State4_Experiments\outputs\station_month_provisional.csv`. Or use `python run.py --monthly "D:\path\station_month_provisional.csv"`. Outputs appear in `outputs`.

## Experiments

1. Per-station internal calendar gaps, not official monitoring completeness.
2. Ten replicated synthetic masking interventions on monthly observed histories: no masking, random 20% of post-2023 historical slots, and intermittent three-month blocks. Models: persistence, seasonal naive, six-month carry forward and hybrid. The **same original observed target** is evaluated under masked histories. No target imputation or future-value leakage.
3. Unseen-station Ridge regression: 80% of eligible stations train on 2022–mid-2023; late-2023 calibrates an absolute-error 90% interval; 20% of stations remain unseen until evaluation in 2024–2025. Models use lag-1, lag-12, calendar seasonality. Both lags must be actually observed. This tests spatial generalization *conditional on available lagged measurements*, not cold-start prediction.
4. Paired station-cluster bootstrap confidence intervals for mean changes in station MAE under synthetic gaps.

## Interpretation safeguards

- Source sign conventions, station identities and sentinel codes remain provisional; do not claim finalized accuracy or physical plausibility.
- Monthly telemetry means do not equal manual seasonal observations.
- The source's candidate exclusion of `958` is unverified; repeat sensitivity after official coding confirmation.
- Observed station months are not official expected-monitoring completeness.
- Rainfall and GEC-2015 effect experiments cannot be executed without appropriate external data.
- Bootstrap uncertainty concerns the experimental sample, not necessarily state-wide generalization.
- The unseen-station model is deliberately modest; stronger model selection and external replication may be needed for Q1 publication.

Upload `outputs/report.json`, `outputs/gap_metrics.csv`, `outputs/paired_station_bootstrap.csv`, and `outputs/unseen_station_metrics.csv` together for interpretation. Predictions can remain on your computer unless needed for debugging.
