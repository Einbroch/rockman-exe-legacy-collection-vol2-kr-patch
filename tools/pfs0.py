"""NSP(PFS0) 풀기: python pfs0.py <nsp> <outdir>"""
import os, struct, sys
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
with open(src, 'rb') as f:
    magic, n, stsz, _ = struct.unpack('<4sIII', f.read(16))
    assert magic == b'PFS0'
    ents = [struct.unpack('<QQII', f.read(24)) for _ in range(n)]
    strs = f.read(stsz)
    base = 16 + 24 * n + stsz
    for off, size, no, _ in ents:
        name = strs[no:strs.index(b'\0', no)].decode()
        f.seek(base + off)
        with open(os.path.join(out, name), 'wb') as o:
            left = size
            while left:
                b = f.read(min(left, 1 << 24)); o.write(b); left -= len(b)
        print(name, size)
