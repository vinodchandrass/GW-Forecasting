import csv,json,hashlib,pathlib,sys
root=pathlib.Path(__file__).resolve().parent; inp=root/'inputs';out=root/'outputs';out.mkdir(exist_ok=True)
files={'effects':'source_specific_matched_effects.csv','four_sensitivity':'four_sensitivity.csv','mh_sensitivity':'mh_sensitivity.csv','unseen':'source_specific_unseen_station.csv'}
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
missing=[v for v in files.values() if not (inp/v).is_file()]
if missing:sys.exit('Missing inputs: '+', '.join(missing)+'\nSee README.md')
data={k:rows(inp/v) for k,v in files.items()}; effects=data['effects']; issues=[]; entries=[]
if len(effects)!=12:issues.append('Expected 12 matched source/scenario records')
keys=[(r['source'],r['scenario']) for r in effects]
if len(keys)!=len(set(keys)):issues.append('Duplicate source/scenario matched rows')
for r in effects:
 s=r['source'];sc=r['scenario'];ow=float(r['observation_weighted_delta_mae']);se=float(r['station_equal_delta_mae']);lo=float(r['ci_low']);hi=float(r['ci_high']);
 entries.append({'source':s,'scenario':sc,'matched_targets':int(r['matched_targets']),'stations':int(r['stations']),'observation_weighted_delta':ow,'station_equal_delta':se,'station_equal_ci_low':lo,'station_equal_ci_high':hi,'ci_excludes_zero':lo>0 or hi<0,'different_estimands':True})
 if not lo<=hi:issues.append('Invalid CI '+s+' '+sc)
with (out/'matched_estimands_audit.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
sensitivity=[]
for r in data['four_sensitivity']:
 if r.get('rule') in ('all','target_abs_le_p999','target_abs_le_p99'):
  sensitivity.append({'source':r['source'],'scenario':r['scenario'],'rule':r['rule'],'delta':float(r['observation_weighted_delta']),'retained':r.get('retained_fraction','')})
for r in data['mh_sensitivity']:
 q=float(r['target_abs_quantile']);rule={1.0:'all',.999:'target_abs_le_p999',.99:'target_abs_le_p99'}.get(q)
 if rule:sensitivity.append({'source':r['source'],'scenario':r['scenario'],'rule':rule,'delta':float(r['observation_weighted_delta_mae']),'retained':''})
with (out/'sensitivity_harmonized_labels.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['source','scenario','rule','delta','retained']);w.writeheader();w.writerows(sensitivity)
summary=[]
for key in sorted(set((r['source'],r['scenario']) for r in sensitivity)):
 subset={r['rule']:r['delta'] for r in sensitivity if (r['source'],r['scenario'])==key}
 if len(subset)!=3:issues.append('Missing sensitivity thresholds '+str(key))
 summary.append({'source':key[0],'scenario':key[1],**subset,'same_sign_all_thresholds':all(v>0 for v in subset.values()) or all(v<0 for v in subset.values())})
with (out/'sensitivity_summary.csv').open('w',newline='',encoding='utf-8') as f:
 fields=['source','scenario','all','target_abs_le_p999','target_abs_le_p99','same_sign_all_thresholds'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(summary)
manifest={v:hashlib.sha256((inp/v).read_bytes()).hexdigest() for v in files.values()}
report={'status':'DESCRIPTIVE_EVIDENCE_AUDIT_COMPLETE' if not issues else 'INPUT_OR_INTEGRITY_WARNINGS','issues':issues,'sources':sorted(set(r['source'] for r in effects)),'matched_comparisons':len(entries),'unseen_source_rows':len(data['unseen']),'sensitivity_comparisons':len(summary),'input_sha256':manifest,'protocol_harmonized':False,'reason':'Original four-state and Maharashtra experiments used different pipelines and evaluation eligibility; summary relabeling does not harmonize experiments.','inferential_warning':'Observation-weighted point estimates and station-equal confidence intervals have different estimands.','source_quality_unverified':['manual monitoring schedule','telemetry sign/datum and sentinel definitions'],'outside_scope_not_executed':['IMD rainfall linkage','GEC-2015 resource estimation'],'decision':'FREEZE_DESCRIPTIVE_ONLY_OR_RUN_NEW_COMMON_PROTOCOL','recommended_scope':'Source-specific evidence on simulated observation gaps and unseen-station forecasting, without causal or state-ranking claims.'}
(out/'final_gate_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('AUDIT COMPLETE:',out);print('Status:',report['status']);print('Protocol harmonized:',report['protocol_harmonized']);print('Issues:',len(issues))
