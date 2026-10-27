import csv,json,hashlib,math,collections,pathlib,datetime,random
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT.parent/'Maharashtra_GW_Download'/'downloads'
PREV=ROOT.parent/'Maharashtra_Experiment'/'outputs'
OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
SOURCES={'MH_manual':('manual.csv','Well ID','Date of Monitoring','Water Level, m bgl','State Name '),'MH_telemetry':('telemetry.csv','Station','Data Acquisition Time','Groundwater Level Telemetry 6 Hourly (meter)','State')}
EXPECTED={'manual.csv':'5003c9030b34df310f0bdd0527df022b9b0e73aa780b5bbacc88cc49d1be0eb6','telemetry.csv':'b4bf746c09eae07b7998328a5699ddc22989f7ec829509919b60421e7a366822'}
SENTINELS={-9999,-999.999,-999.99,-999.9,-999,999,9999,958}
def save(name,rows,cols):
 with (OUT/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4194304),b''):h.update(chunk)
 return h.hexdigest()
def ymback(ym,n):
 y,m=map(int,ym.split('-'));i=y*12+m-1-n;return f'{i//12:04d}-{i%12+1:02d}'
def features(ym,values):
 # Only past months, no target or future information
 v=[values.get(ymback(ym,i)) for i in range(1,13)]
 if sum(x is not None for x in v)<3:return None
 last=next((x for x in v if x is not None),None)
 mean=sum(x for x in v if x is not None)/sum(x is not None for x in v)
 y,m=map(int,ym.split('-'))
 return [last,mean,sum(x is not None for x in v),math.sin(2*math.pi*m/12),math.cos(2*math.pi*m/12)]
def quantile(a,q):return float(np.quantile(np.asarray(a,dtype=float),q)) if a else None
report={'status':'COMPUTED_PROVISIONAL','note':'Source-specific experiments; telemetry sign/datum and manual observation schedule remain unauthenticated. No IMD or GEC evaluation.','sources':{},'encoding':'utf-8-sig with cp1252 fallback only if strict UTF-8 fails; decoding replacement is not used.'}
monthly={}
for sid,(filename,stationcol,datecol,valuecol,statecol) in SOURCES.items():
 path=DATA/filename
 if not path.exists():raise SystemExit('Missing '+str(path))
 if digest(path)!=EXPECTED[filename]:raise SystemExit('SHA256 mismatch '+filename)
 counts=collections.Counter();acc=collections.defaultdict(lambda:[0,0.0]);encoding='utf-8-sig'
 # Encoding detection on entire CSV to avoid silently replacing station IDs
 try:
  with path.open('r',encoding=encoding,newline='') as f:
   for _ in f:pass
 except UnicodeDecodeError:encoding='cp1252'
 with path.open('r',encoding=encoding,newline='') as f:
  reader=csv.DictReader(f)
  for row in reader:
   counts['raw_rows']+=1
   if row.get(statecol,'').strip().casefold()!='maharashtra':counts['other_state']+=1;continue
   try:d=datetime.datetime.strptime(row[datecol].strip().split(' ')[0],'%d-%m-%Y')
   except (ValueError,AttributeError):counts['bad_date']+=1;continue
   if not 2021<=d.year<=2025:continue
   counts['period_rows']+=1
   station=row[stationcol].strip()
   if not station:counts['empty_station']+=1;continue
   try:v=float(row[valuecol].strip())
   except (ValueError,TypeError):counts['nonnumeric']+=1;continue
   if not math.isfinite(v) or v in SENTINELS:counts['excluded_nonfinite_or_candidate_sentinel']+=1;continue
   key=(station,d.strftime('%Y-%m'));acc[key][0]+=1;acc[key][1]+=v
 monthly[sid]={k:s/n for k,(n,s) in acc.items()}
 report['sources'][sid]={'encoding':encoding,'counts':dict(counts),'station_months':len(acc),'stations':len({k[0] for k in acc})}
 print(sid,'monthly cells',len(acc),'encoding',encoding,flush=True)
# Matched scenario comparisons using original frozen Maharashtra predictions
p=PREV/'forecast_predictions.csv'
if not p.exists():raise SystemExit('Missing '+str(p)+'; retain earlier outputs')
group=collections.defaultdict(dict);nrows=0
with p.open(encoding='utf-8-sig',newline='') as f:
 for r in csv.DictReader(f):
  key=(r['source'],r['station'],r['month']);sc=r['scenario']
  if sc in group[key]:raise SystemExit('Duplicate prediction key '+str((key,sc)))
  group[key][sc]=(float(r['truth']),float(r['absolute_error']));nrows+=1
