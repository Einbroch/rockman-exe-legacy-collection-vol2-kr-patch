"""Vol.2 런처 그림 글자.

- InGameUI/exe4|5|6/title_moji_{start,con,con_plus}_ct.png: Vol.1 launcher_gallery.title() 재사용
  (con_plus 「繼續第 _ 輪的遊戲」 은 가운데 빈칸에 숫자가 들어간다 -> 「제 _ 회차 이어하기」 로 앞뒤 나눠 그림)
- UI/T_Amends_T.png: 수정 업데이트 안내(검은 바탕 회색 글자)
- 갤러리 머리글·T_* 안내 그림 17장은 Vol.1 과 바이트까지 같아 Vol.1 빌드 결과를 그대로 복사한다(make 단계).
    python tools/launcher_vol2.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import launcher_gallery as LG  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FONTS = Path(r'D:\Games\Kor Patch\CLude\폰트\S-Core_Dream_OTF')


def title_split(game, kind, left, right):
    """빈칸(숫자 자리)을 사이에 둔 두 덩어리: 원본 채움 열의 가장 큰 빈 구간 앞뒤에 그린다."""
    fn = LG.SRC / 'InGameUI' / game / f'title_moji_{kind}_ct.png'
    a = np.array(Image.open(fn).convert('RGBA'))
    H = a.shape[0]
    rows = np.nonzero(a[:, :, 3].max(axis=1) > 0)[0]
    first_end = rows[0]
    while first_end + 1 < H and a[first_end + 1, :, 3].max() > 0:
        first_end += 1
    n = max(2, round(H / (first_end + 1)))
    L = H // n
    lay0 = a[:L]
    fill0, edge0 = LG.layer_colors(lay0)
    F = (lay0[:, :, 3] > 200) & (np.abs(lay0[:, :, :3].astype(float) - fill0).sum(axis=2) < 40)
    S = lay0[:, :, 3] > 128
    ys, xs = np.nonzero(F)
    fy0, fy1 = ys.min(), ys.max() + 1
    cols = np.nonzero(F.any(axis=0))[0]
    gaps = np.diff(cols)
    g = int(gaps.argmax())
    gx0, gx1 = cols[g] + 1, cols[g + 1]          # 숫자 자리
    E = S & ~ndimage.binary_dilation(F, iterations=2)
    dF = ndimage.distance_transform_edt(~F)
    w = max(2, int(np.percentile(dF[E], 90))) if E.any() else 4
    sy, sx = np.nonzero(S)
    off = (int(round(sx.mean() - xs.mean())), int(round(sy.mean() - ys.mean())))
    T = np.zeros((L, a.shape[1]))
    ml = LG.line_mask(left, LG.HEAVY, fy1 - fy0, max_w=gx0 - 10)
    mr = LG.line_mask(right, LG.HEAVY, fy1 - fy0, max_w=a.shape[1] - gx1 - 8 - 2 * w - abs(off[0]))   # 그림자가 np.roll 로 왼쪽에 감기지 않게
    T[fy0:fy1, gx0 - 10 - ml.shape[1]:gx0 - 10] = ml
    T[fy0:fy1, gx1 + 4:gx1 + 4 + mr.shape[1]] = mr
    Sn = ndimage.binary_dilation(T > 0.5, iterations=w)
    Sn = np.roll(np.roll(Sn, off[1], axis=0), off[0], axis=1) | ndimage.binary_dilation(T > 0.5, iterations=max(1, w // 2))
    Sa = ndimage.gaussian_filter(Sn.astype(float), 0.6)
    out = np.zeros_like(a, dtype=float)
    for i in range(n):
        lay = a[i * L:(i + 1) * L]
        fill, edge = LG.layer_colors(lay)
        y = i * L
        if fill is None:
            out[y:y + L, :, 3] = Sa * 255
            continue
        o = out[y:y + L]
        o[:, :, :3] = edge
        o[:, :, 3] = Sa * 255
        o[:, :, :3] = o[:, :, :3] * (1 - T[:, :, None]) + fill * T[:, :, None]
        o[:, :, 3] = np.maximum(o[:, :, 3], T * 255)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
    (LG.OUT / 'InGameUI' / game).mkdir(parents=True, exist_ok=True)
    img.save(LG.OUT / 'InGameUI' / game / fn.name)
    return img


def amends():
    src = ROOT / '_work' / 'romfs' / 'launcher' / 'UI' / 'T_Amends_T.png'
    a = np.array(Image.open(src).convert('RGB'))
    lum = a.mean(axis=2)
    col = tuple(int(v) for v in np.median(a[lum > 120], axis=0))
    img = Image.new('RGB', (a.shape[1], a.shape[0]), (0, 0, 0))
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(str(FONTS / 'SCDream6.otf'), 74)
    fb = ImageFont.truetype(str(FONTS / 'SCDream5.otf'), 42)
    W = a.shape[1]
    for text, f, y in (('수정 업데이트를 적용했습니다', ft, 380), ('각 게임의 개조 카드 메뉴 「스페셜 카드」에서', fb, 530),
                       ('보상 칩을 받을 수 있습니다.', fb, 615)):
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=col)
    out = ROOT / 'build' / 'romfs' / 'launcher' / 'UI' / 'T_Amends_T.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return img


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    LG.PREVIEW.mkdir(parents=True, exist_ok=True)
    ims = []
    for game, kinds in (('exe4', ('start', 'con')), ('exe5', ('start', 'con')), ('exe6', ('start', 'con'))):
        for k in kinds:
            ims.append(LG.title(game, k))
            print('ok', game, k)
    ims.append(title_split('exe4', 'con_plus', '제', '회차 이어하기'))
    print('ok exe4 con_plus')
    W = max(i.width for i in ims)
    sheet = Image.new('RGBA', (W, sum(i.height for i in ims)), (60, 60, 120, 255))
    y = 0
    for im in ims:
        sheet.alpha_composite(im, (0, y))
        y += im.height
    s = 1400 / sheet.height
    sheet.resize((int(sheet.width * s), 1400)).convert('RGB').save(LG.PREVIEW / 'titles_vol2.png')
    amends().resize((960, 540)).save(LG.PREVIEW / 'amends.png')
    print('ok amends')


if __name__ == '__main__':
    main()
