#!/usr/bin/env python3
"""Read-only instruction-level Pokémon Red bench-text control-flow test.

Execute the actual ROM's conditional jumps, comparisons and table reads.
Deliberately stop at VRAM ($8000): not a whole-console emulator.
Usage: python tests/test_bench_text_rom.py 'Pokemon Red.gb'
"""
from hashlib import sha1
from pathlib import Path
import sys

DIGEST = "ea9bcae617fdf159b045185467ae58b2e4a48b9a"
SIG = bytes.fromhex("21 7e 64 fa 5e d3 47 2a fe ff c8 b8 28 04 23 23 18 f5 2a 47 fa 09 c1 b8 20 ed 7e c3 f5 3e")
BASE = 0x60000  # bank 24, at CPU 0x4000

def trace(rom, map_id, facing):
    pc, a, b, hl, zero, steps = 0x6460, 0, 0, 0, False, 0
    ram = {0xD35E: map_id, 0xC109: facing}
    def mem(addr):
        if addr in ram: return ram[addr]
        if 0x4000 <= addr < 0x8000: return rom[BASE + addr - 0x4000]
        raise AssertionError("Unexpected memory read " + hex(addr))
    def byte():
        nonlocal pc
        x = mem(pc)
        pc += 1
        return x
    def word():
        low, high = byte(), byte()
        return low | (high << 8)
    def branch():
        nonlocal pc
        offset = byte()
        pc = (pc + (offset if offset < 128 else offset - 256)) & 65535
    for _ in range(30000):
        op = byte()
        steps += 1
        if op == 0x21: hl = word() # LD HL,nn
        elif op == 0xFA: a = mem(word()) # LD A,[nn]
        elif op == 0x47: b = a # LD B,A
        elif op == 0x2A: # LD A,[HL+]
            if hl >= 0x8000: return ("VRAM", steps, hl)
            a = mem(hl)
            hl += 1
        elif op == 0xFE: zero = (a == byte()) # CP n
        elif op == 0xC8:
            if zero: return ("RET", steps, hl) # RET Z
        elif op == 0xB8: zero = a == b # CP B
        elif op == 0x28: # JR Z,e
            if zero: branch()
            else: pc += 1
        elif op == 0x23: hl += 1 # INC HL
        elif op == 0x18: branch() # JR e
        elif op == 0x20: # JR NZ,e
            if not zero: branch()
            else: pc += 1
        elif op == 0x7E: # LD A,[HL]
            if hl >= 0x8000: return ("VRAM", steps, hl)
            a = mem(hl)
        elif op == 0xC3: # JP text routine (stop)
            assert word() == 0x3EF5
            return ("TEXT_" + format(a, "02X"), steps, hl)
        else: raise AssertionError("Unexpected opcode " + hex(op))
    raise AssertionError("Exceeded instruction ceiling")

def main(path):
    rom = Path(path).read_bytes()
    assert len(rom) == 1048576 and sha1(rom).hexdigest() == DIGEST
    assert rom.find(SIG) == 0x62460 and rom.find(SIG, 0x62461) < 0
    table = 0x6247E
    assert rom[table + 36] == 0xFF
    records = [rom[table + 3*i:table + 3*i + 3] for i in range(12)]
    for i, (map_id, expected, text_id) in enumerate(records):
        assert expected == 8
        correct = trace(rom, map_id, 8)
        mismatch = trace(rom, map_id, 4)
        assert correct[0] == "TEXT_" + format(text_id, "02X"), (i,correct)
        assert mismatch == ("VRAM",18790,0x8001), (i,mismatch)
        print(f"{i:2d} map={map_id:02X} left={correct[0]} up={mismatch}")
    print("PASS: 12 legitimate left-facing matches; 12 upward-facing overreads into VRAM.")
    print("VRAM behavior unknown. No full-game emulation was performed.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Pokemon Red.gb")
