# 먼가 작고 신나는 레이브 — Claude Code 작업 지시서

이 문서 하나에 프로젝트 배경, 이번 마감 작업, 기능 명세, API 명세, 참고 코드가 모두 들어 있다.
처음부터 끝까지 읽은 뒤 **4장 작업 목록의 P0를 순서대로** 진행한다.

---

## 0. 작업 규칙 (Claude에게)

- 사용자는 Windows 노트북에서 TouchDesigner(이하 TD)를 쓴다. TD 프로젝트 파일(.toe)은 바이너리라 직접 만들 수 없다. 너의 결과물은 **Python 스크립트, 아두이노 스케치, JSON, 그리고 사람이 TD에서 따라 할 단계별 가이드(md)** 이다.
- TD Python API는 확실한 것만 쓴다(`op()`, `.par.<이름>`, `op('x')['채널']`, Extension 클래스 패턴, `run()` 등). 확실하지 않은 파라미터 이름이나 콜백 시그니처는 추측해서 확정하지 말고 코드에 `# TODO(TD에서 확인): ...` 주석을 남긴다.
- TD 콜백 DAT은 TD가 자동 생성하는 템플릿의 함수 시그니처를 그대로 쓰게 하고, 함수 본문만 제공한다. 가이드에도 그렇게 적는다.
- MIDI 번호, 채널, 시리얼 형식은 7장 API 명세를 기준으로 한다. 명세와 다르게 구현해야 할 이유가 생기면 구현 전에 사용자에게 묻는다.
- 패키지 설치가 필요하면 설치 명령을 먼저 보여주고 진행한다. 의존성은 최소로 한다(mido, python-rtmidi 정도).
- 설명은 짧고 평이한 한국어로 한다. 과장된 표현은 쓰지 않는다.
- 각 작업을 끝낼 때마다 만든 파일 목록과 사용자가 직접 확인해야 할 것(TD에서 눌러볼 것 등)을 3줄 이내로 알려준다.

---

## 1. 프로젝트 배경

- 수업: 중앙대 예술공학부 [이머시브 AI 기술], 먼작귀 팀 (고명진(팀장), 박큰별, 송수빈, 안재욱). AI 사용은 필수가 아니다.
- 프로젝트: DJ 컨트롤러 조작값, DJ 실루엣·손 제스처, 관객 점프 데이터를 실시간 영상으로 바꿔 무대 뒤 백월 하나에 보여주는 관객 참여형 DJ 퍼포먼스.
- 백월은 좌:중앙:우 = 1:2:1. 중앙(A)은 DJ 조작 이펙트 + DJ 실루엣, 좌우(B)는 관객 점프 이펙트이며 드롭 구간에만 켜진다(DJ가 주먹 쥐었다 펴는 제스처 → 3·2·1 카운트다운 → 활성화, 같은 제스처로 끔).
- 가장 보여주고 싶은 것은 곡 전환: 두 곡을 다른 색으로 표시하고, 크로스페이더만큼 다음 곡 색이 늘고, 베이스 스왑(두 덱 EQ LOW 교체)을 하면 음악에 반응하는 요소가 이전 곡에서 다음 곡으로 넘어간다. 점 구름 프로토타입으로 한 번 구현해 봤다.
- 사용자(송수빈)는 팀의 DJ이며 담당은 **DJ 컨트롤러 조작부 ↔ TD 이펙트 매칭, DJ 모션(실루엣) 이펙트 구현**이다.
- 장비: Pioneer DDJ-FLX4 + rekordbox. **아직 기기를 사지 않았다.** 중간 보고서 때는 빌려서 테스트만 했다. 그래서 이번 마감까지는 가상 컨트롤러로 작업한다.
- 중간 보고서 대비 변경: 곡 정보는 스포티파이 API를 쓰지 않는다(신규 앱은 BPM 등 audio features 사용 불가, 개발 모드 제한). rekordbox XML 내보내기를 쓴다.

---

## 2. 환경

- OS: Windows
- TD: 무료 버전 기준으로 동작하게 한다(해상도 제한 고려, 1280×720 이하로 테스트).
- Python 3.10 이상 (TD 밖에서 도는 도구용)
- 가상 MIDI: loopMIDI (사용자가 설치, 포트 1개 생성)
- 웹캠: 노트북 내장, MediaPipe TD 플러그인(torinmb/mediapipe-touchdesigner) 사용. 웹캠 입력은 720p 이하.
- 아두이노 우노 + FSR406 + 10kΩ 전압 분배 (팀 다른 담당, 이번 마감 범위 아님)

---

## 3. 마감과 범위

- **마감: 2026-11-09(월) 13:30 멘토(장우진) 첫 미팅 전**
- 미팅에서 보여줄 것: 가상 컨트롤러로 조작하면 TD 중앙 화면이 반응하는 시연 영상, 매핑표, DJ 실루엣 잔상 효과
- 이번 범위: 4장의 P0. P1은 시간이 남으면.

---

## 4. 작업 목록

### 저장소 구조 (먼저 만든다)

