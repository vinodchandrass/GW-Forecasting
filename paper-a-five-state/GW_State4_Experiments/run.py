import argparse, pathlib, json, hashlib, csv, math
import pandas as pd, numpy as np
from collections import defaultdict
P=pathlib.Path(__file__).resolve().parent
SOURCES={'KA_manual':('data_0_44aeb7689d.csv','Station Code','Monitoring Date','Ground Water Level'), 'RJ_manual':('data_7_0f2da7ec6d.csv','Station','Data Acquisition Time','Groundwater Level Quarterly Manual (meter)'), 'PB_telemetry':('data_35_','Station','Data Acquisition Time','Groundwater Level Telemetry 6 Hourly (meter)'), 'TN_telemetry':('data_33_','Station','Data Acquisition Time','Groundwater Level Telemetry 6 Hourly (meter)'), 'RJ_telemetry':('data_41_','Station','Data Acquisition Time','Groundwater Level Telemetry 6 Hourly (meter)')}
def run(args):
 root=pathlib.Path(args.data_dir);out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
 audits=[]; monthly=[]; flags=[]; results=[]; coverage=[]; split=[]
 for source,(pattern,sid,dt,val) in SOURCES.items():
  paths=list(root.glob(pattern+'*.csv')) if pattern.endswith('_') else [root/pattern]; paths=[p for p in paths if p.is_file()]
  if len(paths)!=1:audits.append({'source':source,'status':'BLOCKED_MISSING_OR_AMBIGUOUS','matches':len(paths)});continue
  path=paths[0];sha=hashlib.sha256()
  with path.open('rb') as f:
   for block in iter(lambda:f.read(4*1024*1024),b''):sha.update(block)
  if source in args.expected_hashes and sha.hexdigest()!=args.expected_hashes[source]:
   audits.append({'source':source,'status':'BLOCKED_HASH_MISMATCH'});continue
  accum=defaultdict(lambda:[0.,0]); n=0; nonnumeric=0; sent=0; dates_bad=0; year_counts=defaultdict(int)
  for chunk in pd.read_csv(path,dtype=str,chunksize=120000,encoding='utf-8-sig',on_bad_lines='warn',low_memory=False):
   if not all(c in chunk.columns for c in [sid,dt,val]):raise ValueError(f'Schema mismatch {source}')
   dates=pd.to_datetime(chunk[dt],dayfirst=True,errors='coerce');dates_bad+=int(dates.isna().sum());mask=dates.dt.year.between(2021,2025);c=chunk.loc[mask,[sid,val]].copy();d=dates.loc[mask];n+=len(c)
   if c.empty:continue
   for yr,count in d.dt.year.value_counts().items():year_counts[str(yr)]+=int(count)
   numeric=pd.to_numeric(c[val],errors='coerce');nonnumeric+=int(numeric.isna().sum()); sentinel=numeric.isin([-999,-999.0,-999.999,-9999,9999,958]);sent+=int(sentinel.sum());valid=numeric.notna() & np.isfinite(numeric) & ~sentinel & c[sid].notna() & c[sid].str.strip().ne('')
   tmp=pd.DataFrame({'station':c.loc[valid,sid].str.strip().values,'month':d.loc[valid].dt.to_period('M').astype(str).values,'value':numeric.loc[valid].values})
   grouped=tmp.groupby(['station','month'],sort=False).value.agg(['sum','count'])
   for (station,month),r in grouped.iterrows(): a=accum[(station,month)];a[0]+=float(r['sum']);a[1]+=int(r['count'])
  for (station,month),(total,count) in accum.items():monthly.append({'source':source,'station':station,'month':month,'value_mean':total/count,'observations':count})
  audits.append({'source':source,'status':'PROVISIONAL_NUMERIC_WITH_SENTINEL_SENSITIVITY','sha256':sha.hexdigest(),'rows_2021_2025':n,'non_numeric':nonnumeric,'candidate_sentinel_rows_excluded':sent,'unparsed_dates':dates_bad,'station_month_cells':len(accum),'year_counts':dict(year_counts),'warning':'Sentinel list is provisional; value 958 requires agency confirmation. Monthly aggregation is arithmetic mean, not official seasonal statistic.'})
 if not monthly:(out/'report.json').write_text(json.dumps({'audit':audits,'status':'NO_USABLE_DATA'},indent=2));return
 df=pd.DataFrame(monthly);df.to_csv(out/'station_month_provisional.csv',index=False)
 for source,sub in df.groupby('source'):
  is_tele='telemetry' in source; months=pd.period_range('2021-01','2025-12',freq='M');
  for station,g in sub.groupby('station'):
   g=g.sort_values('month');obs=set(g.month);active_start=min(obs);active_end=max(obs)
   active=pd.period_range(active_start,active_end,freq='M').astype(str); coverage.append({'source':source,'station':station,'observed_months':len(obs),'active_span_months':len(active),'active_span_fraction':len(obs)/len(active),'calendar_months_2021_2025':60,'calendar_fraction':len(obs)/60,'schedule_verified':False})
   # Evaluation: strictly past-only one-step forecasts. Calendar gaps are never filled with future observations.
   v=dict(zip(g.month,g.value_mean));ordered=sorted(obs);test=[m for m in ordered if m>='2024-01' and m<='2025-12']; train=[m for m in ordered if m<'2024-01'];
   if len(train)<12 or len(test)<3:continue
   for m in test:
    period=pd.Period(m,freq='M');prev=str(period-1);lastyear=str(period-12)
    if prev not in v:continue
    truth=v[m];pred=v[prev]; results.append({'source':source,'station':station,'month':m,'model':'persistence','truth':truth,'prediction':pred,'absolute_error':abs(truth-pred),'squared_error':(truth-pred)**2,'protocol':'rolling_one_step_observed_previous_month'})
    if lastyear in v:
     pred=v[lastyear];results.append({'source':source,'station':station,'month':m,'model':'seasonal_naive_12','truth':truth,'prediction':pred,'absolute_error':abs(truth-pred),'squared_error':(truth-pred)**2,'protocol':'rolling_one_step_observed_same_month_last_year'})
 pd.DataFrame(coverage).to_csv(out/'station_coverage.csv',index=False)
 if results:
  pred=pd.DataFrame(results);pred.to_csv(out/'forecast_predictions.csv',index=False)
  summary=pred.groupby(['source','model']).agg(n=('absolute_error','size'),mae=('absolute_error','mean'),mse=('squared_error','mean'),stations=('station','nunique')).reset_index();summary['rmse']=np.sqrt(summary.pop('mse'));summary.to_csv(out/'forecast_metrics.csv',index=False)
  # paired errors only where both models were available on the same station-month
  pair=pred.pivot_table(index=['source','station','month'],columns='model',values='absolute_error').dropna()
  if not pair.empty:
   pair['seasonal_minus_persistence']=pair['seasonal_naive_12']-pair['persistence'];pair.reset_index().to_csv(out/'paired_errors.csv',index=False)
 report={'status':'EXPLORATORY_EXPERIMENTS_ONLY','source_audits':audits,'source_month_cells':df.groupby('source').size().to_dict(),'forecast_predictions':len(results),'limits':['No official monitoring schedule: observed-month coverage is not expected-observation completeness','Station identity not independently authenticated','Candidate sentinel exclusions provisional, particularly 958','Manual and telemetry are not pooled','No IMD rainfall data: rainfall experiment NOT EXECUTED','No GEC resource-estimation input records: GEC impact NOT EXECUTED','No unseen-station model training: unseen-station experiment NOT EXECUTED','No 90-percent calibrated interval: interval coverage NOT EXECUTED','No randomized gap masking: causal missingness impact NOT EXECUTED','2024-2025 test uses rolling observed historical values; not a fixed-origin multi-step forecast','No inferential p-values: avoid superiority claims']}
 (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'status':report['status'],'forecast_predictions':len(results),'outputs':str(out)},indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--data-dir',default=r'D:\GW\GW_State4_Gate4\outputs');a.add_argument('--out',default=str(P/'outputs'));args=a.parse_args();args.expected_hashes={'KA_manual':'8aa4ee64e27bf36bee0fc9d6c2408693b1ea7dffabd105700df31a399cdde596','RJ_manual':'29b4da988251c646dc4d7fe0e781607feebf98d69cffb25d6a228ce2303943a6','PB_telemetry':'a43d7754c3f324596e3d5299899caa56adcf6b54a46bd34e433dcb9e4027988c','TN_telemetry':'3c8713179b39338b8e4adccb1ec911375df5a16bc45facaa83d9968d2d3637bc','RJ_telemetry':'ae9438b3c72ade8142140a8dc7b081fde319208ad0cf973adc5bd095831feec3'};run(args)
