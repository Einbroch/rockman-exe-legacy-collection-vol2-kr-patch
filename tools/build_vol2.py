"""Vol.2 한국어 빌드: GBA 한글 롬 대사 -> 번체(cht) 칸 message_cht.mpak/.map + 폰트.

    python tools/build_vol2.py exe5 [--report]

코드 배치: 번체 폰트 보존 칸(기호·가나·아이콘, build/cht_symbols_<게임>.json)은 그대로, 나머지 칸에 한글을 배정.
"""
from __future__ import annotations

import json
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bnscript import archive_table, load_tbl  # noqa: E402
from game_cfg import GROUPS, ROOT, VERS  # noqa: E402
from ksrc import NL, k_archives, lc_tokenizer, read_map  # noqa: E402

NORMALIZE = {'⋯': '…', '、': ','}
# 제니 기호: 번체 폰트에 [z] 칸이 없으면(EXE5·6) Ψ 칸이 제니 그림이다
ZENNY_ALIAS = 'Ψ'


def lc_scripts(cfg, lang):
    """컬렉션 mpak 을 아카이브·스크립트 번호별 바이트로."""
    pak = (cfg.msg_dir / f'message_{lang}.mpak').read_bytes()
    out = {}
    for a, o, s in read_map(cfg.msg_dir / f'message_{lang}.map'):
        d = pak[o:o + s]
        if len(d) < 2:
            out[a] = None
            continue
        t = archive_table(d)
        st = sorted(set(t)) + [len(d)]
        out[a] = [d[x:min(y for y in st if y > x)] if x < len(d) else b'' for x in t]
    return out


def simple_scripts(cfg):
    """컬렉션 일본어 mpak 을 본 DB 와 간이 DB 로 읽어, 간이 DB 쪽이 해석 못 한 바이트가 적은 스크립트."""
    main, simp = lc_tokenizer(cfg), lc_tokenizer(cfg, simple=True)
    out = set()
    for a, scr in lc_scripts(cfg, 'jap').items():
        for i, b in enumerate(scr or ()):
            if not b:
                continue
            rm = sum(1 for k, _, _ in main.tokens(b, 0, len(b)) if k == 'raw')
            if rm and sum(1 for k, _, _ in simp.tokens(b, 0, len(b)) if k == 'raw') < rm:
                out.add((a, i))
    return out


def is_jp(ch):
    return any(('぀' <= c <= 'ヿ' and c not in '・ー゛゜') or '一' <= c <= '鿿' for c in ch)


def report(cfg):
    sys.stdout.reconfigure(encoding='utf-8')
    simple = simple_scripts(cfg)
    arcs = k_archives(cfg, simple, {a: len(x) for a, x in jp.items() if x})
    hows = Counter(v['how'] for v in arcs.values())
    print(cfg.key, '간이 스크립트', len(simple), '방법', dict(hows))
    rows = []
    for a, v in arcs.items():
        if 'scripts' not in v:
            rows.append((a, v['how'], 0, 0, 0, ''))
            continue
        raw = sum(1 for t in v['scripts'].values() for kd, _, _ in t if kd == 'raw')
        jp = [x for t in v['scripts'].values() for kd, _, x in t if kd == 'chr' and is_jp(x)]
        bad = Counter(s for s in v['status'].values() if s != 'end')
        bad = ','.join(f'{x}{c}' for x, c in bad.items()) or 0
        if raw or jp or bad or v['how'] not in ('ptr', 'inplace'):
            rows.append((a, v['how'], raw, len(jp), bad, ''.join(jp[:30])))
    for r in rows:
        print(f'{r[0]:#x} {r[1]:<14} raw={r[2]:<4} jp={r[3]:<5} unend={r[4]:<3} {r[5]}')
    return arcs


def newline_byte(cfg):
    dec, _ = load_tbl(cfg.jp_tbl)
    return [b for b, v in dec.items() if v == NL][0]


def lc_codes(b, cfg):
    """번체 스크립트 바이트에서 쓰는 글자 코드."""
    return {x for kd, _, x in lc_tokenizer(cfg).tokens(b, 0, len(b)) if kd == 'chr' and isinstance(x, int)}


