"""Actual original Pokémon Red LCD captures: 3 synthetic Day Care RAM states."""
from pathlib import Path
from pyboy import PyBoy
from PIL import Image,ImageDraw,ImageFont
import subprocess,sys
if len(sys.argv)!=4: raise SystemExit("Usage: python render_daycare_glitch_video.py ROM.gb prepared.state OUT.mp4")
ROM, STATE, OUT = sys.argv[1:]
cases=[('CONTROL: LEVEL 100',1059860),('LEVEL 0 WINDOW',0xFFFF74),('UNDERFLOW: SOFTLOCK',0xFFFFCA)]
games=[];counters=[]
for name,exp in cases:
 p=PyBoy(ROM,window='null',sound_emulated=False);p.set_emulation_speed(0)
 with open(STATE,'rb') as f:p.load_state(f)
 for i,v in enumerate(exp.to_bytes(3,'big')):p.memory[0xda6d+i]=v
 c={'loop':0,'return':0,'wraps':0,'level':None}
 def inc(s, pp=p):
  s['loop']+=1
  if pp.register_file.D==0:s['wraps']+=1
 def ret(s,pp=p):
  s['return']+=1;s['level']=pp.register_file.D
 p.hook_register(22,0x4f4e,inc,c);p.hook_register(22,0x4f69,ret,c)
 games.append(p);counters.append(c)
WIDTH,HEIGHT=1490,570; N=370;FPS=24
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{WIDTH}x{HEIGHT}','-r',str(FPS),'-i','-', '-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',OUT]
f=subprocess.Popen(cmd,stdin=subprocess.PIPE)
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';big=ImageFont.truetype(fontfile,17);small=ImageFont.truetype(fontfile,13);title=ImageFont.truetype(fontfile,22)
for tick in range(N):
 for p in games:
  if tick in [10,110,180,240,300]:p.button_press('a')
  if tick in [19,119,189,249,309]:p.button_release('a')
  p.tick(1,render=True,sound=False)
 image=Image.new('RGB',(WIDTH,HEIGHT),(13,19,28));d=ImageDraw.Draw(image)
 d.text((26,13),'Pokemon Red: THREE Day Care outcomes, original game emulator',font=title,fill='#f0f5ff')
 d.text((26,44),'Identical original ROM + full PyBoy; deliberately constructed Day Care RAM states (not an unassisted playthrough).',font=small,fill='#b3c6d8')
 for index,((name,exp),p,c) in enumerate(zip(cases,games,counters)):
  x=14+index*494
  d.rounded_rectangle((x,76,x+477,551),radius=9,fill='#202c3d')
  d.text((x+11,91),name,font=big,fill='#ffffff')
  d.text((x+11,119),f'EXP = 0x{exp:06X}',font=small,fill='#d4deef')
  im=p.screen.image.convert('RGB').resize((432,389),Image.Resampling.NEAREST)
  image.paste(im,(x+22,142))
  d.text((x+13,533),f'Checks: {c["loop"]}  Wraps: {c["wraps"]}  Returns: {c["return"]}',font=small,fill='#ffffff')
 f.stdin.write(image.tobytes())
f.stdin.close();ret=f.wait()
for p in games:p.stop()
assert ret==0
print('video',OUT,Path(OUT).stat().st_size,'end states',counters)
