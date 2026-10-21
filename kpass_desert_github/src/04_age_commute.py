import pandas as pd, numpy as np, sys
sys.path.insert(0,'src'); from utils_regions import tag
num=lambda s: pd.to_numeric(s.astype(str).str.strip().replace({'-':'0'}),errors='coerce')
# ---- age-specific mode share
a=pd.read_csv('work/DT_1PA2003.csv',skiprows=1); a.columns=['region','sex','age','type','item','unit','val']; a['val']=num(a.val)
blk=(a.region!=a.region.shift()).cumsum(); names=a.groupby(blk).region.first()
t=dict(zip(names.index,tag(names.tolist()))); a['sido']=blk.map(lambda b:t[b][0]); a['level']=blk.map(lambda b:t[b][1])
print(sorted(a.age.unique()))
a=a[a.level=='sgg']
PT=['시내,좌석,마을버스','고속,시외버스','전철,지하철','기차']
old=[x for x in a.age.unique() if x.startswith(('65','70','75','80','85'))]; teen=['12~14세','15~19세']
print('old groups',old)
def share(g):
    tot=g[g.item=='통근·통학 인구(12세 이상)'].val.sum(); pt=g[g.item.isin(PT)].val.sum(); car=g[g.item=='승용차,승합차(벤)'].val.sum()
    return pd.Series({'n':tot,'pt':pt/tot*100 if tot else np.nan,'car':car/tot*100 if tot else np.nan})
res=[]
for lab,ages in [('old',old),('teen',teen)]:
    r=a[a.age.isin(ages)].groupby(['sido','region'],sort=False).apply(share,include_groups=False).add_prefix(lab+'_'); res.append(r)
age=pd.concat(res,axis=1).reset_index().rename(columns={'region':'sgg'})
# ---- OD
o=pd.read_csv('work/DT_1PA2021.csv',skiprows=1); o.columns=['orig','dest','item','unit','val']; o['val']=num(o.val)
ob=(o.orig!=o.orig.shift()).cumsum(); onames=o.groupby(ob).orig.first(); ot=dict(zip(onames.index,tag(onames.tolist())))
o['osido']=ob.map(lambda b:ot[b][0]); o['olevel']=ob.map(lambda b:ot[b][1])
o['blk']=ob; parts=[]
for b,g in o.groupby('blk',sort=False):
    tg=tag(g.dest.tolist()); g=g.copy(); g['dsido']=[x[0] for x in tg]; g['dlevel']=[x[1] for x in tg]; parts.append(g)
o=pd.concat(parts); o=o[o.olevel=='sgg']
rows=[]
for (s,n),g in o.groupby(['osido','orig'],sort=False):
    tot=g[g.dlevel=='nat'].val.sum()
    same=g[(g.dlevel=='sgg')&(g.dsido==s)&(g.dest==n)].val.sum()
    samesido=g[(g.dlevel=='sido')&(g.dest==s)].val.sum()
    rows.append({'sido':s,'sgg':n,'od_total':tot,'within_sgg_pct':same/tot*100,'out_sgg_pct':(tot-same)/tot*100,'out_sido_pct':(tot-samesido)/tot*100})
od=pd.DataFrame(rows)
m=pd.read_csv('data/sgg_mode_share_2020.csv').merge(age,on=['sido','sgg'],how='left').merge(od,on=['sido','sgg'],how='left')
print('rows',len(m),'missing age',m.old_pt.isna().sum(),'missing od',m.od_total.isna().sum())
print('od_total vs all_total max abs diff',(m.od_total-m.all_total).abs().max())
m.round(3).to_csv('data/sgg_master_v1.csv',index=False,encoding='utf-8-sig')
print(m[['old_pt','teen_pt','out_sgg_pct','out_sido_pct']].describe().round(1).to_string())
print(m.sort_values('out_sgg_pct',ascending=False)[['sido','sgg','out_sgg_pct','commute_pt_share']].head(8).to_string())
print(m[['commute_pt_share','old_pt','out_sgg_pct','commute_car_share']].corr().round(2))
