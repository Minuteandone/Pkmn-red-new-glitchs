#!/usr/bin/env python3
"""Record actual rendered Pokemon Red PyBoy frames for bench dialogue A/B test.

USAGE: python full_emulator_bench_video.py ROM.gb bench.state video.mp4
Use prepare_pyboy_bench_state.py first to generate bench.state.
Requires pyboy, Pillow and ffmpeg. Does not modify or contain the Pokemon ROM.
Output shows the *game screen* in both cases, not a simulated trace.
"""
from pathlib import Path
from hashlib import sha1
from PIL import Image,ImageDraw,ImageFont
from pyboy import PyBoy
import subprocess,sys

SHA1="ea9bcae617fdf159b045185467ae58b2e4a48b9a"
SCENARIOS={
 "control":[(0,"left",True),(10,"left",False),(35,"a",True),(41,"a",False),(210,"a",True),(218,"a",False)],
 "mismatch":[(0,"up",True),(9,"up",False),(36,"left",True),(45,"left",False),
             (74,"down",True),(83,"down",False),(110,"a",True),(116,"a",False),
             (235,"right",True),(245,"right",False)],
}
TOTAL=360
WIDTH,HEIGHT=1120,650

def capture(rom,state,case):
    p=PyBoy(str(rom),window="null",sound_emulated=False)
    p.set_emulation_speed(0)
    with state.open("rb") as f:p.load_state(f)
    events={}
    for when,key,press in SCENARIOS[case]:
        events.setdefault(when,[]).append((key,press))
    hooks=[]
    def bench_callback(context):
        context.append((p.frame_count,p.memory[0xD35E],p.memory[0xC109]))
    p.hook_register(24,0x6460,bench_callback,hooks)
    frames=[]
    for tick in range(TOTAL):
        for key,press in events.get(tick,[]):
            if press:p.button_press(key)
            else:p.button_release(key)
        p.tick(1,render=True,sound=False)
        frames.append((p.screen.image.copy(),p.memory[0xD362],p.memory[0xD361],p.memory[0xC109],len(hooks)))
    p.stop()
    return frames,hooks

def main(rom,state,out):
    raw=rom.read_bytes()
    assert len(raw)==1048576 and sha1(raw).hexdigest()==SHA1
    control,left_calls=capture(rom,state,"control")
    glitch,down_calls=capture(rom,state,"mismatch")
    assert len(left_calls)==len(down_calls)==1
    assert left_calls[0][1:]==(0x59,8),left_calls
    assert down_calls[0][1:]==(0x59,0),down_calls
    assert glitch[300][1]!=glitch[225][1],"No movement after interaction"
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    title=ImageFont.truetype(font,22)
    body=ImageFont.truetype(font,15)
    small=ImageFont.truetype(font,12)
    cmd=["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pixel_format","rgb24",
         "-video_size",f"{WIDTH}x{HEIGHT}","-framerate","30","-i","-",
         "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    ffmpeg=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(TOTAL):
        image=Image.new("RGB",(WIDTH,HEIGHT),(17,23,32))
        d=ImageDraw.Draw(image)
        d.text((32,20),"Pokemon Red: real emulator, bench dialogue comparison",font=title,fill="white")
        d.text((32,53),"Original ROM; game map entered by emulator-assisted warp; video 0.5x speed",font=small,fill=(185,195,207))
        for side,(case,clip) in enumerate((("control",control),("mismatch",glitch))):
            x=34+side*550
            d.rectangle((x,82,x+517,624),fill=(29,39,54))
            label="LEFT: Normal bench dialogue" if side==0 else "RIGHT: Failed interaction from above"
            d.text((x+16,94),label,font=body,fill="white")
            shot,px,py,facing,visits=clip[i]
            image.paste(shot.resize((480,432),Image.Resampling.NEAREST),(x+17,127))
            note=("A opens normal text" if i>=35 else "Face left") if side==0 else \
                 ("Move right: gameplay responsive" if i>=235 else
                  "A does not show text" if i>=110 else "Approach bench from above")
            d.text((x+16,570),note,font=body,fill="white")
            d.text((x+16,597),f"x={px} y={py} facing={facing:02X} bench-hook={visits}",font=small,fill=(192,211,230))
        d.text((32,634),"Control shows text; wrong-facing branch is silent; no emulator freeze observed.",font=small,fill=(200,208,215))
        ffmpeg.stdin.write(image.tobytes())
    ffmpeg.stdin.close()
    assert ffmpeg.wait()==0
    print("PASS: left callback",left_calls,"down callback",down_calls,"video",out)

if __name__=="__main__":
    main(*(Path(v) for v in sys.argv[1:]))
