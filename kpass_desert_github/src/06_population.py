import pandas as pd, numpy as np, sys
sys.path.insert(0,'src'); from utils_regions import tag, norm
def load(path, valcol, skip):
    d=pd.read_excel(path,'데이터',header=None).iloc[skip:]
    names=d[0].astype(str).str.replace('　','').str.strip().map(norm)
    t=tag(names.tolist())
    return pd.DataFrame({'name':names.values,'sido':[x[0] for x in t],'level':[x[1] for x in t],'val':pd.to_numeric(d[valcol],errors='coerce').values})
def to_sgg(x,col):
    s=x[x.level=='sgg'][['sido','name','val']].rename(columns={'name':'sgg','val':col})
    sj=x[(x.level=='sido')&(x.name=='세종특별자치시')]
    if len(sj) and not ((s.sido=='세종특별자치시').any()):
        s=pd.concat([s,pd.DataFrame({'sido':['세종특별자치시'],'sgg':['세종시'],col:sj.val.values[:1]})])
    return s
pop=load('data_raw/kosis_DT_1B04006_2020_total.xlsx',2,2); hh=load('data_raw/kosis_DT_1B040B3_2020.xlsx',12,1)
m=pd.read_csv('data/sgg_master_v2.csv')
m2=m.merge(to_sgg(pop,'pop2020'),on=['sido','sgg'],how='left').merge(to_sgg(hh,'hh2020'),on=['sido','sgg'],how='left')
print('missing pop',m2[m2.pop2020.isna()][['sido','sgg']].values.tolist())
print('missing hh',m2[m2.hh2020.isna()][['sido','sgg']].values.tolist())
# sanity: sido sums
print('pop total',m2.pop2020.sum(), ' 전국',pop[pop.level=='nat'].val.iloc[0])
m2.to_csv('data/sgg_master_v3.csv',index=False,encoding='utf-8-sig')
print(m2[['pop2020','hh2020']].describe().round(0))
