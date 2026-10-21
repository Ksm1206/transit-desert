"""KOSIS에서 내려받은 .xls(XML Spreadsheet, EUC-KR)를 CSV로 변환해 work/에 저장"""
import os, csv
from lxml import etree
NS='{urn:schemas-microsoft-com:office:spreadsheet}'
MAP={'kosis_DT_1PA2004_2020.xls':'DT_1PA2004.csv','kosis_DT_1PA2003_2020.xls':'DT_1PA2003.csv',
     'kosis_DT_1PA2021_2020.xls':'DT_1PA2021.csv','kosis_DT_1B040M5_1_2023_2025.xls':'pop2025_age.csv',
     'kosis_DT_MLTM_5498_202608.xls':'car202608.csv','kosis_DT_MLTM_5498_2020.xls':'car2020.csv',
     'kosis_DT_MLTM_2300_2020.xls':'land2020.csv','kosis_DT_1B04006_2020_age.xls':'age2020.csv'}
os.makedirs('work',exist_ok=True)
for src,dst in MAP.items():
    raw=open('data_raw/'+src,'rb').read().decode('cp949',errors='replace').lstrip().replace('encoding="EUC-KR"','encoding="UTF-8"',1)
    root=etree.fromstring(raw.encode('utf-8'),etree.XMLParser(huge_tree=True,recover=True))
    ws=root.find(NS+'Worksheet')
    with open('work/'+dst,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        for row in ws.iter(NS+'Row'):
            out=[]
            for c in row.findall(NS+'Cell'):
                idx=c.get(NS+'Index')
                if idx:
                    while len(out)<int(idx)-1: out.append('')
                d=c.find(NS+'Data'); out.append(d.text if d is not None and d.text else '')
            w.writerow(out)
    print('ok',dst)