def parse(cfg):
    """{롬주소: [스크립트 번호별 ('k', 토큰) | ('cht', 바이트)]}, 글자 사용량, 보존할 번체 코드, 통계."""
    simple = simple_scripts(cfg)
    jp = lc_scripts(cfg, 'jap')
    arcs = k_archives(cfg, simple, {a: len(x) for a, x in jp.items() if x})
    cht = lc_scripts(cfg, 'cht')
    plan, usage, keep, why = {}, Counter(), set(), Counter()
    fallback_log = []
    for a, scr in cht.items():
        if scr is None:
            continue
        v = arcs.get(a, {})
        tbl = v.get('table')
        whole = None
        if 'scripts' not in v:
            whole = v.get('how', 'missing')
        elif len(tbl) > len(scr):
            whole = f'표 길이 {len(tbl)}>{len(scr)}'
        elif v['how'].endswith('=orig'):
            whole = '한글판 미번역(원본 그대로)'
        row = []
        for i, b in enumerate(scr):
            reason = whole
            if (a, i) in cfg.text_fixes:
                row.append(('fix', cfg.text_fixes[(a, i)]))
                for run in cfg.text_fixes[(a, i)]:
                    for c in run.replace('|', ''):
                        usage[c] += 1
                continue
            if reason is None and i >= len(tbl):
                reason = '컬렉션이 덧붙인 스크립트'
            if reason is None:
                if not b:
                    reason = '번체 빈 스크립트'
                elif tbl[i] not in v['scripts']:
                    reason = '한글 스크립트 없음'
                else:
                    toks = v['scripts'][tbl[i]]
                    st = v['status'][tbl[i]]
                    if any(kd == 'raw' for kd, _, _ in toks):
                        reason = '해석 못 한 바이트'
                    elif any(kd == 'chr' and is_jp(x) for kd, _, x in toks):
                        reason = '가나·한자 남음'
                    elif st not in ('end', 'bound') and not (st == 'eof' and v['comp']):
                        reason = '끝 없음:' + st
            if reason:
                row.append(('cht', b, reason))
            else:
                toks = v['scripts'][tbl[i]]
                row.append(('k', toks))
                for kd, _, x in toks:
                    if kd == 'chr' and x != NL:
                        usage[NORMALIZE.get(x, x)] += 1
        plan[a] = row
    # 번역 메모리로 메우기: 번체로 남을 스크립트의 일본어 글자 구간이 전부 메모리에 있으면 일본어판 골격에 옮겨 심는다
    tm = build_tm(cfg, plan, jp)
    lc_tok = lc_tokenizer(cfg)
    jdec = lc_jp_decoder(cfg)
    filled = 0
    for a, row in plan.items():
        for i, item in enumerate(row):
            if item[0] != 'cht':
                continue
            _, b, reason = item
            jb = jp[a][i] if jp.get(a) and i < len(jp[a]) else b''
            runs = [jdec(r) for r in runs_of(lc_tok.tokens(jb, 0, len(jb)))] if reason != '번체 빈 스크립트' else []
            if runs and any(is_jp(r) for r in runs) and all(r in tm for r in runs):
                ko = [tm[r] for r in runs]
                row[i] = ('fix', ko)
                for run in ko:
                    for c in run.replace('|', ''):
                        usage[NORMALIZE.get(c, c)] += 1
                filled += 1
                why['번역 메모리로 메움'] += 1
                continue
            row[i] = ('cht', b)
            keep |= lc_codes(b, cfg)
            why[reason.split(':')[0]] += 1
            if b and reason != '번체 빈 스크립트':
                fallback_log.append((a, i, reason))
    return plan, usage, keep, why, fallback_log


def lc_jp_decoder(cfg):
    d, _ = load_tbl(cfg.lc_jp_tbl)
    ch = {b: v for b, v in d.items()}
    nl = newline_byte(cfg)

    def dec(raw):
        out, p = [], 0
        while p < len(raw):
            if raw[p:p + len(nl)] == nl:
                out.append('\n')
                p += len(nl)
            elif raw[p:p + 2] in ch:
                out.append(ch[raw[p:p + 2]])
                p += 2
            else:
                out.append('?')
                p += 1
        return ''.join(out)
    return dec


