# TD 구축 가이드

TouchDesigner에서 직접 따라 하는 순서. [checklist.md](checklist.md)의 금·토·일 순서와 같다.

- 이 문서의 파라미터 이름은 **TD 화면에 보이는 라벨** 기준이다. Python 이름이 필요한 곳은 따로 적었다.
- `TODO(TD에서 확인)` 표시는 확실하지 않은 부분이다. 실제 화면과 다르면 화면을 따르고, 이 문서와 [mapping.md](mapping.md)를 고친다.
- 콜백 DAT(MIDI In DAT, Execute DAT, Keyboard In DAT, Script CHOP)은 **TD가 자동으로 만든 템플릿의 `def` 줄을 그대로 두고, 함수 본문만** `td/scripts/*.py`에서 복사해 붙여 넣는다. 파일 맨 위 상수들도 같이 붙여 넣는다.
- 모든 이펙트는 `/project1/ctrl` 채널만 참조한다. 입력 장치가 바뀌어도 `ctrl` 아래는 고치지 않는다 (IN-01).
- 무료 버전 기준: 캔버스 1280×720, 중앙 화면 640×720, 웹캠 720p 이하.

## 전체 구조 (`/project1`)

```
midiin1 (MIDI In CHOP) ─┬ sel_fader → ren_fader → math_fader →           lag_fader  ─┐
                        ├ sel_eq    → ren_eq    → math_eq    → lim_eq    → lag_eq     ─┤
                        ├ sel_filter→ ren_filter→ math_filter→ lim_filter→ lag_filter ─┤
                        └ sel_fx    → ren_fx    → math_fx    →           lag_fx     ─┤
midiin_dat (MIDI In DAT) ── 콜백 → jog_acc (Constant CHOP) ──────────────────────────┤
                                 → btn     (Constant CHOP) ──────────────────────────┤
audio_file → … → lag_level / lag_low ────────────────────────────────────────────────┤
show (Base COMP, ShowExt) ── out1 ────────────────────────────────────────────────────┤
                                                                         ctrl_in (Merge)
                                                    ctrl_in → derive (Script CHOP)   │
                                         ctrl_merge (Merge: ctrl_in + derive) → ctrl (Null)
center (Base COMP)  : ctrl → 점 구름 → 후처리 → center_out
silhouette (Base COMP): MediaPipe → 실루엣 잔상·외곽선 → sil_out → center에 합성
```

---

## 1부. 제어 버스 `ctrl` (금요일)

### 1-1. loopMIDI와 시뮬레이터

1. loopMIDI 설치 후 실행, 아래 `+` 버튼으로 포트 1개 생성 (이름에 `loopMIDI`가 들어가면 된다).
2. 터미널에서 `rave-visual` 폴더로 가서 `python tools/flx4_sim.py`. 창이 뜨면 정상.
   - `'loopMIDI' 포트 없음. 현재 포트: [...]`가 나오고 끝나면 loopMIDI가 꺼져 있거나 포트가 없는 것.
3. 시뮬레이터는 TD를 켜는 동안 계속 켜 둔다.

### 1-2. MIDI Device Mapper에 loopMIDI 등록

1. 메뉴 `Dialogs > MIDI Device Mapper`.
2. 새 매핑 추가 (`Create New Mapping` 버튼). TODO(TD에서 확인): 버튼 이름.
3. `In Device` = loopMIDI 포트, `Out Device`는 비움, `Device ID` = **1**.
4. 실제 FLX4를 받으면 이 매핑의 In Device만 FLX4로 바꾼다. 아래 네트워크는 그대로 (IN-01).

### 1-3. MIDI In CHOP `midiin1`과 채널 이름 확인

