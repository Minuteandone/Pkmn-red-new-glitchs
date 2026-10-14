#!/usr/bin/env python3
"""Read-only targeted audit of Pokémon Red. Original tool, no ROM data exported.

Usage: python rom_deep_audit.py '/path/to/Pokemon Red.gb'

This mini-executor supports only the opcodes needed by IncrementDayCareMonExp.
It is deliberately *not* a full Game Boy emulator.
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

EXPECTED_SHA1 = 'ea9bcae617fdf159b045185467ae58b2e4a48b9a'
DAYCARE_SIGNATURE = bytes.fromhex('fa 48 da a7 c8 21 6f da 34 c0 2b 34 c0 2b 34 7e fe 50 d8 3e 50 77 c9')
SLOT_WEIGHTS = (51, 51, 39, 25, 25, 25, 13, 13, 11, 3)
SLOT_TABLE = bytes(v for pair in ((sum(SLOT_WEIGHTS[:i + 1]) - 1, i * 2) for i in range(10)) for v in pair)


def locate_once(data: bytes, pattern: bytes, what: str) -> int:
    pos = data.find(pattern)
    assert pos >= 0, f'{what}: no matching ROM bytes'
    assert data.find(pattern, pos + 1) < 0, f'{what}: signature not unique'
    return pos


def location(offset: int) -> str:
    bank = offset // 0x4000
    addr = offset % 0x4000 + (0x4000 if bank else 0)
    return f'offset 0x{offset:05X}, bank {bank}, CPU 0x{addr:04X}'


def simulated_exp_advance(exp: int, enabled: bool = True) -> int:
    if not enabled:
        return exp
    low = (exp + 1) & 0xFFFF
    high = ((exp >> 16) + (1 if low == 0 else 0)) & 0xFF
    if low == 0 and high >= 0x50:
        high = 0x50
    return (high << 16) | low


def execute_daycare_rom(rom: bytes, offset: int, exp: int, enabled: bool = True) -> int:
    """Execute genuine GB opcodes from the provided ROM, with isolated 64-KiB WRAM.

    ROM instructions validated by signature. Emulates A, HL, Z/C for these only;
    hardware timing, graphics, and the entire game are intentionally out of scope.
    """
    mem = bytearray(0x10000)
    mem[0xDA48] = int(enabled)  # wDayCareInUse
    mem[0xDA6D] = (exp >> 16) & 255  # EXP is stored big-endian
    mem[0xDA6E] = (exp >> 8) & 255
    mem[0xDA6F] = exp & 255
    pc = offset
    a, hl, z, carry = 0, 0, False, False
    for _ in range(64):
        opcode = rom[pc]
        pc += 1
        if opcode == 0xFA:  # ld a, [nn]
            addr = rom[pc] | (rom[pc + 1] << 8)
            pc += 2
            a = mem[addr]
        elif opcode == 0xA7:  # and a
            z = (a == 0)
            carry = False
        elif opcode == 0xC8:  # ret z
            if z:
                break
        elif opcode == 0x21:  # ld hl, nn
            hl = rom[pc] | (rom[pc + 1] << 8)
            pc += 2
        elif opcode == 0x34:  # inc [hl] (C flag unaffected)
            mem[hl] = (mem[hl] + 1) & 255
            z = (mem[hl] == 0)
        elif opcode == 0xC0:  # ret nz
            if not z:
                break
        elif opcode == 0x2B:  # dec hl
            hl = (hl - 1) & 0xFFFF
        elif opcode == 0x7E:  # ld a, [hl]
            a = mem[hl]
        elif opcode == 0xFE:  # cp n
            n = rom[pc]
            pc += 1
            z = (a == n)
            carry = (a < n)
        elif opcode == 0xD8:  # ret c
            if carry:
                break
        elif opcode == 0x3E:  # ld a, n
            a = rom[pc]
            pc += 1
        elif opcode == 0x77:  # ld [hl], a
            mem[hl] = a
        elif opcode == 0xC9:  # ret
            break
        else:
            raise AssertionError(f'unexpected opcode 0x{opcode:02x} at offset 0x{pc-1:x}')
    else:
        raise AssertionError('routine did not return within 64 opcodes')
    return mem[0xDA6D] * 0x10000 + mem[0xDA6E] * 0x100 + mem[0xDA6F]


def main(path: Path) -> None:
    rom = path.read_bytes()
    digest = hashlib.sha1(rom).hexdigest()
    assert len(rom) == 1024 * 1024, 'Unexpected ROM size'
    assert digest == EXPECTED_SHA1, 'ROM differs from baseline; do not assume offsets'
    routine = locate_once(rom, DAYCARE_SIGNATURE, 'Day Care EXP routine')
    chances = locate_once(rom, SLOT_TABLE, 'wild encounter slot probability table')
    print('SHA-1:', digest)
    print('Day Care IncrementDayCareMonExp:', location(routine))
    print('WildMonEncounterSlotChances:', location(chances))
    print('Wild encounter slot weights:', SLOT_WEIGHTS, 'sum:', sum(SLOT_WEIGHTS))
    for start in (0x000000, 0x4FFFFE, 0x4FFFFF, 0x500000, 0x50FFFE, 0x50FFFF, 0xFFFFFE, 0xFFFFFF):
        actual = execute_daycare_rom(rom, routine, start)
        expected = simulated_exp_advance(start)
        assert actual == expected, (start, actual, expected)
        print(f'Day Care enabled: 0x{start:06X} -> 0x{actual:06X}')
    for start in (0, 0x4FFFFF, 0x50FFFF):
        assert execute_daycare_rom(rom, routine, start, enabled=False) == start
    # Deterministic wide-boundary fuzz test (sample 1024 states over four windows).
    for base in (0x4F0000, 0x4FFF00, 0x500000, 0x50FF00, 0xFFFF00):
        for low in range(256):
            initial = base + low
            actual = execute_daycare_rom(rom, routine, initial)
            expected = simulated_exp_advance(initial)
            assert actual == expected, (initial, actual, expected)
    print('PASS: 1,280 boundary-adjacent EXP states + 3 disabled samples')
    # Parse probabilities as stored in the user's actual ROM and verify 256 outcomes.
    table = rom[chances:chances + 20]
    counts = [0] * 10
    for rng in range(256):
        for i in range(10):
            if rng <= table[2*i]:
                assert table[2*i + 1] == 2*i
                counts[i] += 1
                break
        else:
            raise AssertionError(f'RNG value {rng} has no table entry')
    assert tuple(counts) == SLOT_WEIGHTS
    print('PASS: all 256 encounter slot RNG inputs map to their table weights')
    print('All ROM-backed checks passed (not an in-game playthrough).')


if __name__ == '__main__':
    main(Path(sys.argv[1] if len(sys.argv) > 1 else 'Pokemon Red.gb'))
