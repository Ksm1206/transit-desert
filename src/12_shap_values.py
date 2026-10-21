import pandas as pd, numpy as np, pickle, sys, time
sys.path.insert(0,'src'); from utils_shap import exact_shap
b=pd.read_pickle('out/best_model.pkl'); mdl,F=b['model'],b['F']
m=pd.read_csv('data/sgg_master_v7.csv'); d=m[m.stops_missing==0].reset_index(drop=True)
X=d[F].values; rng=np.random.default_rng(0); B=X[rng.choice(len(X),100,replace=False)]
t=time.time(); phi,base,fx=exact_shap(lambda a: mdl.predict(pd.DataFrame(a,columns=F)),X,B); print('sec',round(time.time()-t,1))
# 검증: 효율성(additivity) — base + sum(phi) == f(x)
print('additivity max err',np.abs(base+phi.sum(1)-fx).max(), ' f(x) vs model.predict',np.abs(fx-mdl.predict(d[F])).max())
S=pd.DataFrame(phi,columns=F); S.insert(0,'sgg',d.sgg); S.insert(0,'sido',d.sido); S['base']=base
S.to_csv('out/shap_values.csv',index=False,encoding='utf-8-sig')
imp=pd.Series(np.abs(phi).mean(0),index=F).sort_values(ascending=False)
print((imp/imp.sum()*100).round(1).to_string())
# 방향: SHAP과 원값의 상관
for f in F: print(f, 'corr(value,shap)=',round(np.corrcoef(d[f],S[f])[0,1],2))