```
rave-visual/
  README.md
  docs/
    mapping.md            # 조작부 ↔ MIDI ↔ TD 채널 ↔ 화면 반응 표
    td_build_guide.md     # 사람이 TD에서 따라 할 단계별 가이드
    checklist.md          # 주말 체크리스트 (8장 내용 기반)
  tools/
    flx4_sim.py           # 가상 FLX4 (9장 코드 그대로 저장)
    make_setlist.py       # rekordbox XML → setlist.json (P1)
  td/scripts/
    jog_callbacks.py      # MIDI In DAT 콜백 본문 (조그 누적)
    show_ext.py           # 쇼 컨트롤러 Extension (ShowExt)
    gesture.py            # 주먹→편손 토글 판정
    keyboard_callbacks.py # 운영자 키 입력 → ShowExt 호출
    serial_callbacks.py   # 아두이노 시리얼 파싱 (P1)
  arduino/jump_sensor/
    jump_sensor.ino       # 점프 감지 펌웨어 (P1)
  presets/
    setlist.json          # 예시 곡 세트 2~3곡
  assets/
    center/  side/        # 빈 폴더 + README
```

### P0 — 월요일까지 (이 순서대로)

| # | 작업 | 결과물 | 완료 기준 |
|---|---|---|---|
| 1 | 저장소 구조 생성, README 작성 | 위 폴더/파일 | 폴더 생성, README에 실행 방법 요약 |
| 2 | 가상 컨트롤러 저장·점검 | `tools/flx4_sim.py` | 9장 코드 저장. `python tools/flx4_sim.py` 실행 방법과 loopMIDI 준비 방법을 README에 기록. 포트를 못 찾으면 사용 가능한 포트 목록을 출력하고 종료하는지 확인 |
| 3 | 매핑표 문서 | `docs/mapping.md` | 7.2절 MIDI 규격 + 7.3절 제어 버스 + 6장 화면 반응을 한 표로. "TD 채널 이름" 열은 비워두고 사용자가 채우게 한다 |
| 4 | TD 제어 버스 구축 가이드 | `docs/td_build_guide.md` 1부 | MIDI Device Mapper에 loopMIDI 등록 → MIDI In CHOP → Select → Rename → Math → Lag → Null `ctrl`까지 오퍼레이터 이름·설정값을 단계별로. 채널 이름 확인 방법(시뮬레이터로 조작부 하나씩 움직이기) 포함 |
| 5 | 조그 처리 | `td/scripts/jog_callbacks.py` + 가이드 2부 | MIDI In DAT 콜백 본문. CC33(옆면)·CC34(윗면) 상대값(64 기준)을 메시지마다 Constant CHOP `jog_acc`에 누적. 같은 값 반복 수신에도 누적됨. 처음엔 print로 index 확인하게 함 |
| 6 | 파생 채널 계산 가이드 | 가이드 3부 | 7.3절 파생 채널(`d1_gain`, `deck_mix`, `bass_w`, `pulse`)을 Math/Expression CHOP 또는 Script CHOP으로 만드는 방법. 크로스페이더 곡선 계산은 한 곳에만 둔다 |
| 7 | 중앙 화면 이펙트 연결 가이드 | 가이드 4부 | 6장 VA-01~VA-09를 기존 점 구름(또는 Instancing 기반 간단한 소스)에 연결하는 방법. 이펙트는 `ctrl` 채널만 참조 |
| 8 | 실루엣 이펙트 가이드 | 가이드 5부 | MediaPipe 플러그인에서 세그멘테이션만 켜기 → Threshold → Feedback 잔상 루프(Level opacity, Transform scale) → Edge 외곽선 → 크로스페이더 색 적용 → `fx_level`을 잔상 길이에 연결 |
| 9 | 쇼 컨트롤러 최소 버전 | `td/scripts/show_ext.py`, `keyboard_callbacks.py` | `Toggle()`, `SetState()`, `Panic()`, `Flash()`와 4장 상태 기계(카운트다운 3초 포함). F1·P 키 연결. 곡 세트 기능은 스텁만 |
| 10 | 제스처 판정 | `td/scripts/gesture.py` + 가이드 6부 | 7.5절 규칙대로 `gesture_toggle` 펄스 생성 후 `ShowExt.Toggle()` 호출. MediaPipe 출력 채널 이름은 TODO로 남기고 확인 방법 안내 |
| 11 | 예시 프리셋 | `presets/setlist.json` | 7.7절 형식, 곡 2~3개 |
| 12 | 주말 체크리스트 | `docs/checklist.md` | 8장 내용을 체크박스로 |

### P1 — 시간 남으면 / 팀원 작업 지원

| # | 작업 | 결과물 |
|---|---|---|
| 13 | 곡 세트 전환 완성 (`LoadSetlist`, `AdvanceSong`, `OnAirSong`, LOAD 버튼 연동) | `show_ext.py` |
| 14 | 프리셋 변환기 | `tools/make_setlist.py` (7.8절) |
| 15 | 아두이노 점프 펌웨어 | `arduino/jump_sensor/jump_sensor.ino` (7.4절 프로토콜) |
| 16 | 시리얼 파싱 | `td/scripts/serial_callbacks.py` |
| 17 | 아두이노 없이 점프 테스트할 시리얼 에뮬레이터 | `tools/jump_sim.py` (가상 COM 포트 필요 여부 안내) |
| 18 | 운영자 화면 가이드 | 가이드 7부 (OP-01) |

---

## 5. 시스템 구성