1. MIDI In CHOP 생성, 이름 `midiin1`.
2. `Device ID`(또는 `ID`) = 1.
3. 받을 범위를 넓게 연다. TODO(TD에서 확인): 채널·컨트롤러·노트 범위 파라미터의 형식. 처음엔 채널 1~16, 컨트롤러 전부를 받게 한다. 조작해도 채널이 안 생기면 이 범위부터 본다.
4. 값 범위 확인: 시뮬레이터 `CH FADER`를 끝까지 올렸을 때 127이 나오면 원시값, 1이 나오면 정규화된 값이다. TODO(TD에서 확인): 정규화 옵션이 있으면 원시값(0~127)으로 둔다. 1이 나오는 상태로 갈 거면 아래 Math의 From Range를 127로 나눈 값으로 바꾼다.
5. **채널 이름 확인**: `midiin1`의 뷰어를 켜 두고(가운데 클릭이나 뷰어 토글) 시뮬레이터 조작부를 **하나씩만** 움직인다. 새로 생기거나 바뀌는 채널 이름을 [mapping.md](mapping.md) 1장의 "TD 채널 이름 (확인)" 열에 적는다.
   - 예상: CC 번호 +1 (CC15 → `ch1ctrl16`). 다르면 아래 Select의 이름을 확인한 이름으로 바꾼다.
   - LSB 채널(번호 +32)도 같이 생긴다. Select에서 뺀다.
   - 노트(PLAY, 패드 등)가 CHOP에서 어떤 이름으로 보이는지도 적어 둔다 (노트 처리는 2부의 DAT이 하므로 CHOP에서 쓰지는 않는다).

### 1-4. Select → Rename → Math → (Limit) → Lag, 4갈래

평활 시간과 범위가 달라서 4갈래로 나눈다. 각 갈래는 `midiin1`에서 출발한다.

| 갈래 | Select `Channel Names` | Rename `From` → `To` | Math `From Range` → `To Range` | Limit | Lag |
|---|---|---|---|---|---|
| fader | `ch7ctrl32 ch1ctrl20 ch2ctrl20` | → `xfader d1_fader d2_fader` | 0, 127 → 0, 1 | 없음 | 0.05, 0.05 |
| eq | `ch1ctrl16 ch1ctrl12 ch1ctrl8 ch2ctrl16 ch2ctrl12 ch2ctrl8` | → `d1_eq_low d1_eq_mid d1_eq_hi d2_eq_low d2_eq_mid d2_eq_hi` | 1, 127 → 0, 1 | Clamp 0~1 | 0.08, 0.08 |
| filter | `ch7ctrl24 ch7ctrl25` | → `d1_filter d2_filter` | 1, 127 → -1, 1 | Clamp -1~1 | 0.08, 0.08 |
| fx | `ch5ctrl3` | → `fx_level` | 0, 127 → 0, 1 | 없음 | 0.08, 0.08 |

- 오퍼레이터 이름: `sel_fader`, `ren_fader`, `math_fader`, `lag_fader` … 처럼 갈래 이름을 붙인다.
- Rename의 `From`과 `To`는 공백으로 구분하고 **같은 순서**로 적는다.
- Math는 `Range` 페이지의 `From Range`, `To Range`.
- EQ·필터를 1~127로 잡는 이유: 가운데 64가 정확히 0.5 / 0이 된다. 0이 들어오면 범위를 살짝 벗어나므로 Limit CHOP(`Type` = Clamp, `Minimum`/`Maximum`)으로 자른다. TODO(TD에서 확인): Limit 파라미터 라벨.
- Lag는 `Lag` 파라미터 두 칸(올라갈 때 / 내려갈 때)에 같은 값.
- 1-3에서 확인한 채널 이름이 예상과 다르면 Select의 이름만 고친다. Rename 이후 이름(`xfader` 등)은 고정이다.

### 1-5. Constant CHOP 2개, 오디오

**Constant CHOP** (채널 이름은 1-6의 ShowExt가 시작할 때 자동으로 채운다)

- `jog_acc`: 6채널 (`d1_jog_angle d2_jog_angle d1_jog_vel d2_jog_vel d1_scratch d2_scratch`)
- `btn`: 14채널 (`d1_touch d2_touch fx_on d1_pad_pulse …`, 전체 목록은 [tdutil.py](../td/scripts/tdutil.py)의 `CONST_CHANNELS`)
- TODO(TD에서 확인): Constant CHOP 칸 수를 늘리는 방법. 최신 버전은 `+` 버튼으로 칸을 추가해야 할 수 있다. 칸이 모자라면 Textport에 `[tdutil] 칸 부족`이 찍힌다.

**오디오** (기기 없는 동안은 파일 재생, M2)

