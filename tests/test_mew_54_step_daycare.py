#!/usr/bin/env python3
"""Replay the 54-step Day Care rescue using synthetic Mew in unchanged Pokemon Red ROM.

Usage: python test_54_step_daycare_rescue.py ROM.gb prepared_daycare.state output_folder
The starting deposited Lv1 Mew and its EXP are synthetic WRAM data
from our earlier research; the player movements, XP accumulation, dialogue
and withdrawals all execute the actual game. NO ROM changes or game code patch.
"""
from pathlib import Path
from hashlib import sha1
import json,sys
from pyboy import PyBoy
SHA1="ea9bcae617fdf159b045185467ae58b2e4a48b9a"
EXP_ADDR=0xDA6D
NAME=[0x8C,0x84,0x96,0x50,0x50,0x50,0x50,0x50,0x50,0x50,0x50] # MEW
def press(p,key,hold=10,release=27):
    p.button_press(key)
    p.tick(hold,render=False,sound=False)
    p.button_release(key)
    p.tick(release,render=False,sound=False)
def setup(p,savestate):
    with savestate.open("rb") as f:p.load_state(f)
    m=p.memory
    assert m[0xD35E]==0x48 and (m[0xD362],m[0xD361])==(2,4)
    assert m[0xDA48]==1 and m[0xDA62]==1
    m[0xDA5F]=0x15 # Mew internal species ID, not Bulbasaur\n    m[0xDA66]=45 # Mew catch-rate byte (does not affect this test)\n    for i,v in enumerate((0xFF,0xFF,0xCA)):m[EXP_ADDR+i]=v
    for i,v in enumerate(NAME):m[0xDA49+i]=v
def main(rom,state,out):
    assert len(rom.read_bytes())==1048576 and sha1(rom.read_bytes()).hexdigest()==SHA1
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for steps in (0,52,54,108):
        p=PyBoy(str(rom),window="null",sound_emulated=False);p.set_emulation_speed(0)
        setup(p,state);m=p.memory
        keys=["left","left","right","right"]*(steps//4)
        if steps%4==2:keys+=["left","right"]
        trace=[int.from_bytes(bytes(m[EXP_ADDR:EXP_ADDR+3]),"big")]
        for i,key in enumerate(keys):
            pos=(m[0xD362],m[0xD361])
            press(p,key)
            assert pos != (m[0xD362],m[0xD361]),(steps,i,key,"blocked")
            trace.append(int.from_bytes(bytes(m[EXP_ADDR:EXP_ADDR+3]),"big"))
            assert trace[-1]==(trace[-2]+1)&0xFFFFFF
        assert (m[0xD362],m[0xD361])==(2,4)
        press(p,"up") # Face caretaker but NPC blocks movement
        assert (m[0xD362],m[0xD361])==(2,4)
        count={"iterations":0,"returns":0}
        def inc(c):c["iterations"]+=1
        def ret(c):c["returns"]+=1
        p.hook_register(22,0x4F4E,inc,count)
        p.hook_register(22,0x4F69,ret,count)
        press(p,"a",8,450)
        p.tick(1,render=True,sound=False)
        p.screen.image.save(out/f"{steps:03d}_steps_dialogue.png")
        assert count["iterations"]>0 and count["returns"]==(0 if steps<54 else 1),count
        entry=dict(steps=steps,exp=f"0x{trace[-1]:06X}",**count,
                   resulting_daycare_level=m[0xDA62])
        if steps>=54:
            for j in range(10):
                press(p,"a",8,110)
                if m[0xD163]==2:break
            assert m[0xDA48]==0 and m[0xD163]==2
            entry["withdrawn_level"]=m[0xD197+33]\n            entry["withdrawn_species"]=m[0xD197]\n            assert entry["withdrawn_species"]==0x15
            entry["money_after_BCD"]=bytes(m[0xD347:0xD34A]).hex()
            assert (entry["withdrawn_level"],entry["money_after_BCD"])==(
                (1,"009899") if steps==54 else (2,"009799"))
            p.tick(1,render=True,sound=False)
            p.screen.image.save(out/f"{steps:03d}_steps_withdrawn.png")
        print("PASS:",entry,flush=True);results.append(entry);p.stop()
    (out/"results.json").write_text(json.dumps({"rom_sha1":SHA1,
       "state":"Synthetic previously deposited Mew, not full Trainer-Fly route",
       "player_progression":"Genuine emulated button presses and real Day Care code",
       "cases":results},indent=2)+"\n")
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("Usage: test_54_step_daycare_rescue.py ROM.gb prepared.state out/")
    main(*(Path(x) for x in sys.argv[1:]))
