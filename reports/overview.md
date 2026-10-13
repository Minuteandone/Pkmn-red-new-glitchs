# Research overview

Investigated the original Pokémon Red game engine. This public collection contains notes and test code, never the game ROM or save-state data.

## Findings

- **Day Care level calculation:** With a specifically constructed Medium-Slow Pokémon experience value from `0xFFFF74` through `0xFFFFC9`, the game can calculate level zero. At `0xFFFFCA`, level checks can repeat without completing. Tests were performed in the PyBoy emulator with a synthetic RAM state; a natural-gameplay route to those states is not proven.
- **Day Care pricing:** Under constructed conditions, the charge saturates at $9,999.
- **Bench interaction:** Talking from the wrong direction is intentionally silent. Separately, the routine's incorrect table-pointer movement causes a memory overread. This implementation bug is already noted in the public game disassembly.
- **Step EXP counter and Exp. All:** Additional ROM-oriented tests examine counter rollover and already-known EXP division behavior.

Novelty has not been established. Tests require a separate user-supplied copy of the original game, which is not distributed in this repository.

Source reference: https://github.com/pret/pokered
