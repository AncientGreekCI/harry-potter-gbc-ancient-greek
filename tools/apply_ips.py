#!/usr/bin/env python3
"""Apply an IPS patch to a clean ROM (no external patcher needed).
Usage: python3 tools/apply_ips.py <clean_rom.gbc> patches/hp1_greek_us.ips <output.gbc>"""
import sys, zlib
BASE_CRC32 = 0x4FD8B7C5      # Harry Potter and the Sorcerer's Stone (USA, Europe) (En,Fr,De,Es,It,Nl,Pt,Sv,No,Da,Fi).gbc
PATCHED_CRC32 = 0xCFEBDBE5   # expected result for patches/hp1_greek_us.ips

def apply(rom, ips):
    assert ips[:5] == b'PATCH', 'not an IPS file'
    rom = bytearray(rom); i = 5
    while ips[i:i+3] != b'EOF':
        off = int.from_bytes(ips[i:i+3], 'big'); size = int.from_bytes(ips[i+3:i+5], 'big'); i += 5
        if size == 0:                                   # RLE record
            run = int.from_bytes(ips[i:i+2], 'big'); rom[off:off+run] = bytes([ips[i+2]]) * run; i += 3
        else:
            rom[off:off+size] = ips[i:i+size]; i += size
    return bytes(rom)

if __name__ == '__main__':
    src, patch, dst = sys.argv[1:4]
    rom = open(src, 'rb').read()
    crc = zlib.crc32(rom) & 0xFFFFFFFF
    if crc != BASE_CRC32:
        print(f'WARNING: base ROM CRC32 is {crc:08X}, expected {BASE_CRC32:08X}. The patch may not work on this dump.')
    out = apply(rom, open(patch, 'rb').read())
    open(dst, 'wb').write(out)
    print(f'wrote {dst}  CRC32 {zlib.crc32(out) & 0xFFFFFFFF:08X}  (expected {PATCHED_CRC32:08X} for hp1_greek_us.ips)')
