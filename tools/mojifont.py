"""컬렉션 Vol.2 대화창 HD 글꼴 <lang>_mojiFont.fnt 해석.

구조(2026-11-10 실측):
  0x00 'font', u16 0x8001, u16 n_map, u16 n_glyph, u16 셀 폭, u16 셀 높이, u16 기준선?, ...
  0x14 u16 ascii_lo(9), u16 ascii_cnt(=다음 표 첫 시작) — 0x00xx 는 map[0..] 직접
  0x110 버킷 224개 x 8B: (u32 map 시작, u16 하위 바이트 시작, u16 개수), 버킷 = 유니코드 상위 바이트 - 0x20
  0x810 map u16 x n_map = 글리프 번호
  레코드 20B x (장 수 + n_glyph): 장 레코드(첫 바이트 0x00) 뒤 글리프 레코드
     = u8 장 번호, u8 플래그, fp16 x9 (베어링x, 베어링y, 폭, 높이, u0, v0, u1, v1, 전진폭)
  RGBA 아틀라스 장들(장마다 2048 폭)
  끝: u32 n_code + u16 x n_code = 게임 글자 코드 -> 유니코드
"""
import struct
from pathlib import Path
import numpy as np


class MojiFont:
    def __init__(self, path):
        self.path = Path(path)
        d = self.raw = bytearray(self.path.read_bytes())
        self.n_map, self.n_glyph = struct.unpack_from('<HH', d, 6)
        self.cell = struct.unpack_from('<HH', d, 10)
        self.ascii_lo, self.ascii_cnt = struct.unpack_from('<HH', d, 0x14)
        self.buckets = [struct.unpack_from('<IHH', d, 0x110 + 8 * i) for i in range(224)]
        self.map_off = 0x810
        self.map = list(struct.unpack_from('<%dH' % self.n_map, d, self.map_off))
        rec = self.map_off + 2 * self.n_map   # 글리프 레코드 n_glyph 개가 바로 이어진다(0~2번은 빈 글리프)
        self.rec_off = rec
        self.glyphs = []
        for g in range(self.n_glyph):
            o = rec + 20 * g
            page, flag = d[o], d[o + 1]
            vals = struct.unpack_from('<9e', d, o + 2)
            self.glyphs.append((page, flag) + vals)
        n = len(d)
        for cnt in range(1, 8000):
            if struct.unpack_from('<I', d, n - 2 * cnt - 4)[0] == cnt:
                break
        self.code_off = n - 2 * cnt - 4
        self.codes = list(struct.unpack_from('<%dH' % cnt, d, self.code_off + 4))
        # 아틀라스 = 폭 4096 RGBA 한 장(높이 512 배수), 코드 표 바로 앞에 붙어 있다.
        # 글리프는 가로로 늘려 저장(UV 로 화면 비율 복원)
        self.page_w = 4096
        avail = self.code_off - (rec + 20 * self.n_glyph)
        self.page_h = -(-avail // (4 * self.page_w * 512)) * 512
        if 4 * self.page_w * self.page_h - avail > 64:
            self.page_h -= 512
        self.pix_off = self.code_off - 4 * self.page_w * self.page_h
        # 장: 0번 = 위 1024줄(아이콘), 1번 = 그 아래 나머지(정사각이 아닐 수 있음). y = v * 장높이 + 장시작
        self.pages = {0: (0, 1024), 1: (1024, self.page_h - 1024)}

    def atlas(self):
        o = self.pix_off
        return np.frombuffer(self.raw, np.uint8, self.page_w * self.page_h * 4, o).reshape(self.page_h, self.page_w, 4).copy()

    def set_atlas(self, px):
        o = self.pix_off
        self.raw[o:o + px.size] = px.astype(np.uint8).tobytes()

    def glyph_of(self, u):
        if self.ascii_lo <= u < self.ascii_lo + self.ascii_cnt:
            return self.map[u - self.ascii_lo]
        hi, lo = u >> 8, u & 0xFF
        if not 0x20 <= hi < 0x20 + 224:
            return None
        s, l0, cnt = self.buckets[hi - 0x20]
        if cnt and l0 <= lo < l0 + cnt:
            return self.map[s + lo - l0]
        return None

    def rect(self, g):
        page, flag, x0, y0, x1, y1, u0, v0, u1, v1, adv = self.glyphs[g]
        top, h = self.pages[page]
        return (int(round(u0 * self.page_w)), int(round(v0 * h + top)),
                int(round(u1 * self.page_w)), int(round(v1 * h + top)))

    def save(self, path):
        Path(path).write_bytes(bytes(self.raw))
