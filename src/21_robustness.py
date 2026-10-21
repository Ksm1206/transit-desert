"""단점 보완 분석: (1) 환급의 탄소 효율 배분 (2) 교통 사막 기준 민감도 (3) 같은 밀도 내 격차·정책변수 비중"""
import pandas as pd, numpy as np, pickle, sys
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
A=pd.read_csv('out/shap_all229.csv'); m=pd.read_csv('data/sgg_master_v7.csv'); C=pd.read_csv('out/carbon_detail.csv')
F=pd.read_csv('data/final_vars.csv')['var'].tolist()
x=A[['sido','sgg','all_kpass_share','grade']+['shap_'+f for f in F]].merge(
  C[['sido','sgg','pop2020','refund_won','car_commuters','co2_t','kp_users','all_total']],on=['sido','sgg'])
out={}
# (1) 탄소 효율: 환급 1억원당 승용차 통근자, 혜택 대비 승용차 통근자 비중
g=x.groupby('grade').agg(refund=('refund_won','sum'),car=('car_commuters','sum'),pop=('pop2020','sum'),co2=('co2_t','sum'))
g['refund_pct']=g.refund/g.refund.sum()*100; g['car_pct']=g.car/g.car.sum()*100
g['car_per_100m_won']=g.car/(g.refund/1e8)
print(g.round(1).to_string()); g.to_csv('out/carbon_efficiency.csv',encoding='utf-8-sig')
# (2) 민감도
base=pd.read_csv('out/desert_clusters.csv')[['sido','sgg','cluster']]
rows=[]
for t in [8,10,12,15]:
    d=x[x.all_kpass_share<t]
    r={'기준(%)':t,'지역수':len(d),'인구비중':d.pop2020.sum()/x.pop2020.sum()*100,'승용차통근비중':d.car_commuters.sum()/x.car_commuters.sum()*100,
       '혜택비중':d.refund_won.sum()/x.refund_won.sum()*100,
       '1인당혜택배율(양호/사막)':(x[x.all_kpass_share>=20].refund_won.sum()/x[x.all_kpass_share>=20].pop2020.sum())/(d.refund_won.sum()/d.pop2020.sum())}
    km=KMeans(3,n_init=50,random_state=42).fit(d[['shap_'+f for f in F]].values)
    dd=d[['sido','sgg']].assign(c=km.labels_).merge(base,on=['sido','sgg'])
    r['기준10%와 공통지역 유형일치(ARI)']=adjusted_rand_score(dd.cluster,dd.c) if len(dd) else np.nan
    # 유형 구성: 각 군집의 평균 밀도 순서로 크기
    prof=d.assign(c=km.labels_).merge(m[['sido','sgg','pop_density_dae','car_per_1k','old_ratio']],on=['sido','sgg']).groupby('c').agg(n=('sgg','size'),dens=('pop_density_dae','mean'),old=('old_ratio','mean')).sort_values('dens')
    r['유형크기(저밀→고밀)']='/'.join(map(str,prof.n.tolist())); r['유형 고령비율']='/'.join(f'{v:.0f}' for v in prof.old)
    rows.append(r)
S=pd.DataFrame(rows); print(S.round(2).to_string()); S.to_csv('out/sensitivity_threshold.csv',index=False,encoding='utf-8-sig')
# (3) 같은 밀도 내 격차
y=x.merge(m[['sido','sgg','pop_density_dae']],on=['sido','sgg'])
y['dens_q']=pd.qcut(y.pop_density_dae,5,labels=['1(저)','2','3','4','5(고)'])
q=y.groupby('dens_q',observed=True).all_kpass_share.agg(['count','min','median','max']); q['max/min']=q['max']/q['min']
print(q.round(1).to_string()); q.to_csv('out/within_density_gap.csv',encoding='utf-8-sig')
# 밀도 통제 후 설명력: 밀도만 vs 전체 (교차검증)
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, RepeatedKFold
tr=m[m.stops_missing==0]; cv=RepeatedKFold(n_splits=5,n_repeats=5,random_state=42)
gb=lambda: GradientBoostingRegressor(learning_rate=0.03,max_depth=3,n_estimators=300,subsample=0.8,random_state=42)
r_d=cross_val_score(gb(),tr[['log_pop_density_dae']],tr.all_kpass_share,cv=cv,scoring='r2').mean()
r_a=cross_val_score(gb(),tr[F],tr.all_kpass_share,cv=cv,scoring='r2').mean()
print('R2 density only',round(r_d,3),' all',round(r_a,3))
# 교통 사막 내 SHAP 비중(정책변수)
D=x[x.grade=='교통사막']; imp=D[['shap_'+f for f in F]].abs().mean(); imp=imp/imp.sum()*100
print('사막 내 SHAP 비중',imp.round(1).to_dict())
pd.to_pickle({'r2_density':r_d,'r2_all':r_a,'desert_imp':imp},'out/robust_extra.pkl')
