#!/usr/bin/env python3
"""Pokémon Red: actual full-PyBoy Day Care experience-boundary tests.

Prepare a synthetic Level 1, Medium-Slow Bulbasaur in Day Care by altering
**emulator WRAM only**, then let the original game code calculate experience,
price, and withdrawal. No ROM patches, redistributions, or user save changes.

Usage:
  python tests/prepare_pyboy_bench_state.py 'Pokemon Red.gb' /tmp/bench.state
  python tests/test_daycare_xp_boundary_pyboy.py 'Pokemon Red.gb' /tmp/bench.state /tmp/daycare_results

Setup note: This tests game behavior *conditional upon the constructed memory
state*. It does not prove a normal-play route can reach these states.
"""
from pathlib import Path
from hashlib import sha1
import json,sys
from pyboy import PyBoy

ROM_SHA1='ea9bcae617fdf159b045185467ae58b2e4a48b9a'
LEVEL_HOOK_BANK=22
LEVEL_ENTRY=0x4f43
LEVEL_INCREASE=0x4f4e
LEVEL_RETURN=0x4f69

# Synthetic Gen-I Bulbasaur data. Its Medium Slow level 1 XP is negative 54,
# represented in the original 24-bit EXP format as 0xFFFFCA.
SPECIES_BULBASAUR=0x99
SYNTH_BOX=[0x99,0,16,1,0,22,3,45,33,45,0,0,0,1,0,0,0]+[0]*10+[0x88,0x88,35,40,0,0]
assert len(SYNTH_BOX)==33


def initialize_room(game):
    # Add a spectator Pokémon. User's original save is not touched.
    m=game.memory
    assert m[0xD163]==0,'Base state unexpectedly has a party already'
    m[0xD163]=1; m[0xD164]=SPECIES_BULBASAUR;m[0xD165]=0xff
    spectator=SYNTH_BOX.copy(); spectator[2]=19;spectator[3]=5;spectator[16]=125
    for i,v in enumerate(spectator):m[0xD16B+i]=v
    m[0xD16B+33]=5
    for i,v in enumerate([0,19,0,11,0,11,0,11,0,11]):m[0xD16B+34+i]=v
    for base in [0xD273,0xD2B5]:m[base]=0x80;m[base+1]=0x50
    # Day Care is populated with a distinct synthetic level-1 Bulbasaur.
    m[0xDA48]=1
    # Correct Gen I English nickname encoding: BULBASAUR (terminated and padded)
    name=[0x81,0x94,0x8B,0x81,0x80,0x92,0x80,0x94,0x91,0x50,0x50]
    for i,v in enumerate(name):m[0xDA49+i]=v
    m[0xDA54]=0x80;m[0xDA55]=0x50
    for i,v in enumerate(SYNTH_BOX):m[0xDA5F+i]=v
    m[0xD347]=0;m[0xD348]=0x99;m[0xD349]=0x99 # initial $9,999
    # Map entry via game-original fixed-bank EnterMap at 0x03A6, jump
    # trampoline in WRAM. Needs EI so interrupts continue to work.
    m[0xD35E]=0x48;m[0xD365]=0x10;m[0xD42F]=0
    for i,b in enumerate([0xFB,0,0xC3,0xA6,0x03]):m[0xC0F0+i]=b
    game.register_file.PC=0xC0F0
    game.tick(600,render=False,sound=False)
    assert (m[0xD35E],m[0xD362],m[0xD361])==(0x48,2,7)
    # Walk directly up to caretaker at (2,3) and face up from (2,4).
    for key in ['up','up','up']:
        game.button_press(key);game.tick(10,render=False,sound=False)
        game.button_release(key);game.tick(27,render=False,sound=False)
    assert (m[0xD362],m[0xD361])==(2,4)
    assert m[0xDA62]==1


def tap(game,key='a',hold=9,release=100):
    game.button_press(key);game.tick(hold,render=False,sound=False)
    game.button_release(key);game.tick(release,render=True,sound=False)


