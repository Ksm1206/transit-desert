import pandas as pd, numpy as np
m=pd.read_csv('data/sgg_master_v6.csv')
m['log_pop_density_dae']=np.log(m.pop_density_dae)
m['log_pop_density']=np.log(m.pop_density)
m['log_stops_dae']=np.log(m.bus_stops.clip(lower=1)/m.area_dae_km2)
def vif(X):
    X=(X-X.mean())/X.std(); out={}
    for c in X.columns:
        y=X[c].values; A=np.c_[np.ones(len(X)),X.drop(columns=c).values]
        b,*_=np.linalg.lstsq(A,y,rcond=None); r2=1-((y-A@b)**2).sum()/((y-y.mean())**2).sum(); out[c]=1/(1-r2)
    return pd.Series(out)
d=m[m.stops_missing==0]
# 후보 변수 (부문별)
cand={'log_pop_density':'밀도','log_pop_density_dae':'밀도',
 'stops_per_1k':'공급','stops_per_km2':'공급','log_stops_dae':'공급','rail_st_per_100k':'공급','has_rail_2020':'공급',
 'car_per_1k':'자동차','car_per_hh':'자동차',
 'out_sgg_pct':'이동구조','out_sido_pct':'이동구조','commute_avg_min':'이동구조',
 'old_ratio':'교통약자','old75_ratio':'교통약자','teen_ratio':'교통약자'}
print('후보',len(cand))
# ① 유사 변수 통합: 쌍별 상관
pairs=[('log_pop_density','log_pop_density_dae'),('stops_per_1k','stops_per_km2'),('rail_st_per_100k','has_rail_2020'),('car_per_1k','car_per_hh'),('out_sgg_pct','out_sido_pct'),('old_ratio','old75_ratio')]
for a,b in pairs: print(f'  r({a},{b})={d[a].corr(d[b]):.2f}')
step1=['log_pop_density_dae','stops_per_1k','rail_st_per_100k','car_per_1k','out_sgg_pct','out_sido_pct','commute_avg_min','old_ratio','teen_ratio']
# commute_avg_min, out_sgg_pct: 통근 행태 자체(결과에 가까움) → 역인과 우려 검토
print('VIF step1'); print(vif(d[step1]).round(2).sort_values(ascending=False).to_string())
cur=step1[:]; log=[]
while True:
    v=vif(d[cur]); mx=v.idxmax()
    if v[mx]<=10: break
    log.append((mx,round(v[mx],2))); cur.remove(mx)
print('기계적 VIF 제거',log)
# ② 판단 기반 제거: 통근 행태 변수(평균 통근시간, 관외 통근)는 대중교통 이용의 '결과'일 가능성(역인과) → 제거, 밀도 유지
final=['log_pop_density_dae','log_stops_dae','rail_st_per_100k','car_per_1k','out_sido_pct','old_ratio','teen_ratio']
print('최종 VIF'); fv=vif(d[final]).round(2).sort_values(ascending=False); print(fv.to_string())
sector={k:cand[k] for k in final}
pd.DataFrame({'var':final,'sector':[sector[k] for k in final],'vif':[fv[k] for k in final]}).to_csv('data/final_vars.csv',index=False,encoding='utf-8-sig')
m.to_csv('data/sgg_master_v7.csv',index=False,encoding='utf-8-sig')
