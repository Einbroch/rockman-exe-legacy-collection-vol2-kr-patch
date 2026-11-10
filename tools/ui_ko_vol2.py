"""Vol.2 번체 칸 그림 글자 -> 한국어.

    python tools/ui_ko_vol2.py [판 ...]        (판: exe4 exe4b exe5 exe5k exe6 exe6f)

결과: build/romfs/<판>/data/ui/<이름>.pak, 미리보기 work/ui_ko/<판>__<이름>.png
좌표는 work/ui_survey(번체·일본어 차이 상자, 상하좌우 4px 여유 포함)에서 읽었다.
용어는 각 GBA 한글패치(EXE4~6) 용어집과 Vol.1 결정(E-메일)을 따른다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from ui_vol2 import F, draw, erase, label, lines, measure, segments  # noqa: E402
from uilib1 import text_mask  # noqa: E402
from uipak import read, write  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'work' / 'ui_ko'


# ------------------------------------------------------------------ 공통 모양
def job_title_moji(px, orig):
    for (y0, y1), t in zip(((0, 148), (166, 318), (336, 488), (506, 658)), ('처음부터', '처음부터', '이어하기', '이어하기')):
        label(px, orig, (0, y0, 714, y1), t, font=F[8], er=(0, y0, 716, y1), max_w=700)


SUBMENU5 = ['칩 폴더', '서브칩', '도감', '록맨', 'E-메일', '키 아이템', '통신', '세이브']


def submenu_rows(px, orig, rows, texts, cols=((55, 372), (605, 922)), font=F[8]):
    for (y0, y1), t in zip(rows, texts):
        for x0, xr in cols:
            label(px, orig, (x0, y0, x0 + 120, y1), t, font=font, er=(x0 - 4, y0, xr, y1), max_w=xr - x0 - 12)


def job_submenu5(px, orig):
    rows = [(0, 80), (116, 200), (236, 320), (364, 441), (484, 561), (604, 680), (724, 801), (836, 921)]
    submenu_rows(px, orig, rows, SUBMENU5)
    # 맨 아래 줄(어둡게 칠한 판): 왼쪽 통신, 오른쪽 세이브
    label(px, orig, (55, 934, 175, 1019), '통신', font=F[8], er=(51, 934, 372, 1019), max_w=300)
    label(px, orig, (603, 934, 724, 1019), '세이브', font=F[8], er=(599, 934, 922, 1019), max_w=300)


def job_sort(px, orig):
    rows = [(205, 308, '이름'), (334, 436, '코드'), (456, 564, '공격력'), (584, 692, '속성'), (712, 820, '매수'),
            (851, 958, '칩 용량')]
    for y0, y1, t in rows:
        label(px, orig, (26, y0, 360, y1), t, font=F[5], er=(22, y0, 395, y1), strip=(400, 406), max_w=360)


def job_result(px, orig):
    label(px, orig, (48, 23, 240, 76), '딜리트 타임', font=F[6], er=(46, 21, 420, 77), max_w=370, strip=(560, 568))
    label(px, orig, (50, 83, 293, 135), '버스팅 레벨', font=F[6], er=(46, 81, 420, 135), max_w=370, strip=(560, 568))


# ------------------------------------------------------------------ EXE5
def job_map5(px, orig):
    names = ['아키하라 마을', '과학성', '오란섬', '엔드 시티']
    sty = measure(orig, (0, 0, 278, 85), (300, 308))
    erase(px, orig, (0, 0, 640, 341), (600, 608))
    for i, t in enumerate(names):
        y0 = 4 + i * 85
        H = 60
        mi = text_mask(t, F[7], H, 600)
        draw(px, mi, (8, y0 + 8), sty)
    for row in ((360, 412), (457, 515), (560, 612)):
        y0, y1 = row
        # 「:說明」 -> 「: 설명」 (쌍점은 그대로)
        bx = 232 if y0 != 457 else 213
        label(px, orig, (bx, y0, bx + 170, y1), '설명', font=F[3], er=(bx, y0, bx + 200, y1), max_w=190)


def job_bbs5(px, orig):
    label(px, orig, (226, 10, 724, 184), '게시판', font=F[5], align='center', er=(200, 6, 900, 186), max_w=640,
          strip=(130, 140))
    sty_p = measure(orig, (106, 230, 324, 404), (60, 70))
    sty_w = measure(orig, (347, 230, 845, 404), (60, 70))
    erase(px, orig, (80, 226, 900, 406), (60, 70))
    bx0, by0, bx1, by1 = sty_w['bright_ink']
    H = by1 - by0
    x = 130
    for t, sty in (('언더', sty_p), (' 게시판', sty_w)):
        mi = text_mask(t, F[5], H, 600)
        draw(px, mi, (x, by0), sty)
        x += mi.width


def job_navi_moji5(px, orig):
    for (y0, y1), t in zip(((39, 138), (171, 266), (359, 458), (491, 586)), ('옮기기', '되돌리기', '옮기기', '되돌리기')):
        sty = measure(orig, (152, y0, 432, y1), (30, 38))
        # 체크무늬 판: 글자 상자만 다시 칠한다 — 체크 주기 2칸(원본 좌우에서 복사)
        _checker_erase(px, orig, (150, y0, 440, y1))
        bx0, by0, bx1, by1 = sty['bright_ink']
        H = by1 - by0
        mi = text_mask(t, F[7], H, 300)
        draw(px, mi, ((150 + 440) // 2 - mi.width // 2, by0), sty)


def _checker_erase(px, orig, box):
    """체크무늬: 같은 행에서 주기 P 만큼 떨어진 상자 밖 픽셀을 복사."""
    x0, y0, x1, y1 = box
    # 주기 찾기: 상자 왼쪽 깨끗한 구간
    clean = orig[y0:y1, 22:146]
    best, bp = -1, 2
    for P in range(2, 60):
        s = (clean[:, :-P] == clean[:, P:]).all(axis=2).mean()
        if s > best + 1e-6:
            best, bp = s, P
        if s > 0.999:
            bp = P
            break
    for x in range(x0, x1):
        k = 1
        while x - k * bp >= x0:
            k += 1
        src = x - k * bp
        px[y0:y1, x] = orig[y0:y1, src]


def job_patch_card(px, orig, box=(121, 17, 394, 75), dark=True):
    label(px, orig, box, '개조 카드', font=F[5], align='center', er=(box[0] - 20, box[1], box[2] + 20, box[3]),
          dark_text=dark, strip=(60, 70), max_w=330)


def job_patch_card5k(px, orig):
    job_patch_card(px, orig, (122, 17, 396, 77))


def job_mission_bonus5(px, orig):
    rows = [(0, 64, [('1페이즈 동안 ', 'w'), ('무적', 'c'), ('!', 'w')]),
            (76, 144, [('HP', 'c'), (' 회복!', 'w')]),
            (156, 225, [('오더 포인트', 'c'), (' GET!', 'w')]),
            (236, 304, [('배틀칩', 'c'), (' GET!', 'w')]),
            (316, 384, [('적 1체에 ', 'w'), ('큰 대미지', 'c'), ('!', 'w')])]
    # 색: 흰 글자 = 「HP 回復」 의 回復, 하늘색 = HP
    sty = measure(orig, (0, 76, 362, 144), 'clear')
    white = np.array([[235, 250, 250]], float)
    cyan = np.array([[30, 180, 230]], float)
    for y0, y1, parts in rows:
        erase(px, orig, (0, y0, 650, y1), 'clear')
        H = y1 - y0 - 2 * sty['outline'] - sty['shadow'][1] - 6
        segments(px, orig, sty['outline'] + 2, y0 + sty['outline'] + 2, H,
                 [(t, white if c == 'w' else cyan) for t, c in parts], F[7], sty)


def job_mission_guide5(px, orig):
    sty = measure(orig, (0, 421, 201, 486), 'clear')
    for (x0, y0, x1, y1), t, ell in (((0, 336, 350, 402), '카메라 이동', True), ((401, 336, 613, 402), '페이즈', False),
                                     ((0, 421, 201, 486), '돌아가기', True), ((0, 496, 456, 564), '카메라 이동(빠름)', True),
                                     ((0, 571, 460, 637), '목표 페이즈', False)):
        if ell:
            # 「…」 는 남기고 뒤만
            label(px, orig, (52, y0, x1, y1), t, font=F[6], er=(50, y0, max(x1, 470), y1), strip='clear',
                  max_w=420, sty=sty)
        else:
            label(px, orig, (x0, y0, x1, y1), t, font=F[7], er=(x0, y0, x1 + 20, y1), strip='clear',
                  max_w=x1 + 16 - x0, sty=sty)


def job_cockpit_cards5(px, orig):
    """패널 4장: 영어 제목은 그대로, 아래 중국어 줄만(번체 줄 위치를 차이로 실측)."""
    sty = measure(orig, (40, 190, 410, 250), (40, 48))
    lines(px, orig, (30, 180, 420, 345), [(190, 250), (280, 338)], ['칩 데이터를', '송신 중...'], strip=(40, 48), sty=sty)
    lines(px, orig, (555, 180, 925, 345), [(190, 250), (280, 338)], ['칩이 선택되지', '않았습니다!'], strip=(560, 568),
          sty=sty)
    lines(px, orig, (30, 660, 420, 815), [(668, 735), (756, 812)], ['칩 폴더를', '셔플!'], strip=('v', 625, 660), sty=sty)
    lines(px, orig, (524, 636, 950, 856), [(642, 700), (712, 770), (784, 842)],
          ['보쿠타이에서 온', '방해 박쥐를', '튕겨 냅니다!'], strip=('v', 604, 636), sty=sty)   # 글자 없는 위 띠를 열별로


# ------------------------------------------------------------------ EXE6
SUBMENU6 = SUBMENU5   # 칩 폴더 … 세이브


def job_submenu6(px, orig, rows):
    cols = ((39, 395, (400, 408)), (551, 907, (912, 920)))
    for (y0, y1), t in zip(rows[:8], SUBMENU6):
        for x0, xr, strip in cols:
            label(px, orig, (x0, y0, x0 + 120, y1), t, font=F[8], er=(x0 - 4, y0, xr, y1), strip=strip,
                  max_w=xr - x0 - 10)
    y0, y1 = rows[8]
    label(px, orig, (39, y0, 160, y1), '통신', font=F[8], er=(35, y0, 395, y1), strip=(400, 408), max_w=340)
    label(px, orig, (551, y0, 680, y1), '세이브', font=F[8], er=(547, y0, 907, y1), strip=(912, 920), max_w=340)
    y0, y1 = rows[3]
    for x0, xr, strip in ((1062, 1415, (1420, 1428)), (1574, 1927, (1932, 1940))):
        label(px, orig, (x0, y0, x0 + 120, y1), '스테이터스', font=F[8], er=(x0 - 4, y0, xr, y1), strip=strip,
              max_w=xr - x0 - 10)


ROWS6 = [(3, 114), (117, 228), (231, 342), (356, 456), (470, 570), (584, 684), (698, 798), (801, 912), (915, 1026)]
ROWS6F = [(8, 114), (122, 228), (236, 342), (356, 456), (470, 570), (584, 684), (698, 798), (806, 912), (915, 1026)]


def job_sort6(px, orig):
    rows = [(210, 304, '이름'), (338, 432, '코드'), (460, 560, '공격력'), (588, 688, '속성'), (716, 816, '매수'),
            (851, 949, '칩 용량')]
    for y0, y1, t in rows:
        label(px, orig, (26, y0, 360, y1), t, font=F[5], er=(22, y0, 365, y1), strip=(368, 376), max_w=330)
    for (y0, y1), t in zip(((33, 130), (162, 258), (291, 386)), ('편집하기', '장비하기', '이름 바꾸기')):
        label(px, orig, (480, y0, 900, y1), t, font=F[5], er=(475, y0, 990, y1), strip=(995, 1003), max_w=500)


def job_sort_mail6(px, orig):
    for (y0, y1), t in zip(((82, 180), (200, 307), (329, 436), (456, 564)), ('아이콘', '제목', '보낸 사람', '수신 No.')):
        label(px, orig, (25, y0, 384, y1), t, font=F[5], er=(20, y0, 395, y1), strip=(398, 404), max_w=360)


def job_map_guide6(px, orig):
    for (y0, y1), t in zip(((1, 61), (65, 124), (128, 187), (191, 250), (254, 313)),
                           ('현재 위치', '워프 홀', '숍', '게시판', '홈페이지')):
        label(px, orig, (132, y0, 330, y1), t, font=F[5], er=(132, y0, 412, y1), strip=(412, 418), max_w=270)


def job_minigame_guide6(px, orig):
    sty = measure(orig, (0, 421, 201, 486), 'clear')
    for (x0, y0, x1, y1), t in (((0, 336, 350, 402), '카메라 이동'), ((0, 421, 201, 486), '돌아가기'),
                                ((0, 496, 456, 564), '카메라 이동(빠름)')):
        label(px, orig, (52, y0, x1, y1), t, font=F[6], er=(50, y0, 470, y1), strip='clear', max_w=420, sty=sty)


def job_navi_moji6(px, orig):
    for (y0, y1), t in zip(((39, 138), (171, 266)), ('옮기기', '되돌리기')):
        sty = measure(orig, (152, y0, 432, y1), (30, 38))
        _checker_erase(px, orig, (150, y0, 440, y1))
        bx0, by0, bx1, by1 = sty['bright_ink']
        mi = text_mask(t, F[7], by1 - by0, 300)
        draw(px, mi, ((150 + 440) // 2 - mi.width // 2, by0), sty)


def job_patch_card6(px, orig):
    job_patch_card(px, orig, (137, 14, 413, 75), dark=False)   # EXE6 은 흰 글자


def job_cockpit_chips6(px, orig):
    sty = measure(orig, (40, 190, 410, 250), (40, 48))
    lines(px, orig, (30, 180, 420, 345), [(190, 250), (280, 338)], ['칩 데이터를', '송신 중...'], strip=(40, 48), sty=sty)
    lines(px, orig, (555, 180, 925, 345), [(190, 250), (280, 338)], ['칩이 선택되지', '않았습니다!'], strip=(560, 568),
          sty=sty)
    lines(px, orig, (30, 660, 420, 815), [(668, 735), (756, 812)], ['칩 폴더를', '셔플!'], strip=('v', 625, 660), sty=sty)
    lines(px, orig, (524, 636, 950, 856), [(646, 702), (716, 772), (786, 842)], ['1턴 동안', '방해 공격을', '튕겨 낸다!'],
          strip=('v', 604, 636), sty=sty)


CROSS_G = ['히트', '일렉', '슬래시', '킬러', '차지']
CROSS_F = ['아쿠아', '토마호크', '텐구', '그랜드', '더스트']


def job_cross(px, orig, names, boxes):
    for (x0, y0, x1, y1), t in zip(boxes, names):
        label(px, orig, (x0, y0, x1, y1), t, font=F[8], align='right', er=(x0, y0 + 2, x1 + 2, y1 - 2),
              strip=(x0 - 1, x0), max_w=x1 - x0 - 6)


CROSS6_BOX = [(124, 7, 288, 57), (454, 7, 618, 57), (124, 77, 288, 127), (454, 77, 618, 127), (124, 147, 288, 197),
              (454, 147, 618, 197), (124, 217, 288, 267), (454, 217, 618, 267), (123, 284, 288, 337), (453, 284, 618, 337),
              (124, 354, 288, 407), (453, 354, 618, 407), (124, 427, 288, 477), (124, 497, 288, 547), (124, 567, 288, 617)]
# 상자 순서 = 왼쪽 열 5개(컬러) / 오른쪽 열 5개(회색) … 차례: (행, 열) 순으로 이름을 붙인다
CROSS6_ORDER = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 4, 1, 2, 3]


def job_cross6(px, orig):
    job_cross(px, orig, [CROSS_G[i] for i in CROSS6_ORDER], CROSS6_BOX)


def job_cross6f(px, orig):
    job_cross(px, orig, [CROSS_F[i] for i in CROSS6_ORDER], CROSS6_BOX)


# ------------------------------------------------------------------ EXE4
ROWS4 = [(2, 92), (115, 205), (228, 318), (347, 431), (463, 544), (576, 657), (689, 770), (793, 883), (906, 993)]


def job_submenu4(px, orig):
    for i, ((y0, y1), t) in enumerate(zip(ROWS4[:8], SUBMENU5)):
        xr = 436 if i < 6 else 300   # 아래 세 줄은 판이 짧다
        for dx in (0, 512):
            label(px, orig, (35 + dx, y0, 155 + dx, y1), t, font=F[8], er=(31 + dx, y0, xr + dx, y1),
                  strip=(xr + dx, xr + dx + 6), max_w=xr - 45)
    y0, y1 = ROWS4[8]
    for dx, t in ((0, '통신'), (512, '세이브')):
        label(px, orig, (35 + dx, y0, 155 + dx, y1), t, font=F[8], er=(31 + dx, y0, 300 + dx, y1),
              strip=(300 + dx, 306 + dx), max_w=255)


def job_result4(px, orig):
    label(px, orig, (0, 0, 330, 104), '딜리트 타임', font=F[8], er=(0, 0, 395, 104), strip=(396, 402), max_w=390)
    label(px, orig, (0, 118, 330, 224), '버스팅 레벨', font=F[8], er=(0, 118, 525, 224), strip=(526, 532), max_w=520)


def job_bbs_tag4(px, orig):
    rows = [((61, 15, 259, 136), (277, 15, 599, 136), '의뢰', (610, 618)),
            ((60, 231, 259, 353), (277, 231, 599, 353), '배틀', (610, 618)),
            ((59, 451, 319, 573), (342, 451, 664, 573), '잡담', (672, 680)),
            ((59, 671, 189, 792), (212, 671, 534, 792), '언더', (540, 548))]
    for pb, qb, t, strip in rows:
        s1 = measure(orig, pb, strip)
        s2 = measure(orig, qb, strip)
        erase(px, orig, (pb[0], pb[1], strip[0], pb[3]), strip)
        bx0, by0, bx1, by1 = s2['bright_ink']
        H = by1 - by0
        x = pb[0] + 8
        m1 = text_mask(t, F[5], H, 300)
        draw(px, m1, (x, by0), s1)
        m2 = text_mask('게시판', F[5], H, strip[0] - x - m1.width - 40)
        draw(px, m2, (x + m1.width + int(H * 0.35), by0), s2)


MAP4 = [((0, 4, 360, 74), '아키하라 마을'), ((0, 82, 286, 152), '전기가'), ((0, 160, 286, 230), '덴산 돔'),
        ((0, 238, 286, 308), '셰로 카스티요'), ((0, 318, 300, 390), '덴산 공항'), ((0, 400, 300, 472), '니혼'),
        ((326, 400, 560, 472), '샤로'), ((0, 480, 300, 552), '아메로파'), ((0, 558, 300, 630), '아프리크'),
        ((326, 480, 560, 552), '아지나'), ((326, 558, 560, 630), 'ANSA')]


def job_map4(px, orig):
    sty = measure(orig, (0, 0, 300, 76), 'clear')
    for (x0, y0, x1, y1), t in MAP4:
        erase(px, orig, (x0, y0 - 4, x1 + 4, y1 + 2), 'clear')
    for (x0, y0, x1, y1), t in MAP4:
        H = 56
        mi = text_mask(t, F[7], H, max(x1 - x0, 360) - 10)   # 글자는 띠 위로 넘어가도 된다(원본도 겹침)
        draw(px, mi, (x0 + 6, y0 + 6), sty)


def job_minigame_icon4(px, orig):
    label(px, orig, (868, 30, 940, 140), '개', font=F[7], align='center', er=(860, 30, 948, 150))
    label(px, orig, (100, 218, 280, 291), '체온', font=F[7], align='center', er=(96, 216, 284, 291),
          strip=(300, 306), max_w=180)
    label(px, orig, (275, 485, 363, 602), '회', font=F[7], align='center', er=(270, 480, 368, 606))


def job_navi_submenu4(px, orig):
    job_navi_moji6(px, orig)


def job_patch_card4(px, orig):
    for y0, y1 in ((15, 75), (120, 180), (225, 285), (330, 394), (435, 499), (540, 604)):
        label(px, orig, (118, y0, 394, y1), '개조 카드', font=F[5], align='center', er=(110, y0, 400, y1),
              strip=(402, 410), max_w=280)


TOURN4 = ['덴산 배틀 토너먼트', '이글 토너먼트', '레드선 토너먼트', '프리 토너먼트']
TOURN4B = ['덴산 배틀 토너먼트', '이글 토너먼트', '블루문 토너먼트', '프리 토너먼트']


def job_tournament(px, orig, names, widths):
    for (y0, y1), t, w, s in zip(((0, 85), (116, 205), (236, 325), (356, 445)), names, widths, (40, 60, 60, 60)):
        sty = measure(orig, (s + 10, y0, w - 60, y1), (s, s + 8))
        erase(px, orig, (s + 8, y0, w - 30, y1), (s, s + 8))   # 글자 왼쪽 띠 열의 행별 색(띠·투명)
        bx0, by0, bx1, by1 = sty['ink']
        by0 += sty['outline']
        by1 -= sty['outline']
        H = by1 - by0
        mi = text_mask(t, F[8], H, w - 140)
        draw(px, mi, ((w - 20) // 2 - mi.width // 2, by0), sty)


def job_tournament4(px, orig):
    job_tournament(px, orig, TOURN4, (830, 820, 820, 820))


def job_tournament4b(px, orig):
    job_tournament(px, orig, TOURN4B, (830, 820, 820, 820))


def job_title_moji_plus4(px, orig):
    for y0, y1 in ((746, 882), (886, 1022)):
        sty = measure(orig, (0, y0, 360, y1), 'clear')
        erase(px, orig, (0, y0, 1024, y1), 'clear')
        bx0, by0, bx1, by1 = sty['bright_ink']
        H = by1 - by0
        m1 = text_mask('제', F[8], H, 200)
        draw(px, m1, (360 - m1.width, by0), sty)          # 숫자 칸(372~510) 앞
        m2 = text_mask('회차 이어하기', F[8], H, 1000 - 515)
        draw(px, m2, (515, by0), sty)


def job_cockpit_cards4(px, orig):
    sty = measure(orig, (40, 190, 410, 250), (40, 48))
    lines(px, orig, (30, 180, 420, 345), [(190, 250), (280, 338)], ['칩 데이터를', '송신 중...'], strip=(40, 48), sty=sty)
    lines(px, orig, (555, 180, 925, 345), [(190, 250), (280, 338)], ['칩이 선택되지', '않았습니다!'], strip=(560, 568),
          sty=sty)
    lines(px, orig, (24, 660, 426, 815), [(668, 735), (756, 812)], ['칩 폴더를', '셔플!'], strip=('v', 625, 660), sty=sty)


SUB4 = {f'submenu_{c}_ct': job_submenu4 for c in ('base', 'black', 'blue', 'green', 'pink')}
RES4 = {f'result_{c}_ct': job_result4 for c in ('base', 'black', 'blue', 'green', 'pink')}

JOBS = {
    'exe4': dict(SUB4, **RES4, **{
        'title_moji_ct': job_title_moji, 'title_moji_plus_ct': job_title_moji_plus4, 'sort_ct': job_sort,
        'bbs_tag_ct': job_bbs_tag4, 'map_ct': job_map4, 'minigame_icon_ct': job_minigame_icon4,
        'navi_submenu_ct': job_navi_submenu4, 'patch_card_ct': job_patch_card4, 'tournamant_ct': job_tournament4, 'cockpitCards_ct': job_cockpit_cards4,
    }),
    'exe4b': {'submenu_base_ct': job_submenu4, 'result_base_ct': job_result4, 'tournamant_ct': job_tournament4b},
    'exe5': {
        'title_moji_ct': job_title_moji, 'submenu_base_ct': job_submenu5, 'sort_ct': job_sort, 'result_ct': job_result,
        'map_ct': job_map5, 'bbs_ct': job_bbs5, 'navi_moji_ct': job_navi_moji5, 'patch_card_ct': job_patch_card,
        'mission_bonus_ct': job_mission_bonus5, 'mission_guide_ct': job_mission_guide5,
        'cockpit_cards_ct': job_cockpit_cards5,
    },
    'exe6': {
        'title_moji_ct': job_title_moji, 'submenu_base_ct': lambda p, o: job_submenu6(p, o, ROWS6), 'sort_ct': job_sort6,
        'result_ct': job_result, 'map_guide_ct': job_map_guide6, 'minigame_guide_ct': job_minigame_guide6,
        'navi_moji_ct': job_navi_moji6, 'patch_card_ct': job_patch_card6, 'cockpit_chips_ct': job_cockpit_chips6,
        'cross_ct': job_cross6,
    },
    'exe6f': {
        'submenu_base_ct': lambda p, o: job_submenu6(p, o, ROWS6F), 'sort_ct': job_sort6, 'sort_mail_ct': job_sort_mail6,
        'patch_card_ct': job_patch_card6, 'cross_ct': job_cross6f,
    },
    'exe5k': {
        'submenu_base_ct': job_submenu5, 'sort_ct': job_sort, 'map_ct': job_map5, 'patch_card_ct': job_patch_card5k,
    },
}


def main(vers=None, only=None):
    sys.stdout.reconfigure(encoding='utf-8')
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for ver, jobs in JOBS.items():
        if vers and ver not in vers:
            continue
        src = ROOT / '_work' / 'romfs' / ver / 'data' / 'ui'
        out = ROOT / 'build' / 'romfs' / ver / 'data' / 'ui'
        out.mkdir(parents=True, exist_ok=True)
        for name, fn in jobs.items():
            if only and name not in only:
                continue
            raw, start, px = read(src / f'{name}.pak')
            orig = px.copy()
            fn(px, orig)
            write(out / f'{name}.pak', raw, start, px)
            im = Image.fromarray(px, 'RGBA')
            bg = Image.new('RGBA', im.size, (90, 0, 90, 255))
            bg.alpha_composite(im)
            s = min(1.0, 1200 / im.width)
            bg.resize((int(im.width * s), int(im.height * s))).convert('RGB').save(PREVIEW / f'{ver}__{name}.png')
            print('ok', ver, name)


if __name__ == '__main__':
    args = sys.argv[1:]
    main([a for a in args if a.startswith('exe')] or None, [a for a in args if not a.startswith('exe')] or None)
