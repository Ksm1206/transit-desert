import pandas as pd, numpy as np, json, pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.model_selection import RepeatedKFold, cross_validate, GridSearchCV, KFold
m=pd.read_csv('data/sgg_master_v7.csv'); F=pd.read_csv('data/final_vars.csv')['var'].tolist()
d=m[m.stops_missing==0].reset_index(drop=True); X=d[F]; y=d['all_kpass_share']
print('n=',len(d),'features',F)
cv=RepeatedKFold(n_splits=5,n_repeats=5,random_state=42)
grids={
 'RandomForest':(RandomForestRegressor(random_state=42,n_jobs=-1),{'n_estimators':[300],'max_depth':[None,6],'min_samples_leaf':[1,3]}),
 'GradientBoosting':(GradientBoostingRegressor(random_state=42),{'n_estimators':[300,600],'max_depth':[2,3],'learning_rate':[0.03],'subsample':[0.8]}),
 'ExtraTrees':(ExtraTreesRegressor(random_state=42,n_jobs=-1),{'n_estimators':[300],'max_depth':[None,8],'min_samples_leaf':[1,3]}),
}
rows=[]; best={}
for name,(est,grid) in grids.items():
    gs=GridSearchCV(est,grid,cv=KFold(5,shuffle=True,random_state=0),scoring='r2',n_jobs=-1).fit(X,y)
    r=cross_validate(gs.best_estimator_,X,y,cv=cv,scoring=['r2','neg_root_mean_squared_error','neg_mean_absolute_error'],n_jobs=-1)
    rows.append({'Model':name,'CV R2':r['test_r2'].mean(),'R2 sd':r['test_r2'].std(),'RMSE':-r['test_neg_root_mean_squared_error'].mean(),'MAE':-r['test_neg_mean_absolute_error'].mean(),'params':json.dumps(gs.best_params_)})
    best[name]=gs.best_estimator_.fit(X,y)
res=pd.DataFrame(rows); print(res.round(4).to_string())
res.to_csv('out/model_compare.csv',index=False,encoding='utf-8-sig')
top=res.sort_values('CV R2',ascending=False).iloc[0].Model; print('BEST',top)
pd.to_pickle({'model':best[top],'name':top,'F':F},'out/best_model.pkl')
