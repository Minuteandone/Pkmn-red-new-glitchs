# Pokémon Red glitch research 🧪

Public-ready research archive covering Pokémon Red (original English Game Boy ROM).

**Status:** Day Care Level 0 and underflow softlock were observed in the complete PyBoy emulator with **constructed game RAM**. This is not evidence that the necessary experience values can be obtained via normal play. The bench's silent interaction is intentional; its unnecessary memory scan is a known implementation bug. Neither behavior is claimed to be a first-ever discovery.

## Included
- `reports/initial-rom-audit.md`: ROM opcode analysis, Exp. All behavior, stationary-sprite hypothesis.
- `reports/daycare-healing-candidate.md`: unconfirmed HP/status/PP preservation hypothesis.
- `reports/daycare-level-zero.md`: source and full emulator investigation of Level 0, unbounded level calculation, and Day Care payment cap.
- `reports/bench-overrun.md`: corrected analysis of how bench dialogue scans beyond its table.
- `tests/`: original Python scripts for audit, PyBoy testing and optional video generation.
- `results/`: non-sensitive test outputs.

No ROM, emulator state, screenshots, video, proprietary Nintendo assets, credentials, or private repository references are included. All scripts operate on a user's own original game ROM.

## Reproduce

```shell
python rom_deep_audit.py 'Pokemon Red.gb'
python tests/test_bench_text_rom.py 'Pokemon Red.gb'
python tests/test_bench_map_reachability.py 'Pokemon Red.gb'
python tests/test_daycare_healing_model.py 'Pokemon Red.gb'
```

Full emulator checks require PyBoy 2.8.1; screen recording also uses Pillow and FFmpeg.

Original source disassembly: https://github.com/pret/pokered


## New multistep investigations (2026-10-13)

**A. Day Care underflow recovery by walking 54 steps — full PyBoy test**

- [Step-by-step root cause and findings](reports/daycare-underflow-54-step-rescue.md)
- [Run the original-game movement + dialogue test](tests/test_daycare_rescue_walk.py)
- [Actual emulator measurements](results/daycare_54_step_rescue.json)

The constructed `0xFFFFCA` XP state causes the Day Care level calculation to loop indefinitely. **54 successful in-game steps**, via the Day Care's XP increment, cause `0xFFFFFF → 0x000000`. The recalculation subsequently returns normally. The previously published `rom_deep_audit.py` has been **corrected** to handle the `0xFF → 0x00` high-byte rollover and now passes 1,280 EXP boundary tests.

**B. Bide damage diverging after an opponent faints — exact ROM opcode tests**

- [Multistep link-battle code-path analysis](reports/bide-faint-link-state-divergence.md)
- [1,024-state original-ROM faint-reset regression test](tests/test_bide_faint_reset.py)
- [Recorded test results](results/bide_faint_reset.json)

One faint-cleanup routine zeroes only the high byte of the Bide counter; the symmetric routine clears both bytes. Tests found **1,020 divergent cleanup results out of 1,024**. This is a **previously documented** Gen I implementation bug; no two-console link battle has been played or recorded in this project.

Both reports distinguish emulator-confirmed results from source/ROM-based predictions, and **neither demonstrates a previously undiscovered naturally triggered glitch**.