def test(rom, state, out):
    out.mkdir(parents=True,exist_ok=True)
    rb=rom.read_bytes()
    assert len(rb)==1_048_576 and sha1(rb).hexdigest()==ROM_SHA1
    p=PyBoy(str(rom),window='null',sound_emulated=False)
    p.set_emulation_speed(0)
    with state.open('rb') as f:p.load_state(f)
    initialize_room(p)
    with (out/'prepared.state').open('wb') as f:p.save_state(f)
    p.tick(1,render=True,sound=False)
    p.screen.image.save(out/'prepared.png')
    report={'rom_sha1':ROM_SHA1,'emulator':'PyBoy 2.8.1','setup':'synthetic WRAM-only Day Care Pokémon', 'cases':{}}
    cases={
      'normal_100xp':0x000064,
      'before_zero_window':0xFFFF73,
      'level_zero_start':0xFFFF74,
      'level_zero_end':0xFFFFC9,
      'softlock_start':0xFFFFCA,
      'softlock_plus_three_steps':0xFFFFCD,
      'softlock_ceiling':0xFFFFFF,
      'normal_level100_price_cap':1_059_860,
    }
    for name,exp in cases.items():
        with (out/'prepared.state').open('rb') as f:p.load_state(f)
        for i,v in enumerate(exp.to_bytes(3,'big')):p.memory[0xDA6D+i]=v
        observations={'iterations':0,'returns':0,'d_wraps':0,'d_on_return':[],'entered':0}
        def entry(data):data['entered']+=1
        def inc(data):
            data['iterations']+=1
            if p.register_file.D==0:data['d_wraps']+=1
        def returns(data):
            data['returns']+=1
            data['d_on_return'].append(p.register_file.D)
        hooks=[(LEVEL_ENTRY,entry),(LEVEL_INCREASE,inc),(LEVEL_RETURN,returns)]
        for address,fn in hooks:p.hook_register(LEVEL_HOOK_BANK,address,fn,observations)
        tap(p,hold=8,release=172)
        # Give softlocks sufficient emulated time to demonstrate counter wrap.
        if name.startswith('softlock'):p.tick(350,render=True,sound=False)
        else:p.tick(90,render=True,sound=False)
        level=p.memory[0xDA62]
        p.screen.image.save(out/f'{name}_after_a.png')
        record={**observations,'input_exp':exp,'input_exp_hex':f'0x{exp:06X}',
                'daycare_level_after_a':level,'party_count_after_a':p.memory[0xD163]}
        for address,_ in hooks:p.hook_deregister(LEVEL_HOOK_BANK,address)
        # For the two interesting *nonlocked* cases, progress caretaker's
        # messages, agree to pay and verify the party/fee results.
        if name in ('level_zero_start','normal_level100_price_cap'):
            for n in range(12):tap(p)
            record.update(party_count_after_withdrawal=p.memory[0xD163],
                second_pokemon_level=p.memory[0xD197+33],
                money_after_hex=bytes(p.memory[0xD347:0xD34A]).hex())
            p.screen.image.save(out/f'{name}_after_withdraw.png')
        report['cases'][name]=record
        print(name,record,flush=True)
    p.stop()
    assert report['cases']['normal_100xp']['returns']==1
    assert report['cases']['before_zero_window']['daycare_level_after_a']==100
    assert report['cases']['level_zero_start']['daycare_level_after_a']==0
    assert report['cases']['level_zero_end']['daycare_level_after_a']==0
    assert report['cases']['softlock_start']['returns']==0
    assert report['cases']['softlock_start']['d_wraps']>=2
    assert report['cases']['normal_level100_price_cap']['daycare_level_after_a']==100
    assert report['cases']['level_zero_start']['party_count_after_withdrawal']==2
    assert report['cases']['level_zero_start']['second_pokemon_level']==0
    assert report['cases']['level_zero_start']['money_after_hex']=='000000'
    assert report['cases']['normal_level100_price_cap']['second_pokemon_level']==100
    assert report['cases']['normal_level100_price_cap']['money_after_hex']=='000000'
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Day Care Lv0 window, Lv1 underflow softlock, and $9,999 price cap. No game ROM exported.')

if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: script.py Pokemon-Red.gb booted-new-game.state output_folder')
    test(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
