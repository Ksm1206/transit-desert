SIDO=['서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시','울산광역시','세종특별자치시','경기도','강원도','충청북도','충청남도','전라북도','전라남도','경상북도','경상남도','제주특별자치도']
ALIAS={'강원특별자치도':'강원도','전북특별자치도':'전라북도','창원시(통합)':'창원시'}
def norm(r): return ALIAS.get(r,r)
def tag(names):
    """ordered names -> list of (sido, level, parent_city). level: nat/sido/sgg/gu/skip"""
    sido=None; city=None; out=[]
    for r in map(norm,names):
        if r in ['전국','동부','읍부','면부']: out.append((None,'nat',None)); continue
        if r in SIDO: sido=r; city=None; out.append((sido,'sido',None)); continue
        if '출장소' in r: out.append((sido,'skip',None)); continue
        metro=sido.endswith(('특별시','광역시'))
        if (not metro) and r.endswith('구') and city: out.append((sido,'gu',city)); continue
        city=r if r.endswith('시') else None
        out.append((sido,'sgg',None))
    return out
