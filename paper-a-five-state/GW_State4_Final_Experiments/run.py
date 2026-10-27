import argparse, pathlib, json, hashlib
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
ROOT=pathlib.Path(__file__).resolve().parent
SEED=20261020

def metrics(g):
 e=g.truth.to_numpy()-g.pred.to_numpy();return {'n':len(g),'stations':g.station.nunique(),'mae':float(np.abs(e).mean()),'rmse':float(np.sqrt(np.mean(e*e)))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--monthly',default=r'D:\GW\GW_State4_Experiments\outputs\station_month_provisional.csv');ap.add_argument('--out',default=str(ROOT/'outputs'));ap.add_argument('--seeds',type=int,default=10);a=ap.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(SEED)
 p=pathlib.Path(a.monthly);report={'protocol':'PROVISIONAL_RESEARCH_EXPERIMENTS','source_file':str(p),'seed':SEED,'limitations':['Source sign conventions and missing codes not officially confirmed','Station IDs are source-specific; no cross-source physical well linkage','Monthly mean of telemetry is an exploratory proxy, not an official seasonal reading','Missingness interventions are synthetic and estimate algorithmic sensitivity, not real-world causal impact','No IMD rainfall or GEC input data supplied: not executed','90% intervals are empirical split-calibrated and exploratory, not guaranteed distribution-free under dependence']}
 if not p.exists():
  report['status']='BLOCKED_MONTHLY_FILE_NOT_FOUND';(out/'report.json').write_text(json.dumps(report,indent=2));raise SystemExit('Missing station_month_provisional.csv. Run prior GW_State4_Experiments/run.py first, or pass --monthly PATH')
 df=pd.read_csv(p,dtype={'source':str,'station':str,'month':str});required={'source','station','month','value_mean'}
 if not required.issubset(df.columns):raise SystemExit('Unexpected monthly schema')
 df['value_mean']=pd.to_numeric(df.value_mean,errors='coerce');df=df.dropna(subset=['value_mean','station','month']);df['period']=pd.PeriodIndex(df.month,freq='M');df=df.sort_values(['source','station','period']).drop_duplicates(['source','station','period'],keep=False)
 report['monthly_input_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();report['sources']={};rows=[];gaps=[];unseen=[];interval=[]
 for source,src in df.groupby('source',sort=True):
  srep={'observed_month_cells':len(src),'stations':src.station.nunique()};report['sources'][source]=srep
  # Build dense calendar, preserving missing months explicitly; do not impute targets.
  wide=src.pivot(index='station',columns='period',values='value_mean');periods=pd.period_range('2021-01','2025-12',freq='M');wide=wide.reindex(columns=periods)
  observed=wide.notna().sum(axis=1);eligible=wide.loc[observed>=18];srep['stations_with_18plus_observed_months']=len(eligible)
  if eligible.empty:srep['status']='INSUFFICIENT_HISTORY';continue
  # Station-level active-span gaps; denominator does not claim official schedule completeness.
  for st,r in wide.iterrows():
   loc=np.flatnonzero(r.notna().to_numpy());
   if len(loc):gaps.append({'source':source,'station':st,'observed_months':len(loc),'active_span_months':int(loc[-1]-loc[0]+1),'internal_unobserved_months':int(loc[-1]-loc[0]+1-len(loc))})
  # Paired synthetic gap sensitivity, same target and station across methods and scenarios.
  for replicate in range(a.seeds):
   for scenario in ('none','random20','block3'):
    masked=eligible.copy();arr=masked.to_numpy(dtype=float, copy=True);mask=np.zeros(arr.shape,dtype=bool)
    # mask history only, never test target; target values come from untouched eligible.
    for i in range(len(arr)):
     for t in range(36,59):
      if scenario=='random20' and rng.random()<.2:mask[i,t]=True
     if scenario=='block3':
      for start in range(36,59,6):
       if rng.random()<.5:mask[i,start:min(start+3,59)]=True
    arr[mask]=np.nan
    # only one-step t>=2024-01, with lagged observations masked for synthetic outages.
    for t in range(36,60):
     truth=eligible.iloc[:,t].to_numpy(dtype=float);ok=np.isfinite(truth)
     prev=arr[:,t-1] if t>=1 else np.full(len(arr),np.nan)
     seas=arr[:,t-12] if t>=12 else np.full(len(arr),np.nan)
     # past-only carry-forward up to 6 months; fallback seasonal when lag is unavailable.
     carry=np.full(len(arr),np.nan)
     for lag in range(1,7):
      v=arr[:,t-lag];carry=np.where(np.isnan(carry),v,carry)
     preds={'persistence':prev,'seasonal_naive_12':seas,'carry_forward_6':carry,'hybrid_carry_seasonal':np.where(np.isfinite(carry),carry,seas)}
     for model,pred in preds.items():
      sel=ok & np.isfinite(pred)
      for idx in np.flatnonzero(sel):rows.append((source,str(eligible.index[idx]),str(periods[t]),replicate,scenario,model,float(truth[idx]),float(pred[idx])))
  # Unseen-station + chronological holdout, Ridge with raw lag features (no target-station fit).
  stations=np.array(sorted(eligible.index));perm=np.random.default_rng(SEED).permutation(stations);n_hold=max(1,int(np.ceil(.2*len(perm))));held=set(perm[:n_hold]);train=[];test=[];cal=[]
  for st,r in eligible.iterrows():
   vals=r.to_numpy(dtype=float)
   for t in range(12,60):
    if not np.all(np.isfinite([vals[t],vals[t-1],vals[t-12]])):continue
    x=[vals[t-1],vals[t-12],np.sin(2*np.pi*(t%12)/12),np.cos(2*np.pi*(t%12)/12)]
    rec=(st,str(periods[t]),x,float(vals[t]))
    if st in held and t>=36:test.append(rec)
    elif st not in held and t<30:train.append(rec)
    elif st not in held and 30<=t<36:cal.append(rec)
  srep['unseen_split']={'training_stations':len(stations)-n_hold,'heldout_stations':n_hold,'training_examples':len(train),'calibration_examples':len(cal),'test_examples':len(test),'training_period':'2022-01 to 2023-06','calibration_period':'2023-07 to 2023-12','test_period':'2024-01 to 2025-12'}
  if len(train)<100 or len(test)<30 or len(cal)<30:srep['unseen_split']['status']='INSUFFICIENT_EXAMPLES';continue
  model=Ridge(alpha=10.0);model.fit(np.asarray([r[2] for r in train]),np.asarray([r[3] for r in train]));cp=model.predict(np.asarray([r[2] for r in cal]));resid=np.abs(np.asarray([r[3] for r in cal])-cp);q=float(np.quantile(resid,.9,method='higher'))
  preds=model.predict(np.asarray([r[2] for r in test]));
  for (st,month,x,y),pred in zip(test,preds):unseen.append((source,st,month,'ridge_unseen_station',y,float(pred),q))
  srep['unseen_split'].update({'status':'EXECUTED','calibration_absolute_error_q90':q,'empirical_90_interval_note':'Split-calibration is based on non-held-out stations and different years; temporal/spatial exchangeability not established'})
 pd.DataFrame(rows,columns=['source','station','month','replicate','scenario','model','truth','pred']).to_csv(out/'gap_predictions.csv',index=False)
 pred=pd.DataFrame(rows,columns=['source','station','month','replicate','scenario','model','truth','pred'])
 summary=[]
 if len(pred):
  for keys,g in pred.groupby(['source','scenario','model']):summary.append(dict(zip(['source','scenario','model'],keys),**metrics(g)))
 pd.DataFrame(summary).to_csv(out/'gap_metrics.csv',index=False)
 unseen_df=pd.DataFrame(unseen,columns=['source','station','month','model','truth','pred','halfwidth90']);unseen_df.to_csv(out/'unseen_station_predictions.csv',index=False)
 us=[]
 if len(unseen_df):
  for source,g in unseen_df.groupby('source'):
   d=metrics(g);d.update(source=source,model='ridge_unseen_station',coverage90=float(((g.truth-g.pred).abs()<=g.halfwidth90).mean()),mean_interval_width=float((2*g.halfwidth90).mean()));us.append(d)
 pd.DataFrame(us).to_csv(out/'unseen_station_metrics.csv',index=False)
 pd.DataFrame(gaps).to_csv(out/'station_gap_summary.csv',index=False)
 # Paired, station-clustered bootstrap for gap sensitivity, replicate-averaged errors.
 boots=[]
 if len(pred):
  pe=pred.assign(ae=(pred.truth-pred.pred).abs()).groupby(['source','station','scenario','model']).ae.mean().reset_index()
  base=pe[pe.scenario=='none'][['source','station','model','ae']].rename(columns={'ae':'baseline_mae'})
  compare=pe.merge(base,on=['source','station','model']);compare['delta']=compare.ae-compare.baseline_mae
  for (source,scenario,model),g in compare.groupby(['source','scenario','model']):
   vals=g.delta.to_numpy();n=len(vals);brng=np.random.default_rng(SEED);bs=np.array([brng.choice(vals,size=n,replace=True).mean() for _ in range(1000)])
   boots.append({'source':source,'scenario':scenario,'model':model,'stations':n,'mean_station_mae_delta':float(vals.mean()),'bootstrap_ci_low':float(np.quantile(bs,.025)),'bootstrap_ci_high':float(np.quantile(bs,.975)),'note':'Station-cluster bootstrap, synthetic masking; not a causal effect of actual monitoring failures'})
 pd.DataFrame(boots).to_csv(out/'paired_station_bootstrap.csv',index=False)
 report['status']='EXPERIMENTS_EXECUTED_WITH_PROVISIONAL_SOURCE_SEMANTICS';report['gap_prediction_rows']=len(pred);report['unseen_station_prediction_rows']=len(unseen_df);report['outputs']=['gap_metrics.csv','paired_station_bootstrap.csv','unseen_station_metrics.csv','station_gap_summary.csv','gap_predictions.csv','unseen_station_predictions.csv'];(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'gap_prediction_rows':len(pred),'unseen_station_prediction_rows':len(unseen_df)},indent=2))
if __name__=='__main__':main()

