"""공간 자기상관: 시군구 인접(경계 공유, 섬 지역은 최근접 1곳) → Moran's I, LISA(999회 순열)"""
import pandas as pd, numpy as np, pickle
from collections import defaultdict
polys=pd.read_pickle('work/polys2020.pkl')
A=pd.read_csv('out/shap_all229.csv'); keys=list(zip(A.sido,A.sgg)); idx={k:i for i,k in enumerate(keys)}; n=len(keys)
vert=defaultdict(set); cx=np.zeros(n); cy=np.zeros(n); cnt=np.zeros(n)
for sd,sg,cd,v in polys:
    i=idx[(sd,sg)]
    for p in np.round(v,4): vert[(p[0],p[1])].add(i)
    cx[i]+=v[:,0].sum(); cy[i]+=v[:,1].sum(); cnt[i]+=len(v)
cx/=cnt; cy/=cnt
pair=defaultdict(int)
for s in vert.values():
    if len(s)>1:
        s=sorted(s)
        for a in range(len(s)):
            for b in range(a+1,len(s)): pair[(s[a],s[b])]+=1
W=np.zeros((n,n))
for (a,b),c in pair.items():
    if c>=2: W[a,b]=W[b,a]=1
iso=np.where(W.sum(1)==0)[0]
for i in iso:
    d=np.hypot(cx-cx[i],cy-cy[i]); d[i]=np.inf; j=d.argmin(); W[i,j]=W[j,i]=1
print('neighbors mean',W.sum(1).mean().round(2),'isolated filled',[keys[i] for i in iso])
Wr=W/W.sum(1,keepdims=True)
y=A.all_kpass_share.values; z=(y-y.mean())/y.std()
I=(z@Wr@z)/(z@z)
rng=np.random.default_rng(0); perm=np.array([(zp:=rng.permutation(z))@Wr@zp/(zp@zp) for _ in range(999)])
pI=(np.sum(perm>=I)+1)/1000; EI=-1/(n-1)
print(f"Moran's I={I:.4f}, E[I]={EI:.4f}, z={(I-perm.mean())/perm.std():.2f}, p={pI:.3f}")
lag=Wr@z; Ii=z*lag
sims=np.zeros((999,n))
for k in range(999):
    for i in range(n):
        nb=W[i]>0; m_=nb.sum()
        pick=rng.choice(np.delete(z,i),m_,replace=False); sims[k,i]=z[i]*pick.mean()
p_loc=(np.sum(np.abs(sims)>=np.abs(Ii),axis=0)+1)/1000
q=np.where((z>0)&(lag>0),'HH',np.where((z<0)&(lag<0),'LL',np.where((z>0)&(lag<0),'HL','LH')))
lab=np.where(p_loc<0.05,q,'ns')
R=A[['sido','sgg','all_kpass_share','grade']].assign(lisa=lab,p=p_loc)
R.to_csv('out/lisa.csv',index=False,encoding='utf-8-sig')
print(R.lisa.value_counts().to_dict())
ll=R[R.lisa=='LL']; print('LL by sido',ll.sido.value_counts().to_dict()); print('LL desert share',(ll.grade=='교통사막').mean().round(2))
D=pd.read_csv('out/desert_clusters.csv')[['sido','sgg','cluster']]
print(ll.merge(D,on=['sido','sgg'],how='left').cluster.value_counts(dropna=False).to_dict())
pd.to_pickle({'I':I,'p':pI,'z':(I-perm.mean())/perm.std()},'out/moran.pkl')
