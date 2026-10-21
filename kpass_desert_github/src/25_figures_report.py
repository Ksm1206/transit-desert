import pandas as pd, numpy as np, matplotlib, pickle
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator,NullLocator
plt.rcParams.update({'font.family':'Noto Sans CJK KR','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#9a9994','axes.labelcolor':'#52514e','xtick.color':'#52514e','ytick.color':'#52514e','figure.facecolor':'white','axes.facecolor':'white','savefig.dpi':220})
BLUE,ORANGE,AQUA,GRAY,INK,SEC='#2a78d6','#eb6834','#1baf7a','#c9c8c2','#0b0b0b','#52514e'
KOR={'log_pop_density_dae':'인구밀도(대지)','log_stops_dae':'정류장 밀도','rail_st_per_100k':'도시철도역','car_per_1k':'자가용 승용차','out_sido_pct':'타 시도 통근','old_ratio':'고령 비율','teen_ratio':'청소년 비율'}
F=pd.read_csv('data/final_vars.csv')['var'].tolist(); A=pd.read_csv('out/shap_all229.csv')
# ===== Fig A: 역설 (한 장, 낮게)
g=pd.read_csv('out/carbon_refund_by_group.csv',index_col=0); tot=g.sum(); des=g.iloc[:3].sum()
grp=pd.DataFrame({'교통 사막(111)':des,'주의(48)':g.loc['주의'],'양호(70)':g.loc['양호']}).T
share=pd.DataFrame({'인구':grp.인구/tot.인구*100,'승용차 통근자':grp.승용차통근/tot.승용차통근*100,'K-패스 혜택(추정)':grp.환급추정/tot.환급추정*100})
fig,(a1,a2)=plt.subplots(1,2,figsize=(7.2,2.3),gridspec_kw={'width_ratios':[1.35,1]})
w=0.26; xs=np.arange(3)
for i,(c,cl) in enumerate(zip(share.columns,[GRAY,ORANGE,BLUE])):
    a1.bar(xs+(i-1)*w,share[c],width=w-0.03,color=cl,label=c)
    for xx,v in zip(xs+(i-1)*w,share[c]): a1.text(xx,v+1,f'{v:.1f}',ha='center',fontsize=6.5,color=INK)
