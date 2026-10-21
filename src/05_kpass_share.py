"""K-패스 대상 수단(시내·좌석·마을버스 + 전철·지하철) 분담률 산출 → sgg_master_v2"""
import pandas as pd
d=pd.read_csv('work/DT_1PA2004_tidy.csv')
KP=['시내,좌석,마을버스','전철,지하철']; NK=['고속,시외버스','기차']
def b(level):
    x=d[(d.level==level)&(d.time=='계')]; rows=[]
    for (bk,name,sido),g in x.groupby(['blk','name','sido'],sort=False):
        r={'sido':name if level=='sido' else sido,'sgg':name}
        for t,tag in [('계','all'),('통근','commute')]:
            a=g[g.type==t].set_index('item').val; tot=a['통근·통학 인구(12세 이상)']
            r[f'{tag}_kpass_share']=a[KP].sum()/tot*100
            r[f'{tag}_kpass_mixed_share']=(a[KP].sum()+a['복합수단'])/tot*100
            r[f'{tag}_nonkpass_pt_share']=a[NK].sum()/tot*100
        rows.append(r)
    return pd.DataFrame(rows)
m=pd.read_csv('data/sgg_master_v1.csv').merge(b('sgg'),on=['sido','sgg'])
m.round(3).to_csv('data/sgg_master_v2.csv',index=False,encoding='utf-8-sig')
b('sido').to_csv('data/sido_kpass_share_2020.csv',index=False,encoding='utf-8-sig'); print('v2',m.shape)
