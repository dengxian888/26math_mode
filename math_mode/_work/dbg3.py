import re
exec(open('extract_pdf.py', encoding='utf-8').read().split("def unescape_lit")[0])

for num in [46, 50, 48, 52]:
    o = objs.get(num)
    print("obj", num, ":" , o['head'][:500] if o else "MISSING")

# look for FontFile2 anywhere
for num, o in objs.items():
    if b'/FontFile2' in o['head'] or b'/FontFile3' in o['head']:
        print("fontfile obj", num, o['head'][:300], "stream len", len(o['stream']) if o['stream'] else None)
