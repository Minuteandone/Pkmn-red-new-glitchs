#!/usr/bin/env python3
"""Full emulator test: Day Care restores HP while status/PP survive.

Usage:
  python tests/prepare_pyboy_bench_state.py ROM.gb /tmp/bench.state
  python tests/daycare_hp_status_pp_pyboy.py ROM.gb /tmp/bench.state output.json

The original ROM is untouched. Initial Level 5 Charmander data is constructed
in isolated emulator WRAM; withdrawal and subsequent walking are real controls.
"""
from pathlib import Path
from hashlib import sha1
import json, sys
from pyboy import PyBoy
from test_daycare_xp_boundary_pyboy import initialize_room

ROM_SHA1 = "ea9bcae617fdf159b045185467ae58b2e4a48b9a"
CHARMANDER = 0xB0
DAYCARE = 0xDA5F
PARTY_MON2 = 0xD197


def tap(game, key="a", hold=8, rest=100):
    game.button_press(key)
    game.tick(hold, render=False, sound=False)
    game.button_release(key)
    game.tick(rest, render=False, sound=False)


def check_case(rom, initial_state, label, status, pp, hp):
    game = PyBoy(str(rom), window="null", sound_emulated=False)
    game.set_emulation_speed(0)
    with initial_state.open("rb") as handle:
        game.load_state(handle)
    initialize_room(game)
    mem = game.memory
    # A normal-looking, non-Poison-type level 5 Charmander with Scratch/Growl.
    # 135 experience points = Medium-Slow species' level 5 minimum.
    fields = {0: CHARMANDER, 1: 0, 2: hp, 3: 5, 4: status,
              5: 0x14, 6: 0x14, 7: 45, 8: 10, 9: 45, 10: 0, 11: 0,
              14: 0, 15: 0, 16: 135}
    for offset, value in fields.items():
        mem[DAYCARE + offset] = value
    for i, value in enumerate(pp):
        mem[DAYCARE + 29 + i] = value
    # Correct Generation I uppercase charmap, "CHARMANDER" + terminator.
    for i, ch in enumerate([0x82,0x87,0x80,0x91,0x8C,0x80,0x8D,0x83,0x84,0x91,0x50]):
        mem[0xDA49 + i] = ch
    assert mem[0xD163] == 1 and mem[0xDA48] == 1

    tap(game, "a", 8, 170)
    for _ in range(11):
        tap(game, "a", 8, 105)
        if mem[0xD163] == 2:
            break
    assert mem[0xD163] == 2 and mem[0xDA48] == 0
    addr = PARTY_MON2
    result = {
        "scenario": label,
        "before": {"hp": hp, "status": status, "pp": pp, "level": 5},
        "after": {
            "species_id": mem[addr],
            "level": mem[addr + 33],
            "hp": (mem[addr + 1] << 8) | mem[addr + 2],
            "max_hp": (mem[addr + 34] << 8) | mem[addr + 35],
            "status": mem[addr + 4],
            "pp": list(mem[addr + 29:addr + 33]),
            "moves": list(mem[addr + 8:addr + 12])
        }
    }
    v = result["after"]
    assert v["species_id"] == CHARMANDER and v["level"] == 5
    assert v["hp"] == v["max_hp"] and v["hp"] > hp
    assert v["status"] == status and v["pp"] == pp

    if label == "poison":
        # Exit remaining text/menu before walking, so each key press moves.
        for _ in range(3):
            tap(game, "b", 9, 70)
        walking = []
        for i in range(16):
            before = (mem[0xD362], mem[0xD361])
            tap(game, "left" if i % 2 == 0 else "right", 10, 40)
            assert before != (mem[0xD362], mem[0xD361])
            walking.append((mem[addr + 1] << 8) | mem[addr + 2])
        assert walking[-1] == v["hp"] - 4
        result["hp_during_16_actual_steps"] = walking

    game.stop()
    return result


def main(rom, state, output):
    raw = rom.read_bytes()
    assert len(raw) == 1048576 and sha1(raw).hexdigest() == ROM_SHA1
    cases = [
        check_case(rom, state, "healthy", 0, [30,35,0,0], 4),
        check_case(rom, state, "poison", 8, [1,3,0,0], 4),
        check_case(rom, state, "burn", 16, [0,0,0,0], 1),
    ]
    assert cases[1]["hp_during_16_actual_steps"][-1] == 14
    output.write_text(json.dumps({
        "rom_sha1": ROM_SHA1, "emulator": "PyBoy 2.8.1",
        "setup": "synthetic Day Care starting RAM, authentic dialogue, withdrawal and D-pad walking",
        "cases": cases
    }, indent=2) + "\n")
    print("PASS: full HP restored, status and PP retained in three cases.")
    print("PASS: poison persisted and dealt four damage during 16 steps.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: script.py ROM.gb prepared.state results.json")
    main(*(Path(value) for value in sys.argv[1:]))