TM_SOURCES = {
    4: ['Rockman exe 4/_work/exe4-kr/translations/story_authored/*.json'],
    5: ['Rockman exe 5/_work/exe5-kr/translations/story/*.json'],
    6: ['Rockman exe 6/_work/exe6-kr/translations/story/*.json',
        'Rockman exe 6/_work/exe6-kr/translations/story/src/*.json'],
}


def build_tm(cfg, plan, jp):
    """일본어 글자 구간 -> 한국어('|' = 줄바꿈). GBA 한글판 번역 자료 + 이번 빌드에서 짝이 맞은 구간."""
    import glob
    from game_cfg import CLUDE
    tm = {}
    for pat in TM_SOURCES[cfg.n]:
        for f in glob.glob(str(CLUDE / pat)):
            try:
                d = json.loads(Path(f).read_text(encoding='utf-8'))
            except Exception:
                continue
            for k, v in (d.get('by_source') or {}).items():
                if isinstance(v, str) and v:
                    tm.setdefault(k, v.replace('\n', '|'))
    lc_tok = lc_tokenizer(cfg)
    jdec = lc_jp_decoder(cfg)
    for a, row in plan.items():
        for i, item in enumerate(row):
            if item[0] != 'k' or not jp.get(a) or i >= len(jp[a]):
                continue
            jr = [jdec(r) for r in runs_of(lc_tok.tokens(jp[a][i], 0, len(jp[a][i])))]
            kr = []
            cur = None
            for kd, _, x in item[1]:
                if kd == 'chr':
                    cur = (cur or '') + ('|' if x == NL else x)
                else:
                    if cur is not None:
                        kr.append(cur)
                    cur = None
            if cur is not None:
                kr.append(cur)
            if len(jr) == len(kr):
                for j, k in zip(jr, kr):
                    tm.setdefault(j, k)
    return tm


# 번체 폰트 칸이 한국어 문장에 어색한 기호(쉼표가 칸 가운데 높이) -> 새 칸에 그린다
FORCE_DRAW = {','}


def assign(cfg, usage, keep):
    """글자 -> 번체 코드. 기호는 번체 폰트의 같은 기호 칸으로, 나머지(한글 등)는 빈 칸으로."""
    syms = cfg.symbols()
    by_char = {}
    for c, ch in sorted(syms.items()):
        by_char.setdefault(ch, c)
    codes = {}
    need = []
    if '[z]' not in by_char and ZENNY_ALIAS in by_char:
        by_char['[z]'] = by_char[ZENNY_ALIAS]
    for ch in usage:
        if ch in by_char and ch not in FORCE_DRAW:
            codes[ch] = by_char[ch]
        else:
            need.append(ch)
    reserved = set(syms) | keep
    free = [c for c in range(1, 6 * 512) if c not in reserved]
    need.sort(key=lambda c: (not ('가' <= c <= '힣'), c))
    if len(need) > len(free):
        raise ValueError(f'폰트 칸 부족: 필요 {len(need)} 빈 칸 {len(free)}')
    for ch in need:
        codes[ch] = free.pop(0)
    return codes, need


def lc_bytes(code):
    return bytes([0x64 + (code >> 8), code & 0xFF])


def trader_fix(cfg):
    """LC DB 의 상인 명령이 GBA 보다 1바이트 길면 그 바이트를 컬렉션 일본어판에서 가져온다."""
    return cfg.lc_db != cfg.db


