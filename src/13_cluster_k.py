import pandas as pd, numpy as np, pickle, sys
sys.path.insert(0,'src'); from utils_shap import exact_shap
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
b=pd.read_pickle('out/best_model.pkl'); mdl,F=b['model'],b['F']
m=pd.read_csv('data/sgg_master_v7.csv')
tr=m[m.stops_missing==0]; X=tr[F].values; rng=np.random.default_rng(0); B=X[rng.choice(len(X),100,replace=False)]
# 정류장 결측 9곳: 정류장 변수만 비결측 '군' 지역 중앙값으로 대체(해당 변수 SHAP 기여 2.7%로 영향 미미)
gun=tr[tr.sgg.str.endswith('군')].log_stops_dae.median()
mm=m.copy(); mm['stops_imputed']=mm.stops_missing; mm.loc[mm.stops_missing==1,'log_stops_dae']=gun
phi,base,fx=exact_shap(lambda a: mdl.predict(pd.DataFrame(a,columns=F)),mm[F].values,B)
S=pd.DataFrame(phi,columns=F); S['base']=base; S['pred']=fx
A=pd.concat([mm[['sido','sgg','all_kpass_share','stops_imputed']+F].reset_index(drop=True),S.add_prefix('shap_')],axis=1)
A['grade']=pd.cut(A.all_kpass_share,[-1,10,20,101],labels=['교통사막','주의','양호'])
print(A.grade.value_counts().to_string())
A.to_csv('out/shap_all229.csv',index=False,encoding='utf-8-sig')
D=A[A.grade=='교통사막'].reset_index(drop=True); Z=D[['shap_'+f for f in F]].values
rows=[]
for k in range(2,8):
    km=KMeans(k,n_init=50,random_state=42).fit(Z)
    rows.append({'k':k,'WSS':km.inertia_,'silhouette':silhouette_score(Z,km.labels_),'DB':davies_bouldin_score(Z,km.labels_)})
K=pd.DataFrame(rows); print(K.round(3).to_string()); K.to_csv('out/k_selection.csv',index=False)
