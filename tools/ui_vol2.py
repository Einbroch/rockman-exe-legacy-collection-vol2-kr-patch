"""Vol.2 그림 글자 도구(투명 배경 포함 RGBA).

label(): 원본 번체 글자 상자에서 배경(행별 최빈색)·채움색·어두운 색·외곽선/그림자를 재고,
그 자리를 지운 뒤 같은 모양으로 한국어를 그린다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from uilib1 import text_mask  # noqa: E402

FONTS = Path(r'D:\Games\Kor Patch\CLude\폰트\S-Core_Dream_OTF')
F = {i: FONTS / f'SCDream{i}.otf' for i in range(1, 10)}


def row_bg(orig, y0, y1, x0, x1=None):
    """행마다 [x0,x1) 의 최빈 RGBA. x0 == 'clear' 면 투명."""
    if isinstance(x0, str):
        return np.zeros((y1 - y0, 4), np.uint8)
    reg = np.ascontiguousarray(orig[y0:y1, x0:x1])
    v = reg.view(np.uint32)[:, :, 0]
    out = np.empty((y1 - y0, 4), np.uint8)
    for i in range(y1 - y0):
        u, c = np.unique(v[i], return_counts=True)
        out[i] = np.frombuffer(np.uint32(u[c.argmax()]).tobytes(), np.uint8)
    return out


def default_strip(orig, er):
    x0, y0, x1, y1 = er
    W = orig.shape[1]
    if x1 + 8 <= W:
        return (x1, x1 + 8)
    return (max(0, x0 - 8), x0)


def erase(px, orig, er, strip=None):
    x0, y0, x1, y1 = er
    if isinstance(strip, tuple) and strip and strip[0] == 'v':   # ('v', y0, y1): 세로 띠에서 열별로
        px[y0:y1, x0:x1] = col_bg(orig, strip[1:], x0, x1)[None, :, :]
        return
    strip = strip or default_strip(orig, er)
    bg = row_bg(orig, y0, y1, *strip) if not isinstance(strip, str) else row_bg(orig, y0, y1, strip)
    px[y0:y1, x0:x1] = bg[:, None, :]


def col_bg(orig, band, x0, x1):
    """열마다 band(y0,y1) 의 최빈 RGBA."""
    y0, y1 = band
    reg = np.ascontiguousarray(orig[y0:y1, x0:x1].transpose(1, 0, 2))
    v = reg.view(np.uint32)[:, :, 0]
    out = np.empty((x1 - x0, 4), np.uint8)
    for i in range(x1 - x0):
        u, c = np.unique(v[i], return_counts=True)
        out[i] = np.frombuffer(np.uint32(u[c.argmax()]).tobytes(), np.uint8)
    return out


def _premul(c):
    return c[..., :3].astype(float) * (c[..., 3:4].astype(float) / 255)


def measure(orig, box, strip, dark_text=False):
    """{'fill': [N,3], 'edge': [3], 'outline': r, 'shadow': (dx,dy), 'ink': (x0,y0,x1,y1)}"""
    x0, y0, x1, y1 = box
    bg = row_bg(orig, y0, y1, strip) if isinstance(strip, str) else row_bg(orig, y0, y1, *strip)
    reg = orig[y0:y1, x0:x1].astype(int)
    pa = _premul(orig[y0:y1, x0:x1])
    pb = _premul(bg[:, None, :].repeat(x1 - x0, 1))
    m = (np.abs(pa - pb).sum(axis=2) + np.abs(reg[:, :, 3] - bg[:, None, 3].astype(int)) > 60)
    lum = reg[:, :, :3].mean(axis=2)
    ink = lum[m]
    hi, lo = np.percentile(ink, 85), np.percentile(ink, 12)
    bright = m & (lum >= hi - 25) & (reg[:, :, 3] > 200)
    dark = m & (lum <= lo + 20)
    if dark_text:
        bright, dark = dark, bright
    rows = []
    for yy in range(m.shape[0]):
        sel = bright[yy]
        if sel.sum() >= 3:
            rows.append(np.median(reg[yy][sel][:, :3], axis=0))
    fill = np.array(rows) if rows else np.array([[255, 255, 255]])
    edge = np.median(reg[dark][:, :3], axis=0) if dark.any() else np.array([40, 40, 40])
    # 외곽선 r: 밝은 마스크를 r 만큼 키운 고리 중 어두운 비율
    Bi = Image.fromarray((bright * 255).astype(np.uint8))
    best_r, best_cov = 0, 0
    for r in range(1, 11):
        dil = np.array(Bi.filter(ImageFilter.MaxFilter(2 * r + 1))) > 0
        ring = dil & ~bright
        cov = (ring & (dark | m)).sum() / max(1, ring.sum())
        if cov > 0.85:
            best_r, best_cov = r, cov
        else:
            break
    # 그림자: 밝은 마스크를 밀어 어두운 것과 겹치는 정도(외곽선 너머)
    best_o, best_s = (0, 0), 0
    for dy in range(0, 14):
        for dx in range(0, 14):
            if dx == dy == 0:
                continue
            sh = np.zeros_like(bright)
            sh[dy:, dx:] = bright[:bright.shape[0] - dy, :bright.shape[1] - dx]
            sc = (sh & dark & ~bright).sum() - (sh & ~m).sum()
            if sc > best_s:
                best_o, best_s = (dx, dy), sc
    ys, xs = np.nonzero(m)
    return {'fill': fill, 'edge': edge, 'outline': best_r, 'shadow': best_o if best_s > 0 else (0, 0),
            'ink': (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1),
            'bright_ink': _bbox(bright, x0, y0)}


def _bbox(mask, x0, y0):
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return None
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def over(px, x, y, alpha, rgb):
    """alpha [H,W] 0..1, rgb [H,W,3] 를 (x,y) 에 RGBA over 합성."""
    H, W = alpha.shape
    h, w = px.shape[:2]
    xs0, ys0 = max(0, x), max(0, y)
    xs1, ys1 = min(w, x + W), min(h, y + H)
    if xs0 >= xs1 or ys0 >= ys1:
        return
    a = alpha[ys0 - y:ys1 - y, xs0 - x:xs1 - x][:, :, None]
    c = rgb[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
    dst = px[ys0:ys1, xs0:xs1].astype(float)
    da = dst[:, :, 3:4] / 255
    oa = a + da * (1 - a)
    orgb = (c * a + dst[:, :, :3] * da * (1 - a)) / np.maximum(oa, 1e-6)
    px[ys0:ys1, xs0:xs1, :3] = np.clip(orgb, 0, 255).astype(np.uint8)
    px[ys0:ys1, xs0:xs1, 3] = np.clip(oa[:, :, 0] * 255, 0, 255).astype(np.uint8)


def draw(px, mask_img, pos, sty, fill=None, edge=None):
    fill = np.array(sty['fill'] if fill is None else fill, float)
    if fill.ndim == 1:
        fill = fill[None]
    edge = np.array(sty['edge'] if edge is None else edge, float)
    r = sty['outline']
    dx, dy = sty['shadow']
    pad = r + max(dx, dy) + 4
    m = Image.new('L', (mask_img.width + 2 * pad, mask_img.height + 2 * pad))
    m.paste(mask_img, (pad, pad))
    H, W = m.height, m.width
    x, y = pos[0] - pad, pos[1] - pad
    base = np.array(m).astype(float) / 255
    edge_rgb = np.broadcast_to(edge, (H, W, 3))
    if r:
        om = np.array(m.filter(ImageFilter.MaxFilter(2 * r + 1)).filter(ImageFilter.GaussianBlur(0.6))).astype(float) / 255
        if dx or dy:
            sh = np.zeros_like(om)
            sh[dy:, dx:] = om[:H - dy, :W - dx]
            over(px, x, y, sh, edge_rgb)
        over(px, x, y, om, edge_rgb)
    elif dx or dy:
        sh = np.zeros_like(base)
        sh[dy:, dx:] = base[:H - dy, :W - dx]
        over(px, x, y, sh, edge_rgb)
    rows = np.linspace(0, len(fill) - 1, mask_img.height).astype(int)
    fcol = np.zeros((H, W, 3))
    fcol[pad:pad + mask_img.height] = fill[rows][:, None, :]
    fcol[:pad] = fill[0]
    fcol[pad + mask_img.height:] = fill[-1]
    over(px, x, y, base, fcol)


def label(px, orig, box, text, font=F[7], align='left', er=None, strip=None, max_w=None, scale=1.0,
          dark_text=False, sty=None, fill=None, edge=None, x=None):
    """box = 원본 글자 상자. er = 지울 범위(기본 box). 반환: 그린 끝 x."""
    er = er or box
    strip = strip or default_strip(orig, er)
    m = measure(orig, box, strip, dark_text)
    if sty:   # 색·외곽선·그림자만 빌리고 위치는 이 상자에서
        m.update({k: sty[k] for k in ('fill', 'edge', 'outline', 'shadow')})
    sty = m
    erase(px, orig, er, strip)
    bx0, by0, bx1, by1 = sty['bright_ink'] or sty['ink']
    H = max(6, int((by1 - by0) * scale))
    mw = max_w or (er[2] - bx0 - sty['outline'] - sty['shadow'][0] - 2)
    mi = text_mask(text, font, H, mw)
    cy = by0 + (by1 - by0) // 2 - H // 2
    if x is not None:
        cx = x
    elif align == 'left':
        cx = bx0
    elif align == 'center':
        cx = (er[0] + er[2] - sty['shadow'][0]) // 2 - mi.width // 2
    else:
        cx = bx1 - mi.width
    draw(px, mi, (cx, cy), sty, fill, edge)
    return cx + mi.width


def lines(px, orig, er, rows, texts, font=F[4], color=None, strip=None, sty=None, align='center'):
    """여러 줄. rows = 줄별 (y0,y1) 잉크 높이 기준."""
    x0, y0, x1, y1 = er
    strip = strip or default_strip(orig, er)
    sty = sty or measure(orig, er, strip)
    if color is not None:
        sty = dict(sty, fill=np.array([color], float))
    erase(px, orig, er, strip)
    H = int(np.median([b - a for a, b in rows]))
    for t, (a, b) in zip(texts, rows):
        mi = text_mask(t, font, H, x1 - x0 - 12)
        cx = (x0 + x1) // 2 - mi.width // 2 if align == 'center' else x0 + 6
        draw(px, mi, (cx, (a + b) // 2 - H // 2), sty)


def segments(px, orig, x, y, H, parts, font, sty):
    """[(글자, 채움색)] 를 이어서 그린다."""
    for t, col in parts:
        if not t:
            continue
        mi = text_mask(t, font, H, 10_000)
        draw(px, mi, (x, y), sty, fill=col)
        x += mi.width + (int(H * 0.25) if t.endswith(' ') else 0)
    return x
