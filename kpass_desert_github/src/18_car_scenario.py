import pandas as pd, numpy as np, pickle
b=pd.read_pickle('out/best_model.pkl'); mdl,F=b['model'],b['F']
x=pd.read_csv('out/carbon_detail.csv'); A=pd.read_csv('out/shap_all229.csv')
x=x.drop(columns=[c for c in F if c in x.columns]).merge(A[['sido','sgg']+F],on=['sido','sgg'])
eff=pd.read_pickle('out/efficiency.pkl'); car0=eff['자가용']['zero']
KG_PER_KM=2.18/12; SPEED=35; DAYS=250
d=x[x.cluster.notna()].copy()
X1=d[F].copy(); X1['car_per_1k']=np.minimum(X1.car_per_1k,car0)
d['pred0']=mdl.predict(d[F]); d['pred1']=mdl.predict(X1); d['dshare']=d.pred1-d.pred0
d['shift']=d.dshare/100*d.all_total
d['km_per_car_commuter']=(d.commute_car_avg_min/60*SPEED)*2*DAYS
d['co2_saved_t']=d['shift']*d.km_per_car_commuter*KG_PER_KM/1000
s=d.groupby('group').agg(지역수=('sgg','size'),평균분담률변화pp=('dshare','mean'),전환인원=('shift','sum'),CO2감축t=('co2_saved_t','sum'))
print('안정점 car/1k =',round(car0,1)); print(s.round(2).to_string()); print('합계',s[['전환인원','CO2감축t']].sum().round(0).to_dict())
s.to_csv('out/scenario_car.csv',encoding='utf-8-sig')
