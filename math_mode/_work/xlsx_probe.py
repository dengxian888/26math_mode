import zipfile, re, sys, io
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'

files = [
    '附件1_典型日完全信息.xlsx',
    '附件2_用户实际用电量.xlsx',
    '附件3_市场披露信息.xlsx',
    '附件4_市场价格.xlsx',
    '附件5_中长期合约.xlsx',
    '附件6_结果文件.xlsx',
]
base = r'赛题\数理大赛赛题'

for fn in files:
    path = base + '\\' + fn
    print('=' * 70)
    print(fn)
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in sst.findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    sheets = []
    for sh in wb.iter(NS + 'sheet'):
        rid = sh.get(RNS + 'id')
        tgt = relmap.get(rid, '')
        if not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt.lstrip('/')
        sheets.append((sh.get('name'), tgt))
    for name, tgt in sheets:
        try:
            data = z.read(tgt)
        except KeyError:
            print('  [sheet missing]', name, tgt); continue
        ws = ET.fromstring(data)
        rows = ws.iter(NS + 'row')
        count = 0
        preview = []
        dim = ws.find(NS + 'dimension')
        for row in rows:
            count += 1
            if count <= 6:
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
                    vals.append(f"{c.get('r')}={txt}")
                preview.append(vals)
        print(f"  SHEET [{name}] rows={count} dim={dim.get('ref') if dim is not None else '?'}")
        for p in preview:
            print('     ', ' | '.join(p[:12]))
