# 주말 체크리스트 (마감: 2026-11-09(월) 13:30 멘토 미팅 전)

미팅에서 보여줄 것: 가상 컨트롤러로 TD 중앙 화면이 반응하는 시연 영상, 매핑표, DJ 실루엣 잔상 효과.
각 항목의 자세한 방법은 [td_build_guide.md](td_build_guide.md)의 해당 부.

## 금요일 밤 (가이드 1부)

- [ ] loopMIDI 설치, 포트 1개 생성
- [ ] `pip install mido python-rtmidi`, `python tools/flx4_sim.py` 실행
- [ ] TD MIDI Device Mapper에 loopMIDI 등록, MIDI In CHOP 생성
- [ ] 시뮬레이터로 조작부를 하나씩 움직여 [mapping.md](mapping.md)의 TD 채널 이름 열 채우기 (특히 노트 표기, CC +1 여부)
- [ ] Select → Rename → Math → Lag → Null `ctrl` 구성
- [ ] `show` COMP 뼈대 (1-6): F1 / P가 Textport에 찍히는지

## 토요일 (가이드 2~4부)

- [ ] 조그 MIDI In DAT 콜백 연결, print로 index 확인 후 수정
- [ ] 파생 채널(`deck_mix`, `bass_w`, `pulse`) 구성
- [ ] 중앙 화면 소스 하나에 필수 매핑(VA-01~07, 09, 핫큐 플래시) 전부 연결
- [ ] 음악은 Audio File In CHOP으로 셋리스트 곡 재생해서 반응 확인

## 일요일 (가이드 5~6부)

- [ ] MediaPipe 플러그인: 세그멘테이션만 켜고 실루엣 잔상·외곽선 구성, `fx_level`·덱 색 연결
- [ ] (가능하면) 제스처 → `ShowExt.Toggle()` 연결, 안 되면 F1로 시연
- [ ] 화면 녹화로 시연 영상 1~2분 (곡 전환 + 베이스 스왑 + 조그 + 패드 + 실루엣)

## 월요일 오전

- [ ] [mapping.md](mapping.md) 최종 정리
- [ ] 기기 받으면 확인할 항목 정리: TD 노트 채널 표기, 조그 계수, 크로스페이더 곡선, (팀) 센서 임계값
