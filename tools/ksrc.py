"""GBA 한글 롬(EXE4~6)에서 컬렉션 map 의 대사 아카이브를 찾아 스크립트별 토큰으로 푼다.

- 위치: 원본 롬에서 아카이브 주소(bit31 = 압축 표시 포함)를 담은 자리를 모두 찾고, 한글 롬의 같은 자리 값을 읽는다.
- 압축(LZ77 0x10): 해제. EXE5·6 은 해제본 앞 4바이트가 크기 머리.
- 한글 `lead FC lo hi` = U+AC00+n. 롬 점프 `lead FD a0..a3` 은 따라가서 이어 읽는다(GBA 한글판이 넘치는 본문을 롬에 둔 것).
- 스크립트 = 첫 'always' 종료까지(BN 점프는 스크립트 번호로만 가므로 뒤는 실행되지 않는다).
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bnscript import Cmd, Tokenizer, archive_table, load_db, load_tbl  # noqa: E402
from mpak import lz77_gba  # noqa: E402

NL = '\\n'


def read_map(path):
    m = Path(path).read_bytes()
    n = struct.unpack_from('<I', m, 0)[0]
    return [struct.unpack_from('<3I', m, 12 + i * 12) for i in range(n)]


def k_table(cfg):
    dec, _ = load_tbl(cfg.jp_tbl)
    for i in range(11172):
        dec[bytes([cfg.lead, 0xFC, i & 0xFF, i >> 8])] = chr(0xAC00 + i)
    return dec


def jump_cmd(lead):
    return Cmd('kjump', b'\xff\xff\x00\x00\x00\x00', bytes([lead, 0xFD, 0, 0, 0, 0]), 'kjump')


def tokenizer(cfg, korean=True, simple=False):
    cmds = load_db(cfg.simple_db if simple else cfg.db)
    if korean:
        cmds = cmds + [jump_cmd(cfg.lead)]
        return Tokenizer(cmds, k_table(cfg), char_first=(bytes([cfg.lead, 0xFC]),))
    dec, _ = load_tbl(cfg.jp_tbl)
    return Tokenizer(cmds, dec)


def lc_tokenizer(cfg, simple=False):
    dec = {bytes([h, lo]): (h - 0x64) * 256 + lo for h in range(0x64, 0x70) for lo in range(256)}
    jd, _ = load_tbl(cfg.jp_tbl)
    for b, v in jd.items():
        if v == NL:
            dec[b] = NL   # 줄바꿈(E8/E9)은 컬렉션도 GBA 와 같은 1바이트
    return Tokenizer(load_db(cfg.simple_db if simple else cfg.lc_db), dec)


def ptr_sites(rom, addr):
    out = []
    for v in (addr, addr | 0x80000000):
        pat = struct.pack('<I', v)
        i = rom.find(pat)
        while i >= 0:
            out.append(i)
            i = rom.find(pat, i + 1)
    return out


def load_archive(rom, addr):
    """(바이트, 압축 여부, 롬 기준 오프셋 또는 None)."""
    off = addr & 0x1FFFFFF
    if rom[off] == 0x10:
        try:
            d0, _ = lz77_gba(rom, off)
            for d in (d0, d0[4:]):
                try:
                    t = archive_table(d)
                except (ValueError, struct.error):
                    continue
                if t[0] == 2 * len(t) and max(t) <= len(d):
                    return d, True, None
        except Exception:
            pass
    return rom, False, off


def run_script(tok, data, p, rom, bound=None, limit=0x6000):
    """스크립트 하나의 토큰(점프 제거). 끝 명령 또는 경계(아카이브 안 다음 스크립트 시작)에서 멈춘다.
    롬 점프 뒤에는 경계 없이 끝 명령까지."""
    out = []
    src = data
    jumped = False
    while True:
        end = min(len(src), p + 0x10000)
        if bound is not None and not jumped:
            end = min(end, bound)
        if p >= end:
            return out, 'eof'
        for kd, b, x in tok.iter(src, p, end):
            p += len(b)
            if kd == 'cmd' and x.name == 'kjump':
                ra = struct.unpack_from('<I', b, 2)[0]
                src, p = rom, ra & 0x1FFFFFF
                jumped = True
                break
            out.append((kd, b, x))
            if kd == 'cmd' and (x.ends == 'always' or x.name == 'jump'):   # 무조건 jump 뒤는 실행되지 않는다
                return out, 'end'
            if len(out) > limit:
                return out, 'runaway'
        else:
            return out, ('bound' if not jumped and bound is not None and p >= bound else 'eof')


def locate(cfg, orig, k, addr):
    """한글 롬에서 아카이브 시작 주소와 찾은 방법."""
    sites = ptr_sites(orig, addr)
    news = {struct.unpack_from('<I', k, p)[0] & 0x7FFFFFFF for p in sites}
    if len(news) == 1:
        na = news.pop()
        return na, ('ptr' if na != addr else 'inplace')
    moved = sorted(x for x in news if x != addr)
    if len(moved) == 1:
        return moved[0], 'ptr-partial'
    if len(moved) > 1:
        # 한글판이 같은 내용 사본을 여러 벌 둔 경우(EXE4 칩 이름 등): 내용이 같으면 첫 사본
        blobs = set()
        for x in moved:
            d, comp, base = load_archive(k, x)
            blobs.add(bytes(d[:0x800]) if comp else bytes(k[base:base + 0x800]))
        if len(blobs) == 1:
            return moved[0], 'ptr-copies'
        # 표 배치만 다른 렌더러별 사본(EXE4 칩 이름 0x89BBB40/0x89C63C8): 첫 사본. 글자 검사는 스크립트별 판정이 맡는다
        return moved[0], 'ptr-first-copy'
    if not sites:
        return None, 'noptr'
    return None, 'ambiguous:' + ','.join(hex(x) for x in sorted(news))


def k_archives(cfg, simple_set=frozenset(), counts=None):
    """{롬주소: dict(table, scripts{시작: 토큰}, how, comp, status{시작: 'end'|...})}"""
    orig = cfg.orig_rom.read_bytes()
    k = cfg.k_rom.read_bytes()
    tok = tokenizer(cfg)
    tok_s = tokenizer(cfg, simple=True)
    out = {}
    for addr, _, size in read_map(cfg.msg_dir / 'message_cht.map'):
        if size < 4:
            continue
        na, how = locate(cfg, orig, k, addr)
        if na is None:
            out[addr] = {'how': how}
            continue
        data, comp, base = load_archive(k, na)
        try:
            tbl = archive_table(data, base or 0)
            odata0, _, obase0 = load_archive(orig, addr)
            try:
                n = len(archive_table(odata0, obase0 or 0))   # GBA 원본 표 칸 수
            except (ValueError, struct.error):
                n = None
            want = (counts or {}).get(addr)
            # 한글판 표 칸 수가 컬렉션 일본어판과 다르고 GBA 원본과도 다를 때만, 원본 칸 수로 다시 읽는다
            # (GBA 원본 첫 값이 칸 수가 아닌 표[0x87A7780 등]가 있어 원본 칸 수를 무조건 믿으면 안 된다)
            if n and want and n == want and n != len(tbl):
                tbl = [struct.unpack_from('<H', data, (base or 0) + 2 * j)[0] for j in range(n)]
        except ValueError:
            out[addr] = {'how': how + '+badtable', 'at': na}
            continue
        odata, ocomp, obase = load_archive(orig, addr)
        same = False
        if comp == ocomp:
            a_ = data if comp else k[base:base + 0x10000]
            b_ = odata if ocomp else orig[obase:obase + 0x10000]
            same = a_[:len(a_) if comp else 0x10000] == b_[:len(a_) if comp else 0x10000]
        scripts, status = {}, {}
        limit_len = len(data) if comp else 0x10000
        starts = sorted(set(x for x in tbl if x < limit_len))
        for i, s in enumerate(tbl):
            if s >= limit_len or s in scripts:
                continue
            nxt = [x for x in starts if x > s]
            bound = (base or 0) + (nxt[0] if nxt else limit_len)
            t = tok_s if (addr, i) in simple_set else tok
            scripts[s], status[s] = run_script(t, data, (base or 0) + s, k, bound)
        out[addr] = {'how': how + ('=orig' if same else ''), 'at': na, 'comp': comp,
                     'table': tbl, 'scripts': scripts, 'status': status}
    return out