| 모듈 | 역할 | 구현 |
|---|---|---|
| M1 컨트롤러 입력 | FLX4 MIDI 수신, 정규화 | TD MIDI In CHOP/DAT |
| M2 오디오 입력 | 마스터 음량·저역 레벨 | rekordbox PC MASTER OUT → 가상 오디오 장치(VB-CABLE 등) → TD Audio Device In CHOP. 기기 없는 동안은 Audio File In CHOP으로 곡 재생 |
| M3 비전 입력 | 실루엣 마스크, 손 제스처 | 웹캠 + MediaPipe TD 플러그인 |
| M4 점프 입력 | 압력센서 착지 감지 | FSR406 + 아두이노 우노 → 시리얼 |
| M5 쇼 컨트롤러 | 상태 전환, 곡 세트, 비상 정지 | TD Python Extension |
| M6 중앙 화면(A) | 조작·실루엣 시각화 | TD TOP 네트워크 |
| M7 좌우 화면(B) | 카운트다운, 점프 오브젝트 | TD TOP 네트워크 |
| M8 출력·운영 | 1:2:1 합성, 출력, 운영자 모니터 | TD Window COMP |
| M9 가상 컨트롤러 | 기기 없이 FLX4와 같은 MIDI 송신 | Python + mido + loopMIDI |
| M10 프리셋 변환기 | rekordbox XML → 곡 세트 JSON | Python |

흐름: M1·M2·M3·M4 → 제어 버스 `ctrl` → M5 → M6·M7 → M8

---

## 6. 기능 명세

우선순위: 필수 / 권장 / 선택

### 컨트롤러 입력

| ID | 기능 | 설명 | 우선순위 |
|---|---|---|---|
| IN-01 | MIDI 수신 | FLX4 또는 가상 컨트롤러의 CC·노트 수신. 입력 장치를 바꿔도 하위 네트워크는 수정하지 않는다 | 필수 |
| IN-02 | 연속값 정규화 | 페이더·노브는 MSB만 써서 0~1, 필터는 -1~1(가운데 0) | 필수 |
| IN-03 | 평활화 | 연속값에 Lag 0.05~0.1초 | 필수 |
| IN-04 | 조그 누적 | 상대값(64 기준)을 메시지마다 누적해 각도·각속도 생성. 같은 값 반복에도 누적 | 필수 |
| IN-05 | 버튼 펄스 | 노트 수신 시 1프레임 펄스와 눌림 상태(0/1). velocity 0 = 뗌 | 필수 |
| IN-06 | 패드 모드 판별 | 노트 범위로 모드와 패드 번호(1~8) 판별 | 필수 |
| IN-07 | 연결 감시 | 장치 끊기면 마지막 값 유지, 운영자 경고 | 권장 |

### 오디오

| ID | 기능 | 설명 | 우선순위 |
|---|---|---|---|
| AU-01 | 음량 | 마스터 RMS 0~1 정규화. 기준값은 프리셋 `audio_norm` | 필수 |
| AU-02 | 저역 | 150Hz 이하 레벨 0~1 | 필수 |
| AU-03 | 스피커 누수 방지 | PC MASTER OUT을 가상 오디오 장치로 보냄 | 필수(실기기 단계) |
| AU-04 | 박자 신호 | Ableton Link 또는 온셋 검출. Link 사용 가능 여부 미확인 | 선택 |

### 중앙 화면(A)

| ID | 기능 | 설명 | 우선순위 |
|---|---|---|---|
| VA-01 | 덱 색 비율 | `deck_mix`에 따라 덱1 색/덱2 색 비율 | 필수 |
| VA-02 | 베이스 스왑 | 저음이 살아 있는 덱의 요소만 저역에 맞춰 크기 변화(`d{n}_pulse`) | 필수 |
| VA-03 | EQ | LOW = 요소 크기, MID = 요소 개수, HIGH = 밝기 | 필수 |
| VA-04 | 채널 페이더 | 덱 레이어 투명도 | 필수 |
| VA-05 | 필터 | 음수 = 블러 강도, 양수 = 외곽선 비중 | 필수 |
| VA-06 | 조그 | 각도만큼 요소 회전. 윗면(스크래치) 입력 시 RGB 분리 | 필수 |
| VA-07 | Beat FX | `fx_level` = 잔상 길이, `fx_on` = 잔상 on/off | 필수 |
| VA-08 | 패드 | 핫큐 = 패드별 색 플래시(0.15초), 패드FX = 스트로브, 비트점프 = 화면 오프셋 점프, 샘플러 = 스탬프 | 핫큐 필수, 나머지 권장 |
| VA-09 | 곡 전환 완료 | 크로스페이더가 한쪽 끝에 1초 이상 있으면 기본색을 그 덱 곡 색으로 | 필수 |
| VA-10 | 실루엣 | 마스크에 잔상·외곽선 적용, 색은 VA-01을 따름 | 필수 |

### 제스처·쇼 상태

| ID | 기능 | 설명 | 우선순위 |
|---|---|---|---|
| GS-01 | 토글 제스처 | 주먹 0.5초 이상 유지 후 0.7초 안에 손 펴면 토글 1회 | 필수 |
| GS-02 | 오인식 방지 | 토글 후 3초 무시, 점수 0.6 미만 무시 | 필수 |
| GS-03 | 대체 입력 | 운영자 F1. DJ용 하드웨어 대체 입력은 rekordbox 기능과 충돌 없는 조작으로 리허설에서 결정 | 필수 |
| SH-01 | 상태 전이 | 아래 상태 기계 | 필수 |
| SH-02 | 카운트다운 | 3·2·1 1초 간격 표시 후 활성화 | 필수 |
| SH-03 | 비상 정지 | P 키: 좌우 끄고 중앙 기본 상태 | 필수 |

