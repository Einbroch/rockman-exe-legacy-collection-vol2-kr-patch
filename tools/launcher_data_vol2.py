"""Vol.2 전용 런처 데이터 사전(실행 파일 XAML) 번역 -> tools/launcher_data_vol2_ko.json [{off, cht, ko}]

대상 문서(Vol.2 실행 파일 위치): 아트 Vol.2 0x5a2ac8e · 개조 카드 효과 0x5a88363 · EXE1~3 칩 0x5ba9d54(일부) ·
EXE4~6 칩 0x5cf6cc0 · 내비커스 0x5e6779e · 트로피 Vol.2 0x5eebf77.
원천: work/gallery_src.json(work/gallery_src_vol2.py) — 블록마다 *_CHT 와 같은 키의 일본어·영어.
번역 순서: 직접 번역 > 컬렉션 일본어 mpak ↔ 한국어 빌드 짝 사전(work/lc_jp_ko.json + Vol.1 것) > 문형·용어 규칙.

버튼 그림이 끼는 설명(카드 효과·일부 칩)은 번체와 일본어가 글/그림 칸을 다르게 나눈다 → 번체 그림 칸(Inf_img*_CHT,
Name_img*_CHT)을 일본어판 값으로 바꾸고 글 칸은 일본어 조각을 하나씩 옮긴다.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from launcher_gallery_text import ART_TERMS, loose  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT.parent / 'Rockman EXE Collection Vol. 1'
DOCS = {'0x5a2ac8e', '0x5a88363', '0x5ba9d54', '0x5cf6cc0', '0x5e6779e', '0x5eebf77'}
SPLIT_DOCS = {'0x5a88363'}          # 문서 전체를 일본어 칸 배치로
NL = '&#xA;'
JA = re.compile('[ぁ-ゖァ-ヺ一-鿿]')   # ・ ー 는 한국어 문장에도 쓴다


def has_batchim(word):
    for ch in reversed(word):
        if '가' <= ch <= '힣':
            return (ord(ch) - 0xAC00) % 28 != 0
        if ch.isdigit():
            return ch in '013678'
        if ch.isalpha():
            return ch.upper() in 'LMNR'
    return False


def josa(word, pair):
    a, b = pair.split('/')
    if pair == '로/으로':
        w = word.rstrip()
        if w and w[-1].isdigit():   # 숫자 읽기: 영·삼·육 만 받침(ㄹ 아닌), 일·칠·팔은 ㄹ 받침이라 「로」
            return word + ('으로' if w[-1] in '036' else '로')
        last = [c for c in word if '가' <= c <= '힣']
        if last and ((ord(last[-1]) - 0xAC00) % 28 in (0, 8)):
            return word + '로'
        return word + ('으로' if has_batchim(word) else '로')
    return word + (b if has_batchim(word) else a)


# ---------------------------------------------------------------- 용어
TERMS = {
    'ためうちで': '모아 쏘기: ', 'のため撃ちで': ' 모아 쏘기로 ', 'HPバグ': 'HP 버그', 'バトル中': '배틀 중 ', 'カスタム中': '커스텀 중 ',
    'ダメージ時に盲目発生バグ': '피격 시 실명 버그', 'ダメージ時に混乱発生バグ': '피격 시 혼란 버그', 'バスター空撃ちバグ': '버스터 헛방 버그',
    '端まで移動バグ': '끝까지 이동 버그', '移動時のパネルバグを修正': '이동 시 패널 버그 수정', '移動時にパネルあな': '이동 시 패널 구멍',
    'カスタムダメージバグを修正': '커스텀 대미지 버그 수정', 'カスタムダメージバグ': '커스텀 대미지 버그',
    'ココロウインドウバグを修正': '마음 윈도 버그 수정', 'ココロウインドウバグ': '마음 윈도 버그', 'HPバグを修正': 'HP 버그 수정',
    'バグを修正': '버그 수정', 'の追加効果をOFF': ' 추가 효과 해제', 'をOFF': ' 해제', 'チップ使用時にリカバリー': '칩 사용 시 리커버리',
    'チャージショットに盲目': '차지샷에 실명', 'チャージショットに混乱': '차지샷에 혼란', 'チャージショットにマヒ': '차지샷에 마비',
    'チャージショットでパネルマグマ': '차지샷으로 용암 패널', 'チャージショットでパネルこおり': '차지샷으로 얼음 패널',
    'チャージショットの追加効果': '차지샷 추가 효과', 'バスターでパネルくさむら': '버스터로 풀숲 패널', 'バスターでパネルヒビ': '버스터로 금 간 패널',
    'バスターでパネルどくぬま': '버스터로 독늪 패널', 'バスターで右おしやり': '버스터로 오른쪽 밀어내기', 'バスターでチャージショット': '버스터로 차지샷',
    'パネルくさむら': '풀숲 패널', 'パネルヒビ': '금 간 패널', 'パネルこおり': '얼음 패널', 'パネルあな': '패널 구멍', 'で足止め': '로 발 묶기',
    'アタック': '어택', 'ラピッド': '래피드', 'チャージ': '차지', 'カスタム': '커스텀', 'ギガフォルダ': '기가 폴더', 'メガフォルダ': '메가 폴더',
    'ソウルタイム': '소울 타임', 'ヘビーゲージ': '헤비 게이지', 'ダメージ': '대미지', 'バグ': '버그', '盲目': '실명', '混乱': '혼란',
    'チャージショット': '차지샷', 'バスター': '버스터', 'シールド': '실드', 'ソード': '소드', '水鉄砲': '물총', 'フラワー': '플라워',
    'トラップ': '트랩', 'シューティングバスター': '슈팅 버스터', 'フォルテクロスロックマンになる': '포르테 크로스 록맨이 된다',
    'でメテオ×': '로 메테오×', 'メテオ': '메테오', 'リカバリー': '리커버리', 'セルフリカバリー': '셀프 리커버리',
    '1発ごとにHP-1': '1발마다 HP-1', '中': ' 중 ',
}


class Tr:
    def __init__(self):
        lc = {}
        for f in (ROOT / 'work' / 'lc_jp_ko.json', V1 / 'work' / 'lc_jp_ko.json'):
            for k, v in json.loads(f.read_text(encoding='utf-8')).items():
                lc.setdefault(loose(k), v)
        self.lc = lc
        self.terms = dict(TERMS)
        for k, v in MANUAL_TERMS.items():
            self.terms[k] = v

    def name(self, jp):
        """칩·프로그램 이름: 짝 사전(정확) > 직접 용어 > SP/DS/EX 접미사."""
        j = jp.strip()
        if j in self.terms:
            return self.terms[j]
        v = self.lc.get(loose(j))
        if v and not JA.search(v) and '&#xA;' not in v and len(v) < 20:
            return v
        m = re.match(r'(.+?)(ＳＰ|ＤＳ|ＥＸ|SP|DS|EX)$', j)
        if m:
            b = self.name(m.group(1))
            if b:
                return b + m.group(2).translate(str.maketrans('ＳＰＤＥＸ', 'SPDEX'))
        return None

    def phrase(self, s):
        out = s
        pats = [
            (r'^のため撃ちで発射する武器を(.+?)に改造！$', lambda n: f" 모아 쏘기로 발사하는 무기를 {josa(n, '로/으로')} 개조!"),
            (r'^のコマンド入力で(.+?)が(&#xA;)?発動するようになる！$',
             lambda n, br='': f" 커맨드 입력으로 {josa(n, '가/이')}" + (NL if br else ' ') + '발동한다!'),
            (r'^で使う武器を(.+?)に変更する！$', lambda n: f"로 쓰는 무기를 {josa(n, '로/으로')} 변경!"),
            (r'^のため撃ちで(.+?)を発動！$', lambda n: f" 모아 쏘기로 {josa(n, '를/을')} 발동!"),
        ]
        for p, fn in pats:
            m = re.match(p, s)
            if m:
                n = self.name(m.group(1).replace(NL, ''))
                if n is None:
                    return None
                return fn(n, m.group(2)) if m.lastindex and m.lastindex > 1 else fn(n)
        fixed = {'で技発動': '로 기술 발동', '2枚1組で効果が発揮される超強化改造！&#xA;': '2장 1세트로 효과를 내는 초강화 개조!&#xA;',
                 '+': '+', 'をOFF': ' 해제'}
        if s in fixed:
            return fixed[s]
        # 일반: 줄·「 / 」 단위로 나눠 용어 치환
        parts = re.split(r'(&#xA;| / |/ | /|\+|-|×)', out)
        res = []
        for p in parts:
            if p in ('&#xA;', ' / ', '/ ', ' /', '+', '-', '×') or not JA.search(p):
                res.append(p)
                continue
            q = p
            lead = ''
            m = re.match(r'^(ためうちで|で)(.*)$', q)
            if m:
                lead = '모아 쏘기: ' if m.group(1) == 'ためうちで' else '로 '
                q = m.group(2)
            n = self.name(q)
            if n is None:
                n = q
                for k in sorted(self.terms, key=len, reverse=True):
                    if k in n:
                        n = n.replace(k, self.terms[k])
                if JA.search(n):
                    # 남은 가타카나 낱말을 이름 사전으로
                    def sub(mm):
                        return self.name(mm.group(0)) or mm.group(0)
                    n = re.sub(r'[ァ-ヿ]+[0-9]*', sub, n)
            res.append(lead + n)
        r = ''.join(res)
        r = re.sub(r' {2,}', ' ', r)
        return r


# 짝 사전에 없는 이름·용어(GBA 한글판 표기)
MANUAL_TERMS = {
    'エアシューズ': '에어 슈즈', 'フロートシューズ': '플로트 슈즈', 'アンダーシャツ': '언더셔츠', 'スーパーアーマー': '슈퍼 아머',
    'ファーストバリア': '퍼스트 배리어', 'ステータスガード': '스테이터스 가드', 'シノビダッシュ': '시노비 대시',
    'ノーマルボディ': '노멀 보디', 'ファイアボディ': '파이어 보디', 'アクアボディ': '아쿠아 보디', 'エレキボディ': '일렉 보디',
    'ウッドボディ': '우드 보디', 'ラビリング': '라비링', 'パルスビーム': '펄스 빔', 'ヘルズローリング': '헬즈 롤링',
    'ヘルズバーナー': '헬즈 버너', 'ガッツマシンガン': '거츠머신건', 'マシンガン': '머신건', 'サムライソード': '사무라이 소드',
    'フラッシュボム': '플래시봄', 'ドールサンダー': '돌 썬더', 'エレキパルス': '일렉 펄스', 'コーンショット': '콘 샷',
    'サンドワーム': '샌드웜', 'バルカン': '벌컨', 'ガンデルソル': '건 델 솔', 'カワリミ': '카와리미', 'スイコミ': '스이코미',
    'クラックシュート': '크랙 슛', 'リスキーハニー': '리스키 허니', 'マシーンソード': '머신 소드', 'トリプルバスター': '트리플 버스터',
    'メガエナジーボム': '메가에너지봄', 'スーパーキタカゼ': '슈퍼 북풍', 'トリプルクラック': '트리플크랙',
    'インビジブル': '인비저블', 'ヨーヨー': '요요', 'カースシールド': '커스실드', 'ブーメラン': '부메랑', 'ファイアアーム': '파이어 암',
    'ポルターガイスト': '폴터가이스트', 'トルネード': '토네이도', 'エンゲツクナイ': '엔게츠 쿠나이', 'エアホッケー': '에어하키',
    'サークルガン': '서클건', 'ドリルアーム': '드릴 암', 'ブラックボム': '블랙봄', 'オーシャンシード': '오션 시드',
    'カーネルキャノン': '커널 캐논', 'フルカスタム': '풀커스텀', 'メットガード': '메트가드', 'クラックアウト': '크랙아웃',
    'ミニボム': '미니봄', 'リフレクト': '리플렉트', 'ホウガン': '호우건',
}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    rows = json.loads((ROOT / 'work' / 'gallery_src.json').read_text(encoding='utf-8'))
    done = {x['off'] for x in json.loads((ROOT / 'tools' / 'launcher_gallery_ko.json').read_text(encoding='utf-8'))}
    tr = Tr()
    # 그림 칸이 번체·일본어 다른 블록(버튼 그림이 끼는 설명)은 블록째 일본어 배치로
    split_blocks = {(r['doc'], r['block']) for r in rows
                    if r['doc'] in DOCS and '_img' in r['key'] and r['jp'] and r['jp'] != r['cht']}
    out, left = [], []
    for r in rows:
        if r['doc'] not in DOCS or r['off'] in done:
            continue
        cht, jp = r['cht'], r['jp']
        is_img = '_img' in r['key']
        if r['doc'] in SPLIT_DOCS or (r['doc'], r['block']) in split_blocks:
            if is_img:
                if jp != cht:
                    out.append({'off': r['off'], 'cht': cht, 'ko': jp})
                continue
            if not jp.strip('　 '):
                if cht.strip('　 '):
                    out.append({'off': r['off'], 'cht': cht, 'ko': '　'})
                continue
            ko = MANUAL.get(jp) or tr.phrase(jp)
        else:
            if not JA.search(cht) or is_img:
                continue
            if r['doc'] == '0x5a2ac8e':
                ko = MANUAL.get(jp) or art(jp)   # 아트 이름은 규칙으로(게임 속 두 줄 이름을 끌어오지 않게)
            else:
                ko = MANUAL.get(jp) or tr.lc.get(loose(jp)) or (tr.name(jp) if r['key'].startswith('Name') else None)
        if ko is None or JA.search(ko):
            left.append((r['doc'], r['key'], jp, ko))
            continue
        ko = ko.replace('\\n', NL).replace('、', ', ').replace('十자', '십자')
        ko = re.sub(r'&(?!#xA;|amp;)', '&amp;', ko)
        out.append({'off': r['off'], 'cht': cht, 'ko': ko})
    (ROOT / 'tools' / 'launcher_data_vol2_ko.json').write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    print('번역', len(out), '남음', len(left))
    seen = set()
    for x in left:
        if x[2] in seen:
            continue
        seen.add(x[2])
        print(' ', x[0], x[1], repr(x[2])[:70], '->', repr(x[3])[:60])
    return not left


from launcher_data_vol2_tr import ART2_TERMS, MANUAL  # noqa: E402

_TR = None


def art(jp):
    global _TR
    if _TR is None:
        _TR = Tr()
    s = jp
    terms = dict(ART_TERMS, **ART2_TERMS)
    for k in sorted(terms, key=len, reverse=True):
        s = s.replace(k, terms[k])
    # 남은 가타카나 낱말(내비 이름 등)은 이름 사전으로
    s = re.sub(r'[ァ-ヺー]+', lambda m: _TR.name(m.group(0)) or m.group(0), s)
    return re.sub(r' {2,}', ' ', s).strip()

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
