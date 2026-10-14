#!/usr/bin/env python3
"""Prepare an original Pokemon Red ROM in PyBoy for the Vermilion bench test.
Usage: python prepare_pyboy_bench_state.py ROM.gb bench.state
An instrumented RAM warp enters the map through the game's ORIGINAL EnterMap
routine; the ROM itself is not modified and must not be committed to GitHub.
Requires PyBoy 2.8.1 and an exact Pokemon Red (UE) ROM.
"""
from pathlib import Path
from hashlib import sha1
import sys
from pyboy import PyBoy
SHA1="ea9bcae617fdf159b045185467ae58b2e4a48b9a"

def main(rom,state):
    raw=rom.read_bytes()
    assert len(raw)==1048576 and sha1(raw).hexdigest()==SHA1
    p=PyBoy(str(rom),window="null",sound_emulated=False)
    p.set_emulation_speed(0)
    def tick(n):p.tick(n,render=False,sound=False)
    def tap(k,held,released):
        p.button_press(k);tick(held)
        p.button_release(k);tick(released)
    # Original game boot, choose NEW GAME and skip Oak's introduction.
    tick(2400)
    tap("start",10,10);tick(35)
    tap("a",10,10);tick(65)
    for _ in range(6):
        tap("a",10,10);tick(50)
    for _ in range(180):tap("a",6,11)
    for _ in range(80):tap("a",6,10)
    for _ in range(4):tap("b",15,25)
    tap("down",8,25);tap("left",8,25)
    assert p.memory[0xD35E]==0x26
    # Map data and warp destination; use authentic EnterMap to initialize.
    p.memory[0xD35E]=0x59 # Vermilion Pokemon Center
    p.memory[0xD365]=0x05 # Last map Vermilion City
    p.memory[0xD42F]=0x00 # First Pokecenter entrance warp
    for i,opcode in enumerate((0xFB,0x00,0xC3,0xA6,0x03)):
        p.memory[0xC0F0+i]=opcode # EI; NOP; JP $03A6, RAM only
    p.register_file.PC=0xC0F0
    tick(600)
    assert (p.memory[0xD35E],p.memory[0xD361],p.memory[0xD362])==(0x59,7,3)
    for k in ("left","up","up","left","up"):
        tap(k,10,27)
    assert (p.memory[0xD362],p.memory[0xD361])==(1,4)
    p.tick(1,render=True,sound=False)
    with state.open("wb") as f:p.save_state(f)
    p.screen.image.save(str(state.with_suffix(".png")))
    p.stop()
    print("PASS: exact original ROM, in-game Pokecenter loaded, x=1 y=4")

if __name__=="__main__":
    main(*(Path(s) for s in sys.argv[1:]))
