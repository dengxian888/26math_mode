import zipfile, datetime
from xml.etree import ElementTree as ET
exec(open('dates_probe.py', encoding='utf-8').read().split("r1 = ")[0].replace("base = r'赛题\\数理大赛赛题'", "base = r'赛题\\数理大赛赛题'"))

for fn, idx, col in [(r'\附件2_用户实际用电量.xlsx', 0, 3), (r'\附件3_市场披露信息.xlsx', 1, 2)]:
    rows = read_sheet(base + fn, idx)
    hdr = rows[0]
    lags = {}
    for r in rows[1:]:
        if len(r) <= col or not r[0] or not r[col]:
            continue
        try:
            d = datetime.date.fromisoformat(r[0][:10])
            a = datetime.date.fromisoformat(r[col][:10])
        except Exception:
            continue
        lags[(a - d).days] = lags.get((a - d).days, 0) + 1
    print(fn, 'header:', hdr)
    print('  lag distribution:', dict(sorted(lags.items())))
