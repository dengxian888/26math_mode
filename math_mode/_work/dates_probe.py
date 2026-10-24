import zipfile, re
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
base = r'赛题\数理大赛赛题'


def read_sheet(path, idx=0):
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in sst.findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    names = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')]
    names.sort()
    ws = ET.fromstring(z.read(names[idx]))
    rows = []
    for row in ws.iter(NS + 'row'):
        vals = []
        for c in row.findall(NS + 'c'):
            v = c.find(NS + 'v')
            is_ = c.find(NS + 'is')
            if c.get('t') == 's' and v is not None:
                vals.append(shared[int(v.text)])
            elif is_ is not None:
                vals.append(''.join(t.text or '' for t in is_.iter(NS + 't')))
            elif v is not None:
                vals.append(v.text)
            else:
                vals.append('')
        rows.append(vals)
    return rows


r1 = read_sheet(base + r'\附件1_典型日完全信息.xlsx')
dates1 = []
for r in r1[1:]:
    if r and r[0] and r[0] not in dates1:
        dates1.append(r[0])
print('附件1 典型日:', dates1)
print('附件1 行数(含表头):', len(r1))

r2 = read_sheet(base + r'\附件2_用户实际用电量.xlsx')
d2 = sorted({r[0] for r in r2[1:] if r and r[0]})
print('附件2 日期范围:', d2[0], '->', d2[-1], '天数:', len(d2))

r4 = read_sheet(base + r'\附件4_市场价格.xlsx')
lag = sorted({(r[0], r[4]) for r in r4[1:] if r and len(r) > 4 and r[4]})
import datetime
lags = []
for d, a in lag[:8]:
    dd = datetime.date.fromisoformat(d[:10])
    aa = datetime.date.fromisoformat(a[:10])
    lags.append((d, a, (aa - dd).days))
print('附件4 部分可获得延迟:', lags)

r3 = read_sheet(base + r'\附件3_市场披露信息.xlsx', 0)
lag3 = [(r[0], r[2]) for r in r3[1:6] if r and len(r) > 2]
print('附件3 预测信息 可获得:', lag3)
