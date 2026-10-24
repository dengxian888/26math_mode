import zipfile, re, sys, io
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

files = [
    '附件1_典型日完全信息.xlsx',
    '附件2_用户实际用电量.xlsx',
    '附件3_市场披露信息.xlsx',
    '附件4_市场价格.xlsx',
    '附件5_中长期合约.xlsx',
    '附件6_结果文件.xlsx',
]
base = r'赛题\数理大赛赛题'
out = io.open('附件结构.txt', 'w', encoding='utf-8')

for fn in files:
    path = base + '\\' + fn
    out.write('=' * 78 + '\n' + fn + '\n')
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in sst.findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    for sh in wb.iter(NS + 'sheet'):
        name = sh.get('name')
        tgt = relmap.get(sh.get(RNS + 'id'), '')
        if not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt.lstrip('/')
        ws = ET.fromstring(z.read(tgt))
        rows = list(ws.iter(NS + 'row'))
        out.write(f"\n  [SHEET] {name}  行数={len(rows)}\n")
        for row in rows[:4]:
            vals = []
            for c in row.findall(NS + 'c'):
                v = c.find(NS + 'v')
                is_ = c.find(NS + 'is')
                txt = ''
                if c.get('t') == 's' and v is not None:
                    txt = shared[int(v.text)]
                elif is_ is not None:
                    txt = ''.join(t.text or '' for t in is_.iter(NS + 't'))
                elif v is not None:
                    txt = v.text
                vals.append(txt.strip().replace('\n', ''))
            out.write('      ' + ' | '.join(vals) + '\n')
out.close()
print('ok')
