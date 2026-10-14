#!/usr/bin/env python3
"""PyBoy: show that walking 54 steps rescues an underflowed Day Care Pokemon.

Usage:
  python tests/test_daycare_rescue_walk.py ORIGINAL.gb PREPARED_DAYCARE.state output.json

PREPARED_DAYCARE.state is produced locally by the existing
tests/test_daycare_xp_boundary_pyboy.py. No ROM or state is distributed here.
The initial EXP bytes are constructed in RAM; subsequent changes come from
ordinary D-pad overworld steps in the unmodified original game.
"""
import hashlib, io, json, sys
from pathlib import Path
from pyboy import PyBoy

SHA1 = "ea9bcae617fdf159b045185467ae58b2e4a48b9a"
EXP_ADDR = 0xDA6D

def xp(p):
    return int.from_bytes(bytes(p.memory[EXP_ADDR:EXP_ADDR+3]), "big")

def press_step(p, direction):
    p.button_press(direction)
    p.tick(10, render=False, sound=False)
    p.button_release(direction)
    p.tick(28, render=False, sound=False)

def speak(p, snapshot):
    p.load_state(io.BytesIO(snapshot))
    press_step(p, "up")  # face caretaker without walking into occupied tile
    result = {"level_checks":0, "level_returns":0, "counter_wraps":0}
    def loop(c):
        c["level_checks"] += 1
        if p.register_file.D == 0:
            c["counter_wraps"] += 1
    def ret(c):
        c["level_returns"] += 1
    p.hook_register(22, 0x4F4E, loop, result)
    p.hook_register(22, 0x4F69, ret, result)
    p.button_press("a")
    p.tick(8, render=False, sound=False)
    p.button_release("a")
    p.tick(350, render=True, sound=False)
    result["recalculated_level"] = p.memory[0xDA62]
    p.hook_deregister(22, 0x4F4E)
    p.hook_deregister(22, 0x4F69)
    return result

def test(rom, state, outfile):
    raw = rom.read_bytes()
    assert len(raw) == 1048576 and hashlib.sha1(raw).hexdigest() == SHA1
    p = PyBoy(str(rom), window="null", sound_emulated=False)
    p.set_emulation_speed(0)
    with state.open("rb") as stream:
        p.load_state(stream)
    assert (p.memory[0xD35E],p.memory[0xD362],p.memory[0xD361]) == (0x48,2,4)
    assert p.memory[0xDA48] == 1
    for i, b in enumerate((0xFF,0xFF,0xCA)):
        p.memory[EXP_ADDR+i] = b
    checkpoints, saves = [], {}
    for i, direction in enumerate(["right","down","left","up"] * 16, start=1):
        press_step(p, direction)
        if i in (53,54,55,57):
            checkpoints.append({"input_actions":i,
                                "exp_hex":f"0x{xp(p):06X}",
                                "xy":[p.memory[0xD362],p.memory[0xD361]]})
            if i in (53,57):
                buf=io.BytesIO()
                p.save_state(buf)
                saves[i]=buf.getvalue()
    assert [v["exp_hex"] for v in checkpoints] == [
        "0xFFFFFE","0xFFFFFF","0x000000","0x000002"]
    before = speak(p, saves[53])
    after = speak(p, saves[57])
    assert before["level_checks"] > 512 and before["counter_wraps"] >= 2
    assert before["level_returns"] == 0
    assert after["level_checks"] == after["level_returns"] == 1
    assert after["recalculated_level"] == 1
    result={"rom_sha1":SHA1, "checkpoints":checkpoints, "pre_wrap":before,
            "post_wrap":after, "successful_steps_until_24bit_wrap":54,
            "limitations":"Initial Day Care state constructed in RAM. The 54 EXP increments were caused by normal game movement; no unassisted Level-1 acquisition was tested."}
    outfile.write_text(json.dumps(result,indent=2)+"\n")
    p.stop()
    print("PASS: 54 successful steps and Day Care level-calculation recovery")
    print(json.dumps(result,indent=2))

if __name__ == "__main__":
    if len(sys.argv)!=4:
        raise SystemExit("Usage: test_daycare_rescue_walk.py ROM.gb PREPARED.state RESULTS.json")
    test(*(Path(value) for value in sys.argv[1:]))
