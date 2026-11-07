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

## 3. The reduced polytonic set

The source script is full polytonic Greek. `tools/build_patch.py` converts it to what the 8x8 font can draw:

1. **Normalisation** - the text is made NFC; typographic punctuation is folded to ASCII; **iota subscripts are dropped**; **capitals lose all marks**; a **diaeresis is dropped when an accent is also present**.
2. **Composition** - every lowercase vowel (and ρ) can carry any mix of breathing + accent (acute, grave, circumflex) or a diaeresis. A mark takes rows 0-1 of the cell, row 2 stays empty, the 4-pixel-high body sits in rows 3-6.
3. **Symbol limit** - the text engine has **97** unused character codes. Each distinct drawn form needs its own code. If the script needs more, the rarest marked forms are merged into simpler ones in this order: grave to acute, drop the breathing, drop the accent (keep the breathing), bare letter. Every merge is written to `<output>.report.txt`.

Merges applied to this release (21 forms, 325 occurrences out of about 120,000 characters):

| Merged | Into | Times |
| :--- | :--- | ---: |
| ἆ | ᾶ | 40 |
| ῥ | ρ | 34 |
| ὠ | ω | 31 |
| ὡ | ω | 29 |
| ὤ | ώ | 25 |
| ὃ | ὸ | 23 |
| ἁ | α | 22 |
| ἥ | ή | 20 |
| ἅ | ά | 16 |
| ἷ | ῖ | 15 |
| ὧ | ῶ | 15 |
| ἃ | ὰ | 10 |
| ἠ | η | 9 |
| ϊ | ι | 8 |
| ἣ | ὴ | 6 |
| ἧ | ῆ | 6 |
| ἓ | ὲ | 5 |
| ὓ | ὺ | 5 |
| ὢ | ὼ | 3 |
| ἳ | ὶ | 2 |
| ὂ | ὸ | 1 |

## 4. Length and layout limits

* The engine **word-wraps** automatically - no string contains a line-break code (the only forced break is `_`).
* Text advances by **glyph width + 1 pixel**. Measured from the English line breaks: a line of up to **93 px** is known to fit, **101 px** overflows, so the real limit is somewhere in 93-100 px. The builder warns about any single word wider than 93 px (this release: row 2585, 96 px).
* The dialogue box shows three lines; longer strings page forward with the arrow.
* ROM space: the Greek script compresses to 84,514 bytes. The English US slot has room for roughly 88 KB (estimate), plus a free 16 KB bank (`0xFF`) that the builder uses automatically if needed (not needed in this release).

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
