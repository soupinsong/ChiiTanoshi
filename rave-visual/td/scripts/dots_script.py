# 중앙 점 구름 Script CHOP 본문 (VA-01~04, VA-06 회전). TD 위치: /project1/center/dots 의 callbacks DAT
# 입력 0 = /project1/ctrl. 출력은 점 하나당 샘플 하나: tx ty tz scale cr cg cb
# Geometry COMP의 Instancing에 이 CHOP을 넣는다 (가이드 4부).
# 기존 점 구름 프로토타입을 쓸 거면 이 파일 대신 같은 매핑만 옮기면 된다.
# TD 템플릿의 onCook def 줄은 그대로 두고 본문만 붙여 넣는다.

import math
import random

N = 600                 # 최대 점 개수
BASE_SIZE = 0.012       # 점 기본 크기 (화면 높이 2 기준)
SPREAD_X = 0.9          # 중앙 화면이 세로로 약간 긴 편이라 가로를 좁힌다

_pts = None


def _points():
    # 점마다 고정 위치와 두 개의 난수(u: 덱 배정 순서, w: 개수 순서)
    global _pts
    if _pts is None:
        rnd = random.Random(7)
        _pts = []
        for _ in range(N):
            r = math.sqrt(rnd.random()) * 0.95
            a = rnd.random() * 2 * math.pi
            _pts.append((r * math.cos(a) * SPREAD_X, r * math.sin(a), rnd.random(), rnd.random()))
    return _pts


def onCook(scriptOp):
    # ↑ 이 def 줄은 TD 템플릿의 것을 그대로 쓴다. 아래 본문만 붙여 넣는다.
    src = scriptOp.inputs[0] if scriptOp.inputs else None

    def v(name, default=0.0):
        if src is None:
            return default
        c = src[name]
        return c.eval() if c is not None else default

    mix = v('deck_mix')
    deck = {}
    for n in (1, 2):
        p = 'd%d_' % n
        a = math.radians(v(p + 'jog_angle'))
        deck[n] = {
            'low': v(p + 'eq_low', 0.5),
            'mid': v(p + 'eq_mid', 0.5),
            'hi': v(p + 'eq_hi', 0.5),
            'fader': v(p + 'fader', 1.0),
            'pulse': v(p + 'pulse'),
            'cos': math.cos(a), 'sin': math.sin(a),
            'rgb': (v(p + 'r', 1.0), v(p + 'g', 1.0), v(p + 'b', 1.0)),
        }

    cols = {k: [] for k in ('tx', 'ty', 'tz', 'scale', 'cr', 'cg', 'cb')}
    for x, y, u, w in _points():
        d = deck[2 if u < mix else 1]                       # VA-01: deck_mix만큼 덱2 색
        visible = w < 0.15 + 0.85 * d['mid']                # VA-03 MID = 개수
        size = BASE_SIZE * (0.4 + 1.2 * d['low']) * (1.0 + 2.0 * d['pulse'])  # LOW = 크기, VA-02 펄스
        bright = (0.3 + 1.4 * d['hi']) * d['fader']         # HIGH = 밝기, VA-04 페이더
        cols['tx'].append(x * d['cos'] - y * d['sin'])      # VA-06 조그 각도만큼 회전
        cols['ty'].append(x * d['sin'] + y * d['cos'])
        cols['tz'].append(0.0)
        cols['scale'].append(size if visible else 0.0)
        for k, c in zip(('cr', 'cg', 'cb'), d['rgb']):
            cols[k].append(c * bright)

    scriptOp.clear()
    scriptOp.numSamples = N
    for name, vals in cols.items():
        scriptOp.appendChan(name).vals = vals
    return
