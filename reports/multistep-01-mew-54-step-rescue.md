# Multistep investigation A — Trainer-Fly → Level 1 Mew → 54-step Day Care rescue

**Status:** Late-stage chain reproduced in a full Game Boy emulator with Mew-specific RAM data. **Full, natural Trainer-Fly → catch → deposit route NOT executed yet.** Original English Pokémon Red ROM, SHA-1 `ea9bcae617fdf159b045185467ae58b2e4a48b9a`.

## Proposed 15+ step chain

1. Progress through Cerulean and leave the Route 24 long-range trainer and a suitable Cerulean Gym swimmer undefeated.
2. Obtain Teleport and a Pokémon with Growl; keep room in the party.
3. Trigger the documented Trainer-Fly escape from the Route 24 trainer using START and Teleport at the appropriate timing.
4. Defeat the swimmer but lower the last enemy Pokémon's Attack by **six successful Growls** before winning.
5. Return directly to Route 24; close the automatically appearing menu. The known trainer-fly encounter should be a **Level 1 Mew**.
6. Capture Mew to the **party** (a level-1 PC withdrawal has a known softlock), and do not gain any EXP with it.
7. Deposit it at Route 5 Day Care. Mew belongs to the **Medium Slow** growth group, whose level-1 threshold equals −54 stored as 24-bit `0xFFFFCA`.
8. Immediately requesting withdrawal causes the Day Care's level-search counter to loop forever on the original game code (confirmed for synthetic deposited Mew).
9. Alternative: walk **54 actual accepted tiles** inside the Day Care after depositing, returning to the caretaker's tile; every step adds +1 EXP to the deposited Pokémon.
10. The 54th step increments `0xFFFFFF` to `0x000000`, allowing withdrawal of a **Level 1 Mew for $100**.
11. A 108-step branch leaves EXP `0x000036` and returns a **Level 2 Mew for $200**.

The Trainer-Fly and six-Growl manipulation are previously documented; the combined Day Care timing was developed in this research. The unbroken acquisition-to-rescue playthrough is not yet demonstrated.

## Mew-specific full-emulator continuation

The prior run had used Bulbasaur in the deposited data. For this follow-up, a prepared PyBoy state was modified **only in emulator WRAM** to use Gen I Mew species ID `0x15` and a valid Mew nickname. Original game code handled the following button-driven steps and collection:

| Walked steps | EXP after steps | Level routine | Withdrawal |
| ---: | --- | --- | --- |
| 0 | `0xFFFFCA` | 836 checked level candidates during capture, 0 returns | No |
| 52 | `0xFFFFFE` | 836 checked level candidates, 0 returns | No |
| 54 | `0x000000` | 1 check, returned | **Level 1 Mew**, party +1, $9,999 → $9,899 |
| 108 | `0x000036` | 2 checks, returned | **Level 2 Mew**, party +1, $9,999 → $9,799 |

Each accepted step was verified to advance the actual game-stored 24-bit Day Care EXP by exactly one. Day Care collection used game dialogue and buttons, not a direct party write. Game code and ROM remained unchanged.

**Limits:** The initial deposited Mew was synthesized in WRAM. This experiment does not establish a naturally caught or naturally deposited Pokémon; actual Trainer-Fly conditions require their own full-run test. No globally first-discovered glitch is claimed.

## References
- [pret/pokered Day Care script](https://github.com/pret/pokered/blob/master/scripts/Daycare.asm)
- [original Day Care XP increment routine](https://github.com/pret/pokered/blob/master/engine/overworld/daycare_exp.asm)
- [experience level search](https://github.com/pret/pokered/blob/master/engine/pokemon/experience.asm)
- [Mew species data](https://github.com/pret/pokered/blob/master/data/pokemon/base_stats/mew.asm)
- [documented experience underflow glitch](https://bulbapedia.bulbagarden.net/wiki/Experience_underflow_glitch)
