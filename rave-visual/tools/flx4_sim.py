# FLX4 가상 컨트롤러: 실제 DDJ-FLX4와 같은 MIDI 메시지를 loopMIDI 포트로 보낸다.
# 필요: loopMIDI(포트 하나 생성), pip install mido python-rtmidi
import tkinter as tk
import mido

PORT_KEYWORD = "loopMIDI"   # loopMIDI에서 만든 포트 이름 일부

# MIDI 채널은 1부터 센 번호 (mido에는 -1 해서 넘김)
D_CH = {1: 1, 2: 2}         # 덱 채널
MIX_CH = 7                  # 크로스페이더, 필터
FX_CH = 5                   # Beat FX
PAD_CH = {1: 8, 2: 10}      # 패드 (덱2는 9가 아니라 10)

DECK_CC = {"TRIM": 0x04, "EQ HI": 0x07, "EQ MID": 0x0B, "EQ LOW": 0x0F,
           "CH FADER": 0x13, "TEMPO": 0x00}
DECK_NOTE = {"PLAY": 0x0B, "CUE": 0x0C, "SYNC": 0x58}
PAD_BASE = {"HOT CUE": 0x00, "PAD FX": 0x10, "BEAT JUMP": 0x20, "SAMPLER": 0x30}
JOG_SIDE, JOG_TOP, JOG_TOUCH = 0x21, 0x22, 0x36

def open_port():
    names = mido.get_output_names()
    for n in names:
        if PORT_KEYWORD.lower() in n.lower():
            print("출력 포트:", n)
            return mido.open_output(n)
    raise SystemExit(f"'{PORT_KEYWORD}' 포트 없음. 현재 포트: {names}")

out = open_port()

def cc(ch, num, val):
    # 실제 기기처럼 MSB(num) + LSB(num+0x20) 두 개를 보낸다
    out.send(mido.Message("control_change", channel=ch - 1, control=num, value=val))
    if num < 0x20:
        out.send(mido.Message("control_change", channel=ch - 1, control=num + 0x20, value=0))

def note(ch, num, on):
    # FLX4는 note_off를 안 쓰고 velocity 0으로 뗌을 보낸다
    out.send(mido.Message("note_on", channel=ch - 1, note=num, velocity=127 if on else 0))

root = tk.Tk()
root.title("FLX4 simulator")

def slider(parent, label, ch, num, init, col, row):
    s = tk.Scale(parent, from_=127, to=0, length=140, label=label,
                 command=lambda v: cc(ch, num, int(float(v))))
    s.set(init)
    s.grid(column=col, row=row, padx=2)

def hold_button(parent, label, ch, num, col, row, width=7):
    b = tk.Button(parent, text=label, width=width)
    b.bind("<ButtonPress-1>", lambda e: note(ch, num, True))
    b.bind("<ButtonRelease-1>", lambda e: note(ch, num, False))
    b.grid(column=col, row=row, padx=1, pady=1)

# 조그: 슬라이더 값만큼 계속 돌린다 (0이면 정지). 64가 정지, 65 이상 정방향
jog_speed = {1: tk.IntVar(value=0), 2: tk.IntVar(value=0)}
jog_mode = {1: tk.StringVar(value="SIDE"), 2: tk.StringVar(value="SIDE")}

def jog_tick():
    for d in (1, 2):
        v = jog_speed[d].get()
        if v:
            num = JOG_SIDE if jog_mode[d].get() == "SIDE" else JOG_TOP
            out.send(mido.Message("control_change", channel=D_CH[d] - 1,
                                  control=num, value=max(0, min(127, 64 + v))))
    root.after(20, jog_tick)

def deck_frame(d, col):
    f = tk.LabelFrame(root, text=f"DECK {d}")
    f.grid(column=col, row=0, padx=6, pady=6, sticky="n")
    inits = {"TRIM": 64, "EQ HI": 64, "EQ MID": 64, "EQ LOW": 64, "CH FADER": 127, "TEMPO": 64}
    for i, (name, num) in enumerate(DECK_CC.items()):
        slider(f, name, D_CH[d], num, inits[name], i, 0)
    for i, (name, num) in enumerate(DECK_NOTE.items()):
        hold_button(f, name, D_CH[d], num, i, 1)

    j = tk.Frame(f); j.grid(column=0, row=2, columnspan=6, pady=4)
    tk.Label(j, text="JOG").pack(side="left")
    tk.Scale(j, from_=-20, to=20, orient="horizontal", length=200,
             variable=jog_speed[d]).pack(side="left")
    tk.Button(j, text="정지", command=lambda: jog_speed[d].set(0)).pack(side="left")
    tk.OptionMenu(j, jog_mode[d], "SIDE", "TOP").pack(side="left")
    t = tk.Button(j, text="TOUCH")
    t.bind("<ButtonPress-1>", lambda e: note(D_CH[d], JOG_TOUCH, True))
    t.bind("<ButtonRelease-1>", lambda e: note(D_CH[d], JOG_TOUCH, False))
    t.pack(side="left")

    p = tk.Frame(f); p.grid(column=0, row=3, columnspan=6)
    mode = tk.StringVar(value="HOT CUE")
    tk.OptionMenu(p, mode, *PAD_BASE.keys()).grid(column=0, row=0, rowspan=2)
    for i in range(8):
        b = tk.Button(p, text=f"PAD{i+1}", width=5)
        b.bind("<ButtonPress-1>", lambda e, i=i: note(PAD_CH[d], PAD_BASE[mode.get()] + i, True))
        b.bind("<ButtonRelease-1>", lambda e, i=i: note(PAD_CH[d], PAD_BASE[mode.get()] + i, False))
        b.grid(column=1 + i % 4, row=i // 4)

deck_frame(1, 0)

m = tk.LabelFrame(root, text="MIXER / FX")
m.grid(column=1, row=0, padx=6, pady=6, sticky="n")
slider(m, "FILTER 1", MIX_CH, 0x17, 64, 0, 0)
slider(m, "FILTER 2", MIX_CH, 0x18, 64, 1, 0)
slider(m, "FX LEVEL", FX_CH, 0x02, 0, 2, 0)
hold_button(m, "FX ON", FX_CH, 0x47, 0, 1)
hold_button(m, "FX SEL", FX_CH, 0x63, 1, 1)
xf = tk.Scale(m, from_=0, to=127, orient="horizontal", length=220, label="CROSSFADER",
              command=lambda v: cc(MIX_CH, 0x1F, int(float(v))))
xf.set(0)
xf.grid(column=0, row=2, columnspan=3)

deck_frame(2, 2)
root.after(20, jog_tick)
root.mainloop()
