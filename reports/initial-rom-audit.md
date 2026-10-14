# Pokémon Red deep bug hunt — first findings (2026-10-13)

## Scope and evidence key
The independently inspected **unmodified** English Red ROM was inspected read-only. SHA-1: `ea9bcae617fdf159b045185467ae58b2e4a48b9a` (1,048,576 bytes).
- **ROM-backed, opcode-executed**: signature uniquely located and GB instructions executed in a *targeted miniature CPU interpreter*, rather than a full Game Boy emulator.
- **Source-backed**: the disassembly proves the control flow, but no full game playback.
- **Known**: behavior already documented in public sources. Do **not** advertise it as a discovery.
- **Hypothesis**: requires a saved-state/gameplay reproduction or more data auditing.

### PR-001 — Day Care experience uses a 65,536-step ring at extreme XP
**Status:** ROM-backed, opcode-executed; **novelty unverified** (the same numerical cap is previously documented in Generation II).

* ROM file offset `0x0C8DE`, bank 3, CPU address `0x48DE`; unique 24-byte instruction signature.
* Game RAM: `wDayCareInUse = 0xDA48`; `wDayCareMonExp = 0xDA6D..0xDA6F`.
* The routine increments the least significant EXP byte, propagates carry, then clamps only the **most significant byte** to `0x50`, never clearing or saturating the lower two bytes.
* Executed actual uploaded ROM instructions with isolated RAM. Results:
  - `0x4FFFFF -> 0x500000`
  - `0x500000 -> 0x500001`
  - `0x50FFFE -> 0x50FFFF`
  - `0x50FFFF -> 0x500000` (loses 65,535 EXP points after next step)
  - Disabled Day Care: EXP unchanged
* 1,024 model/ROM differential checks around the cap plus 3 disabled checks passed.
* Consequence: internal EXP cycles through `0x500000..0x50FFFF`; it does *not* simply saturate at `0x50FFFF`. This would require millions of steps without collecting the Pokémon. The retrieval script clamps level >= 100 EXP to the species' normal level-100 requirement, so ordinary play is unlikely to show the loop.
* Reproduction (test harness): use `rom_deep_audit.py` with an original English Pokémon Red ROM (no ROM alteration).
* Source: [increment routine](https://github.com/pret/pokered/blob/master/engine/overworld/daycare_exp.asm), [day-care retrieval](https://github.com/pret/pokered/blob/master/scripts/Daycare.asm).
* Prior art: [Bulbapedia Day Care](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Day_Care) explicitly describes this cap/cycle for Generation II; *I did not establish whether someone else has published its Gen I occurrence*.

### PR-002 — Exp. All double-divides the shared pool and truncates per field
**Status:** Source-backed, **known bug**; included as a complicated regression case, NOT a novel discovery.

* `engine/battle/core.asm` halves seven contiguous enemy-base-data bytes in place, calls `GainExperience`, then calls it again with all party EXP flags set.
* `engine/battle/experience.asm` divides those seven bytes in place by the number of EXP-eligible Pokémon **on each call**, not on an unmodified copy. Hence if `p` Pokémon took part and the party has `n` Pokémon, the second share is additionally divided by `p`.
* Potential extra effect of each bytewise floor: zero individual stat EXP or zero base EXP even where a mathematically ideal split would yield a nonzero fraction.
* Example with **Rattata** (base EXP 57), level 2, two participating Pokémon, six-party EXP All: base EXP byte goes `57 -> floor(57/2)=28 -> floor(28/2)=14 -> floor(14/6)=2`. The second share's experience calculation is `floor(2*2/7)=0` for nonparticipants. This models the normal/trainer-unboosted case, not a gameplay screenshot. Participating share uses 14 as its base EXP byte and yields `floor(14*2/7)=4` apiece.
* Prior art: [Bulbapedia Exp. All](https://bulbapedia.bulbagarden.net/wiki/Exp._Share) already explains the bug.
* Sources: [battle core](https://github.com/pret/pokered/blob/master/engine/battle/core.asm), [EXP routine](https://github.com/pret/pokered/blob/master/engine/battle/experience.asm), [Rattata base stats](https://github.com/pret/pokered/blob/master/data/pokemon/base_stats/rattata.asm).

### PR-003 — The two-stationary-sprite VRAM allocation ceiling
**Status:** Source-backed latent edge case, **NOT proven reachable on any vanilla map**.

* `LoadMapSpriteTilePatterns` in `engine/overworld/map_sprites.asm` selects between `vSprites tile $78` (first *distinct* still-picture ID) and `vSprites tile $7C` (every subsequent ID). After the first, `hFourTileSpriteCount` stays 1 and the third distinct still sprite would occupy the second one's VRAM slot.
* A hypothetical map displaying at least 3 distinct still-picture IDs would therefore render corrupted/overwritten artwork for at least one sprite. This matters for ROM hacks as well as any hypothetical vanilla glitch that introduces extra map sprites.
* Outdoor fixed sets contain two still-picture IDs, consistent with this design limit; sampled vanilla indoor object lists showed no confirmed 3-distinct-ID map. **This is not a claim of an ordinary playable Red bug.**
* Sources: [sprite loader](https://github.com/pret/pokered/blob/master/engine/overworld/map_sprites.asm), [sprite sets](https://github.com/pret/pokered/blob/master/data/maps/sprite_sets.asm).

### Control test — the wild encounter slot RNG table
**Status:** ROM-backed check; not a bug.

* `WildMonEncounterSlotChances` uniquely located in uploaded ROM at `0x13918`, bank 4, CPU `0x7918`.
* All 256 possible byte inputs were tested against the original table bytes. Slot counts exactly `51, 51, 39, 25, 25, 25, 13, 13, 11, 3` (sum 256).
* Do not confuse this correctly encoded distribution with the well-known Cinnabar shore terrain-subtile bug, which was also checked against known documentation.

## Updated status
This is the initial ROM and disassembly audit. Full PyBoy experiments were subsequently performed for the Day Care level-boundary behavior and the bench-dialogue lookup. The initial Day Care step-EXP test remains opcode-only, while the three-distinct-stationary-sprite capacity issue remains an *unverified hypothetical*. The Exp. All arithmetic bug is previously documented. No globally first discovery is claimed, and no game ROM or emulator save state is included here.