def emit(cfg, plan, codes):
    nl = newline_byte(cfg)
    jp = lc_scripts(cfg, 'jap')
    cht_pak = (cfg.msg_dir / 'message_cht.mpak').read_bytes()
    ents = read_map(cfg.msg_dir / 'message_cht.map')
    lc_tok = lc_tokenizer(cfg)
    out = {}
    transplanted = []
    for a, o, sz in ents:
        if a not in plan:
            out[a] = cht_pak[o:o + sz]
            continue
        scripts = []
        for i, (kind, val) in enumerate(plan[a]):
            if kind == 'cht':
                scripts.append(val)
                continue
            if kind == 'fix':
                scripts.append(apply_fix(cfg, jp[a][i], val, codes, nl, lc_tok))
                continue
            jb = jp[a][i] if jp.get(a) and i < len(jp[a]) else b''
            jnames = {t[2].name for t in lc_tok.tokens(jb, 0, len(jb)) if t[0] == 'cmd'}
            b = bytearray()
            toks = val
            # 끝 명령 뒤 공백만 남으면 버린다
            for kd, raw, x in toks:
                if kd == 'cmd' and x.name == 'soundPlay' and 'soundPlay' not in jnames:
                    continue   # 컬렉션 일본어판이 지운 효과음 명령
                if kd == 'cmd':
                    if x.name in ('startChipTrader', 'startBugFragTrader') and trader_fix(cfg):
                        hits = [t for t in lc_tok.tokens(jb, 0, len(jb)) if t[0] == 'cmd' and t[2].name == x.name]
                        extra = hits[0][1][len(raw):len(raw) + 1] if hits else b'\xff'
                        b += raw + extra
                    else:
                        b += raw
                elif x == NL:
                    b += nl
                else:
                    b += lc_bytes(codes[NORMALIZE.get(x, x)])
            b = bytes(b)
            fixed = transplant(cfg, b, jb, lc_tok, nl)
            if fixed is not None:
                transplanted.append((a, i))
                b = fixed
            scripts.append(b)
        # 같은 바이트 스크립트는 하나로(번체 원본 표의 공유 구조 대신 내용 기준)
        n = len(scripts)
        pos = 2 * n
        offs, body, seen = [], bytearray(), {}
        for s in scripts:
            if s in seen:
                offs.append(seen[s])
                continue
            seen[s] = pos + len(body)
            offs.append(seen[s])
            body += s
        if pos + len(body) > 0xFFFF:
            big = sorted(((len(x), j, plan[a][j][0]) for j, x in enumerate(scripts)), reverse=True)[:3]
            raise ValueError(f'{cfg.key} {a:#x}: 아카이브 64KB 초과, 큰 스크립트 {big}')
        blob = b''.join(struct.pack('<H', x) for x in offs) + bytes(body)
        if len(blob) > 0xFFFF:
            raise ValueError(f'{cfg.key} {a:#x}: 아카이브 64KB 초과')
        out[a] = blob
    cfg.out_msg.mkdir(parents=True, exist_ok=True)
    pak = bytearray()
    entries = []
    for a, _, _ in ents:
        entries.append((a, len(pak), len(out[a])))
        pak += out[a]
    orig_m = (cfg.msg_dir / 'message_cht.map').read_bytes()
    m = orig_m[:12] + b''.join(struct.pack('<III', *e) for e in entries)
    (cfg.out_msg / 'message_cht.mpak').write_bytes(bytes(pak))
    (cfg.out_msg / 'message_cht.map').write_bytes(m)
    print(cfg.key, 'mpak', len(pak), '아카이브', len(out), '일본어판 골격으로 옮겨 심음', len(transplanted))
    (ROOT / 'build' / f'{cfg.key}_transplant.tsv').write_text(''.join(f'{a:#x}\t{i}\n' for a, i in transplanted), encoding='utf-8')


TERMINAL = ('end', 'jump')


def cut_terminal(toks):
    for j, (kd, _, x) in enumerate(toks):
        if kd == 'cmd' and (x.name in TERMINAL or x.ends == 'always'):
            return toks[:j + 1]
    return toks


def runs_of(toks):
    """연속 글자 구간(줄바꿈 포함) 바이트 목록."""
    out, cur = [], None
    for kd, raw, _ in toks:
        if kd == 'chr':
            cur = (cur or b'') + raw
        else:
            if cur is not None:
                out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


def transplant(cfg, kb, jb, lc_tok, nl):
    """한국어 스크립트의 명령 골격이 컬렉션 일본어판과 다르면(컬렉션이 GBA 스크립트를 고친 곳)
    일본어판 골격에 한국어 글자 구간을 차례로 옮겨 심는다. 구간 수가 같을 때만. 아니면 None."""
    if not jb:
        return None
    kt = cut_terminal(lc_tok.tokens(kb, 0, len(kb)))
    jt = cut_terminal(lc_tok.tokens(jb, 0, len(jb)))
    kc = [x.name for kd, _, x in kt if kd == 'cmd']
    jc = [x.name for kd, _, x in jt if kd == 'cmd']
    if kc == jc or (kc[:len(jc)] == jc and jc and jc[-1] not in TERMINAL):
        return None
    kr = runs_of(kt)
    if len(kr) != len(runs_of(lc_tok.tokens(jb, 0, len(jb)))):
        return None
    out, it, in_run = bytearray(), iter(kr), False
    for kd, raw, _ in lc_tok.tokens(jb, 0, len(jb)):
        if kd == 'chr':
            if not in_run:
                out += next(it)
                in_run = True
            continue
        in_run = False
        out += raw
    return bytes(out)


