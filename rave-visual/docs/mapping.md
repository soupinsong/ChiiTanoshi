# 매핑표: 조작부 ↔ MIDI ↔ TD 채널 ↔ 화면 반응

- MIDI 값은 브리프 7.2절(Mixxx DDJ-FLX4 매핑과 대조한 값) 기준. MIDI 채널은 1부터 센다.
- **예상 TD 채널**: MIDI In CHOP 이름 규칙 추정. 중간 보고서 때 CC15가 `ch1ctrl16`으로 보였으므로 CC 번호 +1로 적었다. 노트 표기는 미확인.
- **TD 채널 이름 (확인)**: 시뮬레이터로 조작부를 하나씩 움직이면서 직접 채운다. 방법은 [td_build_guide.md](td_build_guide.md) 1-3.
- **처리**: CHOP = MIDI In CHOP → Select/Rename/Math/Lag, DAT = MIDI In DAT 콜백([jog_callbacks.py](../td/scripts/jog_callbacks.py)). DAT 행은 print에 찍힌 index를 적는다.
- 덱 표기 `d{n}`: 덱1 = ch1, 덱2 = ch2 (패드는 ch8 / ch10).

## 1. 연속값 (CHOP)

| 조작부 | MIDI | 예상 TD 채널 | TD 채널 이름 (확인) | ctrl 채널 | 범위 · 평활 | 화면 반응 |
|---|---|---|---|---|---|---|
| 크로스페이더 | ch7 CC31 (LSB 63) | `ch7ctrl32` | | `xfader` | 0~1 (0 = 덱1), Lag 0.05 | `deck_mix` 계산 → VA-01 색 비율, VA-09 곡 전환 완료 |
| 채널 페이더 덱1 | ch1 CC19 (LSB 51) | `ch1ctrl20` | | `d1_fader` | 0~1, Lag 0.05 | VA-04 덱1 점 밝기(투명도), `d1_gain` |
| 채널 페이더 덱2 | ch2 CC19 | `ch2ctrl20` | | `d2_fader` | 0~1, Lag 0.05 | VA-04 덱2, `d2_gain` |
| EQ LOW 덱1 / 덱2 | ch1 / ch2 CC15 | `ch1ctrl16` / `ch2ctrl16` | | `d1_eq_low` / `d2_eq_low` | 0~1 (0.5 기본), Lag 0.08 | VA-03 점 크기, VA-02 베이스 스왑 가중치 `bass_w` |
| EQ MID 덱1 / 덱2 | ch1 / ch2 CC11 | `ch1ctrl12` / `ch2ctrl12` | | `d1_eq_mid` / `d2_eq_mid` | 0~1 (0.5 기본), Lag 0.08 | VA-03 점 개수 |
| EQ HI 덱1 / 덱2 | ch1 / ch2 CC7 | `ch1ctrl8` / `ch2ctrl8` | | `d1_eq_hi` / `d2_eq_hi` | 0~1 (0.5 기본), Lag 0.08 | VA-03 밝기 |
| 필터 CH1 | ch7 CC23 | `ch7ctrl24` | | `d1_filter` | -1~1 (가운데 0), Lag 0.08 | VA-05 음수 = 블러, 양수 = 외곽선 |
| 필터 CH2 | ch7 CC24 | `ch7ctrl25` | | `d2_filter` | -1~1, Lag 0.08 | VA-05 |
| Beat FX 레벨 | ch5 CC2 (LSB 34) | `ch5ctrl3` | | `fx_level` | 0~1, Lag 0.08 | VA-07 잔상 길이, 실루엣 잔상 길이 |
| TRIM 덱1 / 덱2 | ch1 / ch2 CC4 | `ch1ctrl5` / `ch2ctrl5` | | (미사용) | | |
| 템포 페이더 | ch1 / ch2 CC0 | `ch1ctrl1` / `ch2ctrl1` | | (미사용) | | |

LSB 채널(번호 +32)은 Select에서 빼고 MSB만 쓴다 (IN-02).

## 2. 상대값·버튼·패드 (DAT 콜백)

