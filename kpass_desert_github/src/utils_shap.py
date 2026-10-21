import numpy as np, itertools, math
def exact_shap(predict, X, B):
    """정확한(interventional) Shapley 값: 모든 특성 부분집합 열거, 배경 B로 결측 특성 평균.
    shap 라이브러리의 Exact/Interventional 방식과 동일한 정의."""
    X=np.asarray(X,float); B=np.asarray(B,float); n,M=X.shape; nb=len(B)
    subsets=list(itertools.product([0,1],repeat=M)); idx={s:i for i,s in enumerate(subsets)}
    V=np.zeros((len(subsets),n))
    for s in subsets:
        mask=np.array(s,bool)
        Z=np.repeat(B[None,:,:],n,axis=0)               # n x nb x M
        Z[:,:,mask]=X[:,None,mask]
        V[idx[s]]=predict(Z.reshape(-1,M)).reshape(n,nb).mean(1)
    phi=np.zeros((n,M))
    for i in range(M):
        for s in subsets:
            if s[i]: continue
            k=sum(s); w=math.factorial(k)*math.factorial(M-k-1)/math.factorial(M)
            s1=list(s); s1[i]=1
            phi[:,i]+=w*(V[idx[tuple(s1)]]-V[idx[s]])
    base=V[idx[tuple([0]*M)]].mean()
    return phi, base, V[idx[tuple([1]*M)]]
