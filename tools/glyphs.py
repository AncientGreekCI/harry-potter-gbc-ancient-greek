"""Glyph composition and metrics for Greek Game Boy Color font.
Supports full polytonic orthography:
- Lowercase combining marks (accents, breathings, diaeresis, iota subscript) with width = 0.
- Uppercase preceding diacritic marks with width = 2-3 px.
- High-Definition 5-pixel x-height (rows 2-6) for lowercase Greek letters.
- 24 uppercase and 25 lowercase base letters.
"""
import unicodedata
from greek_art import UP, LO

SMOOTH, ROUGH, ACUTE, GRAVE, CIRC, DIA, SUB = 0x313, 0x314, 0x301, 0x300, 0x342, 0x308, 0x345

def _bits(rows):
    out = []
    for r in rows:
        r = r.ljust(8, '.'); assert len(r) <= 8, r
        out.append(int(''.join('1' if c == '#' else '0' for c in r), 2))
    return bytes(out)

def _width(b):
    return max((x + 1 for r in b for x in range(8) if r >> (7 - x) & 1), default=0)

# Lowercase combining marks (Width = 0, blitted with OR onto vowel column)
# Top marks in rows 0-1:
COMB_MARKS = {
    # Single marks
    '\ue001': ('acute', [
        '..#.....',
        '.#......',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue002': ('grave', [
        '.#......',
        '..#.....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue003': ('circumflex', [
        '..#.....',
        '.#.#....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue004': ('smooth', [
        '##......',
        '.#......',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue005': ('rough', [
        '##......',
        '#.......',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue006': ('smooth acute', [
        '##.#....',
        '.##.....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue007': ('rough acute', [
        '##.#....',
        '###.....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue008': ('smooth grave', [
        '####....',
        '.##.....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue009': ('rough grave', [
        '####....',
        '###.....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue00a': ('smooth circumflex', [
        '##.#....',
        '.#.#....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue00b': ('rough circumflex', [
        '##.#....',
        '##.#....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue00c': ('diaeresis', [
        '.#.#....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue00d': ('diaeresis acute', [
        '.#.#....',
        '..#.....',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),
    '\ue00e': ('diaeresis grave', [
        '.#.#....',
        '.#......',
        '........',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 0),

    # Uppercase preceding marks (Width = 2 or 3)
    '\ue010': ('cap smooth', [
        '........',
        '##......',
        '.#......',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 2),
    '\ue011': ('cap rough', [
        '........',
        '##......',
        '#.......',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 2),
    '\ue012': ('cap smooth acute', [
        '........',
        '##.#....',
        '.##.....',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 3),
    '\ue013': ('cap rough acute', [
        '........',
        '##.#....',
        '###.....',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 3),
    '\ue014': ('cap smooth circ', [
        '........',
        '##.#....',
        '.#.#....',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 3),
    '\ue015': ('cap rough circ', [
        '........',
        '##.#....',
        '##.#....',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 3),
    '\ue016': ('cap smooth grave', [
        '........',
        '####....',
        '.##.....',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 3),
    '\ue017': ('cap rough grave', [
        '........',
        '####....',
        '###.....',
        '........',
        '........',
        '........',
        '........',
        '........'
    ], 3),
}

# Fast lookup for decomposing NFD diacritics
LOWER_COMB_MAP = {
    (ACUTE,): '\ue001',
    (GRAVE,): '\ue002',
    (CIRC,): '\ue003',
    (SMOOTH,): '\ue004',
    (ROUGH,): '\ue005',
    (DIA,): '\ue00c',
    (ACUTE, SMOOTH): '\ue006',
    (ACUTE, ROUGH): '\ue007',
    (GRAVE, SMOOTH): '\ue008',
    (GRAVE, ROUGH): '\ue009',
    (SMOOTH, CIRC): '\ue00a',
    (ROUGH, CIRC): '\ue00b',
    (ACUTE, DIA): '\ue00d',
    (GRAVE, DIA): '\ue00e',
}

UPPER_PRECEDING_MAP = {
    (SMOOTH,): '\ue010',
    (ROUGH,): '\ue011',
    (ACUTE, SMOOTH): '\ue012',
    (ACUTE, ROUGH): '\ue013',
    (SMOOTH, CIRC): '\ue014',
    (ROUGH, CIRC): '\ue015',
    (GRAVE, SMOOTH): '\ue016',
    (GRAVE, ROUGH): '\ue017',
}

def compose(ch):
    """Return (8 row bytes, pixel width) for a character, combining mark, or punctuation."""
    if ch in COMB_MARKS:
        _, rows, w = COMB_MARKS[ch]
        return _bits(rows), w
    if ch == '·':
        rows = [''] * 8; rows[4] = '#'; b = _bits(rows); return b, 1
    d = unicodedata.normalize('NFD', ch); base = d[0]
    marks = tuple(sorted(ord(m) for m in d[1:]))

    if base in UP:
        b = _bits(list(UP[base]))
        return b, _width(b)

    if base in LO:
        b_rows = list(LO[base])
        if marks:
            top_marks = tuple(m for m in marks if m != SUB)
            m_sym = LOWER_COMB_MAP.get(top_marks)
            if m_sym:
                _, m_rows, _ = COMB_MARKS[m_sym]
                b_rows[0] = m_rows[0]
                b_rows[1] = m_rows[1]
        b = _bits(b_rows)
        return b, _width(b)

    raise KeyError(f'no glyph art for {ch!r}')
