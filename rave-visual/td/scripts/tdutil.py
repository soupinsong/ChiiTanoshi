# 공용 도우미. TD 위치: /project1/show/tdutil (Text DAT)
# 다른 스크립트에서는 mod('/project1/show/tdutil') 로 불러 쓴다.
#
# Python으로 값을 쓰는 Constant CHOP의 채널 이름을 여기 한 곳에서 관리한다.
# ShowExt가 시작할 때 setup_constants()를 불러 이름을 채운다.

CONST_CHANNELS = {
    # 조그 (jog_callbacks.py가 누적, frame_callbacks.py가 속도·스크래치 계산)
    '/project1/jog_acc': [
        'd1_jog_angle', 'd2_jog_angle',
        'd1_jog_vel', 'd2_jog_vel',
        'd1_scratch', 'd2_scratch',
    ],
    # 버튼·패드 (jog_callbacks.py)
    '/project1/btn': [
        'd1_touch', 'd2_touch', 'fx_on',
        'd1_pad_pulse', 'd2_pad_pulse',
        'd1_pad_index', 'd2_pad_index',
        'd1_pad_mode', 'd2_pad_mode',
        'd1_load_pulse', 'd2_load_pulse',
        'strobe', 'beat_off_x', 'beat_off_y',
    ],
    # 쇼 상태 (show_ext.py)
    '/project1/show/show_out': [
        'state', 'state_time', 'countdown', 'side_on',
        'jump_reset', 'panic',
        'flash', 'flash_r', 'flash_g', 'flash_b',
        'd1_r', 'd1_g', 'd1_b', 'd2_r', 'd2_g', 'd2_b',
        'base_r', 'base_g', 'base_b',
    ],
    # 제스처 (gesture.py)
    '/project1/show/gesture_out': [
        'gesture_toggle', 'gesture_hold', 'hand_found',
    ],
}


def _const_par(chop, i, kind):
    # kind: 'name' 또는 'value'
    # TODO(TD에서 확인): Constant CHOP 파라미터 Python 이름.
    #   버전에 따라 name0/value0 또는 const0name/const0value. 파라미터에 마우스를 올리면 이름이 보인다.
    for n in ('%s%d' % (kind, i), 'const%d%s' % (i, kind)):
        p = getattr(chop.par, n, None)
        if p is not None:
            return p
    return None


def setup_constants():
    # 레지스트리의 채널 이름을 각 Constant CHOP에 써 넣는다. 실패한 항목은 print.
    for path, names in CONST_CHANNELS.items():
        chop = op(path)
        if chop is None:
            print('[tdutil] 없음:', path)
            continue
        # TODO(TD에서 확인): 최신 TD의 Constant CHOP은 칸을 늘려야 할 수 있다(+ 버튼).
        #   아래 줄이 실패하면 UI에서 칸 수를 직접 맞춘다.
        try:
            chop.seq.const.numBlocks = max(chop.seq.const.numBlocks, len(names))
        except Exception:
            pass
        for i, name in enumerate(names):
            p = _const_par(chop, i, 'name')
            if p is None:
                print('[tdutil] 칸 부족:', path, i, name)
                break
            p.val = name


def set_value(path, name, value):
    chop = op(path)
    if chop is None:
        return
    p = _const_par(chop, CONST_CHANNELS[path].index(name), 'value')
    if p is not None and p.eval() != value:
        p.val = value


def get_value(path, name, default=0.0):
    chop = op(path)
    if chop is None:
        return default
    p = _const_par(chop, CONST_CHANNELS[path].index(name), 'value')
    return p.eval() if p is not None else default


def chan(chop, name, default=0.0):
    # CHOP 채널 현재값. 채널이 없으면 default
    if chop is None:
        return default
    c = chop[name]
    return c.eval() if c is not None else default


def hex_to_rgb(color, fallback=(1.0, 1.0, 1.0)):
    s = str(color).lstrip('#')
    if len(s) != 6:
        return fallback
    try:
        return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return fallback
