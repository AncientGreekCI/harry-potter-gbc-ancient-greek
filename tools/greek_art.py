"""Tiny5 Greek Glyph Art for Game Boy Color font (8 rows per glyph).
Exact pixel artwork from the Tiny5 font family by Stefan Schmidt (Gissio).
Lowercase x-height occupies rows 3-6 (4 pixels); ascenders reach rows 1-2;
descenders occupy row 7; rows 0-2 provide clean headroom for polytonic diacritics.
"""

def P(*rows):
    rows = list(rows)
    assert len(rows) == 8, rows
    return rows

def caps(*r5):  return P('', '', *r5, '')             # rows 2-6 (height 5, cap height)
def low(*r4):   return P('', '', '', *r4, '')         # rows 3-6 (height 4, standard lowercase body)
def asc(*r5):   return P('', '', *r5, '')             # rows 2-6 (height 5, ascenders)
def low_d(*r5): return P('', '', '', *r5)             # rows 3-7 (height 5, descenders into row 7)
def full_d(*r6):return P('', '', *r6)                 # rows 2-7 (height 6, tall descenders)

# ---- UPPERCASE GLYPHS (Tiny5: 5px Cap Height, Rows 2-6) --------------------
UP = {
 'A': caps('.##.', '#..#', '####', '#..#', '#..#'),
 'B': caps('###.', '#..#', '###.', '#..#', '###.'),
 'G': caps('####', '#...', '#...', '#...', '#...'),
 'D': caps('..#..', '..#..', '.#.#.', '.#.#.', '#####'),
 'E': caps('####', '#...', '###.', '#...', '####'),
 'Z': caps('####', '..#.', '.#..', '#...', '####'),
 'H': caps('#..#', '#..#', '####', '#..#', '#..#'),
 'Q': caps('.##.', '#..#', '####', '#..#', '.##.'),          # Theta
 'I': caps('#', '#', '#', '#', '#'),
 'K': caps('#..#', '#.#.', '##..', '#.#.', '#..#'),
 'L': caps('..#..', '..#..', '.#.#.', '.#.#.', '#...#'),
 'M': caps('#...#', '##.##', '#.#.#', '#...#', '#...#'),
 'N': caps('#..#', '##.#', '#.##', '#..#', '#..#'),
 'C': caps('####', '....', '.##.', '....', '####'),          # Xi
 'O': caps('.##.', '#..#', '#..#', '#..#', '.##.'),
 'P': caps('####', '#..#', '#..#', '#..#', '#..#'),          # Pi
 'R': caps('###.', '#..#', '###.', '#...', '#...'),          # Rho
 'S': caps('####', '.#..', '..#.', '.#..', '####'),
 'T': caps('###', '.#.', '.#.', '.#.', '.#.'),
 'U': caps('#...#', '.#.#.', '..#..', '..#..', '..#..'),
 'F': caps('.###.', '#.#.#', '#.#.#', '#.#.#', '.###.'),     # Phi
 'X': caps('#...#', '.#.#.', '..#..', '.#.#.', '#...#'),
 'Y': caps('#.#.#', '#.#.#', '.###.', '..#..', '..#..'),     # Psi
 'W': caps('.###.', '#...#', '#...#', '.#.#.', '##.##'),     # Omega
}

# ---- LOWERCASE GLYPHS (Tiny5: 4px x-height, Rows 3-6) ----------------------
LO = {
 'a': low('.##', '#.#', '#.#', '.##'),                       # alpha
 'b': full_d('.#.', '#.#', '##.', '#.#', '##.', '#..'),      # beta
 'g': low_d('#.#', '#.#', '.#.', '.#.', '.#.'),              # gamma
 'd': asc('.##', '.#.', '#.#', '#.#', '.#.'),                # delta
 'e': low('###', '.#.', '#..', '.##'),                       # epsilon
 'z': full_d('###', '.#.', '#..', '#..', '.##', '..#'),      # zeta
 'h': low_d('##.', '#.#', '#.#', '#.#', '..#'),              # eta
 'q': asc('.#.', '#.#', '###', '#.#', '.#.'),                # theta
 'i': low('#.', '#.', '#.', '.#'),                           # iota
 'k': low('#.#', '##.', '#.#', '#.#'),                       # kappa
 'l': asc('#..', '.#.', '.#.', '#.#', '#.#'),                # lambda
 'm': low_d('#.#', '#.#', '#.#', '###', '#..'),              # mu
 'n': low('#.#', '#.#', '.#.', '.#.'),                       # nu
 'c': full_d('###', '#..', '.##', '#..', '.##', '..#'),      # xi
 'o': low('.#.', '#.#', '#.#', '.#.'),                       # omicron
 'p': low('###', '#.#', '#.#', '#.#'),                       # pi
 'r': low_d('.#.', '#.#', '#.#', '##.', '#..'),              # rho
 's': low('.###', '#.#.', '#.#.', '.#..'),                   # sigma
 'j': low_d('.##', '#..', '#..', '.##', '..#'),              # final sigma
 't': low('###', '.#.', '.#.', '..#'),                       # tau
 'u': low('#.#', '#.#', '#.#', '.#.'),                       # upsilon
 'f': low_d('#..#.', '#.#.#', '#.#.#', '.###.', '..#..'),    # phi
 'x': low_d('#.#', '#.#', '.#.', '#.#', '#.#'),              # chi
 'y': full_d('..#..', '#.#.#', '#.#.#', '.###.', '..#..', '..#..'), # psi
 'w': low('#...#', '#.#.#', '#.#.#', '.#.#.'),               # omega
}

_UPK = dict(zip('ABGDEZHQIKLMNCOPRSTUFXYW', 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'))
_LOK = dict(zip('abgdezhqiklmncoprsjtufxyw', 'αβγδεζηθικλμνξοπρσςτυφχψω'))
UP = {_UPK[k]: v for k, v in UP.items()}
LO = {_LOK[k]: v for k, v in LO.items()}
