import csv,hashlib,json,math,random,collections,datetime,pathlib,statistics
import numpy as np
R=pathlib.Path(__file__).resolve().parent.parent; OUT=pathlib.Path(__file__).resolve().parent/'outputs';OUT.mkdir(exist_ok=True)
F=R/'GW_State4_Experiments'/'outputs'/'station_month_provisional.csv'
SOURCES={'MH_manual':('manual.csv','Well ID','Date of Monitoring','Water Level, m bgl','State Name '),'MH_telemetry':('telemetry.csv','Station','Data Acquisition Time','Groundwater Level Telemetry 6 Hourly (meter)','State')}
HASH={'manual.csv':'5003c9030b34df310f0bdd0527df022b9b0e73aa780b5bbacc88cc49d1be0eb6','telemetry.csv':'b4bf746c09eae07b7998328a5699ddc22989f7ec829509919b60421e7a366822'}
SENT={-9999,-999.999,-999.99,-999.9,-999,999,9999,958}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(name,rows,cols):
 with (OUT/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def monthnum(s):
 y,m=map(int,s[:7].split('-'));return y*12+m-1
def ident(source,station,month,kind):
 s=f'{source}|{station}|{month}|{kind}'.encode();return int(hashlib.sha256(s).hexdigest()[:15],16)/16**15
series=collections.defaultdict(dict); source_counts=collections.Counter(); hashes={}
if not F.is_file():raise SystemExit('MISSING four-state monthly input: '+str(F))
hashes[str(F)]=digest(F)
with F.open(encoding='utf-8-sig',newline='') as f:
 for row in csv.DictReader(f):
  source=row['source'].strip();station=row['station'].strip();mo=row['month'].strip()
  if source not in {'KA_manual','PB_telemetry','RJ_telemetry','TN_telemetry'} or not station or not ('2021-01'<=mo<='2025-12'):continue
  try:v=float(row['value_mean'])
  except (ValueError,TypeError):continue
  if math.isfinite(v):series[source,station][monthnum(mo)]=v;source_counts[source]+=1
for source,(file,sc,dc,vc,stc) in SOURCES.items():
 p=R/'Maharashtra_GW_Download'/'downloads'/file
 if not p.is_file():raise SystemExit('MISSING Maharashtra CSV: '+str(p))
 hashes[str(p)]=digest(p)
 if hashes[str(p)]!=HASH[file]:raise SystemExit('BLOCKED: Maharashtra raw-file SHA256 mismatch '+str(p))
 enc='utf-8-sig'
 try:
  with p.open(encoding=enc) as f:
   for line in f:pass
 except UnicodeDecodeError:enc='cp1252'
 acc=collections.defaultdict(lambda:[0,0.0]);bad=0
 with p.open(encoding=enc,newline='') as f:
  for row in csv.DictReader(f):
   if row.get(stc,'').strip().lower()!='maharashtra':continue
   try:
    date=datetime.datetime.strptime(row[dc].strip().split(' ')[0],'%d-%m-%Y')
    if not 2021<=date.year<=2025:continue
    v=float(row[vc]);sta=row[sc].strip()
    if not sta or not math.isfinite(v) or v in SENT:bad+=1;continue
   except (ValueError,TypeError,KeyError,AttributeError):bad+=1;continue
   k=(sta,date.year*12+date.month-1);acc[k][0]+=1;acc[k][1]+=v
 for (sta,m),(n,total) in acc.items():series[source,sta][m]=total/n;source_counts[source]+=1
 print(source,'station-month cells',len(acc),'excluded/invalid',bad,flush=True)
if len({s for s,_ in series})!=6:raise SystemExit('BLOCKED: Expected all six source IDs, found '+str(sorted({s for s,_ in series})))
# All sources: same rolling 6-calendar-month most recent observed carry-forward; no target imputation.
# Synthetic intervention affects only history, never target; same target pairs per scenario.
records=[];summaries=[];sensitivity=[];rng=random.Random(20261021)
for source in sorted({s for s,_ in series}):
 per=collections.defaultdict(list)
 for (src,sta),values in series.items():
  if src!=source:continue
  for target in sorted(m for m in values if 2024*12<=m<=2025*12+11):
   hist=[m for m in range(target-6,target) if m in values]
   if not hist:continue
   base=values[max(hist)];truth=values[target]
   for scenario in ('random20','block3'):
    if scenario=='random20': eligible=[m for m in hist if ident(src,sta,f'{m//12:04d}-{m%12+1:02d}','random20')>=.20]
    else:
     # One deterministic 3-month intervention window per station and target; fixed independently of readings.
     start=target-1-int(ident(src,sta,f'{target//12:04d}-{target%12+1:02d}','block3')*4)
     eligible=[m for m in hist if not start<=m<start+3]
    if not eligible:continue
    masked=values[max(eligible)];delta=abs(truth-masked)-abs(truth-base)
    per[scenario].append((sta,truth,delta,abs(truth-base),abs(truth-masked)))
 for scenario,rows in per.items():
  if not rows:continue
  bysta=collections.defaultdict(list)
  for sta,t,d,b,a in rows:bysta[sta].append(d)
  stationmeans=[statistics.mean(ds) for ds in bysta.values()]
  boot=[]
  for i in range(1000):boot.append(statistics.mean(rng.choices(stationmeans,k=len(stationmeans))))
  lo,hi=np.quantile(boot,[.025,.975]);effect=statistics.mean(x[2] for x in rows)
  summaries.append(dict(source=source,scenario=scenario,matched_targets=len(rows),stations=len(bysta),observation_weighted_delta_mae=effect,station_equal_delta_mae=statistics.mean(stationmeans),station_equal_ci_low=float(lo),station_equal_ci_high=float(hi)))
  for q in (1,.999,.99):
   threshold=float(np.quantile([abs(x[1]) for x in rows],q));subset=[x for x in rows if abs(x[1])<=threshold]
   sensitivity.append(dict(source=source,scenario=scenario,target_abs_quantile=q,threshold=threshold,matched_targets=len(subset),observation_weighted_delta_mae=statistics.mean(x[2] for x in subset)))
 print(source,'completed',flush=True)
write('common_matched_effects.csv',summaries,['source','scenario','matched_targets','stations','observation_weighted_delta_mae','station_equal_delta_mae','station_equal_ci_low','station_equal_ci_high'])
write('common_sensitivity.csv',sensitivity,['source','scenario','target_abs_quantile','threshold','matched_targets','observation_weighted_delta_mae'])
report={'status':'COMMON_PROTOCOL_EXPERIMENT_COMPLETE','protocol':'one-step latest-observed carry-forward within preceding six calendar months; deterministic history-only random20 or 3-month window masking; 2024-2025 targets; same-target baseline comparison; station-equal bootstrap 1000; target-absolute trimming','source_station_month_cells':dict(source_counts),'input_sha256':hashes,'n_source_scenario_rows':len(summaries),'n_sensitivity_rows':len(sensitivity),'limitations':['Different underlying monitoring sources, temporal coverage and agency conventions remain; common computation does not equal equivalent data quality','Manual seasonal months are not missing scheduled measurements','Synthetic masking is not real-world causal monitoring failure','Candidate telemetry sentinel/sign conventions not officially authenticated','Unseen-station model harmonization not performed in this package','IMD rainfall and GEC-2015 effects not evaluated']}
(OUT/'common_protocol_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('COMPLETE:',OUT,'comparisons',len(summaries),flush=True)