1. Audio File In CHOP `audio_file`: 셋리스트 곡 하나. 소리를 들으려면 Audio Device Out CHOP을 옆에 연결.
2. 음량: `audio_file` → Math CHOP `audio_mono`(`OP` 페이지 `Combine Channels` = Average) → Analyze CHOP `an_level`(`Function` = RMS Power) → Math `math_level`(From 0, `level_max` → To 0, 1. `level_max`는 프리셋 `audio_norm.level_max`, 기본 0.35) → Limit(Clamp 0~1) → Rename(`*` → `audio_level`) → Lag `lag_level`(0.03, 0.2).
3. 저역: `audio_mono` → Audio Filter CHOP `audio_lp`(`Filter` = Low Pass, `Cutoff Frequency` = 150) → Analyze(RMS Power) → Math(From 0, `low_max`(기본 0.5) → To 0, 1) → Limit → Rename(`*` → `audio_low`) → Lag `lag_low`(0.02, 0.15).
4. 음악을 틀고 `audio_level`, `audio_low`가 0~1 사이에서 움직이는지 본다. 너무 작거나 1에 붙어 있으면 `level_max`, `low_max`를 조정하고 값을 프리셋에 적는다.

### 1-6. 쇼 컴포넌트 `show` 뼈대

ShowExt가 Constant CHOP 채널 이름을 채우고 매 프레임 상태를 계산하므로 여기서 먼저 만든다.

1. `/project1`에 Base COMP `show` 생성. 안으로 들어가서:
2. Text DAT 3개: `tdutil`, `show_ext`, `gesture`. 각각 [tdutil.py](../td/scripts/tdutil.py), [show_ext.py](../td/scripts/show_ext.py), [gesture.py](../td/scripts/gesture.py) 내용.
   - 저장소 파일과 연결하려면 Text DAT의 `File`에 경로를 넣고 파일 동기화 옵션을 켠다. TODO(TD에서 확인): 동기화 옵션 이름(`Sync to File` 등). 안 되면 그냥 붙여 넣는다.
3. Constant CHOP `show_out`(19칸), `gesture_out`(3칸). Merge CHOP `show_merge`에 둘을 연결 → Out CHOP `out1`.
4. Execute DAT `frame_exec`: `Frame Start` 켬. 자동 생성된 callbacks DAT의 `onFrameStart` 본문에 [frame_callbacks.py](../td/scripts/frame_callbacks.py) 본문을 붙여 넣는다. 파일 위쪽 `import math`와 상수, `_smooth`, `_jog_rates` 함수도 같은 DAT에 붙여 넣는다. **처음엔 `USE_GESTURE = False`**.
5. Keyboard In DAT `keyboard1`: callbacks DAT의 `onKey` 본문에 [keyboard_callbacks.py](../td/scripts/keyboard_callbacks.py) 본문과 상수를 붙여 넣는다.
6. `show` COMP 밖으로 나와서 `show` 파라미터 `Extensions` 페이지:
   - `Extension Object 0` = `op('./show_ext').module.ShowExt(me)`
   - `Promote Extension 0` 켬
   - `Re-Init Extensions` 누름
7. 확인 (Textport: `Alt+T` 또는 `Dialogs > Textport`):
   - `op('/project1/show').State` → `'CENTER_ONLY'`
   - `jog_acc`, `btn`, `show_out`, `gesture_out`의 채널 이름이 채워졌는지. 안 채워졌으면 그 CHOP을 만든 뒤 `Re-Init Extensions`를 다시 누른다.
   - TD 창을 클릭해 포커스를 준 뒤 F1 → Textport에 `CENTER_ONLY -> COUNTDOWN`, 3초 뒤 `COUNTDOWN -> SIDE_ACTIVE`. P → `PANIC`.
   - 처음엔 키를 누를 때마다 `KEY 'f1' …` 형식으로 찍힌다. 찍힌 이름이 `KEY_TOGGLE` 등 상수와 다르면 상수를 고친다. 확인 후 `DEBUG_PRINT = False`. TODO(TD에서 확인): F1이 TD 도움말과 겹치면 다른 키로 바꾸고 mapping.md에 적는다.

ShowExt 메서드: `Toggle()`, `SetState(state)`, `Panic()`, `Flash(color, duration=0.15)`, `Update()`(매 프레임). `LoadSetlist`, `AdvanceSong`, `GetSong`, `OnAirSong`, `SendSerial`은 P1까지 스텁(임시 곡 2개로만 동작).

