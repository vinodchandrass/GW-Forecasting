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

# Frozen, disjoint station cohorts: train 70%, calibration 15%, test 15%.
# Training target years 2022-2023; calibration and test target years 2024-2025.
# Historical station measurements at times strictly before the target are allowed.
import sys
results=[];diagnostics=[];hashes_expected={
 'four_state_station_month_sha256':'ecc20c22fa0b52b4ab8295856b35121d0a62bcfdbf138fbbf7e6a757f16f85de'}
if hashes[str(F)] != hashes_expected['four_state_station_month_sha256']:
 raise SystemExit('BLOCKED: Four-state station-month input hash changed')

def cohort(source,sta):
 v=ident(source,sta,'2026-10','unseen-cohort-v1')
 return 'train' if v<.70 else ('calibration' if v<.85 else 'test')

def feature(values,target):
 hist=[m for m in range(target-6,target) if m in values]
 if not hist:return None
 latest=max(hist);v=values[latest]
 # Lagged station readings are permitted, never target/future values.
 return [v, float(target-latest),math.sin(2*math.pi*(target%12)/12),math.cos(2*math.pi*(target%12)/12)]

def fit_ridge(X,y,alpha=10.0):
 X=np.asarray(X,dtype=float);y=np.asarray(y,dtype=float)
 mu=X.mean(axis=0);sd=X.std(axis=0);sd=np.where(sd<1e-10,1,sd)
 Z=(X-mu)/sd; ym=y.mean();
 A=Z.T@Z+alpha*np.eye(Z.shape[1]);coef=np.linalg.solve(A,Z.T@(y-ym))
 return mu,sd,ym,coef

def predict(model,X):
 mu,sd,ym,coef=model
 return ((np.asarray(X,dtype=float)-mu)/sd)@coef+ym

for source in sorted({s for s,_ in series}):
 sets={k:([],[],[],[]) for k in ('train','calibration','test')}
 stations={k:set() for k in sets}
 for (src,sta),values in series.items():
  if src!=source:continue
  group=cohort(src,sta)
  for target in sorted(values):
   yr=target//12
   if group=='train' and not (2022<=yr<=2023):continue
   if group!='train' and not (2024<=yr<=2025):continue
   f=feature(values,target)
   if f is None:continue
   x,y,ids,months=sets[group]
   x.append(f);y.append(values[target]);ids.append(sta);months.append(target)
   stations[group].add(sta)
 (Xtr,ytr,_,_)=sets['train'];(Xca,yca,_,_)=sets['calibration'];(Xte,yte,ste,mte)=sets['test']
 if len(Xtr)<30 or len(Xca)<30 or len(Xte)<30:
  results.append(dict(source=source,status='INSUFFICIENT_ELIGIBLE_TARGETS',train_targets=len(Xtr),calibration_targets=len(Xca),test_targets=len(Xte),train_stations=len(stations['train']),calibration_stations=len(stations['calibration']),test_stations=len(stations['test'])))
  continue
 model=fit_ridge(Xtr,ytr)
 cal_pred=predict(model,Xca);test_pred=predict(model,Xte)
 residuals=np.abs(np.asarray(yca)-cal_pred)
 # Split-conformal finite-sample order statistic, conditional on exchangeability;
 # cluster dependence means marginal 90% guarantee is NOT asserted.
 qindex=min(len(residuals)-1,math.ceil((len(residuals)+1)*.90)-1)
 q=float(np.partition(residuals,qindex)[qindex])
 ae=np.abs(np.asarray(yte)-test_pred)
 by_station=collections.defaultdict(list)
 for sta,err in zip(ste,ae):by_station[sta].append(float(err))
 results.append(dict(source=source,status='COMPUTED',train_targets=len(Xtr),calibration_targets=len(Xca),test_targets=len(Xte),train_stations=len(stations['train']),calibration_stations=len(stations['calibration']),test_stations=len(stations['test']),mae=float(ae.mean()),station_equal_mae=float(np.mean([np.mean(v) for v in by_station.values()])),interval_halfwidth=q,empirical_90pct_coverage=float(np.mean(ae<=q)),nominal_coverage=.9))
 for yr in (2024,2025):
  mask=np.array([m//12==yr for m in mte]);
  if mask.any():diagnostics.append(dict(source=source,year=yr,test_targets=int(mask.sum()),mae=float(ae[mask].mean()),coverage=float(np.mean(ae[mask]<=q))))
 print(source,'train',len(Xtr),'cal',len(Xca),'test',len(Xte),flush=True)
fields=['source','status','train_targets','calibration_targets','test_targets','train_stations','calibration_stations','test_stations','mae','station_equal_mae','interval_halfwidth','empirical_90pct_coverage','nominal_coverage']
write('common_unseen_station_metrics.csv',results,fields)
write('common_unseen_year_diagnostics.csv',diagnostics,['source','year','test_targets','mae','coverage'])
report={'status':'COMMON_UNSEEN_STATION_COMPUTED','input_sha256':hashes,'protocol':{'cohort_assignment':'SHA256(source|station|2026-10|unseen-cohort-v1), 70/15/15 train/calibration/test','train_targets':'2022-2023','calibration_and_test_targets':'2024-2025','features':'latest available value within previous 6 calendar months, lag in months, calendar-month sine/cosine','regression':'pooled ridge with standardized features, alpha=10, intercept unpenalized','calibration':'90% absolute residual quantile on disjoint calibration stations; no formal coverage guarantee under dependence or temporal drift','station_identity':'source-specific; telemetry station names may collide, unresolved official station identity','exclusions':'candidate sentinels from prior common-protocol run; official dictionary unavailable'},'n_sources':len(results),'n_computed':sum(r['status']=='COMPUTED' for r in results),'limitations':['Common computation does not imply equivalent agency measurements or monitoring schedules','No official sign/datum validation','No official missingness schedule, rainfall or GEC-2015 data','Calibration and test stations disjoint, but calibration/test time windows coincide; exchangeability is unverified','Only source-specific evaluation; no state ranking or universal interval guarantee']}
(OUT/'common_unseen_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('COMPLETE:',OUT,'computed sources',report['n_computed'],flush=True)