def apply_fix(cfg, jb, runs, codes, nl, lc_tok):
    """컬렉션 일본어판 스크립트의 글자 구간(줄바꿈 포함 연속 글자)을 차례로 한국어로 바꾼다."""
    out = bytearray()
    runs = list(runs)
    in_run = False
    for kd, raw, x in lc_tok.tokens(jb, 0, len(jb)):
        if kd == 'chr':
            if not in_run:
                in_run = True
                text = runs.pop(0)
                for j, part in enumerate(text.split('|')):   # | = 줄바꿈
                    if j:
                        out += nl
                    for c in part:
                        out += lc_bytes(codes[NORMALIZE.get(c, c)])
            continue
        in_run = False
        out += raw
    if runs:
        raise ValueError(f'번역 구간이 남았다: {runs}')
    return bytes(out)


def main_group(g):
    sys.stdout.reconfigure(encoding='utf-8')
    keys = GROUPS[g]
    parts, usage, keep = [], Counter(), set()
    for key in keys:
        cfg = VERS[key]
        plan, u, kp, why, log = parse(cfg)
        print(key, '번체 원본 유지 사유', dict(why))
        (ROOT / 'build').mkdir(exist_ok=True)
        (ROOT / 'build' / f'{key}_fallback.tsv').write_text(
            ''.join(f'{a:#x}\t{i}\t{r}\n' for a, i, r in log), encoding='utf-8')
        usage.update(u)
        keep |= kp
        parts.append((cfg, plan))
    cfg0 = parts[0][0]
    codes, new = assign(cfg0, usage, keep)
    nonh = [c for c in new if not ('가' <= c <= '힣')]
    print(g, '글자', len(usage), '새 칸', len(new), '한글 외 새 글자', ''.join(nonh), '최대 코드', max(codes.values()))
    for cfg, plan in parts:
        emit(cfg, plan, codes)
    (ROOT / 'build' / f'{g}_codes.json').write_text(
        json.dumps({'codes': codes, 'keep': sorted(keep), 'new': new}, ensure_ascii=False, indent=0), encoding='utf-8')
    for cfg, _ in parts:
        word_utf(cfg, codes)
    import fonts_vol2
    fonts_vol2.build(cfg0, codes, new, keep)
    # 대화창은 비트맵 폰트가 아니라 HD 글꼴(data/font/cht_mojiFont.fnt)로 그린다
    import moji_ko
    n = moji_ko.patch(cfg0.ui_dir.parent / 'font' / 'cht_mojiFont.fnt',
                      cfg0.out_ui.parent / 'font' / 'cht_mojiFont.fnt', codes, new, keep)
    print(g, '대화창 글꼴 한글', n)


def word_utf(cfg, codes):
    """word_utf_cht.map(u16 개수 + (코드, UTF-16) 쌍): 코드 -> 글자 역변환 표. 한글을 배정한 칸은 한글로."""
    src = cfg.msg_dir / 'word_utf_cht.map'
    if not src.exists():
        return
    m = bytearray(src.read_bytes())
    n = struct.unpack_from('<H', m, 0)[0]
    by_code = {c: ch for ch, c in codes.items() if len(ch) == 1}
    changed = 0
    for i in range(n):
        code, _ = struct.unpack_from('<HH', m, 2 + 4 * i)
        if code in by_code:
            struct.pack_into('<H', m, 2 + 4 * i + 2, ord(by_code[code]))
            changed += 1
    cfg.out_msg.mkdir(parents=True, exist_ok=True)
    (cfg.out_msg / 'word_utf_cht.map').write_bytes(bytes(m))
    print(cfg.key, 'word_utf 갱신', changed)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    for g in args:
        if '--report' in sys.argv:
            for key in GROUPS.get(g, [g]):
                report(VERS[key])
        else:
            main_group(g)
