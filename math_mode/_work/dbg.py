import re, zlib, sys
exec(open('extract_pdf.py', encoding='utf-8').read().split('# ---------------- content stream')[0])

for pnum in [1, 18]:
    h = objs[pnum]['head']
    print("=== PAGE OBJ", pnum, "===")
    print(h[:800])
    res = get_attr(pnum, b'Resources')
    print("resources ref:", res)
    if res and objs.get(res):
        print("RES HEAD:", objs[res]['head'][:600])
    cont = get_attr(pnum, b'Contents')
    print("contents ref:", cont, "has stream:", bool(cont and objs.get(cont) and objs[cont]['stream']))
    if cont and objs.get(cont):
        o = objs[cont]
        print("content head:", o['head'][:200])
        dec = inflate(o['stream'], o['head'])
        print("decoded len:", len(dec) if dec else None)
        if dec: print(dec[:300])
