#!/usr/bin/env python3
"""Check a Greek script (index <TAB> x <TAB> greek) against the rules of the game font and engine.
Usage: python3 tools/validate_script.py <clean_rom.gbc> text/greek_script.tsv
Reports: forbidden characters, non-NFC text, special-token mismatches, length vs the English, words that cannot wrap.
Exit status is 1 if a forbidden character is found."""
import sys, re, unicodedata, collections
import build_patch as bp
from glyphs import compose
from greek_art import UP, LO

ALLOWED = set(".,!?:;'()-/&+@_`~·0123456789 ’")
TOKENS = ('@1', '@2', '@3', '_', '~', '`')

def load(path):
    rows = {}
    for line in open(path, encoding='utf-8').read().replace('\r\n', '\n').split('\n'):
        m = re.match(r'^(\d{4})\s+x(?:\s(.*))?$', line)
        if m: rows[int(m.group(1))] = m.group(2) or ''
    return rows

def main(rom_path, tsv):
    rom = open(rom_path, 'rb').read()
    english = [''.join(chr(x) if 32 <= x < 127 else f'<{x:02x}>' for x in s) for s in bp.read_slot(rom, 0x20)]
    rows = load(tsv)
    widths = rom[bp.FONTS[0][1]:bp.FONTS[0][1] + 128]
    def px(word):
        total = 0
        for c in word:
            total += (compose(c)[1] if (unicodedata.normalize('NFD', c)[0] in UP or unicodedata.normalize('NFD', c)[0] in LO or c == '·') else widths[ord(c) if ord(c) < 128 else 0x27]) + 1
        return total
    bad = collections.defaultdict(list); tok = []; nfc = []; wide = []; ratio = [0, 0]; empty_text = []
    for i, t in sorted(rows.items()):
        e = english[i]
        if not t.strip():
            if any(c.isalpha() for c in e): empty_text.append(i)
            continue
        if unicodedata.normalize('NFC', t) != t: nfc.append(i)
        for ch in t:
            d = unicodedata.normalize('NFD', ch)[0]
            if ch in ALLOWED or d in UP or d in LO: continue
            bad[ch].append(i)
        for k in TOKENS:
            if e.count(k) != t.count(k): tok.append((i, k, e.count(k), t.count(k)))
        ratio[0] += len(e); ratio[1] += len(t)
        for w in t.split():
            if px(w) > bp.BOX_W: wide.append((i, w, px(w)))
    missing = [i for i in range(len(english)) if i not in rows]
    print(f'rows: {len(rows)} of {len(english)} | missing: {len(missing)} | translated: {sum(1 for t in rows.values() if t.strip())}')
    print(f'length vs English: {ratio[1] / max(ratio[0], 1):.0%}')
    print('forbidden characters:', {f"{c!r} U+{ord(c):04X}": v[:5] for c, v in bad.items()} or 'none')
    print('not NFC:', nfc[:10] or 'none')
    print('special-token mismatches:', tok[:20] or 'none')
    print(f'words wider than {bp.BOX_W}px (cannot wrap): ' + (', '.join(f'#{i} {w!r}={n}px' for i, w, n in wide) or 'none'))
    print('empty rows whose English has letters (falls back to transliteration):', empty_text or 'none')
    if missing: print('missing indices:', missing[:20], '...' if len(missing) > 20 else '')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
