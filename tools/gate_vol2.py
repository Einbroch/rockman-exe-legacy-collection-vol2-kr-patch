"""Vol.2 빌드 게이트.

1) 만든 message_cht 를 LC DB 로 다시 읽어 해석 못 한 바이트 0.
2) 명령 골격: 한국어 스크립트의 명령 이름 열이 컬렉션 일본어판 같은 스크립트의 명령 이름 열과 같은가
   (번체 원본을 쓴 스크립트는 번체 원본과 바이트 동일한가). 다른 것은 목록으로.
3) 글자 코드가 폰트에 실제로 그려진 칸인가(빈 칸이면 실패).
    python tools/gate_vol2.py exe5
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import uipak  # noqa: E402
from build_vol2 import lc_scripts  # noqa: E402
from game_cfg import GROUPS, ROOT, VERS  # noqa: E402
from ksrc import lc_tokenizer, read_map  # noqa: E402
from bnscript import archive_table  # noqa: E402


def built_scripts(cfg):
    pak = (cfg.out_msg / 'message_cht.mpak').read_bytes()
    out = {}
    for a, o, s in read_map(cfg.out_msg / 'message_cht.map'):
        d = pak[o:o + s]
        if len(d) < 2:
            out[a] = None
            continue
        t = archive_table(d)
        st = sorted(set(t)) + [len(d)]
        out[a] = [d[x:min(y for y in st if y > x)] if x < len(d) else b'' for x in t]
    return out


TERMINAL = ('end', 'jump')


def skeleton(tok, b):
    ts = tok.tokens(b, 0, len(b))
    # 끝(end)·무조건 jump 뒤는 실행되지 않는다 -> 비교에서 뺀다
    for j, (kd, _, x) in enumerate(ts):
        if kd == 'cmd' and x.name in TERMINAL:
            ts = ts[:j + 1]
            break
    return [x.name for kd, _, x in ts if kd == 'cmd'], sum(1 for kd, _, _ in ts if kd == 'raw'), \
        [x for kd, _, x in ts if kd == 'chr']


def gate(g):
    sys.stdout.reconfigure(encoding='utf-8')
    ok = True
    used = set()
    for key in GROUPS[g]:
        cfg = VERS[key]
        tok = lc_tokenizer(cfg)
        new = built_scripts(cfg)
        jp = lc_scripts(cfg, 'jap')
        cht = lc_scripts(cfg, 'cht')
        stat = Counter()
        diffs = []
        for a, scr in new.items():
            if scr is None:
                continue
            if len(scr) != len(cht[a]):
                diffs.append((a, -1, f'스크립트 수 {len(scr)} != {len(cht[a])}'))
                continue
            for i, b in enumerate(scr):
                if b == cht[a][i]:
                    stat['cht 그대로'] += 1
                    continue
                cmds, raw, chars = skeleton(tok, b)
                used |= {c for c in chars if isinstance(c, int)}
                jraw_b = [bb for kd, bb, _ in tok.tokens(jp[a][i], 0, len(jp[a][i])) if kd == 'raw'] if jp.get(a) and i < len(jp[a]) else []
                if raw and raw > len(jraw_b):
                    stat['raw'] += 1
                    diffs.append((a, i, f'해석 못 한 바이트 {raw}'))
                    continue
                jcmds, jraw, _ = skeleton(tok, jp[a][i]) if jp.get(a) and i < len(jp[a]) else ([], 0, [])
                # 일본어판 E5/E6 끝 뒤 공백·화면 정리 차이는 허용하지 않는다: 그대로 보고
                if cmds == jcmds:
                    stat['골격 일치'] += 1
                elif cmds[:len(jcmds)] == jcmds and jcmds and jcmds[-1] not in TERMINAL:
                    stat['다음 스크립트로 흘러감(한글판이 이어 붙임)'] += 1
                else:
                    stat['골격 다름'] += 1
                    diffs.append((a, i, f'명령 {len(cmds)}개 vs 일본어 {len(jcmds)}개 ' + first_diff(cmds, jcmds)))
        print(key, dict(stat))
        (ROOT / 'build' / f'gate_{key}.tsv').write_text(
            ''.join(f'{a:#x}\t{i}\t{m}\n' for a, i, m in diffs), encoding='utf-8')
        if stat['raw']:
            ok = False
    # 폰트: 쓰인 코드 칸이 비어 있으면 실패
    cfg0 = VERS[GROUPS[g][0]]
    pages = [uipak.read(cfg0.out_ui / f'font8x16_cht_{p:02d}.pak')[2] for p in range(6)]
    empty = [c for c in used if c and not pages[c // 512][((c % 512) // 32) * 64:((c % 512) // 32) * 64 + 64,
                                                        (c % 32) * 32:(c % 32) * 32 + 32, 3].any()]
    print(g, '쓰인 코드', len(used), '빈 칸에 찍히는 코드', len(empty), sorted(empty)[:20])
    if empty:
        ok = False
    print('게이트', '통과' if ok else '실패')
    return ok


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f'@{i} {x}≠{y}'
    return f'길이만 다름(끝: {a[len(b):][:3] or b[len(a):][:3]})'


if __name__ == '__main__':
    sys.exit(0 if all(gate(g) for g in sys.argv[1:]) else 1)
