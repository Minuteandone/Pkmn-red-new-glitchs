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
