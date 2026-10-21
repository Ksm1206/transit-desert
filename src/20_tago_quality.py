"""TAGO 노선·배차간격 제공 현황 진단 ('정보 사막')"""
import pandas as pd
r=pd.read_csv('data_raw/tago/tago_routes.csv',dtype=str); i=pd.read_csv('data_raw/tago/tago_route_info.csv',dtype=str)
i['iv']=pd.to_numeric(i.intervaltime,errors='coerce')
print('노선',len(r),'도시',r.citycode.nunique(),'배차 수집',len(i),'배차값 제공(>0) 비율',round((i.iv>0).mean(),3))
x=i.merge(r[['routeid','cityname']].drop_duplicates('routeid'),on='routeid',how='left')
g=x.groupby('cityname').agg(노선=('routeid','size'),제공비율=('iv',lambda s:(s>0).mean())).sort_values('제공비율')
g.to_csv('out/tago_interval_coverage.csv',encoding='utf-8-sig'); print('제공 0% 도시',(g.제공비율==0).sum())
