# Bench dialogue: root cause and correction

The game is **supposed** to ignore interaction with a Pokémon Center bench when the player is not facing LEFT. The missing text is intentional, not the glitch.

The implementation *does* have a known bug: after a failed facing comparison, its table scanner fails to increment past the text pointer. It consequently skips the actual table-ending `FF`, scans unrelated ROM, and continues reading video memory until it encounters another `FF` byte.

An instrumented PyBoy test measured 2,709 comparisons before reading byte `FF` from video RAM address `$8435`. An ephemeral one-byte test fix changed the branch to take the existing `INC HL`, reducing the work to 13 comparisons and exiting at the legitimate table terminator `$64A2`. Changing video memory at `$8435` made the original routine continue to `$87B2` (3,007 comparisons). The original and fixed versions rendered identical visible screens in the tested orientations.

This bug was already documented in the open-source reverse engineering project. No globally novel discovery is claimed.

Source: https://github.com/pret/pokered/blob/master/engine/events/hidden_events/bench_guys.asm
