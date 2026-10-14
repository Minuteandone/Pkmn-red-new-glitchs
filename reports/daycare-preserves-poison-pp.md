# Day Care healing exception: HP restored, poison and depleted PP preserved

**Game:** English Pokémon Red, original 1 MiB ROM, SHA-1 `ea9bcae617fdf159b045185467ae58b2e4a48b9a`. **Test:** full PyBoy 2.8.1 emulator. **Status: confirmed for constructed, ordinary-looking Day Care data, with actual in-game withdrawal and walking.**

## Unexpected behavior

Pokémon Red's Day Care does **not** perform the same general healing operation as a Pokémon Center. It explicitly overwrites the returned party Pokémon's **current HP with calculated maximum HP**, but does not clear its persistent major status condition or replenish its move PP if no new moves are learned.

Three tests used an otherwise standard Level 5 Charmander (Fire type, Scratch and Growl, `135` Medium-Slow XP), with different initial conditions. Each started with exactly one other party Pokémon and a constructed Charmander Day Care record. The game was then allowed to execute the ordinary caretaker interaction, collect $100 and withdraw the Charmander through its unmodified routines.

| Case | Input HP, status, PP | Actual returned HP, status, PP |
| --- | --- | --- |
| Healthy control | 4 HP; no status; `[30,35,0,0]` PP | **18/18 HP**, no status; **same PP** |
| Poisoned | 4 HP; poison `0x08`; `[1,3,0,0]` PP | **18/18 HP**, still `0x08`; **same PP** |
| Burned and fully depleted | 1 HP; burn `0x10`; `[0,0,0,0]` PP | **18/18 HP**, still `0x10`; **same PP** |

In all three cases, party count rose **1 → 2**, the Day Care occupancy flag cleared, and the returned party member was species `0xB0` (Charmander), Level 5.

### Poison remains active after collection

After the poisoned Charmander returned, the test closed the dialogue and used **16 actual completed LEFT/RIGHT steps** in the Day Care building. The returned Charmander's current HP progressed as follows:

```
Starting HP after Day Care: 18
Steps  1–4: 17
Steps  5–8: 16
Steps  9–12: 15
Steps 13–16: 14
```

This is genuine in-game overworld poison damage, not merely a status-bit comparison. The initial poison step-counter phase was such that the first observed step triggered a damage tick.

## Explanation

The Day Care withdrawal script in `scripts/Daycare.asm`:
1. Calls `MoveMon` to copy the stored monster into the party.
2. Calls `WriteMonMoves` for potential Day Care level-up learning.
3. **Directly copies `wPartyMon*MaxHP` into `wPartyMon*HP`**.
4. Does **not** call the Pokémon Center's cure-status or restore-PP routine.

The box-monster struct includes status and PP; they are copied unchanged unless another special case modifies them. If no new moves are learned, existing PP remains intact.

## Scope and prior-art limits

- The initial saved state, one party member and Day Care Charmander were constructed by modifying **emulator WRAM**. Once the room was initialized, the game itself handled all dialogues, pricing, withdrawal, and poison damage through emulated button presses; neither the ROM nor the returned monster was modified mid-test.
- The constructed Charmander uses normal Level 5 experience, legal move IDs and types, and legal poison/burn status states. A complete unassisted sequence (capture → poison → deposit → withdraw) has **not** been filmed.
- Documentation sometimes describes Day Care as fully healing a Pokémon. The result is evidence about the **specific original Red ROM**, not proof that every game's Day Care behaves this way.
- No claim of worldwide first discovery. Related knowledge may already exist in game-mechanics communities.

## Reproduce

```shell
python tests/prepare_pyboy_bench_state.py 'Pokemon Red.gb' /tmp/bench.state
python tests/daycare_hp_status_pp_pyboy.py 'Pokemon Red.gb' /tmp/bench.state /tmp/daycare-healing.json
```

The tested ROM must match the script's expected SHA-1. Output is only JSON; do not commit the ROM, savestates or Nintendo art.

References:
- https://github.com/pret/pokered/blob/master/scripts/Daycare.asm
- https://github.com/pret/pokered/blob/master/engine/pokemon/add_mon.asm
- https://github.com/pret/pokered/blob/master/engine/events/poison.asm
- https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Day_Care
