import re, zlib, sys

PATH = r"赛题\数理大赛赛题\电力市场中的用电申报与风险决策.pdf"
data = open(PATH, 'rb').read()

objs = {}
for m in re.finditer(rb'(?<![0-9])(\d+)\s+(\d+)\s+obj\b', data):
    num = int(m.group(1))
    start = m.end()
    end = data.find(b'endobj', start)
    if end < 0:
        continue
    body = data[start:end]
    sm = re.search(rb'stream\r?\n', body)
    stream = None
    head = body
    if sm:
        head = body[:sm.start()]
        sstart = sm.end()
        send = body.rfind(b'endstream')
        if send > sstart:
            stream = body[sstart:send]
    objs[num] = {'head': head, 'stream': stream}


def inflate(raw, head):
    if raw is None:
        return None
    if b'/FlateDecode' in head:
        try:
            return zlib.decompressobj().decompress(raw)
        except Exception:
            return None
    return raw


for num, o in list(objs.items()):
    if b'/ObjStm' in o['head']:
        dec = inflate(o['stream'], o['head'])
        if dec is None:
            continue
        n = int(re.search(rb'/N\s+(\d+)', o['head']).group(1))
        first = int(re.search(rb'/First\s+(\d+)', o['head']).group(1))
        nums = list(map(int, dec[:first].split()))
        pairs = [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]
        for i, (onum, off) in enumerate(pairs[:n]):
            if onum in objs:
                continue
            s = first + off
            e = first + pairs[i + 1][1] if i + 1 < len(pairs) else len(dec)
            objs[onum] = {'head': dec[s:e], 'stream': None}


def ref(head, key):
    m = re.search(rb'/' + key + rb'\s*(\d+)\s+\d+\s+R', head)
    return int(m.group(1)) if m else None


def get_attr(num, key, depth=0):
    o = objs.get(num)
    if not o or depth > 12:
        return None
    v = ref(o['head'], key)
    if v is not None:
        return v
    p = ref(o['head'], b'Parent')
    if p is not None:
        return get_attr(p, key, depth + 1)
    return None


def parse_cmap(txt):
    cmap = {}
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar', txt, re.S):
        for src, dst in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            cmap[int(src, 16)] = bytes.fromhex(dst.decode()).decode('utf-16-be', 'ignore')
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange', txt, re.S):
        for m in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(?:<([0-9A-Fa-f]+)>|\[(.*?)\])', blk, re.S):
            lo, hi = int(m.group(1), 16), int(m.group(2), 16)
            if m.group(3) is not None:
                base = bytes.fromhex(m.group(3).decode())
                b0 = int.from_bytes(base, 'big')
                nb = len(base)
                for c in range(lo, hi + 1):
                    try:
                        cmap[c] = (b0 + c - lo).to_bytes(nb, 'big').decode('utf-16-be', 'ignore')
                    except Exception:
                        pass
            else:
                items = re.findall(rb'<([0-9A-Fa-f]+)>', m.group(4) or b'')
                for i, it in enumerate(items):
                    cmap[lo + i] = bytes.fromhex(it.decode()).decode('utf-16-be', 'ignore')
    return cmap


fontcache = {}


def font_info(fnum):
    if fnum in fontcache:
        return fontcache[fnum]
    o = objs.get(fnum)
    if not o:
        fontcache[fnum] = (True, {})
        return fontcache[fnum]
    h = o['head']
    two = b'/Type0' in h
    tu = ref(h, b'ToUnicode')
    cmap = {}
    if tu and objs.get(tu) and objs[tu]['stream'] is not None:
        dec = inflate(objs[tu]['stream'], objs[tu]['head'])
        if dec:
            cmap = parse_cmap(dec)
    fontcache[fnum] = (two, cmap)
    return fontcache[fnum]


