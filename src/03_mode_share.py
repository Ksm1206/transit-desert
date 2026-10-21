import pandas as pd, numpy as np
d=pd.read_csv('work/DT_1PA2004_tidy.csv')
PT=['시내,좌석,마을버스','고속,시외버스','전철,지하철','기차']
mid={'15분 미만':7.5,'15~30':22.5,'30~45':37.5,'45~60':52.5,'60~90':75,'90~120':105,'120분 이상':135}
def build(level):
    x=d[d.level==level]
    out=[]
    for (b,name,sido),g in x.groupby(['blk','name','sido'],sort=False):
        row={'sido':name if level=='sido' else sido,'sgg':name}
        for t,tag in [('계','all'),('통근','commute')]:
            a=g[(g.type==t)&(g.time=='계')].set_index('item').val
            tot=a['통근·통학 인구(12세 이상)']
            row[f'{tag}_total']=tot
            row[f'{tag}_pt_share']=a[PT].sum()/tot*100
            row[f'{tag}_pt_mixed_share']=(a[PT].sum()+a['복합수단'])/tot*100
            row[f'{tag}_car_share']=a['승용차,승합차(벤)']/tot*100
            row[f'{tag}_active_share']=(a['걸어서']+a['자전거'])/tot*100
            row[f'{tag}_bus_share']=a['시내,좌석,마을버스']/tot*100
            row[f'{tag}_rail_share']=(a['전철,지하철']+a['기차'])/tot*100
            row[f'{tag}_car_n']=a['승용차,승합차(벤)']
            c=g[(g.type==t)&(g.time!='계')&(g.item=='승용차,승합차(벤)')]
            row[f'{tag}_car_avg_min']=(c.time.map(mid)*c.val).sum()/c.val.sum() if c.val.sum()>0 else np.nan
            p=g[(g.type==t)&(g.time!='계')&(g.item=='통근·통학 인구(12세 이상)')]
            row[f'{tag}_avg_min']=(p.time.map(mid)*p.val).sum()/p.val.sum()
        out.append(row)
    return pd.DataFrame(out)
s=build('sgg'); p=build('sido')
s.round(3).to_csv('data/sgg_mode_share_2020.csv',index=False,encoding='utf-8-sig')
p.round(3).to_csv('data/sido_mode_share_2020.csv',index=False,encoding='utf-8-sig')
# validation: sgg sums vs sido totals
chk=s.groupby('sido').all_total.sum().rename('sgg_sum').to_frame().join(p.set_index('sgg').all_total.rename('sido_total'))
chk['diff']=chk.sgg_sum-chk.sido_total; print(chk.to_string())
print(s.commute_pt_share.describe())
cols=['sido','sgg','commute_pt_share','commute_car_share','commute_total']
print('하위15\n',s.sort_values('commute_pt_share')[cols].head(15).to_string())
print('상위10\n',s.sort_values('commute_pt_share',ascending=False)[cols].head(10).to_string())
