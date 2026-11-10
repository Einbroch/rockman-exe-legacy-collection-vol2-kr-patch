# 록맨 에그제 레거시 컬렉션 Vol.2 한글패치

Mega Man Battle Network Legacy Collection Vol. 2 (Nintendo Switch, 0100734016266000) 한글패치입니다.
게임의 **번체 중국어(繁體中文)** 언어 칸을 한국어로 바꿉니다. 일본어·영어 칸은 그대로입니다.

> 게임 파일(롬·NSP·추출물)은 이 저장소에 없습니다. 패치 파일은 [Releases](../../releases) 에서 받으세요.

## 대상

| 항목 | 값 |
|---|---|
| 본편 | 0100734016266000 (v0) |
| 업데이트 | 0100734016266800 **v262144 (1.0.4)** — 필수. 런처 메뉴 패치가 이 판의 실행 파일에 맞춰져 있습니다 |
| DLC | 0100734016267001 — 있어도 없어도 됩니다(DLC 내용물은 본편 데이터에 들어 있어 같이 한글화됩니다) |

## 한글화 범위

- **록맨 에그제 4 (레드선·블루문) / 5 (팀 오브 블루스·팀 오브 카넬) / 6 (전뇌수 그레이가·전뇌수 팔자)**:
  대사·메뉴·칩 이름·설명, 폰트(대화창 HD 글꼴·본문·메뉴), 그림 글자(서브메뉴·결과·타이틀·지도·개조 카드 등 47장)
- **컬렉션 런처**: 메인 메뉴·설정·통신 화면·PC 조작 안내, 갤러리(아트·뮤직 플레이어·트로피), EXE4~6 칩 목록·내비커스,
  배포 칩·개조 카드 설명, 안내 그림, 타이틀 로고 「콜렉션 2」
- 각 게임 대사는 기존 한글패치의 번역을 컬렉션 형식으로 옮긴 것입니다.
  - EXE4: [rockman-exe4-kr-patch](https://github.com/Einbroch/rockman-exe4-kr-patch) v0.9.4
  - EXE5: [rockman-exe5-kr-patch](https://github.com/Einbroch/rockman-exe5-kr-patch) v0.9.4
  - EXE6: [rockman-exe6-kr-patch](https://github.com/Einbroch/rockman-exe6-kr-patch) v0.9.5
- Vol.1 은 [rockman-exe-legacy-collection-vol1-kr-patch](https://github.com/Einbroch/rockman-exe-legacy-collection-vol1-kr-patch) 에 있습니다.

## 설치

### 스위치 (Atmosphere)

1. `MMBNLC2_KR_v0.9.0_atmosphere.zip` 을 SD 카드 루트에 풉니다.
   - `atmosphere/contents/0100734016266000/romfs/...`
   - `atmosphere/exefs_patches/MMBNLC2_KoreanPatch/A736E99122555BA730FD42DE3A2E3E562BEAD44E.ips`
2. 본체 **시스템 언어를 「繁體中文」** 으로 둡니다(컬렉션은 시스템 언어로 표시 언어를 정합니다).

### 에뮬레이터 (Eden / yuzu 계열, Ryujinx)

1. `MMBNLC2_KR_v0.9.0_emulator.zip` 을 풀면 `KoreanPatch/` 폴더가 나옵니다.
2. 게임 우클릭 → 모드 폴더 열기(Open Mod Data Location)에 `KoreanPatch` 폴더째 넣습니다.
   - Eden/yuzu: `load/0100734016266000/KoreanPatch/{romfs,exefs}`
   - Ryujinx: `mods/contents/0100734016266000/KoreanPatch/{romfs,exefs}`
3. 에뮬레이터의 시스템 언어를 **번체 중국어(Traditional Chinese)** 로 둡니다.
4. 업데이트 1.0.4 가 실제로 적용됐는지 확인하세요. 1.0.0 으로 뜨면 런처 메뉴가 번체로 남습니다.

## 알려진 점

- 한국어로 보려면 언어가 번체 중국어여야 합니다.
- 언어 선택 목록의 「日本語」·「简体中文」은 언어 이름이라 그대로 두었습니다.
- 타이틀 로고(ROCKMAN EXE)와 일부 영어 그림 글자(ROCK BUSTER 등)는 번체판도 영어라 그대로입니다.
- GBA 한글패치에서도 번역되지 않았던 일부 스크립트(디버그·데이터용 등)는 번체 원문 그대로입니다.
- 아직 모든 화면을 실제 플레이로 확인하지는 못했습니다(그래서 0.9 판입니다). 깨지거나 일본어·중국어가 남은 화면을 이슈로 알려 주세요.

## 도구 (`tools/`)

직접 빌드하려면 본편+업데이트 RomFS·exefs 를 추출하고 각 GBA 한글 롬을 준비해야 합니다(경로는 `tools/game_cfg.py`, 글꼴 경로는 각 도구 머리).

| 파일 | 하는 일 |
|---|---|
| `build_vol2.py exe4\|exe5\|exe6` | 한글 롬 대사 → 번체 칸 `message_cht.mpak/.map` + 폰트(두 판본 한 번에) |
| `gate_vol2.py <게임>` | 빌드한 mpak 을 다시 읽어 해석 못 한 바이트·명령 골격·빈 글자 칸 검사 |
| `ksrc.py` | GBA 한글 롬 해석(포인터 대조·LZ·롬 점프 추적) |
| `game_cfg.py` | 판본 6개 설정, 직접 번역 몇 곳 |
| `fonts_vol2.py`, `mojifont.py`, `moji_ko.py` | 비트맵 폰트 / 대화창 HD 글꼴(`cht_mojiFont.fnt`) 형식과 한글 그리기 |
| `cht_symbols.py` | 게임마다 다른 번체 폰트 기호 칸 확정 |
| `ui_vol2.py`, `ui_ko_vol2.py` | 게임 그림 글자 |
| `launcher_xaml.py` | 런처 실행 파일 속 NoesisGUI XAML → exefs IPS32 패치 |
| `launcher_data_vol2.py`, `launcher_data_vol2_tr.py` | Vol.2 전용 런처 데이터(아트·칩·카드·트로피) 번역 생성 |
| `launcher_vol2.py`, `launcher_logo_vol2.py` 외 `launcher_*` | 런처 그림·로고·갤러리 |
| `make_dist.py` | 배포 zip 두 벌 + SHA256SUMS |

폰트는 [에스코어 드림](https://www.s-core.co.kr/company/font/)(S-Core Dream)을 썼습니다(일부 드문 음절은 맑은 고딕).
