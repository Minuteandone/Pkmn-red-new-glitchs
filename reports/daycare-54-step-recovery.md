# Day Care underflow recovery: exact 54-step boundary

**Research date:** 2026-10-13/14. **Game:** original English Pokémon Red, ROM SHA-1 `ea9bcae617fdf159b045185467ae58b2e4a48b9a`. **Emulator:** PyBoy 2.8.1.

## Result

A Medium-Slow **Level 1 Mew** whose 24-bit experience counter is `0xFFFFCA` (-54 mod 2^24) cannot be retrieved immediately from the Day Care: the level calculator repeatedly wraps its 8-bit level counter. The Day Care awards one EXP per normal walkable step. It will still increment *this* high EXP value until the entire 24-bit field wraps at step 54:

| In-game walking steps | Day Care EXP | Result when talking to caretaker |
| --- | --- | --- |
| 0 | `0xFFFFCA` | Level search does not return in observed window |
| 52 | `0xFFFFFE` | Level search does not return |
| 53 | `0xFFFFFF` | Recorded XP checkpoint; level search not separately tested here |
| **54** | **`0x000000`** | **Calculation returns Level 1; Mew withdrawn for $100** |
| 108 | `0x000036` (54 decimal) | Calculates **Level 2**; Mew withdrawn for $200 |

Across two independent runs of the full emulator, 0-step and 52-step attempts made 670 candidate-level comparisons and completed two 8-bit wraps with **zero exits** (after the specified observation interval). At 54 steps, the calculator returned after **one** candidate check. At 108 steps, it returned after **two** checks. After withdrawing, party size increased from one to two, the returned Pokémon had the expected Mew species ID, the Day Care flag was cleared, and initial $9,999 became $9,899 or $9,799 respectively.

## Why this is unusual

This exposes an edge case combining several systems:
1. A known Generation I medium-slow growth formula evaluates Level 1 experience as -54.
2. The unsigned 24-bit stored value `0xFFFFCA` causes an *unbounded* level-search loop during withdrawal.
3. Day Care's overworld walking counter can **increment through `0xFFFFFF -> 0x000000`**, effectively repairing that state after exactly 54 valid steps.
4. Once the game sees small ordinary EXP again, it can calculate and deliver the previously unretrievable Pokémon normally.

**Scope / novelty:** This is not a claim that experience underflow itself is newly discovered. Existing Gen I resources cover Level 1 Mew acquisition and PC withdrawal softlocks. We did not locate a reliable previously published description of this specific Day Care 54-step recovery, but that is not proof of novelty.

## How this was tested

A valid Day Care test scenario was synthesized by initializing original Game Boy **WRAM**, including one spectator party Pokémon and a Level 1 Mew in the Day Care. The test then:
- never rewrote EXP during a scenario;
- repeatedly sent real LEFT/RIGHT D-pad input, asserting that the player actually moved a tile every time and EXP increased exactly once per step;
- faced UP toward the caretaker, pressed A, and installed CPU hooks into the **unmodified** level calculator (ROM bank 22, PCs `$4F43`, `$4F4E`, `$4F69`);
- for non-stalling cases, advanced the real in-game dialogue, paid the stated price, and checked party memory.

The initial setup **was not** a legitimate Trainer-Fly battle or a from-start natural acquisition of Level 1 Mew. The experiment is a **full-emulator reproduction conditional on synthetic initial RAM**, not a hardware/cart test or a completed unassisted glitch route.

Reproduction scripts: `tests/prepare_pyboy_bench_state.py`, `tests/test_daycare_xp_boundary_pyboy.py`, and `tests/daycare_underflow_recovery.py`. The original ROM, savestates, screenshots and private account data are **not** distributed.

## Public references

- Day Care overworld counter: https://github.com/pret/pokered/blob/master/engine/overworld/daycare_exp.asm
- Day Care pickup handler: https://github.com/pret/pokered/blob/master/scripts/Daycare.asm
- Level/experience calculator: https://github.com/pret/pokered/blob/master/engine/pokemon/experience.asm
- Known experience underflow: https://bulbapedia.bulbagarden.net/wiki/Experience_underflow_glitch
