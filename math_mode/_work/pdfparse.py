import re, zlib, sys, json

PATH = r"赛题\数理大赛赛题\电力市场中的用电申报与风险决策.pdf"
data = open(PATH, 'rb').read()

# ---------- collect top-level objects ----------
objs = {}   # num -> dict(text of object body, stream bytes or None)
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
        for cand in (raw, raw.rstrip(b'\r\n'), raw[1:], raw[2:]):
            try:
                return zlib.decompress(cand)
            except Exception:
                continue
        try:
            d = zlib.decompressobj()
            return d.decompress(raw)
        except Exception:
            return None
    return raw

# ---------- expand object streams ----------
expanded = {}
for num, o in list(objs.items()):
    if b'/Type' in o['head'] and b'/ObjStm' in o['head']:
        dec = inflate(o['stream'], o['head'])
        if dec is None:
            continue
        n = int(re.search(rb'/N\s+(\d+)', o['head']).group(1))
        first = int(re.search(rb'/First\s+(\d+)', o['head']).group(1))
        nums = list(map(int, dec[:first].split()))
        pairs = [(nums[i], nums[i+1]) for i in range(0, len(nums), 2)]
        for i, (onum, off) in enumerate(pairs):
            if onum in objs:
                continue
            s = first + off
            e = first + pairs[i+1][1] if i+1 < len(pairs) else len(dec)
            expanded[onum] = {'head': dec[s:e], 'stream': None}
objs.update(expanded)
print("objects:", len(objs))

def get(ref_num):
    return objs.get(ref_num)

def ref(head, key):
    m = re.search(rb'/' + key + rb'\s+(\d+)\s+\d+\s+R', head)
    return int(m.group(1)) if m else None

def dict_of(num, depth=0):
    o = objs.get(num)
    if not o or depth > 5:
        return b''
    return o['head']

# ---------- find pages ----------
pages = []
for num, o in objs.items():
    h = o['head']
    if re.search(rb'/Type\s*/Page\b', h):
        pages.append(num)
pages.sort()
print("pages found:", pages)

def get_attr(num, key, depth=0):
    """look up key in object's dict, following /Parent if absent"""
    o = objs.get(num)
    if not o or depth > 12:
        return None, None
    h = o['head']
    v = ref(h, key)
    if v is not None:
        return v, h
    p = ref(h, b'Parent')
    if p is not None:
        return get_attr(p, key, depth+1)
    return None, None
