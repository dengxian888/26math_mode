import re
exec(open('extract_pdf.py', encoding='utf-8').read().split("def unescape_lit")[0])

for num in [45, 49, 47, 51, 53, 56, 57, 58, 60]:
    o = objs.get(num)
    if not o:
        print(num, "MISSING")
        continue
    print("obj", num, o['head'][:300])
    two, cmap = font_info(num)
    print("   two-byte:", two, "cmap entries:", len(cmap), "sample:", list(cmap.items())[:5])
