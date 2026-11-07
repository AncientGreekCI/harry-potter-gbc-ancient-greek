"""compose(ch) -> (8 row bytes, pixel width) for one precomposed Greek character (NFC).
Lowercase vowels and rho take any combination of: smooth/rough breathing, acute/grave/circumflex, diaeresis.
Capitals take no marks (normalise() strips them first); iota subscript is not drawn."""
import unicodedata
from greek_art import UP, LO
SMOOTH, ROUGH, ACUTE, GRAVE, CIRC, DIA, SUB = 0x313, 0x314, 0x301, 0x300, 0x342, 0x308, 0x345
HOOK = {SMOOTH: ('##', '.#'), ROUGH: ('##', '#.')}
ACC  = {ACUTE: ('.#', '#.'), GRAVE: ('#.', '.#'), CIRC: ('.#.', '#.#')}   # circumflex = small caret
MARKABLE = set('αεηιουωρ')
# horizontal shift of the accent: with a breathing / on its own (iota has its own, narrower values)
SHIFT_HOOK  = {ACUTE: 3, GRAVE: 3, CIRC: 3}
SHIFT_HOOK_CIRC = {SMOOTH: 3, ROUGH: 2}   # rough hook leaves a gap under the caret, so it can sit closer
SHIFT_PLAIN = {ACUTE: 2, GRAVE: 2, CIRC: 1}
SHIFT_IOTA  = {ACUTE: 0, GRAVE: 1, CIRC: 0}
def _bits(rows):
    out = []
    for r in rows:
        r = r.ljust(8, '.'); assert len(r) <= 8, r
        out.append(int(''.join('1' if c == '#' else '0' for c in r), 2))
    return bytes(out)
def _width(b): return max((x + 1 for r in b for x in range(8) if r >> (7 - x) & 1), default=0)
def _stamp(rows, r, x, pat):
    for dy, line in enumerate(pat):
        for dx, c in enumerate(line):
            if c == '#':
                row = list(rows[r + dy].ljust(8, '.')); row[x + dx] = '#'; rows[r + dy] = ''.join(row)
def compose(ch):
    d = unicodedata.normalize('NFD', ch); base = d[0]; marks = {ord(m) for m in d[1:]} - {SUB}
    if ch == '·':
        rows = [''] * 8; rows[4] = '#'; b = _bits(rows); return b, 1
    if base in UP:
        b = _bits(list(UP[base])); return b, _width(b)      # marks on capitals are ignored
    if base not in LO: raise KeyError(f'no glyph art for {ch!r}')
    rows = list(LO[base])
    if marks:
        if base not in MARKABLE: raise KeyError(f'marks on {ch!r} are not supported')
        hook = next((m for m in (SMOOTH, ROUGH) if m in marks), None)
        acc = next((m for m in (ACUTE, GRAVE, CIRC) if m in marks), None)
        dia = DIA in marks
        if dia and acc: acc = None                    # no room for both: diaeresis wins
        rows[0] = rows[1] = rows[2] = ''
        w = max(len(r) for r in rows[3:])
        if hook: _stamp(rows, 0, 0, HOOK[hook])
        if acc:
            shift = (SHIFT_HOOK_CIRC[hook] if acc == CIRC else SHIFT_HOOK[acc]) if hook else (SHIFT_IOTA if base == 'ι' else SHIFT_PLAIN)[acc]
            _stamp(rows, 0, shift, ACC[acc])
        if dia:
            _stamp(rows, 0, 0, ('#',)); _stamp(rows, 0, max(w - 1, 2), ('#',))
    b = _bits(rows); return b, _width(b)
