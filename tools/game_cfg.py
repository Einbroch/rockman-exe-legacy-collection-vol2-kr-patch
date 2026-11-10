"""Vol.2 게임별 설정. 한 게임(폰트 공유) = 판본 두 개."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLUDE = ROOT.parent
WORK = ROOT / '_work'
ROMFS = WORK / 'romfs'


@dataclass
class Ver:
    key: str            # 대사 폴더 이름(romfs/<key>/data/msg)
    game: str           # 폰트 폴더(romfs/<game>/data/ui)
    n: int              # 4/5/6
    coll_rom: Path      # 컬렉션 롬(map 주소 기준)
    orig_rom: Path      # 한글패치의 원본 롬(포인터 위치 기준). 컬렉션 롬과 같으면 같은 파일
    k_rom: Path
    lead: int           # 한글·점프 명령 첫 바이트(EXE4 F9, EXE5·6 FA)
    line_subs: tuple = ()
    text_fixes: dict = field(default_factory=dict)

    @property
    def db(self):
        return f'mmbn{self.n}'

    @property
    def simple_db(self):
        return f'mmbn{self.n}s'

    @property
    def lc_db(self):
        return f'mmbn{self.n}-lc'

    @property
    def jp_tbl(self):
        return f'exe{self.n}-utf8'

    @property
    def lc_jp_tbl(self):
        return f'exeac-exe{self.n}-utf8'

    @property
    def msg_dir(self):
        return ROMFS / self.key / 'data' / 'msg'

    @property
    def ui_dir(self):
        return ROMFS / self.game / 'data' / 'ui'

    @property
    def out_msg(self):
        return ROOT / 'build' / 'romfs' / self.key / 'data' / 'msg'

    @property
    def out_ui(self):
        return ROOT / 'build' / 'romfs' / self.game / 'data' / 'ui'

    def symbols(self):
        """{코드: 글자} 번체 폰트의 보존 칸(기호·가나·아이콘)."""
        d = json.loads((ROOT / 'build' / f'cht_symbols_{self.game}.json').read_text(encoding='utf-8'))
        return {int(k): v for k, v in d.items()}


def _v(key, game, n, coll, orig, k, lead, **kw):
    return Ver(key, game, n, ROMFS / game / coll, orig, WORK / 'kroms' / k, lead, **kw)


E4 = CLUDE / 'Rockman exe 4'

# GBA 한글판이 손대지 않은(포인터로 닿지 않던) 장면 — 직접 번역. 구간 = 컬렉션 일본어판의 연속 글자 구간 순서
EXE5_SHIP = [
    ['자, 슬슬 출발할|시간이다...', '부자들만|모인 파티인가...|좀 긴장되네', '좋아, 한번 힘내 볼까!'],
    ['여기가 기관실인가...', '우선 플러그인할 수 있는|곳을 찾아볼까'],
    ['응? 바람이 느껴져...', '그렇구나, 거기가 통기구로|되어 있는 거구나...', '혹시 범인은|여기서 밖으로 나간 걸지도...',
     '...가 볼까!!'],
]   # | = 줄바꿈
VERS = {
    'exe4': _v('exe4', 'exe4', 4, 'rom.srl', ROMFS / 'exe4' / 'rom.srl', 'exe4r_ko.gba', 0xF9),
    'exe4b': _v('exe4b', 'exe4', 4, 'rom_b.srl', E4 / 'Rockman EXE 4 - Tournament Blue Moon (Japan).gba', 'exe4b_ko.gba', 0xF9),
    'exe5': _v('exe5', 'exe5', 5, 'rom.srl', ROMFS / 'exe5' / 'rom.srl', 'exe5b_ko.gba', 0xFA,
               text_fixes={(a, 0): r for a, r in zip((0x87BE680, 0x87BF084, 0x87BFFD0), EXE5_SHIP)}),
    'exe5k': _v('exe5k', 'exe5', 5, 'rom_k.srl', ROMFS / 'exe5' / 'rom_k.srl', 'exe5k_ko.gba', 0xFA,
                text_fixes={(a, 0): r for a, r in zip((0x87BFB20, 0x87C0524, 0x87C1470), EXE5_SHIP)}),
    'exe6': _v('exe6', 'exe6', 6, 'rom.srl', ROMFS / 'exe6' / 'rom.srl', 'exe6g_ko.gba', 0xFA),
    'exe6f': _v('exe6f', 'exe6', 6, 'rom_f.srl', ROMFS / 'exe6' / 'rom_f.srl', 'exe6f_ko.gba', 0xFA),
}
GROUPS = {'exe4': ['exe4', 'exe4b'], 'exe5': ['exe5', 'exe5k'], 'exe6': ['exe6', 'exe6f']}
