# Execute DAT 콜백 본문 (매 프레임). TD 위치: /project1/show/frame_exec 의 callbacks DAT
# Execute DAT에서 Frame Start를 켠다. TD 템플릿의 onFrameStart def 줄은 그대로 두고 본문만 붙여 넣는다.
#
# 하는 일
#   1. 조그 각도 -> 각속도 d{n}_jog_vel (도/초, 평활 0.15초)
#      스크래치 누적 -> d{n}_scratch (0~1, 평활 0.1초)
#   2. 제스처 판정 (gesture.update)
#   3. ShowExt.Update (카운트다운, 페이드, 플래시, VA-09)

import math

JOG_ACC = '/project1/jog_acc'
SCRATCH_FULL = 400.0    # 초당 이만큼(64 기준 차이 합) 움직이면 scratch = 1. 리허설에서 조정
USE_GESTURE = True      # MediaPipe 연결 전이면 False


def onFrameStart(frame):
    # ↑ 이 def 줄은 TD 템플릿의 것을 그대로 쓴다. 아래 본문만 붙여 넣는다.
    u = mod('/project1/show/tdutil')
    now = absTime.seconds
    dt = now - me.fetch('last_t', now)
    me.store('last_t', now)

    if dt > 0:
        _jog_rates(u, dt)
    if USE_GESTURE:
        try:
            mod('/project1/show/gesture').update()
        except Exception as e:
            # 웹캠/플러그인이 없어도 나머지는 계속 돈다
            if not me.fetch('gesture_err', False):
                print('[frame] gesture 꺼짐:', e)
                me.store('gesture_err', True)
    op('/project1/show').Update()
    return


def _smooth(prev, target, dt, tau):
    # Lag CHOP과 비슷한 1차 평활
    v = prev + (target - prev) * (1.0 - math.exp(-dt / tau))
    return 0.0 if abs(v) < 1e-3 else v


def _jog_rates(u, dt):
    acc = op(JOG_ACC)
    if acc is None:
        return
    for d in (1, 2):
        ang = u.get_value(JOG_ACC, 'd%d_jog_angle' % d)
        prev = acc.fetch('d%d_prev_angle' % d, ang)
        acc.store('d%d_prev_angle' % d, ang)
        vel = _smooth(u.get_value(JOG_ACC, 'd%d_jog_vel' % d), (ang - prev) / dt, dt, 0.15)
        u.set_value(JOG_ACC, 'd%d_jog_vel' % d, vel)

        sc = acc.fetch('d%d_scratch_acc' % d, 0.0)
        prev_sc = acc.fetch('d%d_prev_scratch' % d, sc)
        acc.store('d%d_prev_scratch' % d, sc)
        rate = min(1.0, (sc - prev_sc) / dt / SCRATCH_FULL)
        scratch = _smooth(u.get_value(JOG_ACC, 'd%d_scratch' % d), rate, dt, 0.1)
        u.set_value(JOG_ACC, 'd%d_scratch' % d, scratch)
