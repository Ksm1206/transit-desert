import pandas as pd, numpy as np, pickle, sys
sys.path.insert(0,'src'); from utils_regions import tag, norm
b=pd.read_pickle('out/best_model.pkl'); mdl,F=b['model'],b['F']
m=pd.read_csv('data/sgg_master_v7.csv'); keys=set(zip(m.sido,m.sgg))
def fixkey(s,g):
    if g=='군위군': return ('경상북도','군위군')
    if s=='세종특별자치시': return (s,'세종시')
    return (s,g)
# ---- 2025 연앙인구(연령)
p=pd.read_csv('work/pop2025_age.csv',skiprows=1); p.columns=['region','sex','age','item','unit','y23','y24','y25']
p=p[p.sex=='계']; p['region']=p.region.map(norm)
blk=(p.region!=p.region.shift()).cumsum(); nm=p.groupby(blk).region.first(); t=dict(zip(nm.index,tag(nm.tolist())))
p['sido']=blk.map(lambda x:t[x][0]); p['level']=blk.map(lambda x:t[x][1])
sj=(p.level=='sido')&(p.region=='세종특별자치시'); p.loc[sj,'level']='sgg'
p=p[p.level=='sgg'].drop_duplicates(['sido','region','age'])
p[['sido','sgg']]=[fixkey(a,c) for a,c in zip(p.sido,p.region)]
p['lo']=p.age.str.extract(r'^(\d+)').astype(float)
tot=p[p.age=='계'].groupby(['sido','sgg']).y25.sum()
old=p[p.lo>=65].groupby(['sido','sgg']).y25.sum(); teen=p[p.lo.isin([10,15])].groupby(['sido','sgg']).y25.sum()
P=pd.DataFrame({'pop2025':tot,'old_ratio':old/tot*100,'teen_ratio':teen/tot*100}).reset_index()
print('pop25 rows',len(P),'unmatched',[k for k in zip(P.sido,P.sgg) if k not in keys])
# ---- 2026.08 자가용 승용차
SH={'서울':'서울특별시','부산':'부산광역시','대구':'대구광역시','인천':'인천광역시','광주':'광주광역시','대전':'대전광역시','울산':'울산광역시','세종':'세종특별자치시','경기':'경기도','강원':'강원도','충북':'충청북도','충남':'충청남도','전북':'전라북도','전남':'전라남도','경북':'경상북도','경남':'경상남도','제주':'제주특별자치도'}
c=pd.read_csv('work/car202608.csv',skiprows=1); c.columns=['sido','sgg','kind','use','unit','v']
c=c[(c.kind=='승용')&(c.use=='자가용')&(c.sgg!='계')].copy()
def ck(s,g):
    g=g.split(' ')[0]
    if s=='전남광주': s='광주광역시' if g in ['동구','서구','남구','북구','광산구'] else '전라남도'
    s=SH.get(s,s); return fixkey(s,g)
c[['sido','sgg']]=[ck(a,b_) for a,b_ in zip(c.sido,c.sgg)]
c.loc[c.sgg=='청원군','sgg']='청주시'
C=c.groupby(['sido','sgg']).v.sum().rename('car26').reset_index()
# 2026.7 인천 행정체제 개편(제물포·영종·서해·검단구) → 2020 단위(중구·동구·서구)로 환원: 묶음 합계를 2025 인구 비례 배분
inc=lambda g: C[(C.sido=='인천광역시')&(C.sgg.isin(g))].v.sum() if False else C[(C.sido=='인천광역시')&(C.sgg.isin(g))].car26.sum()
pp=P.set_index(['sido','sgg']).pop2025
jd=inc(['제물포구','영종구','중구','동구']); sw=inc(['서해구','검단구','서구'])
C=C[~((C.sido=='인천광역시')&(C.sgg.isin(['제물포구','영종구','서해구','검단구','중구','동구','서구'])))]
add=[]
for g in ['중구','동구']: add.append(('인천광역시',g,jd*pp['인천광역시',g]/(pp['인천광역시','중구']+pp['인천광역시','동구'])))
add.append(('인천광역시','서구',sw))
C=pd.concat([C,pd.DataFrame(add,columns=['sido','sgg','car26'])],ignore_index=True)
print('car rows',len(C),'unmatched',[k for k in zip(C.sido,C.sgg) if k not in keys])
# ---- rail 2026
r=pd.read_csv('data/metro_stations_located.csv'); R=r.drop_duplicates(['sido','sgg','역사명']).groupby(['sido','sgg']).size().rename('rail26').reset_index()
X=m.merge(P,on=['sido','sgg'],how='left').merge(C,on=['sido','sgg'],how='left').merge(R,on=['sido','sgg'],how='left')
X['rail26']=X.rail26.fillna(0)
print('missing',X[['pop2025','car26']].isna().sum().to_dict())
X26=pd.DataFrame({'log_pop_density_dae':np.log(X.pop2025/X.area_dae_km2),'log_stops_dae':m.log_stops_dae,
 'rail_st_per_100k':X.rail26/X.pop2025*1e5,'car_per_1k':X.car26/X.pop2025*1000,'out_sido_pct':m.out_sido_pct,
 'old_ratio':X.old_ratio_y,'teen_ratio':X.teen_ratio_y})
A=pd.read_csv('out/shap_all229.csv'); X26.loc[m.stops_missing==1,'log_stops_dae']=A.loc[m.stops_missing==1,'log_stops_dae'].values
X['pred2020']=mdl.predict(A[F]); X['pred2026']=mdl.predict(X26[F])
X['grade26']=pd.cut(X.pred2026,[-1,10,20,101],labels=['교통사막','주의','양호'])
print(pd.crosstab(A.grade,X.grade26))
print('2020 vs 2026 예측 변화 평균',(X.pred2026-X.pred2020).describe().round(2).to_dict())
# 검증: 시도별 예측 K-패스 대상 이용자(2026) vs 실제 K-패스 이용자(2026.4)
X['users26']=X.pred2026/100*X.all_total*(X.pop2025/X.pop2020)
k=pd.read_csv('data_raw/kpass_sido_202604.csv'); g=X.groupby('sido')[['users26','pop2025']].sum().reset_index().merge(k,left_on='sido',right_on='시도')
print('corr(수)',np.corrcoef(g.users26,g.이용자수)[0,1].round(3),' spearman',g[['users26','이용자수']].corr('spearman').iloc[0,1].round(3))
# 인구 규모 효과를 뺀 1인당 비교(인구 1천 명당)
g['pred_per_1k']=g.users26/g.pop2025*1000; g['act_per_1k']=g.이용자수/g.pop2025*1000
print('corr(1천 명당)',np.corrcoef(g.pred_per_1k,g.act_per_1k)[0,1].round(3),' spearman',g[['pred_per_1k','act_per_1k']].corr('spearman').iloc[0,1].round(3))
g['ratio']=g.이용자수/g.users26; print(g[['sido','users26','이용자수','ratio']].round(2).sort_values('ratio').to_string())
X26.assign(sido=X.sido,sgg=X.sgg,pred2026=X.pred2026,grade26=X.grade26,pred2020=X.pred2020).to_csv('out/apply2026.csv',index=False,encoding='utf-8-sig')
g.to_csv('out/validation_kpass2026.csv',index=False,encoding='utf-8-sig')
