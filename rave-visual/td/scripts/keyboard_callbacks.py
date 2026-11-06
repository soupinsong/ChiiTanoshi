# Keyboard In DAT 콜백 본문. TD 위치: /project1/show/keyboard1 의 callbacks DAT
# TD 템플릿의 onKey def 줄(인자 목록)은 그대로 두고 본문만 붙여 넣는다.
# 본문에서 쓰는 인자: key, shift, state
#
# F1 = Toggle, P = Panic, ←/→ = 덱1 곡 이동, Shift+←/→ = 덱2 곡 이동, J = SendSerial('C')

DEBUG_PRINT = True      # 처음엔 True로 두고 key 이름이 어떻게 찍히는지 확인

# TODO(TD에서 확인): Keyboard In DAT의 key 이름. print 결과에 맞게 고친다
KEY_TOGGLE = 'f1'
KEY_PANIC = 'p'
KEY_LEFT = 'left'
KEY_RIGHT = 'right'
KEY_SERIAL_CAL = 'j'


def onKey(dat, key, character, alt, lAlt, rAlt, ctrl, lCtrl, rCtrl, shift, lShift, rShift, state, time, cmd, lCmd, rCmd):
    # ↑ 이 def 줄은 TD 템플릿의 것을 그대로 쓴다. 아래 본문만 붙여 넣는다.
    if DEBUG_PRINT:
        print('KEY', repr(key), 'shift' if shift else '', 'down' if state else 'up')
    if not state:           # 누를 때만
        return
    show = op('/project1/show')
    k = str(key).lower()
    if k == KEY_TOGGLE:
        show.Toggle()
    elif k == KEY_PANIC:
        show.Panic()
    elif k in (KEY_LEFT, KEY_RIGHT):
        step = -1 if k == KEY_LEFT else 1
        show.AdvanceSong(2 if shift else 1, step)
    elif k == KEY_SERIAL_CAL:
        show.SendSerial('C')
    return
