# Pokémon Red: recovering from a Day Care XP-underflow softlock by walking

**Tested:** unmodified English Pokémon Red (SHA-1 `ea9bcae617fdf159b045185467ae58b2e4a48b9a`), PyBoy 2.8.1, October 13, 2026.

**Evidence:** Full original-game emulator with a **constructed initial Day Care Pokémon** and **ordinary in-game walking afterward**. No claim that the entire setup has been performed through normal gameplay.

## Multistep mechanism

1. A Medium-Slow Pokémon at Level 1 can hold **negative 54 experience**, represented as unsigned 24-bit `0xFFFFCA`. This underflow is already documented.
2. If the Day Care gentleman recalculates its level while the XP is that high, `CalcLevelFromExperience` never finds a higher XP threshold. Its 8-bit candidate level repeatedly wraps around to 0 and the dialogue never finishes.
3. While the Pokémon remains deposited, `ApplyOutOfBattlePoisonDamage` calls `IncrementDayCareMonExp` during normal overworld movement. The deposited Pokémon gains **1 XP per successful step**.
4. The crucial edge is **`0xFFFFFF + 1 -> 0x000000`**. The Day Care routine increments the three XP bytes independently. At the high byte, `INC $FF` produces **`$00`** before checking whether it is at least `$50`, and therefore the `$50` cap is **not applied to this particular rollover**. This corrects the earlier audit's simplified XP model.
5. Starting at `0xFFFFCA`, exactly **54 successful overworld steps** wrap the stored XP to 0. Returning to the same caretaker now reaches a normal Level 1 result instead of the infinite loop.

## Full-emulator reproduction

Starting from a valid emulator test state with a synthetic deposited Bulbasaur, the script inputs normal D-pad controls to circle around the caretaker. No direct memory editing occurs **after** the initial XP assignment.

| Input action number | XP in emulator | Notes |
| --- | --- | --- |
| Initial | `0xFFFFCA` | Constructed stored XP |
| 53 | `0xFFFFFE` | 52 successful steps; one blocked direction |
| 54 | `0xFFFFFF` | 53 successful steps |
| **55** | **`0x000000`** | **54 successful steps; full 24-bit wrap** |
| 57 | `0x000002` | Returned to the caretaker's interaction position |

**Before walking through the overflow:** pressing A with XP `0xFFFFFE` produced **693 level checks, 2 level-counter wraps, and 0 returns** during the recorded observation.

**After:** pressing A with XP `0x000002` produced **1 level check, 1 successful return**, and the Pokémon's recalculated Day Care level was **1**.

### Validation limits

- The initial Day Care Pokémon was constructed in emulator RAM. The original ROM was not patched.
- The counter change `0xFFFFCA` to `0x000000` **was caused by actual in-game walking**.
- We did not reproduce the initial glitch Pokémon acquisition or its deposit through an unassisted playthrough.
- The long-loop observation is a timed softlock observation, supported by the missing bounded exit in the assembly.
- We have not established whether this exact rescue chain has already been published elsewhere.

## Reproducibility

Use `tests/test_daycare_rescue_walk.py` with an original Pokémon Red ROM and a **locally produced** prepared Day Care emulator state (created by the project's Day Care PyBoy boundary test). The script verifies each step count, the memory rollover, and the successful subsequent return; it exports **no copyrighted game assets**.

Related: [Day Care Level 0 and softlock report](daycare-level-zero.md).

Sources: https://github.com/pret/pokered/blob/master/engine/overworld/daycare_exp.asm ; https://github.com/pret/pokered/blob/master/engine/events/poison.asm ; https://github.com/pret/pokered/blob/master/engine/pokemon/experience.asm ; https://github.com/pret/pokered/blob/master/scripts/Daycare.asm .
