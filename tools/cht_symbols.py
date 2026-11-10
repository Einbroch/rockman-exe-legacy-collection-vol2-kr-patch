"""번체 폰트(6페이지)에서 기호·아이콘 칸을 찾아 {코드: 글자} 표로 저장한다.

기준: 간체·일본어 폰트에서 문자표상 한자가 아닌 칸(숫자·영문·가나·기호·버튼)의 그림과
번체 칸 그림의 정규화 상관도 >= 0.97. 번체 전용 문자표가 없거나 틀린 판(EXE5·EXE6)이 있어 그림으로 확정한다.
    python tools/cht_symbols.py  ->  build/cht_symbols_<게임>.json
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import uipak
from bnscript import load_tbl

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / '_work' / 'romfs'


def cells(path):
    px = uipak.read(path)[2]
    return np.stack([px[(i // 32) * 64:(i // 32) * 64 + 64, (i % 32) * 32:(i % 32) * 32 + 32, 3]
                     for i in range(512)]).reshape(512, -1).astype(np.float32)


def norm(m):
    m = m - m.mean(1, keepdims=True)
    return m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-6)


def is_cjk(v):
    return all('一' <= c <= '鿿' for c in v)


def refs(game, lang, tbl, pages):
    d, _ = load_tbl(tbl)
    ch = {(b[0] - 0x64) * 256 + b[1]: v for b, v in d.items() if len(b) == 2}
    S = np.concatenate([cells(UI / game / 'data' / 'ui' / f'font8x16_{lang}_{p:02d}.pak') for p in range(pages)])
    idx = [c for c, v in ch.items() if not is_cjk(v) and c < len(S) and S[c].any()]
    return S[idx], [ch[c] for c in idx]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    for game, n in (('exe4', 4), ('exe5', 5), ('exe6', 6)):
        rs = [refs(game, 'chs', f'exeac-exe{n}-chs-utf8', 6), refs(game, 'jap', f'exeac-exe{n}-utf8', 1)]
        T = norm(np.concatenate([r[0] for r in rs]))
        names = sum((r[1] for r in rs), [])
        out = {}
        for p in range(6):
            C = cells(UI / game / 'data' / 'ui' / f'font8x16_cht_{p:02d}.pak')
            sc = norm(C) @ T.T
            for i in range(512):
                if not C[i].any():
                    continue
                j = int(sc[i].argmax())
                if sc[i, j] >= 0.97:
                    out[p * 512 + i] = names[j]
        out[0] = ' '
        # 작은 문장부호(: 、 。 등)는 상관도가 낮게 나온다 -> 문자표에서 보탠다. 표가 맞는 구간만:
        # EXE4·6 = 번체 문자표 전부, EXE5 = 번체 표가 없어 간체 표의 640 미만(기호 위치가 번체와 같음을 그림으로 확인)
        tname, lim = {4: ('exeac-exe4-cht-utf8', 4096), 5: ('exeac-exe5-chs-utf8', 640), 6: ('exeac-exe6-cht-utf8', 4096)}[n]
        d, _ = load_tbl(tname)
        for b, v in d.items():
            if len(b) != 2:
                continue
            c = (b[0] - 0x64) * 256 + b[1]
            if c < lim and not is_cjk(v) and c not in out:
                out[c] = v
        icons = (UI / game / 'data' / 'msg' / 'fixed_color_cht.txt').read_text().split()
        for x in icons:
            out.setdefault(int(x), f'[icon{x}]')
        (ROOT / 'build').mkdir(exist_ok=True)
        (ROOT / 'build' / f'cht_symbols_{game}.json').write_text(
            json.dumps({str(k): v for k, v in sorted(out.items())}, ensure_ascii=False, indent=0), encoding='utf-8')
        print(game, len(out), ''.join(v if len(v) == 1 else '' for k, v in sorted(out.items()))[:400])


if __name__ == '__main__':
    main()
