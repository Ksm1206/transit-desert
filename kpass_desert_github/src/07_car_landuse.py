import pandas as pd, numpy as np
SH={'서울':'서울특별시','부산':'부산광역시','대구':'대구광역시','인천':'인천광역시','광주':'광주광역시','대전':'대전광역시','울산':'울산광역시','세종':'세종특별자치시','경기':'경기도','강원':'강원도','충북':'충청북도','충남':'충청남도','전북':'전라북도','전남':'전라남도','경북':'경상북도','경남':'경상남도','제주':'제주특별자치도'}
m=pd.read_csv('data/sgg_master_v3.csv'); keys=set(zip(m.sido,m.sgg))
def fix(s,g):
    s=SH.get(s,s)
    if s=='세종특별자치시': g='세종시'
    if (s,g)==('충청북도','청원군'): g='청주시'
    if g.endswith('(계)'): g=g[:-3]
    if (s,g) in keys: return s,g
    # "포항시 남구" / "창원시 의창구" 형태 → 상위 시
    if ' ' in g: g=g.split(' ')[0]
    return s,g
# --- cars
c=pd.read_csv('work/car2020.csv',skiprows=1)
c.columns=['sido','sgg','kind','use','unit']+[f'm{i}' for i in range(1,13)]
c=c[(c.kind=='승용')&(c.sgg!='계')]
c[['sido','sgg']]=[fix(a,b) for a,b in zip(c.sido,c.sgg)]
car=c.pivot_table(index=['sido','sgg'],columns='use',values='m12',aggfunc='sum').reset_index()
car=car.rename(columns={'자가용':'car_private2020','계':'car_all2020','영업용':'car_biz2020'})[['sido','sgg','car_private2020','car_all2020','car_biz2020']]
print('car unmatched',[k for k in zip(car.sido,car.sgg) if k not in keys])
# --- land
l=pd.read_csv('work/land2020.csv',skiprows=1); l.columns=['sido','sgg','jimok','item','unit','v']
l=l[(l.item=='면적')&(l.jimok.isin(['계','대']))&(l.sido!='전국')&(l.sgg!=l.sido)]
l=l[~l.sgg.str.contains(r'^.+시.+구$',regex=True)|l.sgg.str.endswith('(계)')]
l[['sido','sgg']]=[fix(a,b) for a,b in zip(l.sido,l.sgg)]
land=l.pivot_table(index=['sido','sgg'],columns='jimok',values='v',aggfunc='sum').reset_index().rename(columns={'계':'area_m2','대':'area_dae_m2'})
print('land unmatched',[k for k in zip(land.sido,land.sgg) if k not in keys])
m=m.merge(car,on=['sido','sgg'],how='left').merge(land,on=['sido','sgg'],how='left')
print('missing car',m[m.car_private2020.isna()][['sido','sgg']].values.tolist())
print('missing land',m[m.area_m2.isna()][['sido','sgg']].values.tolist())
print('car total private',m.car_private2020.sum(),' all',m.car_all2020.sum(),' (전국 승용 19,860,955)')
print('area km2 total',(m.area_m2.sum()/1e6).round(1),' (전국 100,412.6)')
m['area_km2']=m.area_m2/1e6; m['area_dae_km2']=m.area_dae_m2/1e6
m['pop_density']=m.pop2020/m.area_km2; m['pop_density_dae']=m.pop2020/m.area_dae_km2
m['car_per_1k']=m.car_private2020/m.pop2020*1000; m['car_per_hh']=m.car_private2020/m.hh2020
m['biz_car_ratio']=m.car_biz2020/m.car_all2020*100
m.round(4).to_csv('data/sgg_master_v4.csv',index=False,encoding='utf-8-sig')
print(m[['pop_density','pop_density_dae','car_per_1k','car_per_hh','biz_car_ratio']].describe().round(2).to_string())
print(m.sort_values('biz_car_ratio',ascending=False)[['sido','sgg','biz_car_ratio']].head(6).to_string())
print(m[['commute_kpass_share','pop_density','pop_density_dae','car_per_1k','car_per_hh']].corr(method='spearman').round(2).iloc[0])