상태 기계:

| 현재 | 이벤트 | 다음 | 동작 |
|---|---|---|---|
| CENTER_ONLY | 토글 | COUNTDOWN | 3·2·1 시작 |
| COUNTDOWN | 3초 경과 | SIDE_ACTIVE | `jump_count` 0, 좌우 켬 |
| COUNTDOWN | 토글 | CENTER_ONLY | 취소 |
| SIDE_ACTIVE | 토글 | CENTER_ONLY | 좌우 0.5초 페이드아웃 |
| 모든 상태 | 비상 정지 | CENTER_ONLY | 모든 효과 초기화 |

### 점프·좌우 화면(B)

| ID | 기능 | 설명 | 우선순위 |
|---|---|---|---|
| JP-01 | 착지 감지 | 상한 임계값 초과 시 착지, 하한 아래로 내려가야 재무장 | 필수 |
| JP-02 | 중복 방지 | 센서별 불응기 250ms, 80ms 안 다중 센서 반응은 1회로 합침 | 필수 |
| JP-03 | 원격 설정 | 임계값·불응기를 TD에서 시리얼 명령으로 변경 | 권장 |
| JP-04 | 생존 확인 | 1초 heartbeat, 3초 없으면 끊김 | 필수 |
| VB-01 | 활성 조건 | SIDE_ACTIVE일 때만 점프 반영 | 필수 |
| VB-02 | 오브젝트 반응 | 곡 세트 `side_rule`(count/scale/burst)에 따라 반응 | 필수 |
| VB-03 | 점프 열기 | 최근 2초 점프 빈도를 밝기·배경 움직임에 반영 | 권장 |
| VB-04 | 센서 장애 대체 | 시리얼 끊기면 저역 레벨로 자동 반응 | 권장 |

### 곡 세트·운영

| ID | 기능 | 설명 | 우선순위 |
|---|---|---|---|
| ST-01 | 프리셋 로드 | 시작 시 JSON 로드, 오류 시 기본 세트 | 필수 |
| ST-02 | 곡 포인터 | 덱별 현재 곡 포인터. LOAD 버튼 시 다음 곡 | 필수 |
| ST-03 | 수동 보정 | ←/→ 덱1, Shift+←/→ 덱2 | 필수 |
| ST-04 | 프리셋 변환 | rekordbox XML → JSON 뼈대 | 권장 |
| OP-01 | 운영자 화면 | 상태, 덱별 곡, 연결 상태, FPS, `ctrl` 값 표시 | 필수 |
| OP-02 | 가상 컨트롤러 | FLX4와 같은 MIDI를 loopMIDI로 송신 | 필수(개발용) |

### 비기능 요구사항

- 출력 30fps 이상 유지, 목표 60fps
- MIDI → 화면 TD 내부 지연 2프레임 이하, 점프 → 화면 100ms 이하, 손을 편 시점 → 카운트다운 시작 0.3초 이하
- 60분 연속 실행 시 멈춤 없음. 입력 하나가 끊겨도 나머지 화면은 계속 출력
- 캔버스 폭 W는 설정값, 좌·중·우 폭은 W/4, W/2, W/4. 기본 1920×1080 (무료 TD 테스트는 1280×720)

### 예외 처리

| 상황 | 처리 |
|---|---|
| MIDI 끊김 | 마지막 값 유지, 경고, 재등록 시 복구 |
| 오디오 0이 5초 지속 | 경고, MIDI 값만으로 동작 |
| 웹캠 끊김 | 실루엣 끔, 제스처는 키보드만 |
| 시리얼 끊김 | VB-04로 전환, 2초마다 재연결 |
| 프리셋 오류 | 기본 세트, 오류 항목 표시 |
| FPS 25 미만 지속 | 경고, 세그멘테이션 해상도 낮춤 옵션 |

---

## 7. API 명세

웹 API는 없다. 여기서 API는 모듈 사이 인터페이스다.

### 7.1 공통 규칙

- 채널 이름은 소문자+밑줄, 덱 구분은 `d1_`, `d2_`
- 연속값 0~1, 양방향 -1~1, 각도는 도, 시간은 초
- 펄스 채널은 이벤트 프레임에만 1
- MIDI 채널 번호는 1부터 센다

### 7.2 MIDI 입력 규격 (FLX4 → M1)

Mixxx의 DDJ-FLX4 매핑과 대조한 값. 중간 보고서 테스트에서 CC 15(`b0 0f`)가 TD에 `ch1ctrl16`으로 표시됐으므로 **TD 채널 이름은 CC 번호 +1로 예상**한다. 노트의 TD 표기는 미확인.

