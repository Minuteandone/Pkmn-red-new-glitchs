#!/usr/bin/env python3
"""Original Pokémon Red ROM opcode test for Bide damage cleanup asymmetry.

Checks 1,024 high/low-byte starting states using original LR35902
instructions. This is NOT a linked pair of Game Boy emulators.
Run: python tests/test_bide_faint_reset.py 'Pokemon Red.gb' results.json
"""
import hashlib, json, sys
from pathlib import Path
SHA1="ea9bcae617fdf159b045185467ae58b2e4a48b9a"
FAINT_ENEMY=bytes.fromhex("af ea 74 d0 21 65 d0 22 22 22 22 77")
FAINT_PLAYER=bytes.fromhex("21 05 cd 22 77 ea 18 d0")
BIDE_START=bytes.fromhex("21 62 d0 11 74 d0 01 6a d0")

def execute(rom,pc,ram,count,a=0):
    hl=0
    for _ in range(count):
        op=rom[pc]
        pc+=1
        if op==0xAF: # XOR A
            a=0
        elif op==0xEA: # LD [nn],A
            n=rom[pc]|(rom[pc+1]<<8)
            pc+=2
            ram[n]=a
        elif op==0x21: # LD HL,nn
            hl=rom[pc]|(rom[pc+1]<<8)
            pc+=2
        elif op==0x22: # LD [HL+],A
            ram[hl]=a
            hl=(hl+1)&65535
        elif op==0x77: # LD [HL],A
            ram[hl]=a
        else:
            raise AssertionError(f"Unsupported opcode {op:02X}")
    return pc

def main(rom_file,out_file):
    rom=rom_file.read_bytes()
    assert len(rom)==1048576 and hashlib.sha1(rom).hexdigest()==SHA1
    locations=[]
    for signature,expected in ((FAINT_ENEMY,0x3C584),
                               (FAINT_PLAYER,0x3C763),
                               (BIDE_START,0x3F6E5)):
        location=rom.find(signature)
        assert location==expected and rom.find(signature,location+1)<0
        locations.append(location)
    mismatch=0
    for hi in (0,1,12,255):
        for lo in range(256):
            own=bytearray(65536)
            other=bytearray(65536)
            own[0xD074:0xD076]=bytes((hi,lo))
            other[0xCD05:0xCD07]=bytes((hi,lo))
            assert execute(rom,locations[0],own,2)==locations[0]+4
            assert execute(rom,locations[1],other,3)==locations[1]+5
            assert own[0xD074:0xD076]==bytes((0,lo))
            assert other[0xCD05:0xCD07]==bytes((0,0))
            mismatch+=lo!=0
    assert mismatch==1020
    report={
        "rom_sha1":SHA1,
        "rom_offsets":[hex(v) for v in locations],
        "tested_states":1024,
        "divergent_cleanup_results":mismatch,
        "example":{
            "before_bide": "0x013A",
            "after_faint_enemy":"0x003A",
            "after_faint_player":"0x0000",
            "additional_damage_received":5,
            "hypothetical_unleashed_damage_own":126,
            "hypothetical_unleashed_damage_other":10
        },
        "warning":"No two-console link battle emulation performed. This previously documented bug can lead to desync in appropriate active-Bide scenarios."
    }
    out_file.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: 1024 original-ROM memory-reset tests; 1020 mismatches")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: test_bide_faint_reset.py original.gb results.json")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
