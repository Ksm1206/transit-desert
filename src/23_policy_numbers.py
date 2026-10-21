"""정책제안 수치 재현: 선지급형 이동 크레딧 재원, 전환 보너스 비용(보고서 '정책제안 및 기대효과')
외부 가정(보도 수치)은 아래 상수로 명시한다.
"""
import pandas as pd

REFUND_Y1 = 3600e8        # K-패스 첫 1년 환급금(원), SBS Biz 2025.5.5 보도 '3,600억 원 이상'
CREDIT_M = 16000          # 월 크레딧(원) = 현행 1인당 월평균 환급(SBS Biz)
DRT_PER_VEH = 322e8 / 226 # 경기 똑버스 2024년 사업비 322억 원 / 226대(경기일보 2025.1.13)
BONUS_MONTHS = 12         # 전환 보너스 지급 기간(개월), 보너스 = 기본 환급과 같은 금액

g = pd.read_csv('out/carbon_refund_by_group.csv').set_index('group')
d = pd.read_csv('out/carbon_detail.csv')
s = pd.read_csv('out/scenario_car.csv').set_index('group')

# 1) 선지급형 이동 크레딧: ① 유형 인구 비중 - 혜택 추정 비중(모델 기반)을 실제 환급 총액에 적용
g1 = '① 농산어촌 이동고립형'
gap = g.loc[g1, '인구_비중%'] - g.loc[g1, '환급추정_비중%']
fund = REFUND_Y1 * gap / 100
people = fund / (CREDIT_M * 12)
old1 = (d[d.group == g1].pop2020 * d[d.group == g1].old_ratio / 100).sum()
print(f'[크레딧] ① 인구 {g.loc[g1,"인구_비중%"]:.1f}% vs 혜택 {g.loc[g1,"환급추정_비중%"]:.1f}% → 차이 {gap:.2f}%p')
print(f'  재원 {fund/1e8:.0f}억 원 → 월 {CREDIT_M:,}원 기준 {people:,.0f}명 '
      f'(① 고령 인구 {old1:,.0f}명의 {people/old1*100:.1f}%), DRT {fund/DRT_PER_VEH:.0f}대 규모')

# 2) 전환 보너스: 자가용 임계 시나리오(②·③)의 전환 인원을 '목표치'로 두고 비용 산정
tgt = s.loc[['② 도농복합 자동차의존형', '③ 지방도시 자동차고착형']]
n, co2 = tgt['전환인원'].sum(), tgt['CO2감축t'].sum()
cost = n * CREDIT_M * BONUS_MONTHS
print(f'[보너스] 목표 전환 {n:,.0f}명, 감축 {co2:,.0f} tCO2/년')
print(f'  보너스 비용 {cost/1e8:.1f}억 원/년, 목표 달성 시 감축 1톤당 {cost/co2:,.0f}원')

pd.DataFrame({'항목': ['크레딧_격차pp', '크레딧_재원억', '크레딧_인원', '크레딧_고령대비pct', '크레딧_DRT대',
                      '보너스_목표인원', '보너스_감축t', '보너스_비용억', '보너스_톤당원'],
              '값': [gap, fund/1e8, people, people/old1*100, fund/DRT_PER_VEH, n, co2, cost/1e8, cost/co2]}
             ).round(2).to_csv('out/policy_numbers.csv', index=False, encoding='utf-8-sig')