matched=[];boots=[];sensitivity=[]
for sid in SOURCES:
 for scenario in ['random20','block3']:
  pairs=[]
  for (src,station,month),d in group.items():
   if src!=sid or scenario not in d or 'none' not in d:continue
   truth0,e0=d['none'];truth1,e1=d[scenario]
   if not math.isclose(truth0,truth1,rel_tol=1e-10,abs_tol=1e-10):raise SystemExit('Target mismatch')
   pairs.append((station,truth0,e1-e0))
  if not pairs:continue
  stations=collections.defaultdict(list)
  for st,truth,delta in pairs:stations[st].append(delta)
  stationmeans=np.array([np.mean(v) for v in stations.values()]);rng=np.random.default_rng(20261021)
  samples=rng.choice(stationmeans,size=(2000,len(stationmeans)),replace=True).mean(axis=1)
  boots.append({'source':sid,'scenario':scenario,'stations':len(stations),'station_equal_delta_mae':float(stationmeans.mean()),'ci_low':float(np.quantile(samples,.025)),'ci_high':float(np.quantile(samples,.975))})
  matched.append({'source':sid,'scenario':scenario,'matched_targets':len(pairs),'stations':len(stations),'observation_weighted_delta_mae':float(np.mean([v[2] for v in pairs]))})
  for trim in [1,.999,.99]:
   threshold=quantile([abs(x[1]) for x in pairs],trim)
   subset=[x[2] for x in pairs if abs(x[1])<=threshold]
   sensitivity.append({'source':sid,'scenario':scenario,'target_abs_quantile':trim,'threshold':threshold,'matched_targets':len(subset),'observation_weighted_delta_mae':float(np.mean(subset))})
save('matched_metrics.csv',matched,['source','scenario','matched_targets','stations','observation_weighted_delta_mae'])
save('station_bootstrap.csv',boots,['source','scenario','stations','station_equal_delta_mae','ci_low','ci_high'])
save('extreme_value_sensitivity.csv',sensitivity,['source','scenario','target_abs_quantile','threshold','matched_targets','observation_weighted_delta_mae'])
# Unseen-station holdout: fixed hash split; strictly prior-month features; 2022-23 training, 2023H2 calibration, 2024-25 test
unseen=[];stationdiag=[]
for sid,vals in monthly.items():
 byst=collections.defaultdict(dict)
 for (st,ym),v in vals.items():byst[st][ym]=v
 def holdout(st):return int(hashlib.sha256((sid+'|'+st).encode()).hexdigest()[:8],16)%5==0
 Xtrain=[];ytrain=[];Xcal=[];ycal=[];Xtest=[];ytest=[];stest=[]
 for st,series in byst.items():
  for ym,y in series.items():
   x=features(ym,series)
   if x is None:continue
   if holdout(st):
    if '2024-01'<=ym<='2025-12':Xtest.append(x);ytest.append(y);stest.append(st)
   elif '2022-01'<=ym<='2023-06':Xtrain.append(x);ytrain.append(y)
   elif '2023-07'<=ym<='2023-12':Xcal.append(x);ycal.append(y)
 if min(len(Xtrain),len(Xcal),len(Xtest))<30:
  unseen.append({'source':sid,'status':'INSUFFICIENT_ELIGIBLE_ROWS','train':len(Xtrain),'calibration':len(Xcal),'test':len(Xtest)});continue
 model=make_pipeline(StandardScaler(),Ridge(alpha=10.0));model.fit(Xtrain,ytrain)
 calerr=np.abs(np.array(ycal)-model.predict(Xcal));q=float(np.quantile(calerr,.9))
 pred=model.predict(Xtest);err=np.abs(np.array(ytest)-pred)
 unseen.append({'source':sid,'status':'COMPUTED','train':len(Xtrain),'calibration':len(Xcal),'test':len(Xtest),'test_stations':len(set(stest)),'mae':float(err.mean()),'interval_halfwidth':q,'empirical_coverage':float(np.mean(err<=q)),'note':'Calibration and test stations disjoint; exchangeability not guaranteed'})
 for st in sorted(set(stest)):
  idx=[i for i,s in enumerate(stest) if s==st];stationdiag.append({'source':sid,'station':st,'test_n':len(idx),'test_mae':float(err[idx].mean())})
save('unseen_station_metrics.csv',unseen,['source','status','train','calibration','test','test_stations','mae','interval_halfwidth','empirical_coverage','note'])
save('unseen_station_diagnostics.csv',stationdiag,['source','station','test_n','test_mae'])
report.update({'matched_metrics':matched,'bootstrap':boots,'unseen_station':unseen,'original_prediction_rows':nrows,'limitations':['Source-specific monthly averages; manual missing months are not necessarily monitoring failures','Telemetry sign and official sentinels not authenticated','Holdout split fixed by station hash; no state-level generalization claim','Calibration is heuristic, not guaranteed 90% coverage','Target trimming only; input anomalies remain','No IMD rainfall or GEC-2015 data supplied']})
(OUT/'completion_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('COMPLETE: outputs at',OUT)