| 조작부 | 종류 | ch | 번호 | 값 |
|---|---|---|---|---|
| 템포 페이더 | CC | 1/2 | 0 (LSB 32) | 0~127 |
| TRIM | CC | 1/2 | 4 (LSB 36) | 0~127 |
| EQ HI / MID / LOW | CC | 1/2 | 7 / 11 / 15 (LSB +32) | 0~127, 가운데 64 |
| 채널 페이더 | CC | 1/2 | 19 (LSB 51) | 0~127 |
| 조그 옆면 | CC | 1/2 | 33 | 64 기준 상대값 |
| 조그 윗면(바이닐 모드) | CC | 1/2 | 34 | 64 기준 상대값 |
| 조그 터치 | Note | 1/2 | 54 | 127 / 0 |
| PLAY / CUE / SYNC | Note | 1/2 | 11 / 12 / 88 | 127 / 0 |
| 필터 CH1 / CH2 | CC | 7 | 23 / 24 | 0~127, 가운데 64 |
| 크로스페이더 | CC | 7 | 31 (LSB 63) | 0 = 덱1 쪽 |
| LOAD 덱1 / 덱2 | Note | 7 | 70 / 71 | 127 / 0 |
| Beat FX 레벨 | CC | 5 | 2 (LSB 34) | 0~127 |
| Beat FX ON | Note | 5 또는 6 | 71 | 127 / 0 |
| Beat FX SELECT | Note | 5 | 99 | 127 / 0 |
| 패드 덱1 / 덱2 | Note | 8 / 10 | 핫큐 0~7, 패드FX 16~23, 비트점프 32~39, 샘플러 48~55 | 127 / 0 |

주의:
- 덱2 패드는 ch9가 아니라 ch10
- note off를 보내지 않는다. 뗌 = note on velocity 0
- 패드는 모드마다 노트 번호가 다르다. 핫큐 범위만 들으면 모드 바꾸는 순간 반응이 끊긴다
- Shift 조작은 별도 채널·노트로 들어온다(예: 덱1 패드 Shift = ch9). 본 시스템은 사용하지 않는다
- 패드·버튼은 rekordbox 기능도 동시에 실행된다

### 7.3 제어 버스 `ctrl`

입력 정규화 채널:

| 채널 | 범위 | 출처 | 평활화 |
|---|---|---|---|
| `xfader` | 0~1 | ch7 CC31 | Lag 0.05 |
| `d{n}_eq_low` / `_mid` / `_hi` | 0~1 (0.5 기본) | CC15/11/7 | Lag 0.08 |
| `d{n}_fader` | 0~1 | CC19 | Lag 0.05 |
| `d{n}_filter` | -1~1 | ch7 CC23/24 | Lag 0.08 |
| `fx_level` | 0~1 | ch5 CC2 | Lag 0.08 |
| `fx_on` | 0/1 토글 상태 | FX ON 노트 | 없음 |
| `d{n}_jog_angle` | 도, 누적 | CC33 | 없음 |
| `d{n}_jog_vel` | 도/초 | angle 기울기 | Lag 0.15 |
| `d{n}_scratch` | 0~1 | CC34 활동량 | Lag 0.1 |
| `d{n}_touch` | 0/1 | 노트 54 | 없음 |
| `d{n}_pad_pulse` | 펄스 | 패드 노트 | 없음 |
| `d{n}_pad_index` | 1~8 | 패드 노트 | 없음 |
| `d{n}_pad_mode` | 0 핫큐 1 패드FX 2 비트점프 3 샘플러 | 노트 범위 | 없음 |
| `d{n}_load_pulse` | 펄스 | LOAD 노트 | 없음 |
| `audio_level` | 0~1 | RMS | Lag 상승 0.03 / 하강 0.2 |
| `audio_low` | 0~1 | 저역 | Lag 상승 0.02 / 하강 0.15 |

조그: `d{n}_jog_angle += (value - 64) * 2.0` (계수 2.0은 기본값, 리허설에서 조정)

파생 채널:

| 채널 | 계산 | 용도 |
|---|---|---|
| `d1_gain` | `d1_fader * (1 - xfader)` | 덱1 출력 비중 근사 |
| `d2_gain` | `d2_fader * xfader` | 덱2 출력 비중 근사 |
| `deck_mix` | `d2_gain / (d1_gain + d2_gain + 0.001)` | 덱2 색 비율 (VA-01) |
| `d{n}_bass_w` | `d{n}_eq_low * d{n}_gain`, 두 값 합이 1이 되게 정규화 | 덱별 저역 가중치 (VA-02) |
| `d{n}_pulse` | `audio_low * d{n}_bass_w` | 덱별 요소 크기 변화량 |

크로스페이더 곡선은 rekordbox 설정에 따라 다르므로 `gain` 계산은 근사이며 한 곳에서만 계산한다.

### 7.4 시리얼 프로토콜 (아두이노 ↔ TD)

115200bps, 8N1, ASCII, `\n` 종료, 쉼표 구분.

아두이노 → TD:

| 메시지 | 형식 | 예 | 시점 |
|---|---|---|---|
| 부팅 | `R,<버전>,<센서수>` | `R,0.1,4` | 시작 1회 |
| 점프 | `J,<센서비트마스크>,<최대ADC>` | `J,5,812` | 착지 판정 시 (80ms 묶음 후) |
| 생존 | `H,<가동ms>` | `H,120034` | 1초마다 |
| 원시값 | `S,<v0>,<v1>,...` | `S,12,640,8,3` | 디버그 모드 50Hz |
| 응답 | `OK,<명령>` / `ERR,<코드>` | `OK,T` | 명령 수신 시 |

