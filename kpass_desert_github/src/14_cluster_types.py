import pandas as pd, numpy as np
from sklearn.cluster import KMeans
A=pd.read_csv('out/shap_all229.csv'); F=pd.read_csv('data/final_vars.csv')['var'].tolist()
m=pd.read_csv('data/sgg_master_v7.csv')
A=A.merge(m[['sido','sgg','pop_density_dae','car_per_1k','rail_st_2020','out_sgg_pct','old_ratio','teen_ratio','pop2020','commute_car_share','old_pt']].rename(columns={'car_per_1k':'raw_car','old_ratio':'raw_old','teen_ratio':'raw_teen'}),on=['sido','sgg'])
D=A[A.grade=='교통사막'].copy(); Z=D[['shap_'+f for f in F]].values
km=KMeans(3,n_init=50,random_state=42).fit(Z); D['cluster']=km.labels_
pd.set_option('display.width',250)
print(D.groupby('cluster')[['shap_'+f for f in F]].mean().round(2).T)
raw=['all_kpass_share','pop_density_dae','raw_car','rail_st_2020','out_sido_pct','raw_old','raw_teen','commute_car_share','out_sgg_pct','pop2020']
print(D.groupby('cluster')[raw].mean().round(1).T)
ref=A[A.grade=='양호'][raw].mean().round(1); print('양호 평균\n',ref)
for c in range(3):
    x=D[D.cluster==c]; print(c,len(x),x.sido.value_counts().head(5).to_dict()); print('   ',(x.sido.str[:2]+' '+x.sgg).tolist()[:40])
D.to_csv('out/desert_clusters.csv',index=False,encoding='utf-8-sig')