### 1-7. 합치기 → `ctrl`

1. Merge CHOP `ctrl_in`: `lag_fader`, `lag_eq`, `lag_filter`, `lag_fx`, `jog_acc`, `btn`, `lag_level`, `lag_low`, `show`(COMP 출력) 연결.
2. 3부의 `derive`를 만든 뒤 Merge CHOP `ctrl_merge`(`ctrl_in` + `derive`) → Null CHOP **`ctrl`**. 3부 전까지는 `ctrl_in` → `ctrl`로 바로 연결해도 된다.
3. 확인: `ctrl` 뷰어에서 시뮬레이터 조작부를 움직이면 해당 채널이 0~1(필터는 -1~1)로 부드럽게 움직이는지. EQ·필터를 가운데(64)에 두면 0.5 / 0인지.
4. Merge에서 길이가 다르다는 경고가 나오면 TODO(TD에서 확인): Merge의 정렬 옵션 또는 오디오 갈래 끝에 단일 샘플로 만드는 오퍼레이터 추가.

---

## 2부. 조그 처리 (토요일)

MIDI In CHOP은 같은 값이 연속으로 오면 변화가 없어서 조그 상대값을 누적할 수 없다. 그래서 MIDI In DAT 콜백에서 메시지마다 누적한다 (IN-04). 노트(터치, FX ON, 패드, LOAD)도 펄스·토글 처리가 필요해서 같은 콜백에서 처리한다.

1. `/project1`에 MIDI In DAT `midiin_dat`, 장치는 1-2의 Device ID 1. TODO(TD에서 확인): MIDI In DAT의 장치 지정 파라미터.
2. MIDI In DAT이 쌓는 표가 계속 커지지 않게 최대 줄 수를 작게(예: 20). TODO(TD에서 확인): 파라미터 이름.
3. 자동 생성된 callbacks DAT의 `onReceiveMIDI` 본문에 [jog_callbacks.py](../td/scripts/jog_callbacks.py) 내용을 붙여 넣는다. 상수, 본문, 맨 아래 `_pulse` 함수까지. `def onReceiveMIDI(...)` 줄은 템플릿 것을 그대로 둔다.
4. **index 확인** (`DEBUG_PRINT = True` 상태에서 Textport를 연다):
   - 시뮬레이터 덱1 JOG 슬라이더를 조금 오른쪽으로 → `MIDI 'Control Change' 1 33 66` 비슷하게 계속 찍힌다.
   - index가 **33**이면 그대로, **34**면 `CC_OFFSET = 1`.
   - channel이 덱1에서 **0**으로 찍히면 `CHANNEL_OFFSET = 1`.
   - message 문자열에 `control` / `note`가 안 들어 있으면 `is_cc`, `is_note` 줄을 찍힌 문자열에 맞게 고친다.
   - JOG 모드를 TOP으로 바꿔 CC34도 확인. 패드(덱1, 덱2), FX ON, LOAD도 하나씩 눌러 index를 [mapping.md](mapping.md) 2장에 적는다. 노트 index가 +1이면 `NOTE_OFFSET = 1`.
5. 동작 확인:
   - JOG 슬라이더를 고정해 두면(같은 값 반복) `jog_acc`의 `d1_jog_angle`이 계속 늘어난다. 정지 버튼 → 멈춘다.
   - `d1_jog_vel`이 도/초로 나오고, TOP 모드에서 `d1_scratch`가 0~1로 움직인다. 너무 쉽게 1이 되면 [frame_callbacks.py](../td/scripts/frame_callbacks.py)의 `SCRATCH_FULL`을 키운다.
   - 핫큐 패드 → `btn`의 `d1_pad_pulse`가 한 프레임 1, `d1_pad_index`가 패드 번호. 패드 모드를 바꿔도 반응이 이어지는지 (IN-06).
   - FX ON → `fx_on`이 0/1 토글. LOAD → Textport에 `덱1 -> 임시 곡 B`.
6. 확인이 끝나면 `DEBUG_PRINT = False` (print는 느리다).

조그 계수: `JOG_COEF = 2.0` (각도 += (value − 64) × 2.0). 윗면(CC34)도 각도에 더할지는 `TOP_ADDS_ANGLE`.

