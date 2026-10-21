import pandas as pd, numpy as np
d=pd.read_csv('work/DT_1PA2004.csv',skiprows=1)
d.columns=['region','type','time','item','unit','val']
d['val']=pd.to_numeric(d['val'].astype(str).str.strip().replace({'-':'0','X':np.nan}),errors='coerce')
SIDO=['서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시','울산광역시','세종특별자치시','경기도','강원도','충청북도','충청남도','전라북도','전라남도','경상북도','경상남도','제주특별자치도']
# contiguous blocks
blk=(d.region!=d.region.shift()).cumsum(); d['blk']=blk
names=d.groupby('blk').region.first()
sido=None; city=None; meta=[]
for b,r in names.items():
    lvl='skip'
    if r in ['전국','동부','읍부','면부']: lvl='nat'
    elif r in SIDO: sido=r; city=None; lvl='sido'
    else:
        metro=sido.endswith(('특별시','광역시'))
        if (not metro) and r.endswith('구') and city: lvl='gu'      # 일반구
        else:
            lvl='sgg'; city=r if r.endswith('시') else None
    meta.append((b,r,sido,lvl,city if lvl=='gu' else None))
m=pd.DataFrame(meta,columns=['blk','name','sido','level','parent'])
d=d.merge(m,on='blk')
sgg=m[m.level=='sgg']; print('기초자치단체 수',len(sgg)); print(sgg.groupby('sido').size().to_string())
d.to_csv('work/DT_1PA2004_tidy.csv',index=False)
m.to_csv('work/region_meta.csv',index=False)
