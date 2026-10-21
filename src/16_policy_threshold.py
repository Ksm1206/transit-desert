import pandas as pd, numpy as np
from sklearn.tree import DecisionTreeRegressor, export_text
A=pd.read_csv('out/shap_all229.csv'); m=pd.read_csv('data/sgg_master_v7.csv')
A=A.merge(m[['sido','sgg','pop_density_dae','car_per_1k']].rename(columns={'car_per_1k':'car_raw'}),on=['sido','sgg'])
def segfit(x,y,grid):
    """2개 절단점 연속 세그먼트 회귀(그리드 탐색, 최소 SSE)"""
    best=None
    for i,b1 in enumerate(grid):
        for b2 in grid[i+3:]:
            X=np.c_[np.ones_like(x),x,np.clip(x-b1,0,None),np.clip(x-b2,0,None)]
            c,res,*_=np.linalg.lstsq(X,y,rcond=None); sse=((y-X@c)**2).sum()
            if best is None or sse<best[0]: best=(sse,b1,b2,c)
    sse,b1,b2,c=best; slopes=[c[1],c[1]+c[2],c[1]+c[2]+c[3]]
    # 절단점 없는 선형과 비교 F검정 (Davies 대용)
    X0=np.c_[np.ones_like(x),x]; c0,*_=np.linalg.lstsq(X0,y,rcond=None); sse0=((y-X0@c0)**2).sum()
    n=len(x); F=((sse0-sse)/4)/(sse/(n-6))
    from scipy import stats
    p=1-stats.f.cdf(F,4,n-6)
    return b1,b2,slopes,F,p
out={}
for var,xcol,lab in [('log_pop_density_dae','log_pop_density_dae','밀도'),('car_per_1k','car_per_1k','자가용')]:
    x=A[xcol].values; y=A['shap_'+var].values
    grid=np.quantile(x,np.linspace(0.05,0.95,60))
    b1,b2,sl,F,p=segfit(x,y,grid)
    tr=DecisionTreeRegressor(max_depth=2,min_samples_leaf=15,random_state=0).fit(x.reshape(-1,1),y)
    print('====',lab); print('breakpoints',b1,b2,'slopes',np.round(sl,3),'F',round(F,1),'p',p)
    print(export_text(tr,feature_names=[xcol],decimals=3))
    # zero crossing: smallest x where rolling mean shap >=0 (density) / largest x where >=0 (car)
    o=np.argsort(x); xs=x[o]; ys=pd.Series(y[o]).rolling(15,center=True,min_periods=5).mean().values
    if lab=='밀도': z=xs[np.argmax(ys>=0)]
    else: z=xs[np.where(ys>=0)[0].max()]
    print('zero crossing',z, np.exp(z) if lab=='밀도' else '')
    out[lab]=dict(b1=b1,b2=b2,slopes=sl,F=F,p=p,zero=z)
pd.to_pickle(out,'out/efficiency.pkl')
