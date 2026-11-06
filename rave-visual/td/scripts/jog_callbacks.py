# MIDI In DAT 콜백 본문. TD 위치: /project1/midiin_dat 의 callbacks DAT
#
# 사용법: MIDI In DAT이 자동으로 만든 callbacks DAT의 함수 시그니처(def 줄)는 그대로 두고,
#         아래 상수와 onReceiveMIDI의 "본문"만 붙여 넣는다.
#
# 처리 내용 (MIDI In CHOP은 같은 값이 반복되면 변화가 없어서, 상대값·노트는 여기서 처리한다)
#   - 조그 옆면 CC33 / 윗면 CC34 (ch1/2): 메시지마다 jog_acc에 누적 (IN-04)
#   - 조그 터치 노트 54 (ch1/2)              -> btn d{n}_touch
#   - Beat FX ON 노트 71 (ch5 또는 6)        -> btn fx_on 토글
#   - 패드 노트 (덱1 ch8, 덱2 ch10)          -> pad_pulse / pad_index / pad_mode, 핫큐는 ShowExt.Flash
#   - LOAD 노트 70/71 (ch7)                  -> load_pulse, ShowExt.AdvanceSong(n, 1)

DEBUG_PRINT = True      # 처음엔 True로 두고 Textport에서 message/channel/index 형식을 확인한다

# TODO(TD에서 확인): MIDI In DAT의 index가 CC/노트 번호 그대로인지 +1인지.
#   시뮬레이터 조그를 돌렸을 때 print된 index가 34면 CC_OFFSET = 1 (CHOP의 ch1ctrl16 = CC15와 같은 규칙)
CC_OFFSET = 0
NOTE_OFFSET = 0
# TODO(TD에서 확인): channel이 1부터 세는지. 덱1 조작 시 0이 찍히면 1로 바꾼다.
CHANNEL_OFFSET = 0

JOG_COEF = 2.0          # 각도 = (value - 64) * 계수. 리허설에서 조정
TOP_ADDS_ANGLE = True   # 윗면(CC34)도 회전 각도에 더할지. False면 명세대로 CC33만 각도

JOG_ACC = '/project1/jog_acc'
BTN = '/project1/btn'
SHOW = '/project1/show'

DECK_CH = {1: 1, 2: 2}
PAD_CH = {8: 1, 10: 2}          # 채널 -> 덱 (덱2는 ch10)
MIX_CH = 7
FX_CH = (5, 6)

JOG_SIDE, JOG_TOP, JOG_TOUCH = 33, 34, 54
FX_ON_NOTE = 71
LOAD_NOTE = {70: 1, 71: 2}
PAD_MODE_BASE = (0, 16, 32, 48)  # 0 핫큐, 1 패드FX, 2 비트점프, 3 샘플러

# 핫큐 패드별 플래시 색 (패드 1~8)
PAD_COLORS = ['#ff3fa4', '#ff8a00', '#ffe600', '#3cff6b',
              '#00e5ff', '#3f6bff', '#a64dff', '#ffffff']


def onReceiveMIDI(dat, rowIndex, message, channel, index, value, input, bytes):
    # ↑ 이 def 줄은 TD 템플릿의 것을 그대로 쓴다. 아래 본문만 붙여 넣는다.
    if DEBUG_PRINT:
        print('MIDI', repr(message), channel, index, value)

    u = mod('/project1/show/tdutil')
    m = str(message).lower()
    # TODO(TD에서 확인): message 문자열. print에 'Control Change' / 'Note On' 비슷하게 찍히는지 확인
    is_cc = 'control' in m
    is_note = 'note' in m
    ch = int(channel) + CHANNEL_OFFSET
    num = int(index) - (CC_OFFSET if is_cc else NOTE_OFFSET)
    val = int(value)

    # 조그
    if is_cc and ch in DECK_CH.values() and num in (JOG_SIDE, JOG_TOP):
        d = ch
        delta = val - 64
        acc = op(JOG_ACC)
        if num == JOG_SIDE or TOP_ADDS_ANGLE:
            name = 'd%d_jog_angle' % d
            u.set_value(JOG_ACC, name, u.get_value(JOG_ACC, name) + delta * JOG_COEF)
        if num == JOG_TOP and acc is not None:
            # 스크래치 활동량은 storage에 누적, frame_callbacks.py가 초당 양으로 바꾼다
            key = 'd%d_scratch_acc' % d
            acc.store(key, acc.fetch(key, 0.0) + abs(delta))
        return

    if not is_note:
        return
    pressed = val > 0           # FLX4는 뗌을 velocity 0으로 보낸다

    # 조그 터치
    if ch in DECK_CH.values() and num == JOG_TOUCH:
        u.set_value(BTN, 'd%d_touch' % ch, 1 if pressed else 0)
        return

    # Beat FX ON: 누를 때마다 토글
    if ch in FX_CH and num == FX_ON_NOTE:
        if pressed:
            u.set_value(BTN, 'fx_on', 0 if u.get_value(BTN, 'fx_on') else 1)
        return

    # LOAD
    if ch == MIX_CH and num in LOAD_NOTE:
        if pressed:
            d = LOAD_NOTE[num]
            _pulse(u, 'd%d_load_pulse' % d)
            show = op(SHOW)
            if show is not None:
                show.AdvanceSong(d, 1)
        return

    # 패드: 모드별 노트 범위 전체를 듣는다 (IN-06)
    if ch in PAD_CH:
        d = PAD_CH[ch]
        mode = num // 16
        if mode > 3 or num % 16 > 7:
            return
        pad = num % 16 + 1
        if pressed:
            u.set_value(BTN, 'd%d_pad_index' % d, pad)
            u.set_value(BTN, 'd%d_pad_mode' % d, mode)
            _pulse(u, 'd%d_pad_pulse' % d)
        if mode == 0 and pressed:
            show = op(SHOW)
            if show is not None:
                show.Flash(PAD_COLORS[pad - 1], 0.15)
        elif mode == 1:
            # 패드FX: 누르고 있는 동안 스트로브
            u.set_value(BTN, 'strobe', 1 if pressed else 0)
        elif mode == 2:
            # 비트점프: 누르는 동안 패드 위치 쪽으로 화면 오프셋
            col, row = (pad - 1) % 4, (pad - 1) // 4
            u.set_value(BTN, 'beat_off_x', (col - 1.5) * 0.06 if pressed else 0.0)
            u.set_value(BTN, 'beat_off_y', (0.5 - row) * 0.08 if pressed else 0.0)
        return
    return


def _pulse(u, name):
    # 1프레임 펄스: 지금 1, 다음 프레임에 0
    u.set_value(BTN, name, 1)
    run("mod('/project1/show/tdutil').set_value(%r, %r, 0)" % (BTN, name), delayFrames=1)
