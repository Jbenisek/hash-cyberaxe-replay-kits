import json,collections,glob
agg=collections.defaultdict(lambda:{'runs':0,'df':[],'fail':collections.Counter(),'ev':[0,0,0,0],'n':0,'dd':[], 'em':[]})
ks=[]
for f in sorted(glob.glob('drop_k[0-9]*.json')):
    R=json.load(open(f)); ks.append(f)
    base={r['att']:r for r in R if r['drop']=='none'}
    for r in R:
        a=agg[r['drop']]; a['runs']+=1
        if r['status']=='ok':
            a['df'].append(r['DF']); a['n']+=r['npts']; a['em'].append(r['EM'])
            for i in range(4): a['ev'][i]+=r['ev_F_R0_R1_R2'][i]
            b=base.get(r['att'])
            if b and b['status']=='ok': a['dd'].append(r['DF']-b['DF'])
        else: a['fail'][r['status']]+=1
print(ks)
for d,a in agg.items():
    print(d,'runs',a['runs'],'ok',len(a['df']),'DF',(min(a['df']),max(a['df'])) if a['df'] else None,'fail',dict(a['fail']),'events F,R0,R1,R2',a['ev'],'of',a['n'],'dDF',(min(a['dd']),max(a['dd'])) if a['dd'] else None)
