import pandas as pd, numpy as np, pickle, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
plt.rcParams.update({'font.family':'Noto Sans CJK KR','axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#9a9994','axes.labelcolor':'#52514e','xtick.color':'#52514e','ytick.color':'#52514e','figure.facecolor':'#fcfcfb','axes.facecolor':'#fcfcfb','savefig.dpi':200})
BLUE,ORANGE,AQUA,RED,GRAY,INK='#2a78d6','#eb6834','#1baf7a','#e34948','#c9c8c2','#0b0b0b'
KOR={'log_pop_density_dae':'인구밀도(대지 기준)','log_stops_dae':'정류장 밀도','rail_st_per_100k':'도시철도역(인구 10만당)','car_per_1k':'자가용 승용차(1천명당)','out_sido_pct':'타 시도 통근·통학 비율','old_ratio':'고령인구 비율','teen_ratio':'청소년 비율'}
F=pd.read_csv('data/final_vars.csv')['var'].tolist()
# 1 model compare
mc=pd.read_csv('out/model_compare.csv')
fig,ax=plt.subplots(figsize=(6,3))
col=[BLUE if r==mc['CV R2'].max() else GRAY for r in mc['CV R2']]
ax.barh(mc.Model,mc['CV R2'],color=col,height=0.5,xerr=mc['R2 sd'],error_kw=dict(ecolor='#52514e',lw=1,capsize=3))
for i,r in mc.iterrows(): ax.text(r['CV R2']+r['R2 sd']+0.005,i,f"R² {r['CV R2']:.3f}  RMSE {r['RMSE']:.2f}",va='center',fontsize=9,color=INK)
ax.set_xlim(0.8,1.0); ax.set_xlabel('5-Fold×5회 반복 교차검증 R²'); ax.invert_yaxis()
ax.set_title('모델 성능 비교',loc='left',fontsize=12,color=INK); fig.tight_layout(); fig.savefig('fig/01_model_compare.png'); plt.close()
# 2 SHAP beeswarm
A=pd.read_csv('out/shap_all229.csv')
imp=A[['shap_'+f for f in F]].abs().mean().rename(lambda s:s[5:]).sort_values()
cmap=LinearSegmentedColormap.from_list('d',[BLUE,'#d6d5cf',RED])
fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.2),gridspec_kw={'width_ratios':[1.6,1]})
rng=np.random.default_rng(0)
for j,f in enumerate(imp.index):
    s=A['shap_'+f].values; v=A[f].values; vn=(pd.Series(v).rank(pct=True)).values
    # beeswarm-ish jitter by density
    order=np.argsort(s); y=np.zeros(len(s)); bins=np.round(s/0.35)
    for b in np.unique(bins):
        idx=np.where(bins==b)[0]; y[idx]=(np.arange(len(idx))-len(idx)/2)*0.018
    a1.scatter(s,j+np.clip(y,-0.38,0.38),c=vn,cmap=cmap,s=10,edgecolors='none')
a1.axvline(0,color='#9a9994',lw=1); a1.set_yticks(range(len(imp))); a1.set_yticklabels([KOR[f] for f in imp.index])
a1.set_xlabel('SHAP 값 (대중교통 분담률에 대한 기여, %p)'); a1.set_title('변수별 SHAP 분포  (빨강=값 높음, 파랑=값 낮음)',loc='left',fontsize=11,color=INK)
pct=imp/imp.sum()*100
a2.barh([KOR[f] for f in imp.index],pct,color=BLUE,height=0.55)
for i,p in enumerate(pct): a2.text(p+0.8,i,f'{p:.1f}%',va='center',fontsize=9,color=INK)
a2.set_xlim(0,65); a2.set_xlabel('평균 |SHAP| 비중 (%)'); a2.set_yticklabels([]); a2.set_title('변수 중요도',loc='left',fontsize=11,color=INK)
fig.tight_layout(); fig.savefig('fig/02_shap_summary.png'); plt.close()
# 3 k selection
K=pd.read_csv('out/k_selection.csv')
fig,(a1,a2)=plt.subplots(1,2,figsize=(8,3))
for ax,col_,lab in [(a1,'WSS','군집 내 제곱합(WSS)'),(a2,'silhouette','실루엣 계수')]:
    ax.plot(K.k,K[col_],color=BLUE,lw=2,marker='o',ms=6)
    ax.plot(3,K.set_index('k').loc[3,col_],'o',color=ORANGE,ms=10,zorder=3)
    ax.axvline(3,color=ORANGE,lw=1,ls='--'); ax.set_xlabel('군집 수 k'); ax.set_title(lab,loc='left',fontsize=11,color=INK)
fig.tight_layout(); fig.savefig('fig/03_k_selection.png'); plt.close()
# 4 map
import pickle as pk
polys=pd.read_pickle('work/polys2020.pkl')
D=pd.read_csv('out/desert_clusters.csv'); NAME={2:'① 농산어촌 이동고립형',0:'② 도농복합 자동차의존형',1:'③ 지방도시 자동차고착형'}
CC={2:ORANGE,0:BLUE,1:AQUA}
key={(r.sido,r.sgg):r.cluster for r in D.itertuples()}
grade={(r.sido,r.sgg):r.grade for r in A.itertuples()}
fig,ax=plt.subplots(figsize=(6.5,7.5))
verts=[p[3] for p in polys]; cols=[]
for sd,sg,cd,v in polys:
    k=key.get((sd,sg)); cols.append(CC[k] if k is not None else ('#e4e3de' if grade.get((sd,sg))=='주의' else '#f1f0ec'))
ax.add_collection(PolyCollection(verts,facecolors=cols,edgecolors='#fcfcfb',linewidths=0.15))
ax.set_xlim(124.5,130.0); ax.set_ylim(33.1,38.7); ax.set_aspect(1.2); ax.axis('off')
from matplotlib.patches import Patch
cnt=D.cluster.value_counts()
h=[Patch(color=CC[k],label=f'{NAME[k]} ({cnt[k]}곳)') for k in [2,0,1]]+[Patch(color='#e4e3de',label='주의 (분담률 10~20%)'),Patch(color='#f1f0ec',label='양호 (20% 이상)')]
ax.legend(handles=h,loc='lower right',frameon=False,fontsize=9)
ax.set_title('교통 사막(K-패스 대상 분담률 10% 미만) 유형 지도',loc='left',fontsize=12,color=INK)
fig.tight_layout(); fig.savefig('fig/04_cluster_map.png'); plt.close()
print('done')
