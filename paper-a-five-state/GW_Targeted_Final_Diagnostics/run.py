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


# Bounded diagnostic: frozen model definition, no new model selection.
rows=[]; yrrows=[]; identity=[]; discrepancies=[]
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
 Xtr,ytr,_,_=sets['train']; Xca,yca,_,_=sets['calibration'];Xte,yte,ste,mte=sets['test']
 if min(len(Xtr),len(Xca),len(Xte))<30:continue
 model=fit_ridge(Xtr,ytr)
 pred=predict(model,Xte); target=np.asarray(yte,dtype=float); ae=np.abs(target-pred)
 station_arr=np.asarray(ste); year=np.asarray(mte)//12
 threshold=float(np.quantile(np.abs(target),.99))
 mask=np.abs(target)<=threshold
 for subset,selected in [('all',np.ones(len(target),dtype=bool)),('target_abs_le_p99',mask)]:
  rows.append(dict(source=source,subset=subset,targets=int(selected.sum()),stations=len(set(station_arr[selected])),mae=float(ae[selected].mean()),p99_abs_target=threshold,max_abs_target=float(np.abs(target[selected]).max()),max_abs_prediction=float(np.abs(pred[selected]).max()),station_equal_mae=float(np.mean([ae[selected & (station_arr==s)].mean() for s in set(station_arr[selected])]))))
 for y in (2024,2025):
  ym=year==y
  if not ym.any():continue
  ym99=ym & mask
  yrrows.append(dict(source=source,year=y,targets=int(ym.sum()),stations=len(set(station_arr[ym])),mae=float(ae[ym].mean()),mae_trimmed_global_p99=float(ae[ym99].mean()) if ym99.any() else None,median_abs_target=float(np.median(np.abs(target[ym]))),p99_abs_target=float(np.quantile(np.abs(target[ym]),.99)),median_abs_error=float(np.median(ae[ym])),p99_abs_error=float(np.quantile(ae[ym],.99))))
 # 2024-2025 common-station comparison (paired station means, not same-month targets)
 if source=='MH_telemetry':
  by={y:{} for y in (2024,2025)}
  for y in (2024,2025):
   for s in set(station_arr[year==y]):
    sm=(year==y)&(station_arr==s)
    by[y][s]=float(ae[sm].mean())
  common=set(by[2024])&set(by[2025]);only24=set(by[2024])-common;only25=set(by[2025])-common
  discrepancies.append(dict(source=source,stations_2024=len(by[2024]),stations_2025=len(by[2025]),common_stations=len(common),only_2024=len(only24),only_2025=len(only25),paired_station_equal_mae_2024=float(np.mean([by[2024][s] for s in common])) if common else None,paired_station_equal_mae_2025=float(np.mean([by[2025][s] for s in common])) if common else None,paired_station_equal_change=float(np.mean([by[2025][s]-by[2024][s] for s in common])) if common else None))
 print('DIAGNOSTIC',source,len(target),flush=True)
write('extreme_error_diagnostics.csv',rows,list(rows[0]))
write('year_distribution_diagnostics.csv',yrrows,list(yrrows[0]))
write('maharashtra_station_composition.csv',discrepancies,list(discrepancies[0]))
# Reconcile against frozen aggregate metrics; do not overwrite them.
reference=R/'GW_Common_Unseen_Station'/'outputs'/'common_unseen_station_metrics.csv'
checks=[]
if reference.is_file():
 with reference.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   if row.get('status')!='COMPUTED':continue
   got=next((r for r in rows if r['source']==row['source'] and r['subset']=='all'),None)
   if got:
    diff=got['mae']-float(row['mae'])
    checks.append(dict(source=row['source'],reconstructed_mae=got['mae'],frozen_mae=float(row['mae']),difference=diff,pass_tolerance=abs(diff)<1e-8))
 write('frozen_metric_reconciliation.csv',checks,list(checks[0]) if checks else ['source'])
status='DIAGNOSTIC_COMPLETE' if len(rows)==12 and len(yrrows)==12 and (not checks or all(c['pass_tolerance'] for c in checks)) else 'REVIEW_REQUIRED'
report={'status':status,'source_count':len(rows)//2,'years_evaluated':len(yrrows),'frozen_reconciliation':checks,'source_hashes':hashes,'limitations':['Target-only trimming is not an official data-quality correction','Raw telemetry sign/datum and candidate sentinels remain unauthenticated','Yearly station composition differences do not prove temporal drift','No causal conclusions or cross-state rankings','This is a bounded diagnostic; original experimental outputs are not overwritten']}
(OUT/'targeted_diagnostic_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(status,OUT)
