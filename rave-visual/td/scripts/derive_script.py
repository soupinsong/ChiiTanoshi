# 파생 채널 Script CHOP 본문 (7.3절). TD 위치: /project1/derive 의 callbacks DAT
# 입력 0 = ctrl_in (정규화 채널 + jog_acc + btn + show). 출력은 파생 채널만, 1샘플.
# TD 템플릿의 onCook def 줄은 그대로 두고 본문만 붙여 넣는다.
#
# 크로스페이더 곡선은 xfader_gains() 한 곳에서만 계산한다.


def xfader_gains(xf):
    # 선형 근사. rekordbox 크로스페이더 커브 설정에 따라 실제와 다르다.
    # 기기 확인 후 이 함수만 고친다.
    return 1.0 - xf, xf


def onCook(scriptOp):
    # ↑ 이 def 줄은 TD 템플릿의 것을 그대로 쓴다. 아래 본문만 붙여 넣는다.
    src = scriptOp.inputs[0] if scriptOp.inputs else None

    def v(name, default=0.0):
        if src is None:
            return default
        c = src[name]
        return c.eval() if c is not None else default

    g1, g2 = xfader_gains(v('xfader'))
    d1_gain = v('d1_fader', 1.0) * g1
    d2_gain = v('d2_fader', 1.0) * g2
    deck_mix = d2_gain / (d1_gain + d2_gain + 0.001)

    b1 = v('d1_eq_low', 0.5) * d1_gain
    b2 = v('d2_eq_low', 0.5) * d2_gain
    bs = b1 + b2
    b1, b2 = (b1 / bs, b2 / bs) if bs > 1e-6 else (0.0, 0.0)
    low = v('audio_low')

    # 아래는 이펙트 식을 단순하게 하려고 미리 계산하는 값
    filt = v('d1_filter') * (1 - deck_mix) + v('d2_filter') * deck_mix
    fx_decay = (0.80 + 0.17 * v('fx_level')) * v('fx_on')

    out = {
        'd1_gain': d1_gain,
        'd2_gain': d2_gain,
        'deck_mix': deck_mix,
        'd1_bass_w': b1,
        'd2_bass_w': b2,
        'd1_pulse': low * b1,
        'd2_pulse': low * b2,
        # 덱 색을 deck_mix로 섞은 색 (VA-01, 실루엣 VA-10)
        'mix_r': v('d1_r', 1) * (1 - deck_mix) + v('d2_r', 1) * deck_mix,
        'mix_g': v('d1_g', 1) * (1 - deck_mix) + v('d2_g', 1) * deck_mix,
        'mix_b': v('d1_b', 1) * (1 - deck_mix) + v('d2_b', 1) * deck_mix,
        # VA-05 필터: 음수 = 블러, 양수 = 외곽선
        'filter_mix': filt,
        'blur_amt': max(0.0, -filt),
        'edge_amt': max(0.0, filt),
        # VA-06 스크래치 -> RGB 분리
        'scratch_mix': max(v('d1_scratch'), v('d2_scratch')),
        # VA-07 잔상 유지율 (fx_on이 0이면 0 = 잔상 없음)
        'fx_decay': fx_decay,
    }

    scriptOp.clear()
    scriptOp.numSamples = 1
    for name, val in out.items():
        scriptOp.appendChan(name)[0] = val
    return
