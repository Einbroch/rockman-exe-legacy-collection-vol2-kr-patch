"""Vol.1 실행 파일 위치로 지정한 갤러리 번역표(launcher_gallery_ko.json)를 Vol.2 실행 파일 위치로 옮긴다.
앞쪽 문맥(같은 항목의 다른 언어 키·이름)으로 Vol.2 이미지에서 유일한 자리를 찾는다. 못 찾거나 여러 곳이면 뺀다."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from launcher_xaml import load_nso
ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT.parent / 'Rockman EXE Collection Vol. 1'

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    img1, _ = load_nso(V1 / '_work' / 'exefs_upd' / 'main')
    img2, _ = load_nso(ROOT / '_work' / 'exefs_upd' / 'main')
    items = json.loads((V1 / 'tools' / 'launcher_gallery_ko.json').read_text(encoding='utf-8'))
    out, miss = [], 0
    for it in items:
        o = it['off']
        for ctx in (160, 400, 1000):
            pat = img1[o - ctx:o]
            i = img2.find(pat)
            if i >= 0 and img2.find(pat, i + 1) < 0:
                out.append(dict(it, off=i + ctx))
                break
        else:
            miss += 1
    (ROOT / 'tools' / 'launcher_gallery_ko.json').write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding='utf-8')
    print('옮김', len(out), '못 찾음', miss)

if __name__ == '__main__':
    main()
