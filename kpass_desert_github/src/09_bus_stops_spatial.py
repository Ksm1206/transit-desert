import json, re, numpy as np, pandas as pd
from matplotlib.path import Path
m=pd.read_csv('data/sgg_master_v5.csv'); keys=set(zip(m.sido,m.sgg))
g=json.load(open('data_raw/HangJeongDong_ver20201001.geojson'))
polys=[]  # (sido,sgg,adm_cd,Path,bbox)
for f in g['features']:
    pr=f['properties']; sd=pr['sidonm']; sg=pr['sggnm']
    mm=re.match(r'^(.+시)(.+구)$',sg)
    if mm and (sd,sg) not in keys: sg=mm.group(1)
    if (sd,sg) not in keys: print('nomatch',sd,sg); continue
    geom=f['geometry']; parts=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    for poly in parts:
        ring=np.array(poly[0])   # outer ring (holes rare in admin dongs; ignored)
        polys.append((sd,sg,pr['adm_cd2'],Path(ring),ring[:,0].min(),ring[:,0].max(),ring[:,1].min(),ring[:,1].max()))
print('polygons',len(polys),' sgg covered',len({(p[0],p[1]) for p in polys}))
import pickle; pd.to_pickle([(p[0],p[1],p[2],p[3].vertices) for p in polys],'work/polys2020.pkl')
# ---- assign bus stops
s=pd.read_csv('data_raw/bus_stops_20251031.csv',encoding='cp949')
lat,lon=s['위도'].values.copy(),s['경도'].values.copy()
sw=lat>90; lat[sw],lon[sw]=s['경도'].values[sw],s['위도'].values[sw]   # 위경도 뒤바뀐 행 교정
print('swapped',sw.sum(),' nan',np.isnan(lat).sum())
pts=np.c_[lon,lat]; res_sd=np.array([None]*len(s),dtype=object); res_sg=res_sd.copy()
for sd,sg,cd,path,x0,x1,y0,y1 in polys:
    idx=np.where((pts[:,0]>=x0)&(pts[:,0]<=x1)&(pts[:,1]>=y0)&(pts[:,1]<=y1)&(res_sd==None))[0]
    if len(idx)==0: continue
    inside=path.contains_points(pts[idx])
    res_sd[idx[inside]]=sd; res_sg[idx[inside]]=sg
s['sido_sp']=res_sd; s['sgg_sp']=res_sg
print('unassigned',pd.isna(s.sgg_sp).sum())
s.to_csv('data/bus_stops_located.csv',index=False,encoding='utf-8-sig')
cnt=s.dropna(subset=['sgg_sp']).groupby(['sido_sp','sgg_sp']).size().rename('bus_stops').reset_index().rename(columns={'sido_sp':'sido','sgg_sp':'sgg'})
m=m.merge(cnt,on=['sido','sgg'],how='left'); m['bus_stops']=m.bus_stops.fillna(0)
m['stops_per_1k']=m.bus_stops/m.pop2020*1000; m['stops_per_km2']=m.bus_stops/m.area_km2
m.round(4).to_csv('data/sgg_master_v6.csv',index=False,encoding='utf-8-sig')
print(m.sort_values('stops_per_1k')[['sido','sgg','bus_stops','pop2020','stops_per_1k']].head(25).round(3).to_string())
print(m.stops_per_1k.describe().round(2))
# TAGO 미연계로 정류장이 비정상적으로 적은 비광역 시군(인구 1천명당 1개 미만) 결측 표시
m=pd.read_csv('data/sgg_master_v6.csv'); metro=m.sido.str.endswith(('특별시','광역시'))
m['stops_missing']=((~metro)&(m.stops_per_1k<1)).astype(int); m.to_csv('data/sgg_master_v6.csv',index=False,encoding='utf-8-sig')
print('stops_missing',m.stops_missing.sum())
