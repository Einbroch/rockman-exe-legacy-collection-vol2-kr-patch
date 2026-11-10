"""Vol.2 번체 폰트(font8x16_cht 본문, subfont_cht 메뉴) 6페이지에 한글을 그린다.

스타일은 파일마다 원본 한자 칸에서 실측한다: 흰 글자 + 오른쪽 아래 그림자(방향·색·불투명도).
보존 칸(기호·가나·아이콘·번체 원본을 그대로 쓰는 스크립트의 글자)은 건드리지 않는다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import uipak  # noqa: E402
from bnscript import load_tbl  # noqa: E402

FONTS = Path(r'D:\Games\Kor Patch\CLude\폰트\S-Core_Dream_OTF')
BODY_FONT = FONTS / 'SCDream5.otf'
MENU_FONT = FONTS / 'SCDream7.otf'
# S-Core Dream 은 KS X 1001(2,350자)뿐 — 그 밖의 음절(쌰·햣 등)은 맑은 고딕으로
FALLBACK = {BODY_FONT: Path(r'C:\Windows\Fonts\malgun.ttf'), MENU_FONT: Path(r'C:\Windows\Fonts\malgunbd.ttf')}


def cell_get(px, i):
    return px[(i // 32) * 64:(i // 32) * 64 + 64, (i % 32) * 32:(i % 32) * 32 + 32]


def cell_put(px, i, c):
    px[(i // 32) * 64:(i // 32) * 64 + 64, (i % 32) * 32:(i % 32) * 32 + 32] = c


def measure_style(px):
    """(dx, dy, 그림자 RGB, 그림자 불투명도 배율)."""
    cells = [cell_get(px, i).astype(np.int32) for i in range(512)]
    cells = [c for c in cells if (c[:, :, 3] > 0).sum() > 50]
    score = {}
    for c in cells[:200]:
        a = c[:, :, 3]
        white = (c[:, :, :3].min(2) > 225) & (a > 200)
        sh = (a > 30) & ~white
        for dx in range(4):
            for dy in range(4):
                if dx == dy == 0:
                    continue
                s = np.zeros_like(white)
                s[dy:, dx:] = white[:64 - dy, :32 - dx]
                score[(dx, dy)] = score.get((dx, dy), 0) + (s & sh).sum() - 0.5 * (s & ~sh & ~white).sum()
    dx, dy = max(score, key=score.get)
    rgb, al = [], []
    for c in cells[:200]:
        a = c[:, :, 3]
        white = (c[:, :, :3].min(2) > 225) & (a > 200)
        s = np.zeros_like(white)
        s[dy:, dx:] = white[:64 - dy, :32 - dx]
        # 그림자만 있는 칸: 흰 글자에서 1px 이상 떨어진 곳
        grow = white.copy()
        grow[1:] |= white[:-1]; grow[:-1] |= white[1:]; grow[:, 1:] |= white[:, :-1]; grow[:, :-1] |= white[:, 1:]
        only = s & ~grow & (a > 0)
        rgb.append(c[only][:, :3])
        al.append(a[only])
    rgb = np.concatenate(rgb)
    al = np.concatenate(al)
    return dx, dy, np.median(rgb, 0).astype(np.uint8), float(np.median(al)) / 255.0


def render(ch, font, box_w=27, box_h=41, top=9, ss=4):
    """글리프 알파 32x64. 세로는 「한」 기준 상자에 맞추고 가로는 box_w 안으로."""
    a = _render(ch, font, box_w, box_h, top, ss)
    if not a.any() and ch.strip() and font in FALLBACK:
        a = _render(ch, FALLBACK[font], box_w, box_h, top, ss)
    return a


def _render(ch, font, box_w, box_h, top, ss):
    size = box_h * ss
    f = ImageFont.truetype(str(font), size)
    W = size * 2
    canvas = Image.new('L', (W, W), 0)
    ImageDraw.Draw(canvas).text((size // 2, size // 2), ch, font=f, fill=255)
    ref = Image.new('L', (W, W), 0)
    ImageDraw.Draw(ref).text((size // 2, size // 2), '한', font=f, fill=255)
    rb = ref.getbbox()
    bb = canvas.getbbox()
    out = Image.new('L', (32, 64), 0)
    if bb is None:
        return np.array(out)
    x0, x1 = min(bb[0], rb[0]), max(bb[2], rb[2])
    crop = canvas.crop((x0, rb[1], x1, rb[3])).resize((box_w, box_h), Image.LANCZOS)
    out.paste(crop, ((32 - box_w) // 2 + 1, top))
    return np.array(out)


def styled(a, style):
    dx, dy, col, k = style
    sh = np.zeros_like(a)
    sh[dy:, dx:] = a[:64 - dy, :32 - dx]
    ga = a.astype(np.float32) / 255.0
    sa = sh.astype(np.float32) / 255.0 * k
    oa = ga + sa * (1 - ga)
    rgb = (255 * ga[:, :, None] + col[None, None, :].astype(np.float32) * (sa * (1 - ga))[:, :, None]) \
        / np.maximum(oa, 1e-6)[:, :, None]
    c = np.zeros((64, 32, 4), np.uint8)
    c[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    c[:, :, 3] = np.clip(oa * 255, 0, 255).astype(np.uint8)
    return c


def jp_cell_index(cfg):
    d, _ = load_tbl(cfg.lc_jp_tbl)
    return {v: (b[0] - 0x64) * 256 + b[1] for b, v in d.items() if len(b) == 2 and (b[0] - 0x64) * 256 + b[1] < 512}


def build(cfg, codes, new, keep):
    out = cfg.out_ui
    out.mkdir(parents=True, exist_ok=True)
    jp_idx = jp_cell_index(cfg)
    for prefix, font, jp_file in (('font8x16_cht', BODY_FONT, 'font8x16_jap_00'),
                                  ('subfont_cht', MENU_FONT, 'subfont_jap_00')):
        pages = [uipak.read(cfg.ui_dir / f'{prefix}_{p:02d}.pak') for p in range(6)]
        style = measure_style(pages[1][2])
        jp_px = uipak.read(cfg.ui_dir / f'{jp_file}.pak')[2]
        print(prefix, '그림자', style[:2], style[2].tolist(), round(style[3], 2))
        drawn = []
        for ch in new:
            code = codes[ch]
            page, idx = divmod(code, 512)
            if code in keep:
                raise ValueError(f'보존 칸 {code} 에 {ch} 배정')
            if not ('가' <= ch <= '힣') and ch in jp_idx and cell_get(jp_px, jp_idx[ch])[:, :, 3].any():
                cell_put(pages[page][2], idx, cell_get(jp_px, jp_idx[ch]))
                continue
            if not ('가' <= ch <= '힣'):
                drawn.append(ch)
            cell_put(pages[page][2], idx, styled(render(ch, font), style))
        for p, (raw, st, px) in enumerate(pages):
            uipak.write(out / f'{prefix}_{p:02d}.pak', raw, st, px)
        if drawn:
            print(prefix, '일본어 폰트에 없어 직접 그린 기호:', ''.join(drawn))