def unescape_lit(s):
    out = bytearray()
    i = 0
    while i < len(s):
        c = s[i]
        if c == 0x5c and i + 1 < len(s):
            n = s[i + 1]
            mp = {0x6e: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
            if n in mp:
                out.append(mp[n]); i += 2; continue
            if 0x30 <= n <= 0x37:
                j = i + 1
                oct_ = b''
                while j < len(s) and len(oct_) < 3 and 0x30 <= s[j] <= 0x37:
                    oct_ += bytes([s[j]]); j += 1
                out.append(int(oct_, 8) & 0xFF); i = j; continue
            out.append(n); i += 2; continue
        out.append(c); i += 1
    return bytes(out)


def decode_str(raw, two, cmap):
    res = []
    if two:
        for i in range(0, len(raw) - 1, 2):
            code = (raw[i] << 8) | raw[i + 1]
            res.append(cmap.get(code, ''))
    else:
        for b in raw:
            res.append(cmap.get(b, chr(b) if 32 <= b < 127 else ''))
    return ''.join(res)


tok_re = re.compile(rb'\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>|\[|\]|/[^\s/\[\]<>(){}]+|[-+]?(?:\d+\.?\d*|\.\d+)|[A-Za-z\'"*]+')


def extract(content, page_fonts):
    lines, cur = [], []
    last_y = [None]
    font = [None]

    def flush():
        t = ''.join(cur).strip()
        if t:
            lines.append(t)
        cur.clear()

    toks = tok_re.findall(content)
    operands = []
    arr = None
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if arr is not None:
            if t == b']':
                operands = [arr]
                arr = None
            elif t == b'[':
                arr.append(b'[')
            else:
                arr.append(t)
            i += 1
            continue
        if t == b'[':
            arr = []
        elif t in (b'Tf',):
            if len(operands) >= 2 and operands[-2].startswith(b'/'):
                font[0] = page_fonts.get(operands[-2][1:].decode())
            operands = []
        elif t in (b'Td', b'TD'):
            if len(operands) >= 2:
                try:
                    dy = float(operands[-1])
                except Exception:
                    dy = 0.0
                if abs(dy) > 0.3:
                    flush()
                    last_y[0] = None
            operands = []
        elif t == b'Tm':
            if len(operands) >= 6:
                try:
                    y = float(operands[-2])
                except Exception:
                    y = 0.0
                if last_y[0] is not None and abs(y - last_y[0]) > 0.3:
                    flush()
                last_y[0] = y
            operands = []
        elif t == b'T*':
            flush(); last_y[0] = None; operands = []
        elif t == b'Tj':
            if operands:
                s = operands[-1]
                raw = b''
                if s.startswith(b'('):
                    raw = unescape_lit(s[1:-1])
                elif s.startswith(b'<'):
                    hx = re.sub(rb'\s', b'', s[1:-1])
                    try:
                        raw = bytes.fromhex(hx.decode())
                    except Exception:
                        raw = b''
                two, cmap = font[0] if font[0] else (True, {})
                cur.append(decode_str(raw, two, cmap))
            operands = []
        elif t in (b"'", b'"'):
            flush(); last_y[0] = None
            if operands:
                s = operands[-1]
                if s.startswith(b'('):
                    raw = unescape_lit(s[1:-1])
                    two, cmap = font[0] if font[0] else (True, {})
                    cur.append(decode_str(raw, two, cmap))
            operands = []
        elif t == b'TJ':
            arr2 = operands[-1] if operands and isinstance(operands[-1], list) else []
            two, cmap = font[0] if font[0] else (True, {})
            for s in arr2:
                if s.startswith(b'('):
                    raw = unescape_lit(s[1:-1])
                elif s.startswith(b'<'):
                    hx = re.sub(rb'\s', b'', s[1:-1])
                    try:
                        raw = bytes.fromhex(hx.decode())
                    except Exception:
                        raw = b''
                else:
                    continue
                cur.append(decode_str(raw, two, cmap))
            operands = []
        elif t == b'BT':
            operands = []
        elif t == b'ET':
            flush(); last_y[0] = None; operands = []
        else:
            if t.startswith(b'/') or re.fullmatch(rb'[-+]?(?:\d+\.?\d*|\.\d+)', t):
                operands.append(t)
                if len(operands) > 8:
                    operands.pop(0)
            else:
                operands = []
        i += 1
    flush()
    return lines


pages = sorted(n for n, o in objs.items() if re.search(rb'/Type\s*/Page[^s]', o['head']))

all_lines = []
for pi, pnum in enumerate(pages, 1):
    h = objs[pnum]['head']
    fonts = {}
    res = ref(h, b'Resources')
    if res and objs.get(res):
        rh = objs[res]['head']
        fm = re.search(rb'/Font\s*<<(.*?)>>', rh, re.S)
        fdict = fm.group(1) if fm else b''
        if not fdict:
            fr = ref(rh, b'Font')
            if fr and objs.get(fr):
                fdict = objs[fr]['head']
        for name, num in re.findall(rb'/(\w+)\s+(\d+)\s+\d+\s+R', fdict):
            fonts[name.decode()] = font_info(int(num))
    cnums = re.search(rb'/Contents\s*\[(.*?)\]', h, re.S)
    cdata = b''
    if cnums:
        for num in re.findall(rb'(\d+)\s+\d+\s+R', cnums.group(1)):
            o = objs.get(int(num))
            if o and o['stream']:
                cdata += (inflate(o['stream'], o['head']) or b'') + b'\n'
    else:
        c = ref(h, b'Contents')
        if c and objs.get(c) and objs[c]['stream']:
            cdata = inflate(objs[c]['stream'], objs[c]['head']) or b''
    lines = extract(cdata, fonts)
    all_lines.append((pi, lines))
    print(f"page {pi}: {len(lines)} lines, content {len(cdata)} bytes, fonts {list(fonts)}", file=sys.stderr)

with open('problem.txt', 'w', encoding='utf-8') as f:
    for pi, lines in all_lines:
        f.write(f"\n===== PAGE {pi} =====\n")
        for ln in lines:
            f.write(ln + "\n")
print("done", file=sys.stderr)
