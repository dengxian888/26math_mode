import re, zlib
p = r"赛题\数理大赛赛题\电力市场中的用电申报与风险决策.pdf"
d = open(p, 'rb').read()
outs = []
for m in re.finditer(rb'stream\r?\n', d):
    start = m.end()
    end = d.find(b'endstream', start)
    if end < 0:
        continue
    raw = d[start:end]
    try:
        outs.append(zlib.decompress(raw))
    except Exception:
        pass
print("streams decoded:", len(outs))
blob = b"\n".join(outs)
print("blob size", len(blob))
for k in [b'/Font', b'/ToUnicode', b'/BaseFont', b'/Type0', b'/CIDFont', b'BT', b'/Image']:
    print(k, blob.count(k))
print(blob[:1500])