---

## 3부. 파생 채널 (토요일)

7.3절 파생 채널을 Script CHOP 하나에서 계산한다. 크로스페이더 곡선은 `xfader_gains()` 한 곳에만 있다. 기기를 받고 rekordbox 크로스페이더 커브를 확인하면 이 함수만 고친다.

1. `/project1`에 Script CHOP `derive`. 입력에 `ctrl_in` 연결.
2. 자동 생성된 callbacks DAT의 `onCook` 본문에 [derive_script.py](../td/scripts/derive_script.py) 본문을, 그 위에 `xfader_gains` 함수를 붙여 넣는다. `onSetupParameters` 등 다른 템플릿 함수는 그대로 둔다.
3. 1-7의 `ctrl_merge`(`ctrl_in` + `derive`) → `ctrl`.
4. 확인 (`ctrl` 뷰어):
   - 크로스페이더 0 → `deck_mix` ≈ 0, 127 → ≈ 1. 덱2 채널 페이더를 내리면 크로스페이더가 오른쪽이어도 `deck_mix`가 내려간다.
   - 베이스 스왑: 덱1 EQ LOW 64, 덱2 EQ LOW 0, 크로스페이더 가운데 → `d1_bass_w` = 1, `d2_bass_w` = 0. 두 EQ LOW를 서로 바꾸면 값이 넘어간다. 음악이 나오면 `d1_pulse`/`d2_pulse`가 `audio_low`를 따라 움직인다.

| 채널 | 계산 |
|---|---|
| `d1_gain`, `d2_gain` | `d{n}_fader × xfader_gains(xfader)` |
| `deck_mix` | `d2_gain / (d1_gain + d2_gain + 0.001)` |
| `d{n}_bass_w` | `d{n}_eq_low × d{n}_gain`, 합이 1이 되게 정규화 (둘 다 0이면 0) |
| `d{n}_pulse` | `audio_low × d{n}_bass_w` |
| `mix_r/g/b`, `blur_amt`, `edge_amt`, `scratch_mix`, `fx_decay` | 이펙트 식을 짧게 하려고 미리 계산 (mapping.md 4장) |

Math/Expression CHOP으로도 만들 수 있지만, 정규화(합 1)와 0으로 나누기 처리가 있어서 Script CHOP이 덜 꼬인다.

---

## 4부. 중앙 화면 이펙트 (토요일)

기존 점 구름 프로토타입이 있으면 그 파라미터에 아래 매핑만 옮긴다. 없으면 [dots_script.py](../td/scripts/dots_script.py)로 Instancing 기반 점 구름을 만든다. 둘 다 **`/project1/ctrl` 채널만 참조**한다.

식은 파라미터를 Expression 모드(파란색)로 바꾸고 넣는다. 예: `op('/project1/ctrl')['blur_amt'] * 30`

### 4-1. 점 구름 소스

1. `/project1`에 Base COMP `center`. 안으로 들어가서:
2. Select CHOP `ctrl_sel`(`CHOP` = `/project1/ctrl`) → Script CHOP `dots`. callbacks DAT의 `onCook` 본문에 dots_script.py 본문, 그 위에 `import`, 상수, `_points` 함수.
3. 확인: `dots`가 600샘플, 채널 7개(`tx ty tz scale cr cg cb`).
4. Circle SOP `dot_shape`(반지름 1, 면이 채워진 원). TODO(TD에서 확인): Circle SOP의 면 채우기 옵션. 안 되면 작은 Sphere SOP.
5. Geometry COMP `dots_geo` 안의 기본 도형을 지우고 `dot_shape`를 넣는다(또는 In SOP으로 받기). Render 플래그 확인.
6. `dots_geo` 파라미터 `Instance` 페이지:
   - `Instancing` 켬, `Instance OP`(Default Instance OP) = `../dots`. TODO(TD에서 확인): 상대 경로가 안 먹으면 절대 경로 `/project1/center/dots`.
   - `Translate X/Y/Z` = `tx`, `ty`, `tz`
   - `Scale X/Y/Z` = 셋 다 `scale`
   - 색: `Instance 2` 페이지(또는 Color 항목)의 `Color R/G/B` = `cr`, `cg`, `cb`. TODO(TD에서 확인): 인스턴스 색 파라미터 위치.
