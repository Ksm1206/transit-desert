import pandas as pd, numpy as np, pickle
A=pd.read_csv('out/shap_all229.csv'); m=pd.read_csv('data/sgg_master_v7.csv'); D=pd.read_csv('out/desert_clusters.csv')
NAME={2:'① 농산어촌 이동고립형',0:'② 도농복합 자동차의존형',1:'③ 지방도시 자동차고착형'}
x=m.merge(A[['sido','sgg','grade']],on=['sido','sgg']).merge(D[['sido','sgg','cluster']],on=['sido','sgg'],how='left')
x['group']=np.where(x.cluster.notna(),x.cluster.map(NAME),x.grade)
# 가정(보고서 명시): K-패스 1인당 월평균 환급 1.6만원(2025 1분기, 국토부 발표 보도) → 연 19.2만원
REFUND_YR=16000*12
# 승용차: 휘발유 2.18 kgCO2/L(에너지공단 배출계수 산출) ÷ 가정 연비 12 km/L, 통근 평균속도 가정 35 km/h, 왕복·연 250일
KG_PER_KM=2.18/12; SPEED=35; DAYS=250
x['kp_users']=x.all_total*x.all_kpass_share/100
x['refund_won']=x.kp_users*REFUND_YR
x['car_commuters']=x.commute_total*x.commute_car_share/100
x['car_km_yr']=x.car_commuters*(x.commute_car_avg_min/60*SPEED)*2*DAYS
x['co2_t']=x.car_km_yr*KG_PER_KM/1000
g=x.groupby('group').agg(지역수=('sgg','size'),인구=('pop2020','sum'),통근통학=('all_total','sum'),Kpass대상이용=('kp_users','sum'),환급추정=('refund_won','sum'),승용차통근=('car_commuters','sum'),CO2=('co2_t','sum'))
tot=g.sum()
for c in ['인구','Kpass대상이용','환급추정','승용차통근','CO2']: g[c+'_비중%']=g[c]/tot[c]*100
g['1인당환급(원)']=g.환급추정/g.인구; g['1인당CO2(kg)']=g.CO2/g.인구*1000
order=['① 농산어촌 이동고립형','② 도농복합 자동차의존형','③ 지방도시 자동차고착형','주의','양호']
g=g.loc[order]; pd.set_option('display.width',250); print(g.round(1).T.to_string())
desert=g.loc[order[:3]].sum()
print('교통사막 합계: 인구비중 %.1f%%, 환급비중 %.1f%%, 승용차통근 CO2 비중 %.1f%%'%(desert['인구']/tot['인구']*100,desert['환급추정']/tot['환급추정']*100,desert['CO2']/tot['CO2']*100))
g.to_csv('out/carbon_refund_by_group.csv',encoding='utf-8-sig'); x.to_csv('out/carbon_detail.csv',index=False,encoding='utf-8-sig')
