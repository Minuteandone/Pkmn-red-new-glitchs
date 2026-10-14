#!/usr/bin/env python3
"""Demonstrate the 54-step recovery of Gen I Day Care EXP underflow.

Usage:
  python tests/prepare_pyboy_bench_state.py PokemonRed.gb /tmp/bench.state
  python tests/daycare_underflow_recovery.py PokemonRed.gb /tmp/bench.state /tmp/recovery.json

Requires PyBoy 2.8.1 and test_daycare_xp_boundary_pyboy.py, in this directory.
The original ROM and user saves are not edited. The initial Level 1 Mew is
deliberately constructed in emulator WRAM, not captured in a real encounter.
"""
from hashlib import sha1
from pathlib import Path
import json
import sys

from pyboy import PyBoy
from test_daycare_xp_boundary_pyboy import initialize_room

SHA1 = "ea9bcae617fdf159b045185467ae58b2e4a48b9a"
DAYCARE_EXP = 0xDA6D


def press(game, key, hold=10, release=27):
    game.button_press(key)
    game.tick(hold, render=False, sound=False)
    game.button_release(key)
    game.tick(release, render=False, sound=False)


def run_case(rom, state, steps):
    game = PyBoy(str(rom), window="null", sound_emulated=False)
    game.set_emulation_speed(0)
    with state.open("rb") as f:
        game.load_state(f)
    initialize_room(game)
    memory = game.memory

    # Synthetic Day Care Mew at Level 1, original Medium-Slow experience -54.
    memory[0xDA5F] = 0x15  # Mew's internal species ID.
    memory[0xDA66] = 45    # Mew's catch rate.
    for i, byte in enumerate([0x8C, 0x84, 0x96] + [0x50] * 8):
        memory[0xDA49 + i] = byte  # Name "MEW", padded.
    for i, byte in enumerate((0xFF, 0xFF, 0xCA)):
        memory[DAYCARE_EXP + i] = byte
    assert memory[0xD163] == 1 and memory[0xDA48] == 1
    assert memory[0xDA62] == 1

    checkpoints = {}
    # Real, completed tile steps only. Once initialized, never modify EXP.
    for i in range(steps):
        before = (memory[0xD362], memory[0xD361])
        key = "left" if i % 2 == 0 else "right"
        press(game, key)
        after = (memory[0xD362], memory[0xD361])
        assert after != before, ("blocked movement", i, before)
        exp = int.from_bytes(bytes(memory[DAYCARE_EXP:DAYCARE_EXP + 3]), "big")
        assert exp == (0xFFFFCA + i + 1) & 0xFFFFFF, (i, exp)
        if i + 1 in (52, 53, 54, 108):
            checkpoints[str(i + 1)] = f"0x{exp:06X}"
    assert (memory[0xD362], memory[0xD361]) == (2, 4)
    press(game, "up")  # Just face caretaker. No tile step.

    stats = {"entered": 0, "level_checks": 0,
             "level_returns": 0, "level_wraps": 0}
    def on_enter(rec):
        rec["entered"] += 1
    def on_check(rec):
        rec["level_checks"] += 1
        if game.register_file.D == 0:
            rec["level_wraps"] += 1
    def on_exit(rec):
        rec["level_returns"] += 1
    for addr, callback in ((0x4F43, on_enter),
                           (0x4F4E, on_check), (0x4F69, on_exit)):
        game.hook_register(22, addr, callback, stats)

    press(game, "a", 8, 340)
    result = {
        "steps": steps,
        "exp": f"0x{int.from_bytes(bytes(memory[DAYCARE_EXP:DAYCARE_EXP+3]), 'big'):06X}",
        "checkpoints": checkpoints,
        "party_before": 1,
        "daycare_level_after_talk": memory[0xDA62],
        **stats,
    }
    if steps >= 54:
        for _ in range(12):
            press(game, "a", 8, 110)
        result.update(
            party_after=memory[0xD163],
            daycare_in_use_after=memory[0xDA48],
            returned_species=memory[0xD197],
            returned_level=memory[0xD197 + 33],
            money_after_bcd=bytes(memory[0xD347:0xD34A]).hex(),
        )
        assert result["party_after"] == 2
        assert result["daycare_in_use_after"] == 0
        assert result["returned_species"] == 0x15
        assert result["returned_level"] == (1 if steps == 54 else 2)
        assert result["money_after_bcd"] == ("009899" if steps == 54 else "009799")
    game.stop()
    return result


def main(rom, state, output):
    blob = rom.read_bytes()
    assert len(blob) == 1048576 and sha1(blob).hexdigest() == SHA1
    cases = [run_case(rom, state, n) for n in (0, 52, 54, 108)]
    assert all(row["entered"] == 1 for row in cases)
    assert cases[0]["level_returns"] == cases[1]["level_returns"] == 0
    assert cases[0]["level_wraps"] >= 2 and cases[1]["level_wraps"] >= 2
    assert cases[2]["level_returns"] == cases[3]["level_returns"] == 1
    assert cases[2]["exp"] == "0x000000"
    assert cases[3]["exp"] == "0x000036"
    output.write_text(json.dumps({
        "rom_sha1": SHA1,
        "emulator": "PyBoy 2.8.1",
        "setup": "synthetic Mew in Day Care; actual D-pad steps thereafter",
        "cases": cases
    }, indent=2) + "\n")
    print("PASS: 54 in-game steps repair the underflowed Day Care Mew.")
    print("PASS: 108 in-game steps yield Level 2; neither controls lock.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: script.py ROM.gb bench.state results.json")
    main(*(Path(arg) for arg in sys.argv[1:]))
