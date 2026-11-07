#!/usr/bin/env python3
"""Dump the English text slot of your own ROM to a tab-separated file: index <TAB> bank:pointer <TAB> text.
Usage: python3 tools/dump_script.py <clean_rom.gbc> english_script.tsv [us|uk]
Control code 0x0C is written as <0c>. Nothing from the ROM is stored in this repository."""
import sys
import build_patch as bp

def dump(rom, slot):
    bank = {'us': 0x20, 'uk': 0x26}[slot]
    strings = bp.read_slot(rom, bank)
    B = bank * 0x4000
    rows = []
    for k, s in enumerate(strings):
        off, ptr = rom[B + 1 + 3*k], rom[B + 2 + 3*k] | rom[B + 3 + 3*k] << 8
        text = ''.join(chr(x) if 32 <= x < 127 else f'<{x:02x}>' for x in s)
        rows.append(f'{k:04d}\t{off}:{ptr:04x}\t{text}')
    return rows

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    slot = sys.argv[3] if len(sys.argv) > 3 else 'us'
    rows = dump(rom, slot)
    open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
    print(f'wrote {len(rows)} strings from the {slot.upper()} slot to {sys.argv[2]}')
