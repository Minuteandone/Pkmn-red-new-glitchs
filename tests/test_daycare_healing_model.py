#!/usr/bin/env python3
"""Reduced dataflow model for the Pokémon Red Day Care behavior finding.

THIS IS NOT AN EMULATOR. The research report traces actual assembly paths.
These tests check consequences of the *hypothesized* copy + HP overwrite
path with no newly learned level-up moves, plus exact reference-ROM identity.
"""
from dataclasses import dataclass
from hashlib import sha1, sha256
from pathlib import Path
import unittest

EXPECTED_SHA1 = "ea9bcae617fdf159b045185467ae58b2e4a48b9a"
EXPECTED_SHA256 = "5ca7ba01642a3b27b0cc0b5349b52792795b62d3ed977e98a09390659af96b7b"


@dataclass(frozen=True)
class Pokemon:
    hp: int
    max_hp: int
    status: int
    pp: tuple[int, int, int, int]


def red_daycare_withdraw_no_new_moves(mon: Pokemon) -> Pokemon:
    """Inferred by tracing MoveMon and Daycare's last two-byte HP write."""
    assert 0 <= mon.hp <= mon.max_hp and mon.max_hp > 0
    return Pokemon(hp=mon.max_hp, max_hp=mon.max_hp,
                   status=mon.status, pp=mon.pp)


def verify_rom(path: Path) -> None:
    blob = path.read_bytes()
    assert len(blob) == 1_048_576
    assert sha1(blob).hexdigest() == EXPECTED_SHA1
    assert sha256(blob).hexdigest() == EXPECTED_SHA256
    assert blob[0x134:0x13F] == b"POKEMON RED"
    assert blob[0x14D] == ((-sum(blob[0x134:0x14D]) - 25) & 0xFF)


class DayCareModelTests(unittest.TestCase):
    def test_full_hp_but_poison_retained(self):
        before = Pokemon(4, 35, 0x08, (1, 0, 5, 0))
        after = red_daycare_withdraw_no_new_moves(before)
        self.assertEqual((after.hp, after.status, after.pp),
                         (35, 0x08, (1, 0, 5, 0)))

    def test_other_status_persists(self):
        for status in [0x01, 0x08, 0x10, 0x20, 0x40]:
            with self.subTest(status=status):
                before = Pokemon(1, 100, status, (5, 3, 9, 0))
                self.assertEqual(red_daycare_withdraw_no_new_moves(before).status, status)

    def test_spent_pp_stays_spent(self):
        before = Pokemon(12, 150, 0, (0, 2, 0, 17))
        self.assertEqual(red_daycare_withdraw_no_new_moves(before).pp, before.pp)

    def test_all_hp_is_restored(self):
        for hp in (1, 3, 45, 99):
            with self.subTest(hp=hp):
                before = Pokemon(hp, 100, 0, (10, 15, 0, 0))
                self.assertEqual(red_daycare_withdraw_no_new_moves(before).hp, 100)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        verify_rom(Path(sys.argv[1]))
        print("Exact Pokémon Red ROM SHA-1/SHA-256/header verified")
        sys.argv = sys.argv[:1]
    unittest.main(verbosity=2)