비트마스크: 센서0 = 1, 센서1 = 2, 센서2 = 4 …

TD → 아두이노:

| 명령 | 형식 | 범위 | 설명 |
|---|---|---|---|
| 상한 임계값 | `T,<값>` | 0~1023 | 착지 판정 |
| 하한 임계값 | `L,<값>` | 0~1023 | 재무장, 상한보다 작아야 함 |
| 불응기 | `D,<ms>` | 50~1000 | 센서별 |
| 디버그 | `M,<0or1>` | | 원시값 스트림 |
| 기준값 측정 | `C` | | 무부하 평균 저장 |

오류 코드: 1 알 수 없는 명령, 2 범위 초과, 3 하한 ≥ 상한

TD 채널: `jump_pulse`, `jump_count`(SIDE_ACTIVE 진입 시 0), `jump_rate`(최근 2초 점프/초), `serial_ok`

우노 아날로그 입력은 6개(A0~A5). 그 이상은 멀티플렉서 필요.

### 7.5 제스처 (M3 → M5)

입력: MediaPipe 손 인식의 제스처 라벨(`Closed_Fist`, `Open_Palm`, 그 외)과 점수 0~1.

규칙: 점수 0.6 이상 `Closed_Fist`가 0.5초 이상 이어진 뒤 0.7초 안에 점수 0.6 이상 `Open_Palm` → `gesture_toggle` 펄스 1회. 이후 3초 판정 정지. 손이 둘 이상이면 가장 큰 손 하나만.

출력: `gesture_toggle`(펄스), `gesture_hold`(0~1 주먹 유지 진행률, 운영자 화면 표시), `hand_found`(0/1)

### 7.6 쇼 컨트롤러 API (`/project1/show`의 Extension `ShowExt`)

호출: `op('/project1/show').<메서드>`

| 메서드 | 인자 | 반환 | 동작 |
|---|---|---|---|
| `Toggle()` | 없음 | 새 상태 str | 상태 기계 토글 |
| `SetState(state)` | `'CENTER_ONLY'`/`'COUNTDOWN'`/`'SIDE_ACTIVE'` | 없음 | 강제 설정(테스트용) |
| `Panic()` | 없음 | 없음 | 비상 정지 |
| `LoadSetlist(path)` | JSON 경로 | 곡 수 int | 실패 시 기본 세트 |
| `AdvanceSong(deck, step=1)` | 1/2, 정수 | 곡 dict | 덱 포인터 이동 |
| `GetSong(deck)` | 1/2 | 곡 dict | 덱 현재 곡 |
| `OnAirSong()` | 없음 | 곡 dict | `deck_mix` 기준 우세 덱의 곡 |
| `Flash(color, duration=0.15)` | `'#rrggbb'`, 초 | 없음 | 중앙 플래시 |
| `SendSerial(cmd)` | str | 없음 | 7.4 명령 전송 |

읽기 전용 속성: `State`, `StateTime`(경과 초), `SongIndex`([i1, i2])

운영자 키: F1 = `Toggle()`, P = `Panic()`, ←/→ = `AdvanceSong(1, ∓1)`, Shift+←/→ = `AdvanceSong(2, ∓1)`, J = `SendSerial('C')`. `d{n}_load_pulse` 수신 시 `AdvanceSong(n, 1)` 자동 호출.

### 7.7 곡 세트 프리셋 (`presets/setlist.json`)

```json
{
  "version": 1,
  "default": {
    "color": "#ffffff",
    "center_source": "dots",
    "side_set": "default",
    "side_rule": { "type": "burst" }
  },
  "audio_norm": { "level_max": 0.35, "low_max": 0.5 },
  "setlist": [
    {
      "id": "t01",
      "title": "곡 제목",
      "artist": "아티스트",
      "bpm": 128.0,
      "key": "8A",
      "color": "#ff3fa4",
      "center_source": "plasma_01",
      "side_set": "cute_chars",
      "side_rule": { "type": "count", "max": 40 }
    }
  ]
}
```

| 필드 | 필수 | 설명 |
|---|---|---|
| `id` | 예 | 셋리스트 안에서 고유 |
| `title`, `artist` | 예 | 운영자 화면 표시 |
| `bpm`, `key` | 아니오 | rekordbox 분석값 |
| `color` | 예 | 그 곡이 올라간 덱의 색 |
| `center_source` | 예 | `assets/center/<이름>/` |
| `side_set` | 예 | `assets/side/<이름>/` 안 PNG |
| `side_rule.type` | 예 | `count` 추가 / `scale` 커짐 / `burst` 터지고 사라짐 |
| `side_rule.max` | 아니오 | count 최대 개수, 기본 30 |

### 7.8 프리셋 변환기 (`tools/make_setlist.py`)

- 실행: `python tools/make_setlist.py rekordbox.xml "플레이리스트 이름" -o presets/setlist.json`
- 플레이리스트 순서대로 `TRACK`의 `Name`, `Artist`, `AverageBpm`, `Tonality` → `title`, `artist`, `bpm`, `key`
- `color`, `center_source`, `side_set`은 기본값
- 기존 JSON이 있으면 같은 `id` 곡의 수동 입력 필드는 덮어쓰지 않는다
- rekordbox XML 구조(PLAYLISTS 노드가 COLLECTION의 TrackID를 참조하는 방식)는 실제 내보낸 파일로 확인 후 구현. 샘플 XML이 없으면 사용자에게 요청한다

