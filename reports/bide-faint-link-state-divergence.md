# Pokémon Red: a multistep Bide/faint sequence can diverge across linked consoles

**Status:** original ROM opcode execution and code-flow analysis; **NOT full two-console link emulation**. The underlying bug was previously described by the Gen I reverse-engineering and battle-mechanics community.

## Multistep reproduction scenario

1. Begin a Pokémon Red link battle and have a Pokémon use **Bide**, which makes the game accumulate incoming damage in a 16-bit counter during its charge. The Bide effect initializes both bytes to zero at its start.
2. While Bide is still active, the opponent inflicts damage, making the accumulated value nonzero (for example `0x013A`, or 314).
3. Before Bide releases, the opponent faints from another effect, such as poison or recoil, and a replacement enters. The game calls faint cleanup while Bide's charging state can remain active.
4. On the console running `FaintEnemyPokemon`, the cleanup does `XOR A; LD [wPlayerBideAccumulatedDamage],A`: **only the high byte becomes zero**. The low byte survives. On the opponent's console, the corresponding `RemoveFaintedPlayerMon` cleanup runs `LD HL,wEnemyBideAccumulatedDamage; LD [HL+],A; LD [HL],A`: **both bytes become zero**.
5. If Bide continues collecting and then releases, the two consoles can calculate **different attack damage**. A difference large enough to affect which Pokémon faints may lead to link-battle desynchronization.

### Original ROM instruction evidence

| Event | Original ROM offset | Execution outcome with initial `0x013A` |
| --- | --- | --- |
| `FaintEnemyPokemon` Bide reset | `0x3C584` | `0x003A` (low byte remains 58) |
| `RemoveFaintedPlayerMon` Bide reset | `0x3C763` | `0x0000` |
| `BideEffect` starts Bide and clears its counter | `0x3F6E5` | Both bytes reset when Bide starts anew |

A dedicated **actual ROM opcode** regression test executed both snippets for four high bytes times all 256 possible low bytes: **1,024 comparisons**. The cleaned counters disagreed in **1,020 cases**, corresponding to all nonzero low bytes.

For an illustration, if both sides then accumulate 5 additional points without restarting Bide, the two stored totals would be 63 vs 5. Doubling these to release Bide yields **126 vs 10 damage**. This is a controlled arithmetic example, not an observed two-console battle log.

## What remains unverified

- No two Game Boys were connected; actual wire-protocol desynchronization was not captured.
- This is **not a new-to-the-world bug**. Existing `pret/pokered` comments, Gen I Smogon research, and fan disassembly bugfix tutorials already describe the missing low-byte clear.
- A full gameplay reproduction should establish a Bide user that stays charging while an opponent faints, then record both consoles' Bide memory and subsequent attack.

## Reproduce the code evidence

Run `python tests/test_bide_faint_reset.py 'Pokemon Red.gb' results.json` against the original English 1 MiB Pokémon Red ROM (SHA-1 `ea9bcae617fdf159b045185467ae58b2e4a48b9a`). It reads original ROM instructions and models just their memory writes: **not a full game emulator**. No ROM, copyrighted graphics, private data or save-state is distributed.

References:
- https://github.com/pret/pokered/blob/master/engine/battle/core.asm
- https://github.com/pret/pokered/blob/master/engine/battle/effects.asm
- https://www.smogon.com/forums/threads/past-gens-research-thread.3506992/post-6741609
