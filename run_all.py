"""전체 파이프라인 실행 (저장소 루트에서)
  python run_all.py                      # 원자료부터 전부
  python run_all.py --from 10            # 포함된 data/sgg_master_v6.csv부터 분석만(10_select_variables부터)
"""
import subprocess, sys, time
STEPS=[('01_prepare_kosis','KOSIS 원자료 → CSV'),('02_build_mode_share','통근·통학 표 정리·행정구역 계층'),
 ('03_mode_share','시군구별 수단 분담률'),('04_age_commute','고령·청소년 분담률, 관외·타 시도 통근'),
 ('05_kpass_share','K-패스 대상 분담률(종속변수)'),('06_population','2020 인구·세대'),('07_car_landuse','자가용 승용차·면적·밀도'),
 ('08_age_rail','2020 연령 비율·도시철도역'),('09_bus_stops_spatial','정류장 공간결합·결측 표시'),('10_select_variables','변수 선정(VIF)'),
 ('11_compare_models','모델 비교(교차검증)'),('12_shap_values','정확 SHAP'),('13_cluster_k','229개 SHAP·K 선정'),
 ('14_cluster_types','K-means(k=3)'),('15_cluster_profile','유형 프로필'),('16_policy_threshold','정책 효율구간'),
 ('17_benefit_carbon','혜택·CO₂ 분배'),('18_car_scenario','자가용 시나리오'),('19_apply_2026','2026 적용·검증'),
 ('20_tago_quality','TAGO 배차 정보 공백'),('21_robustness','탄소 효율·민감도·밀도 통제'),('22_spatial_autocorr',"Moran's I·LISA"),('23_policy_numbers','정책제안 수치(크레딧 재원·보너스 비용)'),('24_figures_extra','보조 그림(모델 비교·SHAP·K 선정·지도)'),('25_figures_report','보고서 그림 A~C')]
start=sys.argv[sys.argv.index('--from')+1] if '--from' in sys.argv else STEPS[0][0]
idx=next(i for i,(s,_) in enumerate(STEPS) if s==start or s.startswith(start.zfill(2)+'_'))
for s,desc in STEPS[idx:]:
    t=time.time(); print(f'\n=== {s}: {desc}',flush=True)
    r=subprocess.run([sys.executable,'-W','ignore',f'src/{s}.py'])
    if r.returncode: sys.exit(f'실패: {s}')
    print(f'--- {time.time()-t:.1f}s')
print('\n완료: data/, out/, fig/ 확인')
