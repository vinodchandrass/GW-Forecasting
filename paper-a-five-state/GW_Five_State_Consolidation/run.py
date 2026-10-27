from pathlib import Path
import pandas as pd, json, hashlib
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
# Place the exported CSVs in inputs/, retaining filenames. All reported comparisons are descriptive, not pooled.
I=ROOT/'inputs'
files={'four_matched':'matched_gap_results.csv','four_sensitivity':'extreme_value_sensitivity.csv','four_unseen':'unseen_station_metrics.csv','mh_matched':'matched_metrics.csv','mh_bootstrap':'station_bootstrap.csv','mh_sensitivity':'extreme_value_sensitivity(1).csv','mh_unseen':'unseen_station_metrics(1).csv'}
missing=[v for v in files.values() if not (I/v).is_file()]
if missing: raise SystemExit('Missing inputs: '+', '.join(missing)+'\nSee README.md')
d={k:pd.read_csv(I/v) for k,v in files.items()}
for k,v in files.items():
 if d[k].empty:raise SystemExit('Empty file: '+v)
# Retain only the comparable carry_forward_6 model, without combining different source types.
f=d['four_matched'];f=f[(f['model']=='carry_forward_6') & f['scenario'].isin(['random20','block3'])].copy()
f=f[['source','scenario','matched_predictions','stations','observation_weighted_mae_delta','station_equal_weight_mae_delta','station_bootstrap_ci_low','station_bootstrap_ci_high']]
f.columns=['source','scenario','matched_targets','stations','observation_weighted_delta_mae','station_equal_delta_mae','ci_low','ci_high']
m=d['mh_matched'].merge(d['mh_bootstrap'],on=['source','scenario','stations'],validate='one_to_one')
m=m[['source','scenario','matched_targets','stations','observation_weighted_delta_mae','station_equal_delta_mae','ci_low','ci_high']]
combined=pd.concat([f,m],ignore_index=True).sort_values(['source','scenario'])
if combined.duplicated(['source','scenario']).any():raise SystemExit('Duplicate source/scenario after consolidation')
combined.to_csv(OUT/'source_specific_matched_effects.csv',index=False)
fu=d['four_unseen']; mu=d['mh_unseen']
fu=fu[['source','stations','n','mae','coverage90']].rename(columns={'stations':'test_stations','n':'test_rows','coverage90':'empirical_coverage'})
mu=mu[['source','test_stations','test','mae','empirical_coverage']].rename(columns={'test':'test_rows'})
unc=pd.concat([fu,mu],ignore_index=True).sort_values('source');unc.to_csv(OUT/'source_specific_unseen_station.csv',index=False)
# Preserve sensitivity outputs verbatim, adding origin marker; do not assume thresholds/definitions identical.
for key in ['four_sensitivity','mh_sensitivity']:
 x=d[key].copy();x.insert(0,'analysis_origin',key);x.to_csv(OUT/(key+'.csv'),index=False)
checks={'four_matched_sources':sorted(f.source.unique().tolist()),'maharashtra_sources':sorted(m.source.unique().tolist()),'unseen_sources':sorted(unc.source.unique().tolist()),'n_matched_rows':len(combined),'n_unseen_rows':len(unc),'source_files':{k:{'name':v,'sha256':hashlib.sha256((I/v).read_bytes()).hexdigest(),'rows':len(d[k])} for k,v in files.items()},'warnings':['Four-state and Maharashtra experimental implementations differ; estimates are not protocol-harmonized','Manual observation schedules are not authenticated; unobserved months do not necessarily imply missing scheduled measurements','Telemetry sign/datum and sentinel definitions remain unauthenticated','IMD rainfall and GEC-2015 resource-estimation experiments have not been performed','Unseen-station splits and calibration may differ; do not rank states by MAE','Rajasthan manual forecasting was not performed due to insufficient eligible histories','Four-state source-specific carry_forward_6 estimates are not equivalent to a pooled five-state model','No new experiments are performed by this consolidation; this is an evidence reconciliation']}
(OUT/'consolidation_report.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('COMPLETE: '+str(OUT));print('Matched sources:',', '.join(combined.source.unique()));print('Unseen sources:',', '.join(unc.source.unique()))
