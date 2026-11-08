"""핵심 수치의 불확실성 점검

1) 2026 검증 상관계수의 신뢰구간
   검증은 시도 단위라 점이 17개뿐입니다. 점이 적으면 상관계수가 쉽게 높게 나오므로
   Fisher z 변환으로 95% 신뢰구간을 구하고, 규모가 큰 서울·경기를 뺀 값도 함께 봅니다.

2) 1인당 환급액 가정의 영향
   17_benefit_carbon은 모든 지역 이용자가 같은 금액(월 1.6만 원)을 환급받는다고 가정합니다.
   이 경우 환급액을 얼마로 잡든 지역 간 비율은 변하지 않으므로, 혜택 격차는 '이용자 수' 차이에서 나옵니다.
   실제로는 이동 거리와 요금이 지역마다 달라 1인당 환급도 다를 수 있으므로,
   교통 사막 이용자가 다른 지역보다 1인당 몇 배를 더 받으면 격차가 줄거나 사라지는지 계산합니다.

입력: out/validation_kpass2026.csv(19), out/carbon_refund_by_group.csv(17)
출력: out/validation_ci.csv, out/refund_heterogeneity.csv
"""
import numpy as np
import pandas as pd


def pearson_ci(x, y, level=0.95):
    n = len(x)
    r = np.corrcoef(x, y)[0, 1]
    z, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    q = 1.959963984540054 if level == 0.95 else None
    return n, r, np.tanh(z - q * se), np.tanh(z + q * se)


# ---- 1) 검증 상관계수 신뢰구간
v = pd.read_csv('out/validation_kpass2026.csv')
rows = []
for name, d in [('17개 시도 전체', v), ('서울·경기 제외', v[~v.sido.isin(['서울특별시', '경기도'])])]:
    for lab, a, b in [('이용자 수', 'users26', '이용자수'), ('인구 1천 명당 이용자', 'pred_per_1k', 'act_per_1k')]:
        n, r, lo, hi = pearson_ci(d[a], d[b])
        rows.append({'대상': name, '기준': lab, 'n': n, '상관계수 r': round(r, 3),
                     '95% 하한': round(lo, 2), '95% 상한': round(hi, 2),
                     '스피어만 순위상관': round(d[[a, b]].corr('spearman').iloc[0, 1], 3)})
ci = pd.DataFrame(rows)
ci.to_csv('out/validation_ci.csv', index=False, encoding='utf-8-sig')

# ---- 2) 1인당 환급액이 지역마다 다를 때의 혜택 격차
g = pd.read_csv('out/carbon_refund_by_group.csv', index_col=0)
desert = ['① 농산어촌 이동고립형', '② 도농복합 자동차의존형', '③ 지방도시 자동차고착형']
d_pop, d_ref = g.loc[desert, '인구'].sum(), g.loc[desert, '환급추정'].sum()
good_pc = g.loc['양호', '환급추정'] / g.loc['양호', '인구']
base_gap = good_pc / (d_ref / d_pop)
out = []
for k in [1.0, 1.5, 2.0, 3.0, round(base_gap, 2)]:
    desert_pc = d_ref * k / d_pop
    out.append({'교통 사막 이용자의 1인당 환급 배수': k,
                '교통 사막 1인당 환급(원/년)': round(desert_pc),
                '양호 지역 1인당 환급(원/년)': round(good_pc),
                '1인당 혜택 격차(배)': round(good_pc / desert_pc, 2)})
het = pd.DataFrame(out)
het.to_csv('out/refund_heterogeneity.csv', index=False, encoding='utf-8-sig')

pd.set_option('display.width', 200)
print(ci.to_string(index=False))
print()
print(het.to_string(index=False))
print(f'\n격차가 사라지려면 교통 사막 이용자 1인당 환급이 다른 지역의 {base_gap:.1f}배여야 함')
