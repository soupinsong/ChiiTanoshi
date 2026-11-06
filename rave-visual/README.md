# rave-visual — 먼가 작고 신나는 레이브

먼작귀 팀 (중앙대 예술공학부 [이머시브 AI 기술]) DJ 퍼포먼스 백월 영상 시스템.
DJ 컨트롤러(Pioneer DDJ-FLX4) 조작값, DJ 실루엣·손 제스처, 관객 점프를 TouchDesigner(TD)에서 실시간 영상으로 바꾼다.
백월은 좌:중앙:우 = 1:2:1. 중앙 = DJ 조작 이펙트 + 실루엣, 좌우 = 드롭 구간의 관객 점프 이펙트.

TD 프로젝트 파일(.toe)은 저장소에 없다. 이 저장소에는 TD에 붙여 넣을 스크립트와 따라 만드는 가이드가 있다.

## 구조

```
docs/
  mapping.md            조작부 ↔ MIDI ↔ TD 채널 ↔ 화면 반응 표
  td_build_guide.md     TD에서 따라 만드는 단계별 가이드
  checklist.md          주말 체크리스트
tools/
  flx4_sim.py           가상 FLX4 (기기 없이 같은 MIDI 송신)
td/scripts/             TD DAT에 넣는 Python
  tdutil.py             공용 도우미, Constant CHOP 채널 목록
  show_ext.py           쇼 컨트롤러 Extension (ShowExt)
  jog_callbacks.py      MIDI In DAT 콜백 (조그 누적, 버튼·패드)
  frame_callbacks.py    Execute DAT 매 프레임 (조그 속도, 제스처, ShowExt.Update)
  keyboard_callbacks.py 운영자 키 → ShowExt
  derive_script.py      파생 채널 Script CHOP (deck_mix, bass_w, pulse …)
  dots_script.py        중앙 점 구름 Script CHOP (Instancing용)
  gesture.py            주먹 → 편 손 토글 판정
presets/setlist.json    곡 세트 예시
assets/center, side/    화면 소스 (README 참고)
arduino/jump_sensor/    점프 센서 펌웨어 (P1)
```

## 준비

1. **Python 3.10 이상** (3.9에서도 시뮬레이터는 동작 확인함)
2. 패키지: `pip install mido python-rtmidi`
3. **loopMIDI** (가상 MIDI 포트)
   - Tobias Erichsen 사이트에서 loopMIDI를 받아 설치, 실행
   - 창 아래 `+` 버튼으로 포트 1개 생성 (기본 이름 `loopMIDI Port`). 이름에 `loopMIDI`가 들어 있으면 시뮬레이터가 자동으로 찾는다
   - loopMIDI는 켜 둔 동안만 포트가 있다
4. TouchDesigner (무료 버전, 1280×720 이하로 테스트)

## 가상 컨트롤러 실행

`rave-visual` 폴더에서:

```
python tools/flx4_sim.py
```

- 창이 뜨면 `출력 포트: loopMIDI Port …`가 찍히고 FLX4와 같은 MIDI를 보낸다 (규격은 [docs/mapping.md](docs/mapping.md)).
- 포트를 못 찾으면 `'loopMIDI' 포트 없음. 현재 포트: [...]`를 출력하고 종료한다. loopMIDI를 켜고 포트를 만든 뒤 다시 실행한다.
- 조작: 슬라이더 = CC(MSB + LSB 0), 버튼 = 누를 때 velocity 127 / 뗄 때 0, JOG 슬라이더 = 20ms마다 `64 + 속도` (SIDE/TOP 선택), 패드 = 모드 메뉴에 따라 노트 범위가 바뀜.

## TD 작업 순서

[docs/td_build_guide.md](docs/td_build_guide.md)를 1부부터 순서대로 따라 한다.

1. 제어 버스 `ctrl` (MIDI In CHOP → Select → Rename → Math → Lag → Null), `show` COMP
2. 조그 (MIDI In DAT 콜백)
3. 파생 채널 (Script CHOP)
4. 중앙 화면 이펙트
5. 실루엣 이펙트 (MediaPipe 세그멘테이션)
6. 제스처 토글

운영자 키 (TD 창에 포커스): F1 = 좌우 화면 토글(3·2·1 카운트다운), P = 비상 정지, ←/→ = 덱1 곡, Shift+←/→ = 덱2 곡.

## TD 밖에서 테스트

```
python td/scripts/gesture.py    # 제스처 판정 자체 테스트
```

## 현재 상태 (2026-11-06)

- P0 스크립트·가이드 작성. TD 안에서는 아직 확인 전이다. 코드의 `TODO(TD에서 확인)`은 TD에서 실제 이름을 보고 고쳐야 하는 부분이다.
- 곡 세트 기능(`LoadSetlist` 등)은 스텁. 임시 곡 2개로만 동작한다 (P1).
- 기기(FLX4)는 아직 없음. 받으면 [docs/mapping.md](docs/mapping.md) 5장 항목을 확인한다.
