import pandas as pd, numpy as np, sys, re
sys.path.insert(0,'src'); from utils_regions import tag, norm
m=pd.read_csv('data/sgg_master_v4.csv'); keys=set(zip(m.sido,m.sgg))
# ---------- age 2020
a=pd.read_csv('work/age2020.csv',skiprows=1); a.columns=['region','age','item','unit','val']
a['region']=a.region.map(norm)
blk=(a.region!=a.region.shift()).cumsum(); names=a.groupby(blk).region.first(); t=dict(zip(names.index,tag(names.tolist())))
a['sido']=blk.map(lambda b:t[b][0]); a['level']=blk.map(lambda b:t[b][1])
sj=(a.level=='sido')&(a.region=='세종특별자치시')
if not ((a.level=='sgg')&(a.sido=='세종특별자치시')).any(): a.loc[sj,'level']='sgg'; a.loc[sj,'region']='세종시'
a=a[a.level=='sgg'].drop_duplicates(['sido','region','age']); a['n']=a.age.str.extract(r'(\d+)').astype(float)
tot=a[a.age=='계'].set_index(['sido','region']).val
old=a[a.n>=65].groupby(['sido','region']).val.sum(); old75=a[a.n>=75].groupby(['sido','region']).val.sum()
teen=a[(a.n>=10)&(a.n<=19)].groupby(['sido','region']).val.sum()
age=pd.DataFrame({'pop_chk':tot,'old_ratio':old/tot*100,'old75_ratio':old75/tot*100,'teen_ratio':teen/tot*100}).reset_index().rename(columns={'region':'sgg'})
# ---------- metro stations
s=pd.read_excel('data_raw/metro_stations_20260630.xlsx')
POST2020=['수도권 경량도시철도 신림선','대경선','진접선']   # 2021년 이후 개통 노선
s['post2020']=s.노선명.isin(POST2020)
SH={'충남':'충청남도','경북':'경상북도','대구':'대구광역시','경남':'경상남도','충북':'충청북도','전남':'전라남도','전북':'전라북도','서울시':'서울특별시','서울':'서울특별시','인천시':'인천광역시','부산시':'부산광역시','대구시':'대구광역시','대전시':'대전광역시','광주시':'광주광역시','울산시':'울산광역시','경기':'경기도'}
def op_sido(r):
    for k,v in [('대구','대구광역시'),('부산','부산광역시'),('대전','대전광역시'),('광주','광주광역시'),('인천','인천광역시'),('김해','경상남도'),('울산','울산광역시')]:
        if k in str(r.노선명)+str(r.운영기관명): return v
    return None
def locate(r):
    tok=str(r.역사도로명주소).split()
    sd=SH.get(tok[0],norm(tok[0]))
    if sd in ['서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시','울산광역시','경기도','강원도','충청북도','충청남도','전라북도','전라남도','경상북도','경상남도','세종특별자치시','제주특별자치도','강원특별자치도']:
        sd=norm(sd); g=tok[1]
    else:
        sd=op_sido(r); g=tok[0]
    if (sd,g) not in keys and len(tok)>2 and (sd,tok[2]) in keys: g=tok[2]
    g={'춘춘시':'춘천시','시승시':'시흥시','남양주':'남양주시'}.get(g,g)
    if g.startswith('수성구'): g='수성구'
    if (sd,g)==('인천광역시','남구'): g='미추홀구'
    if g=='경산시': sd='경상북도'
    if g in ('인창동','수택동'): sd,g='경기도','구리시'
    return pd.Series({'sido':sd,'sgg':g})
s[['sido','sgg']]=s.apply(locate,axis=1)
bad=s[[k not in keys for k in zip(s.sido,s.sgg)]]
print('unmatched stations',len(bad)); print(bad[['역사명','노선명','역사도로명주소','sido','sgg']].head(30).to_string())
s.to_csv('data/metro_stations_located.csv',index=False,encoding='utf-8-sig')
uniq=lambda x: x.drop_duplicates(['sido','sgg','역사명'])     # 환승역 중복 제거
st20=uniq(s[~s.post2020]).groupby(['sido','sgg']).size().rename('rail_st_2020')
st26=uniq(s).groupby(['sido','sgg']).size().rename('rail_st_2026')
m=m.merge(age,on=['sido','sgg'],how='left').merge(st20.reset_index(),on=['sido','sgg'],how='left').merge(st26.reset_index(),on=['sido','sgg'],how='left')
m[['rail_st_2020','rail_st_2026']]=m[['rail_st_2020','rail_st_2026']].fillna(0)
m['has_rail_2020']=(m.rail_st_2020>0).astype(int)
m['rail_st_per_100k']=m.rail_st_2020/m.pop2020*1e5
print('age missing',m.old_ratio.isna().sum(),' pop check diff',(m.pop_chk-m.pop2020).abs().max())
print('rail sgg 2020',m.has_rail_2020.sum(),' stations',m.rail_st_2020.sum())
m.drop(columns='pop_chk').round(4).to_csv('data/sgg_master_v5.csv',index=False,encoding='utf-8-sig')
print(m[['old_ratio','teen_ratio']].describe().round(1).to_string())
print(m.groupby('has_rail_2020').commute_kpass_share.median())
