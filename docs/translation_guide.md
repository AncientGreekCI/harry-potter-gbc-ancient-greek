# Translation & Technical Guide

How the Greek script is stored, converted to the reduced glyph set, compressed and written into the ROM. Everything here was worked out from the clean USA/Europe ROM and checked in an emulator.

## 1. Script format

`text/greek_script.tsv` has one row per game string, 3,063 rows (`0000`-`3062`):

```text
index<TAB>x<TAB>greek text
```

* The middle column is the literal letter `x` (a placeholder kept from the original English dump format).
* An **empty** third column means *leave the string alone*: numbers, dates, placeholders and the single string that contains the special `<0c>` code (row `2601`). The builder then keeps the English text, converted letter-by-letter to Greek glyphs.
* Leading, trailing and double spaces are part of the text (327 English strings use them to align menus); they are preserved.
* The English reference script is not stored in this repository. Dump it from your own ROM: `python3 tools/dump_script.py rom.gbc english_script.tsv us`.

## 2. Special tokens

| Token | Meaning |
| :--- | :--- |
| `@1` `@2` `@3` | Run-time variables (numbers, names). Copy exactly. |
| `_` | Behaves as a forced line break and is not drawn. Keep every one from the English. |
| `~` | Prints the © sign. |
| `` ` `` | Opening quotation mark (the closing quote is `'`). |
| `<0c>` | Control code 0x0C (appears in one string only). |

## 3. Full Polytonic Orthography & Combining VWF Engine

The translation uses **full polytonic Ancient Greek** with zero merged forms:

1. **Combining Diacritics (width = 0)**:
   * Lowercase accents (acute, grave, circumflex), breathings (smooth, rough), compound breathings+accents, and diaereses are rendered using combining marks with `width = 0`.
   * Diacritics occupy rows 0–1 of the 8×8 cell.
   * Iota subscripts (ᾳ, ῃ, ῳ) occupy row 7 with `width = 0` right beneath the vowel.
   * The blitter uses additive `OR` blitting, compositing diacritics directly onto the vowel column without erasing letter pixels.
2. **Preceding Capital Diacritics (width = 2–3 px)**:
   * Because capital letters are 6 pixels tall (rows 1–6) and leave only 1 row of headroom, uppercase breathings and accents are placed directly *before* the capital letter (e.g. `Ἅ`, `Ὦ`, `Ἐ`) in the authentic classical style.
3. **Z80 Engine Assembly Hooks (Bank 1)**:
   * **Cursor Advance (`$65DA`)**: Hooked to `$7FB7`. Checks the character's width in the active width table at `$DD00`; if `width == 0`, cursor advance is skipped (`$C1B2` is unmodified).
   * **Word-Wrap Bounds Check (`$674D`, `$7066`)**: Hooked to `$7FD0`. If `width == 0`, 0 pixels are added to word width accumulator.
4. **Compression Optimization**:
   * The top 24 most frequent accented vowels are precomposed as single tokens to keep Huffman codes compact.
   * Overflow dialogue entries cleanly pack into free Bank `0xFF`.
   * **0 forms merged** — 100% of polytonic distinctions are preserved.

## 4. Length and layout limits

* The engine **word-wraps** automatically - no string contains a line-break code (the only forced break is `_`).
* Text advances by **glyph width + 1 pixel** (combining marks with width 0 advance 0 pixels).
* The dialogue box shows three lines; longer strings page forward with the arrow.
* ROM space: the Greek script compresses to ~93 KB, packed across banks `0x20`–`0x25` plus ~4.3 KB in the free overflow bank (`0xFF`).

## 5. ROM map

| Item | Location |
| :--- | :--- |
| English US text slot | banks `0x20`-`0x25` (file offset `0x80000`) - **replaced by this patch** |
| English UK text slot | banks `0x26`-`0x2B` (`tools/build_patch.py ... uk` targets this instead) |
| Pointer table | start of the slot: 1 header byte, then 3,063 entries of 3 bytes (bank offset 0-5, pointer low, pointer high) |
| Huffman tree | slot + `0x23E6`: node count, then node pairs |
| Strings | Huffman-coded 7-bit symbols; `0x7F` ends a string |
| Font glyphs (three fonts) | `0x2A5CAB`, `0x2A60C3`, `0x2A64E3` - glyph for code *c* at base + 8*c*, 8 bytes, 1 bit per pixel, row 0 first |
| Width tables | `0x682B`, `0x692B`, `0x68AB` - one byte per code = columns used |

Notes:

* The text slots are separate per language, but the **font is shared**, so after patching only the English US slot shows readable Greek; the other languages display scrambled text.
* Symbol allocation: codes `0x01`-`0x7E` minus `0x00`/`0x7F`, `@` (escape), `<` (draws stray dots), and every non-letter code the English text uses (digits, punctuation, space). Letter codes are reused first, then `0x01`-`0x1F`, then leftover punctuation codes.

## 6. Glyph metrics

```text
row 0   marks / ascenders (β δ ζ θ λ ξ φ ψ start here)
row 1   marks / capital top
row 2   (blank under a mark)
row 3-6 x-height body (4 px) - capitals occupy rows 1-6
row 7   descenders (γ η μ ρ φ ψ ς ζ ξ β)
```

The art is defined in `tools/greek_art.py` (base letters) and `tools/glyphs.py` (mark composition). `gfx/greek_font_sheet.png` shows every form.

## 7. Rebuild workflow

```bash
python3 tools/validate_script.py rom.gbc text/greek_script.tsv
python3 tools/build_patch.py rom.gbc text/greek_script.tsv build/hp1_greek.gbc patches/hp1_greek_us.ips full us
```

Arguments: `base.gbc`, script, output ROM, output IPS (`""` to skip), mode (`full` merges rare forms automatically, `reduced` drops breathings first, `strict` fails instead of merging), slot (`us` or `uk`). The ROM, a `.symbols.json` (character to code map) and a `.report.txt` are written next to the output.
