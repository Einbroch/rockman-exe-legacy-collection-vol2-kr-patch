"""대화창 HD 글꼴(cht_mojiFont.fnt)에 한글을 넣는다.

게임은 대화창 글자를 「글자 코드 -> 유니코드(파일 끝 코드표) -> 글리프(유니코드 색인) -> 아틀라스 칸」으로 그린다
(비트맵 폰트 font8x16 은 메뉴·칩 이름용). 한글에 배정한 코드의 원래 한자 유니코드가 가리키는 글리프 칸을
한글로 다시 그린다 — 표는 그대로, 아틀라스 그림과 글리프 상자만 바꾼다.
전제(빌드 때 검사): 그 글리프를 쓰는 코드가 하나뿐일 것(다른 코드·번체로 남긴 글자와 공유 금지).

아틀라스: 폭 4096 RGBA, 흰색 + 알파. 글리프는 가로로 약 3배 늘려 저장(UV 가 화면 비율을 되돌림).
"""
from __future__ import annotations

import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from mojifont import MojiFont  # noqa: E402

FONTS = Path(r'D:\Games\Kor Patch\CLude\폰트\S-Core_Dream_OTF')
FONT = FONTS / 'SCDream4.otf'
FALLBACK = Path(r'C:\Windows\Fonts\malgun.ttf')
# 한글 글리프 상자(글꼴 단위, 셀 54x54). 번체 「太」 상자와 같은 크기
BOX = (2.5, 11.0, 39.0, 49.0)


def _draw(ch, font, w, h, ss=4):
    """BOX 비율로 그린 뒤 (w, h) 로 늘린 알파. 세로 기준 = 「한」의 잉크 상자."""
    bw, bh = BOX[2] - BOX[0], BOX[3] - BOX[1]
    size = 160 * ss // 4
    f = ImageFont.truetype(str(font), size)
    W = size * 3
    canvas = Image.new('L', (W, W), 0)
    ImageDraw.Draw(canvas).text((size, size), ch, font=f, fill=255)
    ref = Image.new('L', (W, W), 0)
    ImageDraw.Draw(ref).text((size, size), '한', font=f, fill=255)
    rb = ref.getbbox()
    if canvas.getbbox() is None:
        return None
    # 「한」 잉크 상자를 BOX 안쪽(여백 4%)에 맞춘다
    rw, rh = rb[2] - rb[0], rb[3] - rb[1]
    s = min(bw / rw, bh / rh) * 0.96
    cx, cy = (rb[0] + rb[2]) / 2, (rb[1] + rb[3]) / 2
    x0, x1 = cx - bw / 2 / s, cx + bw / 2 / s
    y0, y1 = cy - bh / 2 / s, cy + bh / 2 / s
    crop = canvas.crop((int(x0), int(y0), int(x1), int(y1)))
    return np.array(crop.resize((w, h), Image.LANCZOS))


def render(ch, w, h):
    a = _draw(ch, FONT, w, h)
    if a is None or not a.any():
        a = _draw(ch, FALLBACK, w, h)
    return a


def patch(src, dst, codes, new, keep):
    """codes: 글자->코드, new: 새로 그릴 글자 목록, keep: 번체로 남긴 코드."""
    f = MojiFont(src)
    users = defaultdict(set)
    for c, u in enumerate(f.codes):
        users[f.glyph_of(u)].add(c)
    atlas = f.atlas()
    done = 0
    for ch in new:
        c = codes[ch]
        if c >= len(f.codes):
            raise ValueError(f'{ch}: 코드 {c} 가 대화창 글꼴 코드표({len(f.codes)}) 밖')
        g = f.glyph_of(f.codes[c])
        if g is None or g < 3:
            raise ValueError(f'{ch}: 코드 {c} 의 글리프 없음')
        if users[g] - {c}:
            raise ValueError(f'{ch}: 글리프 {g} 를 다른 코드 {sorted(users[g] - {c})[:3]} 도 쓴다')
        x0, y0, x1, y1 = f.rect(g)
        a = render(ch, x1 - x0, y1 - y0)
        cell = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        cell[:, :, :3] = 255
        cell[:, :, 3] = a
        atlas[y0:y1, x0:x1] = cell
        # 글리프 상자(fp16 x0 y0 x1 y1) = BOX
        struct.pack_into('<4e', f.raw, f.rec_off + 20 * g + 2, *BOX)
        done += 1
    f.set_atlas(atlas)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    f.save(dst)
    return done
