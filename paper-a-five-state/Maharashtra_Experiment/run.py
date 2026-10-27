import csv, json, hashlib, math, random, statistics, collections, pathlib, datetime
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT.parent/'Maharashtra_GW_Download'/'downloads'
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
SOURCES={
 'MH_manual':('manual.csv','Well ID','Date of Monitoring','Water Level, m bgl','State Name ','Agency'),
 'MH_telemetry':('telemetry.csv','Station','Data Acquisition Time','Groundwater Level Telemetry 6 Hourly (meter)','State','Agency')}
EXPECTED={'manual.csv':'5003c9030b34df310f0bdd0527df022b9b0e73aa780b5bbacc88cc49d1be0eb6','telemetry.csv':'b4bf746c09eae07b7998328a5699ddc22989f7ec829509919b60421e7a366822'}
SENTINELS={-9999,-999.999,-999.99,-999.9,-999,999,9999,958}
def writecsv(name, rows, fields):
 with (OUT/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def evaluate(sid,monthly):
 rng=random.Random(20261021); grouped=collections.defaultdict(dict)
 for (st,ym),v in monthly.items():grouped[st][ym]=v
 coverage=[]; predictions=[]; metrics=[]
 for st,vals in grouped.items():
  keys=sorted(vals); coverage.append({'source':sid,'station':st,'observed_months':len(keys),'first_month':keys[0],'last_month':keys[-1],'test_months':sum(k>='2024-01' for k in keys)})
  for ym in keys:
   if ym<'2024-01':continue
   year,month=map(int,ym.split('-'));prev=(datetime.date(year,month,1)-datetime.timedelta(days=1)).strftime('%Y-%m')
   if prev not in vals:continue
   truth=vals[ym]; hist=vals[prev]
   # deterministic 20% simulated missingness in the preceding six-month history
   history=[]
   for back in range(1,7):
    y=year;m=month-back
    while m<=0:y-=1;m+=12
    k=f'{y:04d}-{m:02d}';history.append((k,vals.get(k)))
   for scenario in ('none','random20','block3'):
    arr=[v for _,v in history]
    if scenario=='random20':arr=[None if rng.random()<0.2 else v for v in arr]
    if scenario=='block3':arr[:3]=[None]*3
    pred=next((v for v in arr if v is not None),None)
    if pred is not None:predictions.append({'source':sid,'station':st,'month':ym,'scenario':scenario,'truth':truth,'prediction':pred,'absolute_error':abs(truth-pred)})
 for sc in ('none','random20','block3'):
  r=[x for x in predictions if x['scenario']==sc]
  metrics.append({'source':sid,'scenario':sc,'predictions':len(r),'stations':len({x['station'] for x in r}),'mae':sum(x['absolute_error'] for x in r)/len(r) if r else None})
 return coverage,predictions,metrics
report={'status':'COMPUTED_PROVISIONAL','method':'Source-specific monthly arithmetic means; rolling prior-month carry-forward, 2024-2025 evaluation; synthetic 20% and three-month gaps. Not a replication of earlier four-state experiments.','sources':{},'limitations':['No authenticated monitoring schedule or sentinel dictionary','No official telemetry sign convention verified','Monthly telemetry averages are exploratory','No IMD rainfall/GEC-2015 evaluation','Missingness predictions have differing eligible targets; not causal matched effects','No unseen-station trained model in this lightweight run']}
allcoverage=[];allpred=[];allmetrics=[]
for sid,(filename,stationcol,datecol,valuecol,statecol,agencycol) in SOURCES.items():
 path=DATA/filename
 if not path.exists():raise SystemExit(f'MISSING FILE: {path}')
 actual=hashfile(path)
 if actual!=EXPECTED[filename]:raise SystemExit(f'SHA256 MISMATCH {filename}: {actual}')
 counts=collections.Counter(); bymonth=collections.defaultdict(lambda:[0,0.0]); statecounts=collections.Counter(); agencies=collections.Counter(); freq=collections.Counter(); dates=collections.Counter()
 with path.open(encoding='utf-8-sig', errors='replace',newline='') as f:
  reader=csv.DictReader(f); required=(stationcol,datecol,valuecol,statecol,agencycol)
  if any(x not in reader.fieldnames for x in required):raise SystemExit(f'BAD HEADER {sid}: {reader.fieldnames}')
  for row in reader:
   counts['total']+=1
   try:d=datetime.datetime.strptime(row[datecol].strip().split(' ')[0],'%d-%m-%Y')
   except (ValueError,AttributeError):counts['bad_date']+=1;continue
   if not 2021<=d.year<=2025:continue
   counts['period_rows']+=1;state=row[statecol].strip();statecounts[state]+=1;agencies[row[agencycol].strip()]+=1
   if state.casefold()!='maharashtra':counts['non_maharashtra']+=1;continue
   st=row[stationcol].strip()
   if not st:counts['missing_station']+=1;continue
   try:v=float(row[valuecol].strip())
   except (ValueError,TypeError):counts['nonnumeric']+=1;continue
   if not math.isfinite(v):counts['nonfinite']+=1;continue
   if v in SENTINELS:counts['candidate_sentinel']+=1;continue
   k=(st,d.strftime('%Y-%m'));bymonth[k][0]+=1;bymonth[k][1]+=v
   freq[d.strftime('%Y')]+=1;dates[d.strftime('%Y-%m')]+=1
 monthly={k:s/n for k,(n,s) in bymonth.items()}
 coverage,preds,metrics=evaluate(sid,monthly)
 allcoverage+=coverage;allpred+=preds;allmetrics+=metrics
 report['sources'][sid]={'sha256':actual,'counts':dict(counts),'states':dict(statecounts.most_common(10)),'agencies':dict(agencies.most_common(10)),'year_rows':dict(freq),'month_rows':dict(sorted(dates.items())),'station_month_cells':len(monthly),'stations':len(coverage),'forecast_metrics':metrics,'date_min':min(dates) if dates else None,'date_max':max(dates) if dates else None}
 print(sid,'rows',counts['period_rows'],'stations',len(coverage),'months',len(monthly),flush=True)
writecsv('station_coverage.csv',allcoverage,['source','station','observed_months','first_month','last_month','test_months'])
writecsv('forecast_predictions.csv',allpred,['source','station','month','scenario','truth','prediction','absolute_error'])
writecsv('forecast_metrics.csv',allmetrics,['source','scenario','predictions','stations','mae'])
(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'outputs':str(OUT),'forecast_rows':len(allpred)},indent=2))