7. Constant MAT `dot_mat`(흰색) → `dots_geo`의 `Material`. 인스턴스 색이 반영되는지 본다.
8. Camera COMP `cam`: `Projection` = Orthographic, `Ortho Width` = 2, Translate Z = 5.
9. Render TOP `render_center`: 해상도 640×720, Camera = `cam`, Geometry = `dots_geo`. 배경 검정.

점 구름 쪽 매핑 (dots_script.py 안에서 처리):

| ID | 반응 | 사용 채널 |
|---|---|---|
| VA-01 | 점마다 고정 난수 u가 `deck_mix`보다 작으면 덱2 색, 아니면 덱1 색. 크로스페이더만큼 덱2 색 점이 늘어난다 | `deck_mix`, `d{n}_r/g/b` |
| VA-02 | 점 크기 × (1 + 2 × `d{n}_pulse`). 저음이 살아 있는 덱의 점만 커진다 | `d{n}_pulse` |
| VA-03 | LOW = 점 크기, MID = 보이는 점 개수, HIGH = 밝기 | `d{n}_eq_low/mid/hi` |
| VA-04 | 밝기 × 채널 페이더 (검정 배경이라 투명도와 같다) | `d{n}_fader` |
| VA-06 | 점이 속한 덱의 조그 각도만큼 회전 | `d{n}_jog_angle` |

숫자(크기 0.012, 펄스 배율 2.0 등)는 dots_script.py 상수와 본문에서 조정한다.

### 4-2. 후처리 체인 (`render_center` 다음, 순서대로)

| 순서 | 오퍼레이터 | 설정 | ID |
|---|---|---|---|
| 1 | Transform TOP `rgb_r` | `Translate X` = `op('/project1/ctrl')['scratch_mix'] * 0.02` | VA-06 |
| 2 | Transform TOP `rgb_b` | `Translate X` = `op('/project1/ctrl')['scratch_mix'] * -0.02` | VA-06 |
| 3 | Reorder TOP `rgb_split` | 입력 0 = `render_center`, 1 = `rgb_r`, 2 = `rgb_b`. 출력 R ← 입력1 R, G ← 입력0 G, B ← 입력2 B, A ← 입력0 A. TODO(TD에서 확인): Reorder 파라미터 라벨 | VA-06 |
| 4 | Blur TOP `blur` | `Filter Size` = `op('/project1/ctrl')['blur_amt'] * 30` | VA-05 음수 |
| 5 | Edge TOP `edge` | 입력 `blur` | VA-05 양수 |
| 6 | Cross TOP `edge_cross` | 입력 `blur`, `edge`. `Cross` = `op('/project1/ctrl')['edge_amt']` | VA-05 양수 |
| 7 | Transform TOP `beat_jump` | `Translate X` = `op('/project1/ctrl')['beat_off_x']`, `Translate Y` = `op('/project1/ctrl')['beat_off_y']` | VA-08 비트점프 |
| 8 | 잔상 루프 (아래) | 유지율 = `op('/project1/ctrl')['fx_decay']` | VA-07 |
| 9 | Constant TOP `base_bg` + Composite TOP(Add) | 색 = `base_r/g/b` × 0.08 (아주 옅은 배경) | VA-09 |
| 10 | Constant TOP `flash_col` + Cross TOP `flash_cross` | 색 = `flash_r/g/b`, `Cross` = `op('/project1/ctrl')['flash'] * 0.8` | VA-08 핫큐 |
| 11 | Constant TOP 흰색 + Cross TOP `strobe_cross` | `Cross` = `op('/project1/ctrl')['strobe'] * (1 if absTime.frame % 6 < 3 else 0)` | VA-08 패드FX |
| 12 | Null TOP `center_out` | | |

Constant TOP 색 식 예: `Color R` = `op('/project1/ctrl')['base_r'] * 0.08`. 덱 색은 ShowExt가 곡 색(P1 전까지 임시 곡 A `#ff3fa4`, B `#3fc8ff`)에서 넣는다.

**잔상 루프** (5부 실루엣에서도 같은 모양으로 쓴다):

