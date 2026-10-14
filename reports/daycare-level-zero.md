# Day Care level wraparound and softlock: full PyBoy test

The ordinary Pokémon Red Day Care recalculates a Pokémon's level from its 24-bit stored experience, **before** applying a maximum-level clamp. A Medium-Slow Pokémon with an artificial very-high experience value can cause the level-finding routine's 8-bit counter to wrap. In one narrow range, it returns level zero; in another range, it fails to return.

| Experience | Result in full emulator with constructed RAM |
| --- | --- |
| `0x000064` | Normal recalculation to Level 4 |
| `0xFFFF73` | Level estimate capped at 100 |
| `0xFFFF74` | Returns Level 0 |
| `0xFFFFC9` | Returns Level 0 |
| `0xFFFFCA` | Repeated calculation; no return during test |
| `0xFFFFFF` | Repeated calculation; no return during test |

A constructed Level 0 Pokémon was successfully retrieved from the Day Care in PyBoy after paying $9,999. A nominal $10,000 fee in a separate test also saturated at $9,999 due to two-byte decimal accounting.

**Critical limitation:** All these observations used deliberately constructed *emulator memory*. Reproduction via unassisted, ordinary gameplay is not established. Related experience-underflow glitches have been known for years. This project does not establish a first-ever discovery.

The early test-harness image showing a malformed Bulbasaur name arose from incorrectly encoded nickname bytes, not a Pokémon Red glitch. The included public-ready test script corrects the synthetic name string.

Sources:
- https://github.com/pret/pokered/blob/master/engine/pokemon/experience.asm
- https://github.com/pret/pokered/blob/master/scripts/Daycare.asm
- https://github.com/pret/pokered/blob/master/engine/math/bcd.asm
- https://bulbapedia.bulbagarden.net/wiki/Experience_underflow_glitch
