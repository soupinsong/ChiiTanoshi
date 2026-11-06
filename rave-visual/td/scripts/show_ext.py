# 쇼 컨트롤러 Extension. TD 위치: /project1/show/show_ext (Text DAT)
# /project1/show (Base COMP) > Extensions 페이지:
#   Object 0 = op('./show_ext').module.ShowExt(me),  Promote 켬
# 호출: op('/project1/show').Toggle() 등
#
# 매 프레임 Update()가 불려야 한다 (frame_callbacks.py의 onFrameStart).
# 결과는 /project1/show/show_out (Constant CHOP)에 쓰고, show COMP의 Out CHOP으로 ctrl에 합쳐진다.

import math

STATES = ('CENTER_ONLY', 'COUNTDOWN', 'SIDE_ACTIVE')
STATE_ID = {s: i for i, s in enumerate(STATES)}

COUNTDOWN_SEC = 3.0     # SH-02
SIDE_FADE_SEC = 0.5     # SIDE_ACTIVE -> CENTER_ONLY 페이드아웃
XF_END = 0.02           # VA-09: 크로스페이더가 이 값 이하/1-이 값 이상이면 "끝"
XF_HOLD_SEC = 1.0       # VA-09: 끝에 이만큼 있으면 곡 전환 완료

OUT = '/project1/show/show_out'
CTRL = '/project1/ctrl'
JOG_ACC = '/project1/jog_acc'
BTN = '/project1/btn'

DEFAULT_SONG = {
    'id': 'default', 'title': '(기본)', 'artist': '',
    'color': '#ffffff', 'center_source': 'dots',
    'side_set': 'default', 'side_rule': {'type': 'burst'},
}

# P1 전까지 쓰는 임시 곡 목록. 덱1은 0번, 덱2는 1번에서 시작
STUB_SETLIST = [
    dict(DEFAULT_SONG, id='stub_a', title='임시 곡 A', color='#ff3fa4'),
    dict(DEFAULT_SONG, id='stub_b', title='임시 곡 B', color='#3fc8ff'),
]


class ShowExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.u = mod('/project1/show/tdutil')
        self.u.setup_constants()

        self._songs = list(STUB_SETLIST)
        self._default = dict(DEFAULT_SONG)
        self._song_idx = [0, 1 % len(self._songs)]

        self._state = 'CENTER_ONLY'
        self._state_t0 = self._now()
        self._last_t = self._now()
        self._side = 0.0
        self._flash_t0 = None
        self._flash_dur = 0.15
        self._flash_rgb = (1.0, 1.0, 1.0)
        self._pulses = set()        # 이번 프레임에 1로 낼 펄스 채널
        self._xf_end = 0            # 지금 크로스페이더가 있는 끝 (0 없음, 1 덱1, 2 덱2)
        self._xf_t0 = 0.0
        self._base_rgb = self.u.hex_to_rgb(self._default['color'])
        self._write()

    # ---- 읽기 전용 속성 ----
    @property
    def State(self):
        return self._state

    @property
    def StateTime(self):
        return self._now() - self._state_t0

    @property
    def SongIndex(self):
        return list(self._song_idx)

    # ---- 상태 기계 (SH-01) ----
    def Toggle(self):
        if self._state == 'CENTER_ONLY':
            self._enter('COUNTDOWN')
        else:
            # COUNTDOWN이면 취소, SIDE_ACTIVE면 페이드아웃 (Update에서 처리)
            self._enter('CENTER_ONLY')
        return self._state

    def SetState(self, state):
        if state not in STATES:
            print('[ShowExt] 알 수 없는 상태:', state)
            return
        self._enter(state)

    def Panic(self):
        # SH-03: 좌우 즉시 끄고 중앙 기본 상태
        self._enter('CENTER_ONLY')
        self._side = 0.0
        self._flash_t0 = None
        self._pulses.add('panic')
        for name in ('fx_on', 'strobe', 'beat_off_x', 'beat_off_y'):
            self.u.set_value(BTN, name, 0)
        acc = op(JOG_ACC)
        for d in (1, 2):
            self.u.set_value(JOG_ACC, 'd%d_jog_angle' % d, 0.0)
            if acc is not None:
                acc.store('d%d_prev_angle' % d, 0.0)
        print('[ShowExt] PANIC')

    def _enter(self, state):
        prev = self._state
        self._state = state
        self._state_t0 = self._now()
        if state == 'SIDE_ACTIVE':
            self._side = 1.0
            self._pulses.add('jump_reset')      # jump_count 0 (VB 쪽에서 이 펄스를 듣는다)
        print('[ShowExt] %s -> %s' % (prev, state))

    # ---- 플래시 ----
    def Flash(self, color, duration=0.15):
        self._flash_rgb = self.u.hex_to_rgb(color)
        self._flash_dur = max(0.01, float(duration))
        self._flash_t0 = self._now()

    # ---- 곡 세트 (P1에서 완성) ----
    def LoadSetlist(self, path):
        # TODO(P1): JSON 로드, 검증, 오류 시 기본 세트 (ST-01)
        print('[ShowExt] LoadSetlist는 아직 스텁:', path)
        return len(self._songs)

    def AdvanceSong(self, deck, step=1):
        # TODO(P1): 곡 세트 로드 후 동작 확인. 지금은 임시 목록 안에서만 돈다
        i = deck - 1
        self._song_idx[i] = (self._song_idx[i] + int(step)) % len(self._songs)
        song = self.GetSong(deck)
        print('[ShowExt] 덱%d -> %s' % (deck, song.get('title')))
        return song

    def GetSong(self, deck):
        if not self._songs:
            return dict(self._default)
        return self._songs[self._song_idx[deck - 1] % len(self._songs)]

    def OnAirSong(self):
        mix = self.u.chan(op(CTRL), 'deck_mix', 0.0)
        return self.GetSong(2 if mix >= 0.5 else 1)

    def SendSerial(self, cmd):
        # TODO(P1): Serial DAT으로 전송 (7.4절). Serial DAT의 send 메서드 인자를 TD에서 확인
        print('[ShowExt] SendSerial은 아직 스텁:', cmd)

    # ---- 매 프레임 ----
    def Update(self):
        now = self._now()
        dt = max(0.0, now - self._last_t)
        self._last_t = now

        if self._state == 'COUNTDOWN' and now - self._state_t0 >= COUNTDOWN_SEC:
            self._enter('SIDE_ACTIVE')

        if self._state == 'SIDE_ACTIVE':
            self._side = 1.0
        else:
            self._side = max(0.0, self._side - dt / SIDE_FADE_SEC)

        self._update_base_color(now)
        self._write()

    def _update_base_color(self, now):
        # VA-09: 크로스페이더가 한쪽 끝에 1초 이상 있으면 기본색을 그 덱 곡 색으로
        xf = self.u.chan(op(CTRL), 'xfader', 0.0)
        end = 1 if xf <= XF_END else (2 if xf >= 1 - XF_END else 0)
        if end != self._xf_end:
            self._xf_end = end
            self._xf_t0 = now
        elif end and now - self._xf_t0 >= XF_HOLD_SEC:
            self._base_rgb = self.u.hex_to_rgb(self.GetSong(end).get('color'))

    def _write(self):
        now = self._now()
        u = self.u
        elapsed = now - self._state_t0
        if self._state == 'COUNTDOWN':
            countdown = max(1, math.ceil(COUNTDOWN_SEC - elapsed))   # 3, 2, 1
        else:
            countdown = 0

        flash = 0.0
        if self._flash_t0 is not None:
            flash = 1.0 - (now - self._flash_t0) / self._flash_dur
            if flash <= 0:
                flash = 0.0
                self._flash_t0 = None

        u.set_value(OUT, 'state', STATE_ID[self._state])
        u.set_value(OUT, 'state_time', round(elapsed, 2))
        u.set_value(OUT, 'countdown', countdown)
        u.set_value(OUT, 'side_on', self._side)
        for name in ('jump_reset', 'panic'):
            u.set_value(OUT, name, 1 if name in self._pulses else 0)
        self._pulses.clear()
        u.set_value(OUT, 'flash', flash)
        for k, v in zip('rgb', self._flash_rgb):
            u.set_value(OUT, 'flash_' + k, v)
        for d in (1, 2):
            rgb = u.hex_to_rgb(self.GetSong(d).get('color'))
            for k, v in zip('rgb', rgb):
                u.set_value(OUT, 'd%d_%s' % (d, k), v)
        for k, v in zip('rgb', self._base_rgb):
            u.set_value(OUT, 'base_' + k, v)

    def _now(self):
        return absTime.seconds