```
in(직전 결과) ─┬───────────────────────────────┐
               └→ fb (Feedback TOP)            │
                   → fb_level (Level TOP)      │
                   → fb_xform (Transform TOP)  │
                        → fb_comp (Composite TOP: in, fb_xform) → fb_out (Null TOP)
```

1. Feedback TOP `fx_fb`: 입력 = `beat_jump`, `Target TOP` = `fx_out`.
2. Level TOP `fx_fade`: `Opacity` = `op('/project1/ctrl')['fx_decay']`. TODO(TD에서 확인): Opacity가 있는 페이지(Post).
3. Transform TOP `fx_grow`: `Scale` 1.01, 1.01 (잔상이 살짝 퍼지게, 취향).
4. Composite TOP `fx_comp`: 입력 `beat_jump`, `fx_grow`. `Operation` = Maximum.
5. Null TOP `fx_out`.

`fx_on` = 0이면 `fx_decay` = 0이라 잔상이 없다. FX ON을 켜고 FX LEVEL을 올리면 잔상이 길어진다.

### 4-3. 확인 (시연 영상 순서와 같다)

- [ ] 크로스페이더를 덱1 → 덱2로 밀면 분홍 점이 파랑 점으로 점점 바뀐다 (VA-01)
- [ ] 끝에 1초 이상 두면 배경색이 그 덱 곡 색으로 (VA-09)
- [ ] 음악을 틀고 EQ LOW를 두 덱 사이에서 바꾸면 커졌다 작아지는 점이 넘어간다 (VA-02)
- [ ] EQ LOW/MID/HI, 채널 페이더, 필터 양쪽, 조그 SIDE/TOP, FX ON + LEVEL, 핫큐 패드 8개 각각 반응

---

## 5부. 실루엣 이펙트 (일요일)

### 5-1. MediaPipe 플러그인 (세그멘테이션만)

1. GitHub `torinmb/mediapipe-touchdesigner` Releases에서 받은 `.tox`를 `/project1`에 끌어 놓는다 (예: `mediapipe1`).
2. 플러그인 파라미터에서 웹캠을 고르고 해상도는 720p 이하.
3. 모델은 **Image Segmentation만 켜고** 나머지(face, pose, hand 등)는 끈다. 6부에서 제스처를 쓸 때 hand/gesture만 추가로 켠다. TODO(TD에서 확인): 각 모델 토글 이름.
4. 세그멘테이션 마스크가 나오는 TOP 출력을 찾는다. TODO(TD에서 확인): COMP 출력 커넥터 순서 또는 내부 TOP 이름. 찾으면 Select TOP `sil_src`로 가져온다.

### 5-2. 실루엣 체인 (`/project1/silhouette` Base COMP 안)

| 순서 | 오퍼레이터 | 설정 |
|---|---|---|
| 1 | Select TOP `sil_src` | 5-1의 마스크 |
| 2 | Fit TOP `sil_fit` | 해상도 640×720, 꽉 채우기(Fill). 무대 방향에 맞게 필요하면 Flip TOP으로 좌우 반전 |
| 3 | Threshold TOP `sil_mask` | `Threshold` 0.5 (사람 = 흰색). TODO(TD에서 확인): 마스크가 반대면 Level TOP의 Invert |
| 4 | 잔상 루프 | 4-2와 같은 모양. 입력 = `sil_mask`, 이름 `sil_fb` → `sil_decay` → `sil_grow` → `sil_comp`(Maximum) → `sil_trail`. `sil_decay`의 `Opacity` = `0.75 + 0.22 * op('/project1/ctrl')['fx_level']`, `sil_grow`의 `Scale` 1.01 |
| 5 | Edge TOP `sil_edge` | 입력 `sil_mask` (외곽선) |
| 6 | Level TOP `sil_trail_dim` | 입력 `sil_trail`, `Opacity` 0.6 (잔상은 외곽선보다 어둡게) |
| 7 | Composite TOP `sil_sum` | 입력 `sil_trail_dim`, `sil_edge`, `Operation` = Add |
| 8 | Constant TOP `sil_color` | 640×720, `Color R/G/B` = `op('/project1/ctrl')['mix_r']`, `['mix_g']`, `['mix_b']` (VA-01 색을 따름) |
| 9 | Composite TOP `sil_tint` | 입력 `sil_sum`, `sil_color`, `Operation` = Multiply |
| 10 | Null TOP `sil_out` | |

