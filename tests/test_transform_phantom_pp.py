#!/usr/bin/env python3
"""Reproduce the Transform + Metronome ghost PP cascade on original Pokemon Red.

Usage: python test_transform_phantom_pp.py ROM.gb prepared.state results.json

Use tests/prepare_pyboy_bench_state.py to generate a local prepared.state first.
Runs genuine unmodified ROM routines in PyBoy 2.8.1, but constructs the battle
variables in WRAM. It is not a continuous battle or a linked-console test.
"""
from pathlib import Path
from hashlib import sha1
from pyboy import PyBoy
import sys, json

if len(sys.argv) != 4:
    raise SystemExit("Usage: test_transform_phantom_pp.py ROM.gb prepared.state results.json")
ROM, STATE, OUTPUT = [Path(v) for v in sys.argv[1:]]
SHA1 = "ea9bcae617fdf159b045185467ae58b2e4a48b9a"
raw = ROM.read_bytes()
assert len(raw) == 1048576 and sha1(raw).hexdigest() == SHA1

def setup():
    p = PyBoy(str(ROM), window="null", sound_emulated=False)
    p.set_emulation_speed(0)
    with STATE.open("rb") as f:
        p.load_state(f)
    m = p.memory
    m[0x2000] = 15
    for address,values in (
        (0xD173, [0x90,0,0,0]),  # real Ditto's sole move: Transform
        (0xD188, [0,0,0,0]),     # party PP
        (0xD01C, [0x90,0,0x76,0]), # copied Metronome in third move slot
        (0xD02D, [0,0,5,0]),     # temporary copied move PP
    ):
        for i,v in enumerate(values):
            m[address+i] = v
    m[0xCC2E] = 2               # player move index 2
    m[0xCC2F] = 0               # first party Pokémon
    m[0xFFF3] = 0               # player turn
    m[0xD06D] = 0               # no existing disabled move
    m[0xC100] = 0x18            # safe loop at test return address
    m[0xC101] = 0xFE
    return p

def run_at(p, pc):
    p.register_file.SP = 0xC2F0
    p.memory[0xC2F0] = 0
    p.memory[0xC2F1] = 0xC1
    p.register_file.PC = pc

def pp_increment():
    p=setup()
    run_at(p,0x6373) # original IncrementMovePP in ROM bank 15
    p.tick(1,render=False,sound=False)
    m=p.memory
    moves=list(m[0xD173:0xD177])
    pp=list(m[0xD188:0xD18C])
    copied=list(m[0xD02D:0xD031])
    assert p.register_file.PC==0xC100
    assert moves==[0x90,0,0,0] and pp==[0,0,1,0] and copied==[0,0,6,0]
    p.stop()
    return {"party_moves":moves,"party_pp":pp,"copied_pp":copied}

def struggle_check(ghost):
    p=setup()
    m=p.memory
    for i,b in enumerate([0,0,int(ghost),0]):
        m[0xD02D+i]=b
    snapshots=[]
    def record(_):
        snapshots.append({"z":bool(p.register_file.F & 0x80),
                          "pp":list(m[0xD02D:0xD031])})
        p.register_file.PC=0xC100
    p.hook_register(15,0x540B,record,None)
    run_at(p,0x53F5) # original AnyMoveToSelect routine
    p.tick(1,render=False,sound=False)
    assert len(snapshots)==1
    assert snapshots[0]["z"] == (not ghost)
    p.stop()
    return snapshots[0]

def disable_check(mode):
    p=setup()
    m=p.memory
    m[0xFFF3]=1 # enemy uses Disable
    pp={"phantom":[0,0,1,0],"empty":[0,0,0,0],
        "real_pp":[1,0,1,0]}[mode]
    for i,b in enumerate(pp):
        m[0xD02D+i]=b
    data={"candidate_checks":0,"valid_selections":0,"test_stopped":False}
    def candidate(d):
        d["candidate_checks"]+=1
        if d["candidate_checks"]>1500:
            d["test_stopped"]=True
            p.register_file.PC=0xC100
    def rng_zero(_):
        # A possible real BattleRandom output; fixes selection to move slot 0.
        p.register_file.A=0
        p.register_file.PC=0x7AAC
    def valid(d):
        d["valid_selections"]+=1
        p.register_file.PC=0xC100
    p.hook_register(15,0x7AA8,candidate,data)
    p.hook_register(15,0x7AA9,rng_zero,None)
    p.hook_register(15,0x7AE1,valid,data)
    run_at(p,0x7A93) # original DisableEffect after accuracy check
    for _ in range(12):
        p.tick(1,render=False,sound=False)
        if p.register_file.PC==0xC100:
            break
    if mode=="phantom":
        assert (data["candidate_checks"],data["valid_selections"],data["test_stopped"]) == (1501,0,True)
    elif mode=="empty":
        assert data["candidate_checks"]==1 and data["valid_selections"]==0
    else:
        assert data["candidate_checks"]==1 and data["valid_selections"]==1
    p.stop()
    return data

result={
    "rom_sha1":SHA1,
    "method":"PyBoy runs isolated genuine original-ROM battle routines with synthesized WRAM, not a whole battle",
    "increment_pp":pp_increment(),
    "struggle_check":{"phantom":struggle_check(True),"no_pp":struggle_check(False)},
    "disable":{"phantom":disable_check("phantom"),
               "empty":disable_check("empty"),
               "real_pp":disable_check("real_pp")}
}
OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
print("PASS: PP mutation, Struggle gate and 1501 Disable candidate checks")