### 7.9 가상 컨트롤러 (`tools/flx4_sim.py`)

- 이름에 `loopMIDI`가 들어간 출력 포트 자동 선택
- 7.2 규격과 같은 메시지 송신. 연속값은 MSB + LSB(값 0) 함께
- 조그: 속도 슬라이더 v에 대해 20ms마다 `64 + v`
- 버튼: 누를 때 velocity 127, 뗄 때 velocity 0 (note on)

---

## 8. 주말 일정과 사람이 직접 할 일

Claude가 TD 화면을 조작할 수 없으므로, 아래는 사용자가 직접 한다. 가이드 문서는 이 순서에 맞춰 쓴다.

**금요일 밤**
- [ ] loopMIDI 설치, 포트 1개 생성
- [ ] `pip install mido python-rtmidi`, `python tools/flx4_sim.py` 실행
- [ ] TD MIDI Device Mapper에 loopMIDI 등록, MIDI In CHOP 생성
- [ ] 시뮬레이터로 조작부를 하나씩 움직여 `docs/mapping.md`의 TD 채널 이름 열 채우기 (특히 노트 표기, CC +1 여부)
- [ ] Select → Rename → Math → Lag → Null `ctrl` 구성

**토요일**
- [ ] 조그 MIDI In DAT 콜백 연결, print로 index 확인 후 수정
- [ ] 파생 채널(`deck_mix`, `bass_w`, `pulse`) 구성
- [ ] 중앙 화면 소스 하나에 필수 매핑(VA-01~07, 09, 핫큐 플래시) 전부 연결
- [ ] 음악은 Audio File In CHOP으로 셋리스트 곡 재생해서 반응 확인

**일요일**
- [ ] MediaPipe 플러그인: 세그멘테이션만 켜고 실루엣 잔상·외곽선 구성, `fx_level`·덱 색 연결
- [ ] (가능하면) 제스처 → `ShowExt.Toggle()` 연결, 안 되면 F1로 시연
- [ ] 화면 녹화로 시연 영상 1~2분 (곡 전환 + 베이스 스왑 + 조그 + 패드 + 실루엣)

**월요일 오전**
- [ ] `docs/mapping.md` 최종 정리
- [ ] 기기 받으면 확인할 항목 정리: TD 노트 채널 표기, 조그 계수, 크로스페이더 곡선, (팀) 센서 임계값

---

## 9. 참고 코드: `tools/flx4_sim.py`

이미 작성됨. 그대로 저장한다. 송신 바이트는 확인함(EQ LOW = `B0 0F`, 덱2 패드 = `99 xx`, 크로스페이더 = `B6 1F`). GUI 실행은 아직 미확인.

