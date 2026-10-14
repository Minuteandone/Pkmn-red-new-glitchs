#!/usr/bin/env python3
"""Read-only Pokémon Red map collision BFS for four Pokécenter bench events.

The supplied original ROM is accessed only by fixed offsets; no game assets are
exported. This is NOT a whole-game emulation or a screen/playback test.
Usage: python tests/test_bench_map_reachability.py 'Pokemon Red.gb'
"""
from hashlib import sha1
from collections import deque
from pathlib import Path
import sys

SHA1="ea9bcae617fdf159b045185467ae58b2e4a48b9a"
MAP=0x440DF       # one of six identical 7x4 Pokécenter blockmaps
BLOCKSET=0x693BF  # beginning of Pokécenter's 16-byte-per-block table
WIDTH=7
PASSABLE={0x11,0x1A,0x1C,0x3C,0x5E}
# NPC collision blockers from pret/pokered data/maps/objects:
OBJECTS={
 "Vermilion":{(3,1),(10,5),(5,4),(11,2)},
 "Fuchsia":{(3,1),(2,3),(6,5),(11,2)},
 "Cinnabar":{(3,1),(9,4),(2,6),(11,2)},
 "Saffron":{(3,1),(5,5),(8,3),(11,2)},
}

def main(filename):
    rom=Path(filename).read_bytes()
    assert len(rom)==1048576 and sha1(rom).hexdigest()==SHA1
    layout=rom[MAP:MAP+28]
    assert layout[7]==0x21 and layout[14]==0x08
    occurrences=[i for i in range(len(rom)) if rom[i:i+28]==layout]
    assert len(occurrences)==6,occurrences
    def coll(x,y):
        block_id=layout[(y//2)*WIDTH+x//2]
        tile=(y%2*2+1)*4+(x%2)*2  # lower-left tile of 16x16 collision cell
        return rom[BLOCKSET+16*block_id+tile]
    # Tile (0,3) is floor, directly ABOVE unwalkable bench tile (0,4).
    assert coll(0,3)==0x11 and coll(0,4)==0x34
    assert coll(1,3)==0x11 and coll(1,4)==0x3C
    for city,npcs in OBJECTS.items():
        start,goal=(3,7),(0,3)
        queue=deque([(start,[start])])
        seen={start}
        path=None
        while queue:
            (x,y),route=queue.popleft()
            if (x,y)==goal:
                path=route
                break
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nxt=(x+dx,y+dy)
                if 0<=nxt[0]<14 and 0<=nxt[1]<8 and nxt not in seen and nxt not in npcs and coll(*nxt) in PASSABLE:
                    seen.add(nxt)
                    queue.append((nxt,route+[nxt]))
        assert path,city
        print(city,": ", " -> ".join(map(str,path)))
    print("PASS: All 4 Pokémon Centers have a collision-clear route to (0,3).")
    print("Face DOWN toward hidden bench event at (0,4) to exercise failing branch.")
    print("This is a tile collision model, not an emulated button-input demonstration.")

if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv)>1 else "Pokemon Red.gb")
