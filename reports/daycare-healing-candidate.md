> **UPDATE — Full-emulator verification completed.** This was originally a *source-only candidate*. [A subsequent PyBoy experiment](daycare-preserves-poison-pp.md) directly confirmed that the original Pokémon Red Day Care restores HP but preserves poison/burn status and spent PP, and that the preserved poison causes overworld damage. The reproduction and machine-readable results are public. This historical report remains for the development record.

> **Evidence limit:** This is a source-only candidate, not a confirmed in-game Day Care behavior. Later PyBoy experiments in this project investigated *different* Day Care features; they do not prove the status/PP candidate.

# Pokémon Red deep bug hunt — round 2 (2026-10-13)

## Method and limits
- Input: original Pokémon Red UE, exactly 1,048,576 bytes; SHA-1 `ea9bcae617fdf159b045185467ae58b2e4a48b9a`; SHA-256 `5ca7ba01642a3b27b0cc0b5349b52792795b62d3ed977e98a09390659af96b7b`.
- ROM hash and header checksum verified in the original audit.
- Source review: `pret/pokered`, `master`.
- **This specific candidate was evaluated through static code reasoning only.** The emulator was used later for different cases. No physical cartridge observation of this candidate has occurred. Python unit tests use an explicit reduced *model*, not runtime emulation.
- Neither candidate is claimed to be an undocumented world-first bug.

## PR-DC-001 — Day Care withdraw restores HP but apparently leaves status and PP unchanged

**Status:** Source-backed behavioral finding, likely reproducible; novel classification and in-game reproduction pending. This might be a version-specific mechanic rather than an accidental programming oversight.

### Reproduction prediction
1. Make a two-Pokémon party. Have one Pokémon with a persistent status ailment (e.g. poison), less than full HP, and spent move PP; it must not know an HM.
2. Deposit that Pokémon in the Route 5 Day Care.
3. Withdraw it without any level-up, with sufficient funds and a party slot.
4. Inspect stats: **predicted** HP becomes full, but status and existing move PP are retained. A poisoned Pokémon would therefore still take damage from ordinary walking once it is collected.

### Code path
- `scripts/Daycare.asm`: Depositing calls `MoveMon` as `PARTY_TO_DAYCARE`. Withdrawing calls `MoveMon` as `DAYCARE_TO_PARTY`, calls `WriteMonMoves`, then overwrites **only the party Pokémon's two HP bytes** from max HP.
- `engine/pokemon/add_mon.asm`: `_MoveMon` copies the compact Pokémon struct, which includes status and move PP, back to the party, then recalculates level and stats. No general PP refill or status wipe occurs there.
- `engine/pokemon/evos_moves.asm`: When no new moves are learned, `WriteMonMoves` leaves existing move PP unchanged.
- Separate healing paths exist in `engine/events/heal_party.asm` and `engine/items/item_effects.asm`, but Day Care withdrawal does not call them.

### Why it matters
The Day Care is commonly described as completely healing Pokémon. The code for this version appears to **heal only HP**; condition and PP would carry over. The highest-value next step is an emulator save-state test. Do not report as verified on hardware yet.

### Independent model (not an emulator)
See `tests/test_daycare_healing_model.py`. Four local tests passed, and the exact ROM verified. The tests establish the consequences of the traced copy/overwrite behavior, not the live game's execution.

Source URLs:
- https://github.com/pret/pokered/blob/master/scripts/Daycare.asm
- https://github.com/pret/pokered/blob/master/engine/pokemon/add_mon.asm
- https://github.com/pret/pokered/blob/master/engine/pokemon/evos_moves.asm
- https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Day_Care

## PR-GFX-002 — Third distinct stationary sprite would overwrite an existing VRAM slot

**Status:** Conditional graphics-capacity hazard; **no natural trigger yet found**. Do not call this a Pokémon Red gameplay bug.

In `engine/overworld/map_sprites.asm`, the first unique four-tile static sprite loads into `vSprites tile $78`. Subsequent unique still sprites use `vSprites tile $7c`; the bookkeeping changes only for the first sprite. Thus a third unique still sprite would overwrite the second sprite's art if such an arrangement can be loaded. Map checks so far (Oak's Lab, fossil/boulder rooms, Pokémon Mansion, routes with Snorlax) have not established a normal map with three distinct still-sprite types.

Source URLs:
- https://github.com/pret/pokered/blob/master/engine/overworld/map_sprites.asm
- https://github.com/pret/pokered/blob/master/constants/sprite_constants.asm

## Eliminated or already documented
- Repel uses the first Pokémon's level even if it is fainted: **documented**, not new.
- Item-stack corruption, accidental stone evolution, PP Up+Struggle, PP Up+Max Ether, Toxic+Leech Seed, Cinnabar coast encounters and Cooltrainer-F AI: **documented**.
- Apparent hidden event index accumulation: **false positive**; `CheckForHiddenEvent` explicitly clears the event argument, bank, and index with consecutive `ld [hli]` / `ld [hl]` operations.

## Next tests
1. Emulator-confirm the Day Care condition/PP behavior on the exact Red ROM with party structure capture before and after.
2. Audit all map object lists for ≥3 distinct four-tile stationary sprites. Do not promote the sprite hazard without a reachable trigger.
3. Explore stateful battle-AI interactions involving status flags, Disable, and move-choice selection.
