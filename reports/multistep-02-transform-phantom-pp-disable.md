# Multistep investigation B — Transform → Metronome → phantom PP → Struggle suppression → Disable loop

**Category:** independent battle-engine chain. **Status:** ROM-code/dataflow confirmed; three isolated original-ROM routines tested in **PyBoy 2.8.1**. **Not** a continuous normal battle/playthrough. **Prior art:** the underlying *Transform empty move glitch* was already documented by Crystal_ and Glitch City Wiki (2018 or earlier); **not a first discovery**.

## Player-side chain (multiple prerequisites and mechanics)

1. Have a **Ditto** (or another Transform user) with fewer moves than its opponent, leaving at least one empty move slot in its **real party data**.
2. Face a Pokémon that knows **Metronome** or **Mirror Move** in the corresponding otherwise-empty slot. It may require a specific opponent, or in a link battle a coordinated moveset.
3. Use **Transform**. It copies the opponent's move list into the active battle Pokémon and sets each populated copied slot to 5 PP, without replacing the Ditto's underlying party move list.
4. Use the copied **Metronome or Mirror Move**. To compensate for a move invoking a second move and being PP-decremented twice, the battle engine calls `IncrementMovePP` to add one PP back to the used slot.
5. **Bug:** `IncrementMovePP` increments both battle PP *and the real party Pokémon's PP*, **without checking TRANSFORMED**. When the corresponding real move slot is empty, the party now contains `move_id=0` but `PP=1`. The party mutation survives switch-out or battle end; healing does not inherently erase phantom PP.
6. Eventually exhaust the PP of all actual known moves (e.g. Ditto's sole **Transform**). Enter another battle with a move list of only `Transform` with 0 PP and an **empty third slot carrying 1 phantom PP**.
7. **Second bug:** `AnyMoveToSelect` ORs all four move PP bytes and concludes PP is nonzero. It declines to offer **Struggle**, even though no existing move has any PP.
8. **Third bug:** If an opponent uses **Disable**, its initial check also sees nonzero PP, so it proceeds to randomly choose a **nonempty move with positive PP**. No such move exists. The selection routine can cycle indefinitely, causing a battle softlock.

## Actual ROM-instruction experiments (constructed battle RAM)

These tests ran unchanged original English Red ROM bytes through the complete PyBoy CPU, with a controlled RAM-only call harness. ROM SHA-1: `ea9bcae617fdf159b045185467ae58b2e4a48b9a`.

**A. PP compensation:** `IncrementMovePP` at ROM bank 15, CPU `$6373`, given selected move index 2 and real party moves `[Transform,0,0,0]`, party PP `[0,0,0,0]`, copied battle moves `[Transform,0,Metronome,0]` and battle PP `[0,0,5,0]`. The routine changed:
- Party PP `[0,0,0,0] → [0,0,1,0]`, despite unchanged blank real move #3.
- Battle PP `[0,0,5,0] → [0,0,6,0]`.

**B. Struggle selection:** `AnyMoveToSelect` at bank 15, CPU `$53F5` reached `$540B` with the CPU **Z flag unset** when active battle PP was `[0,0,1,0]`, indicating a perceived available move. With `[0,0,0,0]`, Z **set**, indicating all PP gone and eligibility for Struggle. Both are actual ROM opcode conditions.

**C. Disable candidate selection:** Entered the genuine ROM's `DisableEffect` after its accuracy check, at bank 15 `$7A93`, with one actual move (`Transform`, zero PP), phantom third-slot PP 1, and the disabled counter zero. The random candidate selection was **deliberately supplied RNG result 0** (a valid game random outcome), allowing a deterministic test of the routine's own branch behavior. It scanned the sole real move **1,501 times**, never found a valid candidate, and was terminated by the test harness. The no-phantom control left the loop after its initial failure check, while a third control where Transform had 1 real PP found a valid move in one scan.

**Critical accuracy boundary:** The tests confirm **individual original game routines**, not a screenshot of the complete Metronome-through-Disable sequence in a normal battle. Neither a full two-player linked battle nor an unassisted gameplay acquisition of the phantom PP is shown here.

## Tested addresses

- Real party move IDs: `$D173..$D176`; real party PP: `$D188..$D18B`.
- Current battle move IDs: `$D01C..$D01F`; battle PP: `$D02D..$D030`.
- `IncrementMovePP`: bank 15 CPU `$6373`.
- `AnyMoveToSelect`: bank 15 CPU `$53F5`, comparison checkpoint `$540B`.
- `DisableEffect` inner state selection: bank 15 CPU `$7A93`, candidate scan `$7AA8`, valid-selection branch `$7AE1`.

Source trail:
- https://github.com/pret/pokered/blob/master/engine/battle/core.asm
- https://github.com/pret/pokered/blob/master/engine/battle/decrement_pp.asm
- https://github.com/pret/pokered/blob/master/engine/battle/effects.asm
- https://github.com/pret/pokered/blob/master/engine/battle/move_effects/transform.asm
- Prior documentation: https://nintyconservation.github.io/glitchcity.wiki/glitchcity.wiki/Transform_empty_move_glitch-2.html
- Historical demonstration: https://www.youtube.com/watch?v=_c7tQkSyz7E

The research contribution here is a **controlled, three-routine exact-ROM regression experiment**, not original discovery of the known Transform empty-slot glitch.