```python
# FLX4 가상 컨트롤러: 실제 DDJ-FLX4와 같은 MIDI 메시지를 loopMIDI 포트로 보낸다.
# 필요: loopMIDI(포트 하나 생성), pip install mido python-rtmidi
import tkinter as tk
import mido

PORT_KEYWORD = "loopMIDI"   # loopMIDI에서 만든 포트 이름 일부

# MIDI 채널은 1부터 센 번호 (mido에는 -1 해서 넘김)
D_CH = {1: 1, 2: 2}         # 덱 채널
MIX_CH = 7                  # 크로스페이더, 필터
FX_CH = 5                   # Beat FX
PAD_CH = {1: 8, 2: 10}      # 패드 (덱2는 9가 아니라 10)

DECK_CC = {"TRIM": 0x04, "EQ HI": 0x07, "EQ MID": 0x0B, "EQ LOW": 0x0F,
           "CH FADER": 0x13, "TEMPO": 0x00}
DECK_NOTE = {"PLAY": 0x0B, "CUE": 0x0C, "SYNC": 0x58}
PAD_BASE = {"HOT CUE": 0x00, "PAD FX": 0x10, "BEAT JUMP": 0x20, "SAMPLER": 0x30}
JOG_SIDE, JOG_TOP, JOG_TOUCH = 0x21, 0x22, 0x36

def open_port():
    names = mido.get_output_names()
    for n in names:
        if PORT_KEYWORD.lower() in n.lower():
            print("출력 포트:", n)
            return mido.open_output(n)
    raise SystemExit(f"'{PORT_KEYWORD}' 포트 없음. 현재 포트: {names}")

out = open_port()

def cc(ch, num, val):
    # 실제 기기처럼 MSB(num) + LSB(num+0x20) 두 개를 보낸다
    out.send(mido.Message("control_change", channel=ch - 1, control=num, value=val))
    if num < 0x20:
        out.send(mido.Message("control_change", channel=ch - 1, control=num + 0x20, value=0))

def note(ch, num, on):
    # FLX4는 note_off를 안 쓰고 velocity 0으로 뗌을 보낸다
    out.send(mido.Message("note_on", channel=ch - 1, note=num, velocity=127 if on else 0))

root = tk.Tk()
root.title("FLX4 simulator")

def slider(parent, label, ch, num, init, col, row):
    s = tk.Scale(parent, from_=127, to=0, length=140, label=label,
                 command=lambda v: cc(ch, num, int(float(v))))
    s.set(init)
    s.grid(column=col, row=row, padx=2)

def hold_button(parent, label, ch, num, col, row, width=7):
    b = tk.Button(parent, text=label, width=width)
    b.bind("<ButtonPress-1>", lambda e: note(ch, num, True))
    b.bind("<ButtonRelease-1>", lambda e: note(ch, num, False))
    b.grid(column=col, row=row, padx=1, pady=1)

# 조그: 슬라이더 값만큼 계속 돌린다 (0이면 정지). 64가 정지, 65 이상 정방향
jog_speed = {1: tk.IntVar(value=0), 2: tk.IntVar(value=0)}
jog_mode = {1: tk.StringVar(value="SIDE"), 2: tk.StringVar(value="SIDE")}

def jog_tick():
    for d in (1, 2):
        v = jog_speed[d].get()
        if v:
            num = JOG_SIDE if jog_mode[d].get() == "SIDE" else JOG_TOP
            out.send(mido.Message("control_change", channel=D_CH[d] - 1,
                                  control=num, value=max(0, min(127, 64 + v))))
    root.after(20, jog_tick)

def deck_frame(d, col):
    f = tk.LabelFrame(root, text=f"DECK {d}")
    f.grid(column=col, row=0, padx=6, pady=6, sticky="n")
    inits = {"TRIM": 64, "EQ HI": 64, "EQ MID": 64, "EQ LOW": 64, "CH FADER": 127, "TEMPO": 64}
    for i, (name, num) in enumerate(DECK_CC.items()):
        slider(f, name, D_CH[d], num, inits[name], i, 0)
    for i, (name, num) in enumerate(DECK_NOTE.items()):
        hold_button(f, name, D_CH[d], num, i, 1)

    j = tk.Frame(f); j.grid(column=0, row=2, columnspan=6, pady=4)
    tk.Label(j, text="JOG").pack(side="left")
    tk.Scale(j, from_=-20, to=20, orient="horizontal", length=200,
             variable=jog_speed[d]).pack(side="left")
    tk.Button(j, text="정지", command=lambda: jog_speed[d].set(0)).pack(side="left")
    tk.OptionMenu(j, jog_mode[d], "SIDE", "TOP").pack(side="left")
    t = tk.Button(j, text="TOUCH")
    t.bind("<ButtonPress-1>", lambda e: note(D_CH[d], JOG_TOUCH, True))
    t.bind("<ButtonRelease-1>", lambda e: note(D_CH[d], JOG_TOUCH, False))
    t.pack(side="left")

    p = tk.Frame(f); p.grid(column=0, row=3, columnspan=6)
    mode = tk.StringVar(value="HOT CUE")
    tk.OptionMenu(p, mode, *PAD_BASE.keys()).grid(column=0, row=0, rowspan=2)
    for i in range(8):
        b = tk.Button(p, text=f"PAD{i+1}", width=5)
        b.bind("<ButtonPress-1>", lambda e, i=i: note(PAD_CH[d], PAD_BASE[mode.get()] + i, True))
        b.bind("<ButtonRelease-1>", lambda e, i=i: note(PAD_CH[d], PAD_BASE[mode.get()] + i, False))
        b.grid(column=1 + i % 4, row=i // 4)

deck_frame(1, 0)

m = tk.LabelFrame(root, text="MIXER / FX")
m.grid(column=1, row=0, padx=6, pady=6, sticky="n")
slider(m, "FILTER 1", MIX_CH, 0x17, 64, 0, 0)
slider(m, "FILTER 2", MIX_CH, 0x18, 64, 1, 0)
slider(m, "FX LEVEL", FX_CH, 0x02, 0, 2, 0)
hold_button(m, "FX ON", FX_CH, 0x47, 0, 1)
hold_button(m, "FX SEL", FX_CH, 0x63, 1, 1)
xf = tk.Scale(m, from_=0, to=127, orient="horizontal", length=220, label="CROSSFADER",
              command=lambda v: cc(MIX_CH, 0x1F, int(float(v))))
xf.set(0)
xf.grid(column=0, row=2, columnspan=3)

deck_frame(2, 2)
root.after(20, jog_tick)
root.mainloop()
```

## 10. 참고 코드: 조그 콜백 초안 (`td/scripts/jog_callbacks.py`의 출발점)

TD MIDI In DAT의 callbacks DAT에 들어갈 본문 초안. 함수 시그니처는 TD 자동 생성 템플릿 것을 쓰게 하고, `message`·`index` 값 형식은 print로 확인하게 한다.

```python
def onReceiveMIDI(dat, rowIndex, message, channel, index, value, input, bytes):
    # print(message, channel, index, value)   # 처음엔 이걸로 조그 index가 33인지 34인지 확인
    JOG_IDX = (34,)                           # 확인한 값으로 수정
    if index in JOG_IDX and channel in (1, 2):
        acc = op('jog_acc')                   # Constant CHOP: name0=d1_jog, name1=d2_jog
        p = acc.par.value0 if channel == 1 else acc.par.value1
        p.val += (value - 64)
    return
```

---

## 11. 변경 이력

- v0.1 (2026-11-06): 최초 작성. 곡 정보 출처를 스포티파이 → rekordbox XML로 변경. 곡 세트 전환은 LOAD 버튼 + 운영자 키로 확정.
