"""교통 사막 유형별 프로필·소속 지역표"""
import pandas as pd
D=pd.read_csv('out/desert_clusters.csv'); A=pd.read_csv('out/shap_all229.csv'); m=pd.read_csv('data/sgg_master_v7.csv')
NAME={2:'① 농산어촌 이동고립형',0:'② 도농복합 자동차의존형',1:'③ 지방도시 자동차고착형'}
D['유형']=D.cluster.map(NAME)
raw={'all_kpass_share':'분담률(%)','pop_density_dae':'대지 인구밀도','raw_car':'자가용/1천명','rail_st_2020':'도시철도역','raw_old':'고령비율(%)','commute_car_share':'승용차 통근(%)','pop2020':'인구'}
t=D.groupby('유형')[list(raw)].mean().rename(columns=raw)
ref=A[A.grade=='양호'][['sido','sgg','all_kpass_share']].merge(m[['sido','sgg','pop_density_dae','car_per_1k','rail_st_2020','old_ratio','commute_car_share','pop2020']],on=['sido','sgg'])
r=pd.Series({'분담률(%)':ref.all_kpass_share.mean(),'대지 인구밀도':ref.pop_density_dae.mean(),'자가용/1천명':ref.car_per_1k.mean(),'도시철도역':ref.rail_st_2020.mean(),'고령비율(%)':ref.old_ratio.mean(),'승용차 통근(%)':ref.commute_car_share.mean(),'인구':ref.pop2020.mean()},name='(참고) 양호')
t=pd.concat([t,r.to_frame().T]); t.round(1).to_csv('out/cluster_profile.csv',encoding='utf-8-sig'); print(t.round(1).T)
D[['유형','sido','sgg','all_kpass_share','stops_imputed']].sort_values(['유형','all_kpass_share']).to_csv('out/cluster_members.csv',index=False,encoding='utf-8-sig')