a1.set_xticks(xs); a1.set_xticklabels(share.index); a1.set_ylabel('전국 대비 비중(%)'); a1.set_ylim(0,85); a1.legend(frameon=False,fontsize=7,loc='upper left')
a1.set_title('(a) 인구·승용차 통근 대비 K-패스 혜택',loc='left',fontsize=8.5,color=INK)
pc=(g.환급추정/g.인구).reindex(['① 농산어촌 이동고립형','② 도농복합 자동차의존형','③ 지방도시 자동차고착형','주의','양호'])
lab=['① 이동고립형','② 자동차의존형','③ 자동차고착형','주의','양호']
a2.barh(lab,pc,color=[ORANGE]*3+[GRAY,BLUE],height=0.55); a2.invert_yaxis()
for i,v in enumerate(pc): a2.text(v+500,i,f'{v:,.0f}원',va='center',fontsize=6.5,color=INK)
a2.set_xlim(0,44000); a2.set_xlabel('주민 1인당 연간 혜택 추정(원)'); a2.set_title('(b) 1인당 혜택 최대 8.1배 차이',loc='left',fontsize=8.5,color=INK)
fig.tight_layout(); fig.savefig('fig/A_paradox.png'); plt.close()
# ===== Fig B: SHAP 중요도 + 방향 | 유형 지도
fig=plt.figure(figsize=(7.2,3.1)); a1=fig.add_axes([0.14,0.14,0.27,0.74]); a2=fig.add_axes([0.40,0.0,0.42,1.0])
imp=A[['shap_'+f for f in F]].abs().mean().rename(lambda s:s[5:]).sort_values(); pct=imp/imp.sum()*100
sign={f:np.sign(np.corrcoef(A[f],A['shap_'+f])[0,1]) for f in F}
cols=[BLUE if sign[f]>0 else ORANGE for f in imp.index]
a1.barh([KOR[f] for f in imp.index],pct,color=cols,height=0.6)
for i,(f,p) in enumerate(pct.items()): a1.text(p+0.8,i,f"{p:.1f}% {'(+)' if sign[f]>0 else '(−)'}",va='center',fontsize=6.5,color=INK)
a1.set_xlim(0,70); a1.set_xlabel('평균 |SHAP| 비중(%)'); a1.set_title('(a) SHAP 변수 중요도  (+)높을수록 분담률↑ (−)↓',loc='left',fontsize=8.5,color=INK)
polys=pd.read_pickle('work/polys2020.pkl'); D=pd.read_csv('out/desert_clusters.csv')
CC={2:ORANGE,0:BLUE,1:AQUA}; key={(r.sido,r.sgg):r.cluster for r in D.itertuples()}; grade={(r.sido,r.sgg):r.grade for r in A.itertuples()}
fc=[CC[key[(s,g_)]] if (s,g_) in key else ('#dddcd6' if grade.get((s,g_))=='주의' else '#f1f0ec') for s,g_,c,v in polys]
a2.add_collection(PolyCollection([p[3] for p in polys],facecolors=fc,edgecolors=fc,linewidths=0.2))
R=pd.read_csv('out/lisa.csv'); LL={(r.sido,r.sgg) for r in R.itertuples() if r.lisa=='LL'}
a2.add_collection(PolyCollection([p[3] for p in polys if (p[0],p[1]) in LL],facecolors='none',edgecolors=INK,linewidths=0,hatch='/////'))
plt.rcParams['hatch.linewidth']=0.6
a2.set_xlim(124.6,130.0); a2.set_ylim(33.1,39.15); a2.set_aspect(1.2); a2.axis('off')
cnt=D.cluster.value_counts(); NAME={2:'① 농산어촌 이동고립형',0:'② 도농복합 자동차의존형',1:'③ 지방도시 자동차고착형'}
a2.legend(handles=[Patch(color=CC[k],label=f'{NAME[k]} {cnt[k]}곳') for k in [2,0,1]]+[Patch(color='#dddcd6',label='주의 10~20%'),Patch(color='#f1f0ec',label='양호 20%+'),Patch(facecolor='white',edgecolor=INK,hatch='/////',lw=0.5,label=f'LISA 냉점(LL) {len(LL)}곳')],loc='lower right',bbox_to_anchor=(1.6,0.0),frameon=False,fontsize=6.5)
a2.text(125.2,39.1,"(b) 교통 사막 유형과 LISA 냉점 (Moran's I=0.88)",fontsize=8.5,color=INK,va='top')
fig.savefig('fig/B_shap_map.png'); plt.close()
# ===== Fig C: 효율구간(밀도) | 2026 검증
eff=pd.read_pickle('out/efficiency.pkl'); e=eff['밀도']; v=pd.read_csv('out/validation_kpass2026.csv')
fig,(a1,a2)=plt.subplots(1,2,figsize=(7.2,2.3),gridspec_kw={'width_ratios':[1.35,1]})
x=np.exp(A.log_pop_density_dae); a1.scatter(x,A.shap_log_pop_density_dae,s=6,color=BLUE,alpha=0.7,edgecolors='none')
a1.axvspan(np.exp(e['b1']),np.exp(e['b2']),color=ORANGE,alpha=0.15,lw=0); a1.axvline(np.exp(e['zero']),color=ORANGE,lw=1.2,ls='--'); a1.axhline(0,color='#9a9994',lw=0.8)
a1.set_xscale('log'); a1.xaxis.set_major_locator(FixedLocator([3000,10000,30000,60000])); a1.xaxis.set_minor_locator(NullLocator()); a1.set_xticklabels(['3천','1만','3만','6만'])
for k,lab_,yy in [(2,'①',-12.2),(0,'②',-12.2),(1,'③',-12.2)]:
    xv=np.exp(D[D.cluster==k].log_pop_density_dae).mean(); a1.annotate(lab_,(xv,-10.6),xytext=(xv,yy),ha='center',fontsize=7,color=CC[k],arrowprops=dict(arrowstyle='-',color=CC[k],lw=0.8))
a1.set_ylim(-13,17); a1.set_xlabel('인구밀도(대지 기준, 명/㎢)'); a1.set_ylabel('SHAP(%p)')
a1.text(np.exp(e['zero'])*1.06,-7,f"안정점 ≈{np.exp(e['zero'])/1e4:.1f}만",fontsize=6.5,color=INK)
a1.set_title(f"(a) 정책 효율구간 {np.exp(e['b1']):,.0f}~{np.exp(e['b2']):,.0f}명/㎢",loc='left',fontsize=8.5,color=INK)
a2.scatter(v.pred_per_1k,v.act_per_1k,s=18,color=BLUE,edgecolors='white',linewidths=0.8)
b=np.polyfit(v.pred_per_1k,v.act_per_1k,1); xx=np.array([25,220]); a2.plot(xx,b[0]*xx+b[1],color=GRAY,lw=0.8,ls='--')
rr=np.corrcoef(v.pred_per_1k,v.act_per_1k)[0,1]
SN={'서울특별시':'서울','경기도':'경기','경상남도':'경남','인천광역시':'인천'}
for r in v.itertuples():
    if r.sido in SN: a2.annotate(SN[r.sido],(r.pred_per_1k,r.act_per_1k),xytext=(4,-3),textcoords='offset points',fontsize=6.5,color=SEC)
a2.set_xlim(20,225); a2.set_ylim(10,155); a2.annotate('강원·전북·전남·충북 등 도 지역',(42,24),xytext=(70,16),fontsize=6.5,color=SEC,arrowprops=dict(arrowstyle='-',color=SEC,lw=0.6))
a2.set_xlabel('모델 예측 대중교통 통근·통학(인구 1천 명당)'); a2.set_ylabel('실제 K-패스 이용자(1천 명당)'); a2.set_title(f'(b) 2026 검증: 17개 시도 1인당 r={rr:.2f}',loc='left',fontsize=8.5,color=INK)
fig.tight_layout(); fig.savefig('fig/C_eff_valid.png'); plt.close(); print('ok')
