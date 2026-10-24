import re
p = r"赛题\数理大赛赛题\电力市场中的用电申报与风险决策.pdf"
d = open(p, 'rb').read()
print("size", len(d))
print("header", d[:20])
for k in [b'/ToUnicode', b'/FontFile2', b'/FontFile3', b'/Type0', b'/TrueType', b'/Encoding', b'/ObjStm', b'/XRef']:
    print(k, d.count(k))
m = re.findall(rb'/BaseFont\s*/([#\w+\-,]+)', d)
print("fonts", m[:20])
print(d[-400:])