| 조작부 | MIDI | 콜백 index (확인) | ctrl 채널 | 범위 | 화면 반응 |
|---|---|---|---|---|---|
| 조그 옆면 덱1 / 덱2 | ch1 / ch2 CC33, 64 기준 상대값 | | `d{n}_jog_angle`, `d{n}_jog_vel` | 도 누적 (`(v-64)*2.0`), 도/초 | VA-06 점 회전 |
| 조그 윗면 (바이닐) | ch1 / ch2 CC34 | | `d{n}_scratch` (+ 각도) | 0~1 | VA-06 RGB 분리 |
| 조그 터치 | ch1 / ch2 Note 54 | | `d{n}_touch` | 0/1 | (예비) |
| PLAY / CUE / SYNC | ch1 / ch2 Note 11 / 12 / 88 | | (미사용) | | rekordbox 기능만 |
| Beat FX ON | ch5 또는 ch6 Note 71 | | `fx_on` | 0/1 토글 | VA-07 잔상 on/off |
| Beat FX SELECT | ch5 Note 99 | | (미사용) | | |
| LOAD 덱1 / 덱2 | ch7 Note 70 / 71 | | `d{n}_load_pulse` | 펄스 | ST-02 `AdvanceSong(n, 1)` |
| 패드 핫큐 1~8 | 덱1 ch8 / 덱2 ch10, Note 0~7 | | `d{n}_pad_pulse`, `_pad_index`, `_pad_mode`=0 | 펄스, 1~8 | VA-08 패드별 색 플래시 0.15초 |
| 패드 패드FX 1~8 | ch8 / ch10 Note 16~23 | | `strobe`, `_pad_mode`=1 | 누르는 동안 1 | VA-08 스트로브 (권장) |
| 패드 비트점프 1~8 | ch8 / ch10 Note 32~39 | | `beat_off_x`, `beat_off_y`, `_pad_mode`=2 | 누르는 동안 오프셋 | VA-08 화면 오프셋 (권장) |
| 패드 샘플러 1~8 | ch8 / ch10 Note 48~55 | | `_pad_mode`=3 | | VA-08 스탬프 (권장, 미구현) |

주의: 덱2 패드는 ch10. 뗌은 note on velocity 0. Shift 조작(덱1 패드 Shift = ch9 등)은 쓰지 않는다. 패드·버튼을 누르면 rekordbox 기능도 같이 실행된다.

## 3. 오디오·쇼 상태 (MIDI 아님)

| 출처 | ctrl 채널 | 범위 · 평활 | 화면 반응 |
|---|---|---|---|
| 마스터 RMS (Audio File In → Analyze) | `audio_level` | 0~1, Lag 상승 0.03 / 하강 0.2 | (예비) |
| 150Hz 이하 레벨 | `audio_low` | 0~1, Lag 상승 0.02 / 하강 0.15 | VA-02 `d{n}_pulse` |
| ShowExt | `state`, `countdown`, `side_on`, `flash`, `flash_r/g/b`, `d{n}_r/g/b`, `base_r/g/b` | | SH-01~03, VA-08 플래시, 덱 색, VA-09 기본색 |
| 제스처 | `gesture_toggle`, `gesture_hold`, `hand_found` | 펄스, 0~1, 0/1 | GS-01 → `ShowExt.Toggle()` |

## 4. 파생 채널 ([derive_script.py](../td/scripts/derive_script.py))

| 채널 | 계산 | 화면 반응 |
|---|---|---|
| `d1_gain` / `d2_gain` | `d1_fader * (1 - xfader)` / `d2_fader * xfader` (곡선은 `xfader_gains()` 한 곳) | |
| `deck_mix` | `d2_gain / (d1_gain + d2_gain + 0.001)` | VA-01 덱2 색 비율 |
| `d{n}_bass_w` | `d{n}_eq_low * d{n}_gain`, 합 1로 정규화 | VA-02 |
| `d{n}_pulse` | `audio_low * d{n}_bass_w` | VA-02 점 크기 펄스 |
| `mix_r/g/b` | 덱 색을 `deck_mix`로 섞음 | VA-10 실루엣 색 |
| `blur_amt` / `edge_amt` | 덱 필터를 `deck_mix`로 섞은 뒤 음수/양수 부분 | VA-05 |
| `scratch_mix` | 두 덱 `scratch` 중 큰 값 | VA-06 RGB 분리 |
| `fx_decay` | `(0.80 + 0.17 * fx_level) * fx_on` | VA-07 잔상 유지율 |

## 5. 기기 받으면 확인할 것

- [ ] TD 노트 채널 표기 (MIDI In CHOP 이름, DAT index가 +1인지)
- [ ] 조그 계수 2.0이 실제 한 바퀴에 맞는지
- [ ] 크로스페이더 곡선 (rekordbox 설정) → `xfader_gains()` 수정
- [ ] Beat FX ON이 ch5인지 ch6인지