`fx_level`을 올리면 잔상이 길어진다 (`fx_on`과 관계없이 실루엣 잔상은 항상 조금 남는다).

### 5-3. 중앙 화면에 합성

`/project1/center`에서 `fx_out` 다음에 Select TOP(`/project1/silhouette/sil_out`) + Composite TOP(Add)을 넣는다. 점 구름의 잔상 루프와 실루엣 잔상 루프가 겹치지 않게 **잔상 루프 뒤**에 합친다.

### 5-4. 확인

- [ ] 사람이 움직이면 외곽선과 잔상이 따라온다
- [ ] 크로스페이더에 따라 실루엣 색이 덱1 색 → 덱2 색
- [ ] FX LEVEL을 올리면 잔상이 길어진다
- [ ] FPS가 25 미만이면 플러그인 해상도를 낮춘다 (Performance Monitor: `Dialogs > Performance Monitor`)

---

## 6부. 제스처 → `ShowExt.Toggle()` (일요일, 가능하면)

판정 규칙(7.5절): 점수 0.6 이상 `Closed_Fist`가 0.5초 이상 → 0.7초 안에 점수 0.6 이상 `Open_Palm` → `gesture_toggle` 펄스 1회 → 3초 판정 정지. 손이 여럿이면 가장 큰 손. 로직은 [gesture.py](../td/scripts/gesture.py)의 `GestureDetector`이고, TD 밖에서 `python td/scripts/gesture.py`로 테스트할 수 있다.

### 6-1. 플러그인 출력 확인

1. 플러그인에서 hand(제스처 인식 포함)를 켠다. TODO(TD에서 확인): 제스처 인식 토글 이름.
2. 제스처 라벨과 점수가 어디에 나오는지 찾는다 (DAT 표인지 CHOP 채널인지, 이름이 무엇인지). 플러그인 COMP 출력과 내부를 열어 본다. 주먹/편 손을 번갈아 하며 바뀌는 값을 찾는다.
3. 표(DAT)라면 `/project1`에 Select DAT `mp_gesture`로 끌어온다. gesture.py의 `read_hands()`는 아래 형식을 가정한다:
   - 첫 줄이 머리글, 열 이름에 `gesture`(또는 `category`, `name`)와 `score`가 들어 있음
   - 손 하나당 한 줄. `size` 열이 있으면 가장 큰 손을 고른다 (없으면 첫 손)
4. 형식이 다르면 `read_hands()`만 고친다. 반환값은 `[(라벨, 점수, 크기), ...]`. CHOP이라면 예:

```python
def read_hands():
    c = op('/project1/mp_hand')            # TODO: 실제 경로
    if c is None or c['TODO_score'] is None:
        return []
    label = 'Closed_Fist' if ... else ...  # 채널 값 -> 라벨 변환
    return [(label, c['TODO_score'].eval(), 0.0)]
```

### 6-2. 연결

1. `/project1/show/gesture` Text DAT에 수정한 gesture.py가 들어 있는지 확인.
2. `frame_exec` callbacks의 `USE_GESTURE = True`.
3. 확인: `ctrl`의 `hand_found`가 손을 보이면 1, 주먹을 쥐면 `gesture_hold`가 0 → 1로 0.5초에 걸쳐 오른다. 손을 펴면 Textport에 `CENTER_ONLY -> COUNTDOWN`. 3초 안에 다시 해도 무시된다.
4. gesture.update()에서 오류가 나면 Textport에 `[frame] gesture 꺼짐: …`이 한 번 찍히고 나머지는 계속 돈다.
5. 인식이 불안하면 시연은 F1로 한다 (GS-03).

조정값(gesture.py 위쪽): `SCORE_MIN` 0.6, `FIST_HOLD` 0.5, `OPEN_WINDOW` 0.7, `LOCKOUT` 3.0, `FIST_GAP` 0.1(주먹 인식이 1~2프레임 끊겨도 이어진 것으로 봄).

---

## 남은 부 (P1)

- 7부 운영자 화면 (OP-01): 상태, 덱별 곡, 연결 상태, FPS, `ctrl` 값
- 좌우 화면(B), 점프 입력, 곡 세트 전환 완성
