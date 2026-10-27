import argparse,csv,json,pathlib,tempfile,hashlib
import numpy as np,pandas as pd
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',default=r'D:\GW\GW_State4_Final_Experiments\outputs\gap_predictions.csv');p.add_argument('--out',default=str(ROOT/'outputs'));p.add_argument('--bootstrap',type=int,default=1000);a=p.parse_args()
 inp=pathlib.Path(a.input);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if not inp.exists():raise SystemExit('Missing gap_predictions.csv: '+str(inp))
 report={'status':'STARTED','input':str(inp),'method':'exact source/station/month/replicate/model paired comparisons; station bootstrap','source_sha256':hashlib.file_digest(open(inp,'rb'),'sha256').hexdigest(),'sources':{}}
 keys=['source','station','month','replicate','model'];outrows=[];checks=[]
 with tempfile.TemporaryDirectory(prefix='gw_matched_') as td:
  handles={};writers={};counts={}
  try:
   for chunk in pd.read_csv(inp,chunksize=150000,dtype={'source':str,'station':str,'month':str,'scenario':str,'model':str},usecols=keys+['scenario','truth','pred']):
    for source,g in chunk.groupby('source'):
     if source not in handles:
      f=open(pathlib.Path(td)/(source+'.csv'),'w',newline='',encoding='utf8');handles[source]=f;writers[source]=csv.writer(f);writers[source].writerow(keys+['scenario','truth','pred'])
     writers[source].writerows(g[keys+['scenario','truth','pred']].itertuples(index=False,name=None));counts[source]=counts.get(source,0)+len(g)
  finally:
   for f in handles.values():f.close()
  for source in sorted(counts):
   data=pd.read_csv(pathlib.Path(td)/(source+'.csv'),dtype={'source':str,'station':str,'month':str,'scenario':str,'model':str,'replicate':'int16'})
   duplicated=int(data.duplicated(keys+['scenario']).sum())
   if duplicated:raise SystemExit(f'Duplicate prediction keys for {source}: {duplicated}; cannot safely match')
   base=data[data.scenario=='none'][keys+['truth','pred']].rename(columns={'truth':'truth_base','pred':'pred_base'})
   for scenario in ['random20','block3']:
    treated=data[data.scenario==scenario];merged=treated.merge(base,on=keys,how='inner',validate='one_to_one')
    if not len(merged):continue
    mismatched=int((~np.isclose(merged.truth,merged.truth_base,rtol=0,atol=1e-9)).sum())
    if mismatched:raise SystemExit(f'Target truth mismatch: {source} {scenario} {mismatched}')
    merged['ae_base']=(merged.truth-merged.pred_base).abs();merged['ae_gap']=(merged.truth-merged.pred).abs();merged['delta']=merged.ae_gap-merged.ae_base
    for model,g in merged.groupby('model'):
     st=g.groupby('station',sort=False).agg(delta=('delta','mean'),n=('delta','size'));vals=st.delta.to_numpy();rng=np.random.default_rng(20261020)
     bs=np.array([rng.choice(vals,len(vals),replace=True).mean() for _ in range(a.bootstrap)])
     outrows.append({'source':source,'scenario':scenario,'model':model,'matched_predictions':len(g),'stations':len(st),'baseline_matched_mae':g.ae_base.mean(),'masked_matched_mae':g.ae_gap.mean(),'observation_weighted_mae_delta':g.delta.mean(),'station_equal_weight_mae_delta':vals.mean(),'station_bootstrap_ci_low':np.quantile(bs,.025),'station_bootstrap_ci_high':np.quantile(bs,.975),'baseline_predictions':len(base[base.model==model]),'masked_predictions':len(treated[treated.model==model]),'truth_mismatch_count':mismatched})
    checks.append({'source':source,'scenario':scenario,'matched_rows':len(merged),'target_mismatch':mismatched})
   report['sources'][source]={'input_rows':counts[source],'duplicate_prediction_keys':duplicated,'truth_abs_p99':float(data.truth.abs().quantile(.99)),'truth_abs_p999':float(data.truth.abs().quantile(.999)),'truth_abs_max':float(data.truth.abs().max()),'truth_abs_gt100':int((data.truth.abs()>100).sum()),'warning':'Extreme-value thresholds are diagnostics, not verified physical validity limits'}
 pd.DataFrame(outrows).to_csv(out/'matched_gap_results.csv',index=False);pd.DataFrame(checks).to_csv(out/'matching_checks.csv',index=False)
 report['status']='MATCHED_SENSITIVITY_COMPLETE';report['limitations']=['Station bootstrap describes sensitivity to synthetic masks, not causal effects of real outages','Source sign/datum and sentinel semantics remain provisional','Missing target/prediction pairs excluded; report matched sample sizes','No IMD/GEC experiments executed'];(out/'validation_report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'comparison_rows':len(outrows),'sources':list(counts)},indent=2))
if __name__=='__main__':main()
