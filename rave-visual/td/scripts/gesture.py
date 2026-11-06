# 주먹 -> 편 손 토글 판정 (7.5절). TD 위치: /project1/show/gesture (Text DAT)
# frame_callbacks.py가 매 프레임 update()를 부른다.
# 판정 로직(GestureDetector)은 TD 없이 돈다: python td/scripts/gesture.py 로 자체 테스트

SCORE_MIN = 0.6     # GS-02
FIST_HOLD = 0.5     # 주먹 유지 시간
OPEN_WINDOW = 0.7   # 주먹이 끝난 뒤 이 시간 안에 편 손
LOCKOUT = 3.0       # 토글 후 판정 정지
FIST_GAP = 0.1      # 주먹 인식이 이 시간 이하로 끊기는 건 이어진 것으로 본다 (한두 프레임 오인식 대비)

FIST, PALM = 'Closed_Fist', 'Open_Palm'

SHOW = '/project1/show'
OUT = '/project1/show/gesture_out'
# TODO(TD에서 확인): MediaPipe 플러그인의 제스처 결과를 가리키는 오퍼레이터.
#   가이드 6부대로 플러그인 출력을 Select DAT 'mp_gesture'로 끌어온다.
MP_GESTURE = '/project1/mp_gesture'


class GestureDetector:
    def __init__(self):
        self.reset()
        self.lock_until = -1.0

    def reset(self):
        self.fist_start = None
        self.last_fist = None

    def step(self, now, label, score):
        """한 프레임 판정. label/score는 가장 큰 손의 결과(손이 없으면 None).
        반환: (toggle 0/1, hold 0~1)"""
        if now < self.lock_until:
            self.reset()
            return 0, 0.0

        ok = label is not None and score >= SCORE_MIN
        if ok and label == FIST:
            if self.last_fist is None or now - self.last_fist > FIST_GAP:
                self.fist_start = now
            self.last_fist = now
        elif self.fist_start is not None:
            held = self.last_fist - self.fist_start
            since = now - self.last_fist
            if held >= FIST_HOLD:
                if ok and label == PALM and since <= OPEN_WINDOW:
                    self.reset()
                    self.lock_until = now + LOCKOUT
                    return 1, 1.0
                if since > OPEN_WINDOW:
                    self.reset()
            elif since > FIST_GAP:
                self.reset()

        if self.fist_start is None:
            return 0, 0.0
        return 0, min(1.0, (self.last_fist - self.fist_start) / FIST_HOLD)


def read_hands():
    """MediaPipe 결과 -> [(label, score, size), ...]
    TODO(TD에서 확인): 플러그인 출력 형식에 맞게 고친다. 지금은 아래 형식의 표를 가정한다.
      첫 줄 머리글에 'gesture'(또는 'category', 'name')와 'score' 열, 손 하나당 한 줄.
      'size' 열이 없으면 첫 번째 손을 쓴다."""
    t = op(MP_GESTURE)
    if t is None or t.numRows < 2:
        return []
    head = [str(c.val).lower() for c in t.row(0)]

    def col(*keys):
        for i, h in enumerate(head):
            if any(k in h for k in keys):
                return i
        return None

    ci, si, zi = col('gesture', 'category', 'name'), col('score'), col('size')
    if ci is None or si is None:
        return []
    hands = []
    for r in range(1, t.numRows):
        try:
            size = float(t[r, zi].val) if zi is not None else 0.0
            hands.append((str(t[r, ci].val), float(t[r, si].val), size))
        except (TypeError, ValueError):
            pass
    return hands


_det = GestureDetector()


def update():
    # 매 프레임 호출. gesture_out에 쓰고, 토글이면 ShowExt.Toggle()
    u = mod('/project1/show/tdutil')
    hands = read_hands()
    label, score = None, 0.0
    if hands:
        label, score, _ = max(hands, key=lambda h: h[2])   # 가장 큰 손 하나
    toggle, hold = _det.step(absTime.seconds, label, score)
    u.set_value(OUT, 'gesture_toggle', toggle)
    u.set_value(OUT, 'gesture_hold', hold)
    u.set_value(OUT, 'hand_found', 1 if hands else 0)
    if toggle:
        op(SHOW).Toggle()


if __name__ == '__main__':
    # TD 밖 자체 테스트 (60fps 가정)
    def run_seq(seq, t0=0.0):
        d = GestureDetector()
        t, toggles = t0, []
        for dur, label, score in seq:
            end = t + dur
            while t < end - 1e-9:
                tg, _ = d.step(t, label, score)
                if tg:
                    toggles.append(round(t, 2))
                t += 1 / 60
        return toggles

    assert len(run_seq([(0.6, FIST, 0.9), (0.3, None, 0), (0.2, PALM, 0.9)])) == 1, '기본 토글'
    assert run_seq([(0.3, FIST, 0.9), (0.3, PALM, 0.9)]) == [], '주먹이 짧음'
    assert run_seq([(0.6, FIST, 0.9), (0.9, None, 0), (0.2, PALM, 0.9)]) == [], '0.7초 초과'
    assert run_seq([(0.6, FIST, 0.5), (0.2, PALM, 0.9)]) == [], '점수 낮음'
    assert len(run_seq([(0.6, FIST, 0.9), (0.2, PALM, 0.9),
                        (0.6, FIST, 0.9), (0.2, PALM, 0.9)])) == 1, '3초 판정 정지'
    assert len(run_seq([(0.6, FIST, 0.9), (0.2, PALM, 0.9), (3.0, None, 0),
                        (0.6, FIST, 0.9), (0.2, PALM, 0.9)])) == 2, '정지 후 다시 토글'
    assert len(run_seq([(0.3, FIST, 0.9), (0.05, None, 0), (0.3, FIST, 0.9),
                        (0.2, PALM, 0.9)])) == 1, '짧은 끊김은 이어짐'
    print('gesture self-test OK')
