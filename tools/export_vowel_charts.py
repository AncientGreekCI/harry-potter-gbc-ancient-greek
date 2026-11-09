import sys, os, unicodedata
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from glyphs import compose, LOWER_COMB_MAP, UPPER_PRECEDING_MAP, COMB_MARKS, SUB
from greek_art import UP, LO

OUT_DIR = r"C:\Users\User\.gemini\antigravity\brain\f6a80726-eb7e-42d4-820a-0c47840e13ec"
os.makedirs(OUT_DIR, exist_ok=True)

FONT_LABEL = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
FONT_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 18)
FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
FONT_MONO = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 14)

def render_vowel_tile(ch):
    d = unicodedata.normalize('NFD', ch)
    base = d[0]
    marks = tuple(sorted(ord(m) for m in d[1:]))
    tile = bytearray(8)
    w = 0
    if base in UP:
        b, bw = compose(base)
        tile = bytearray(b)
        w = bw
    elif base in LO:
        top_marks = tuple(m for m in marks if m != SUB)
        has_sub = SUB in marks
        if top_marks:
            m_sym = LOWER_COMB_MAP.get(top_marks)
            if m_sym:
                mb, _ = compose(m_sym)
                for y in range(8): tile[y] |= mb[y]
        if has_sub:
            sb, _ = compose('\ue00f')
            for y in range(8): tile[y] |= sb[y]
        bb, bw = compose(base)
        for y in range(8): tile[y] |= bb[y]
        w = bw
    return bytes(tile), w

def draw_glyph_cell(ch, label=None, scale=12):
    """Draw a single 8x8 glyph in a styled card."""
    tile, w = render_vowel_tile(ch)
    
    # 8x8 tile scaled + margins + labels
    tile_w = 8 * scale
    tile_h = 8 * scale
    
    card_w = tile_w + 32
    card_h = tile_h + 80
    
    img = Image.new("RGBA", (card_w, card_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Rounded card background
    card_rect = [0, 0, card_w - 1, card_h - 1]
    draw.rounded_rectangle(card_rect, radius=10, fill="#1e1e24", outline="#3a3d4a", width=2)
    
    # Grid area
    gx = 16
    gy = 16
    
    # Pixel background (Game Boy Color light olive/screen tint)
    grid_rect = [gx, gy, gx + tile_w, gy + tile_h]
    draw.rectangle(grid_rect, fill="#2b2d38", outline="#4a4d5e", width=1)
    
    # Draw subtle grid lines
    for r in range(9):
        # highlight row boundaries: row 2 (separator), row 3 (x-height top), row 7 (subscript)
        col = "#383a48"
        if r in [2, 3, 7]: col = "#52576b"
        draw.line([(gx, gy + r * scale), (gx + tile_w, gy + r * scale)], fill=col, width=1)
    for c in range(9):
        draw.line([(gx + c * scale, gy), (gx + c * scale, gy + tile_h)], fill="#383a48", width=1)
        
    # Draw pixels
    for y in range(8):
        b = tile[y]
        for x in range(8):
            if (b >> (7 - x)) & 1:
                # Color code:
                # rows 0-1: accent (coral/amber)
                # rows 3-6: letter body (crisp white/cyan)
                # row 7: subscript (mint green)
                if y in [0, 1]:
                    pcol = "#fca311" # gold/amber for diacritics
                elif y == 7 and (SUB in [ord(m) for m in unicodedata.normalize('NFD', ch)[1:]]):
                    pcol = "#00f5d4" # mint teal for iota subscript
                else:
                    pcol = "#ffffff" # bright white for base letter
                
                px = gx + x * scale
                py = gy + y * scale
                draw.rectangle([px + 1, py + 1, px + scale - 1, py + scale - 1], fill=pcol)
                
    # Labels
    name_txt = label if label else ch
    draw.text((card_w // 2, gy + tile_h + 16), name_txt, font=FONT_BOLD, fill="#ffffff", anchor="mt")
    
    u_txt = f"U+{ord(ch):04X}" if len(ch) == 1 else ""
    draw.text((card_w // 2, gy + tile_h + 42), u_txt, font=FONT_MONO, fill="#9da3b4", anchor="mt")
    draw.text((card_w // 2, gy + tile_h + 58), f"width: {w}px", font=FONT_MONO, fill="#6c7280", anchor="mt")
    
    return img

def create_gallery_strip(title, char_list, out_filename, scale=11):
    cards = [draw_glyph_cell(c, scale=scale) for c in char_list]
    
    margin = 24
    spacing = 16
    title_h = 60
    
    cols = len(char_list)
    total_w = margin * 2 + cols * cards[0].width + (cols - 1) * spacing
    total_h = margin * 2 + title_h + cards[0].height
    
    img = Image.new("RGBA", (total_w, total_h), "#131418")
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.text((margin, margin + 4), title, font=FONT_TITLE, fill="#fca311")
    draw.text((margin, margin + 34), "Exact 8x8 Tiny5 rendering in Harry Potter GBC (Gold=Accent, White=Letter, Teal=Iota Subscript)", font=FONT_LABEL, fill="#9da3b4")
    
    # Place cards
    x = margin
    y = margin + title_h
    for c in cards:
        img.paste(c, (x, y), c)
        x += c.width + spacing
        
    out_path = os.path.join(OUT_DIR, out_filename)
    img.save(out_path)
    print(f"Saved: {out_path}")

def create_grid_sheet(title, rows, out_filename, scale=9):
    """rows is list of (category_label, [char1, char2, ...])"""
    margin = 28
    col_spacing = 14
    row_spacing = 20
    header_h = 70
    cat_label_w = 170
    
    # Sample card size
    sample_card = draw_glyph_cell('α', scale=scale)
    card_w = sample_card.width
    card_h = sample_card.height
    
    max_cols = max(len(chars) for _, chars in rows)
    total_w = margin * 2 + cat_label_w + max_cols * card_w + (max_cols - 1) * col_spacing
    total_h = margin * 2 + header_h + len(rows) * (card_h + row_spacing)
    
    img = Image.new("RGBA", (total_w, total_h), "#121316")
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.text((margin, margin), title, font=FONT_TITLE, fill="#ffffff")
    draw.text((margin, margin + 34), "Pixel-perfect representation of Game Boy Color font engine: Rows 0-1 Accents | Row 2 Gap | Rows 3-6 Body | Row 7 Subscript", font=FONT_LABEL, fill="#9da3b4")
    
    curr_y = margin + header_h
    for cat_name, char_list in rows:
        # Category label on left
        draw.text((margin, curr_y + card_h // 2), cat_name, font=FONT_BOLD, fill="#fca311", anchor="lm")
        
        curr_x = margin + cat_label_w
        for ch in char_list:
            c_img = draw_glyph_cell(ch, scale=scale)
            img.paste(c_img, (curr_x, curr_y), c_img)
            curr_x += card_w + col_spacing
            
        curr_y += card_h + row_spacing
        
    out_path = os.path.join(OUT_DIR, out_filename)
    img.save(out_path)
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    # 1. Master Vowel Comparison (All 7 vowels across the 10 core forms)
    vowels_7 = ['α', 'ε', 'η', 'ι', 'ο', 'υ', 'ω']
    master_rows = [
        ("1. Plain Base", ['α', 'ε', 'η', 'ι', 'ο', 'υ', 'ω']),
        ("2. Acute (ὀξεῖα)", ['ά', 'έ', 'ή', 'ί', 'ό', 'ύ', 'ώ']),
        ("3. Grave (βαρεῖα)", ['ὰ', 'ὲ', 'ὴ', 'ὶ', 'ὸ', 'ὺ', 'ὼ']),
        ("4. Circumflex (περισπ.)", ['ᾶ', '—', 'ῆ', 'ῖ', '—', 'ῦ', 'ῶ']),
        ("5. Smooth (ψιλή)", ['ἀ', 'ἐ', 'ἠ', 'ἰ', 'ὀ', 'ὐ', 'ὠ']),
        ("6. Rough (δασεῖα)", ['ἁ', 'ἑ', 'ἡ', 'ἱ', 'ὁ', 'ὑ', 'ὡ']),
        ("7. Smooth Acute", ['ἄ', 'ἔ', 'ἤ', 'ἴ', 'ὄ', 'ὔ', 'ὤ']),
        ("8. Rough Acute", ['ἅ', 'ἕ', 'ἥ', 'ἵ', 'ὅ', 'ὕ', 'ὥ']),
        ("9. Circumflex Breathing", ['ἆ', '—', 'ἦ', 'ἶ', '—', 'ὖ', 'ὦ']),
        ("10. Iota Subscript (ᾳ,ῃ,ῳ)", ['ᾳ', '—', 'ῃ', '—', '—', '—', 'ῳ']),
        ("11. Circ + Iota Subscript", ['ᾷ', '—', 'ῇ', '—', '—', '—', 'ῷ']),
    ]
    # Replace placeholder '—' with space or empty card
    cleaned_rows = []
    for cat, chars in master_rows:
        row_c = []
        for ch in chars:
            row_c.append(ch if ch != '—' else ' ')
        cleaned_rows.append((cat, row_c))
        
    # Build custom grid supporting blank cards
    def draw_cell_safe(ch, scale=9):
        if ch == ' ':
            w = 8 * scale + 32
            h = 8 * scale + 80
            im = Image.new("RGBA", (w, h), (0,0,0,0))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle([0,0,w-1,h-1], radius=10, fill="#18191f", outline="#272933", width=1)
            d.text((w//2, h//2), "—", font=FONT_TITLE, fill="#424656", anchor="mm")
            return im
        return draw_glyph_cell(ch, scale=scale)

    def create_master_sheet(title, rows, out_filename, scale=9):
        margin = 28
        col_spacing = 14
        row_spacing = 16
        header_h = 70
        cat_label_w = 200
        
        sample_card = draw_cell_safe('α', scale=scale)
        card_w = sample_card.width
        card_h = sample_card.height
        
        max_cols = 7
        total_w = margin * 2 + cat_label_w + max_cols * card_w + (max_cols - 1) * col_spacing
        total_h = margin * 2 + header_h + len(rows) * (card_h + row_spacing)
        
        img = Image.new("RGBA", (total_w, total_h), "#0f1013")
        draw = ImageDraw.Draw(img)
        
        draw.text((margin, margin), title, font=FONT_TITLE, fill="#ffffff")
        draw.text((margin, margin + 34), "Exact Game Boy Color 8x8 font rendering: Gold = Accent/Breathing | White = Letter Body | Teal = Iota Subscript", font=FONT_LABEL, fill="#9da3b4")
        
        # Column headers (α, ε, η, ι, ο, υ, ω)
        curr_x = margin + cat_label_w
        for v in vowels_7:
            draw.text((curr_x + card_w // 2, margin + 52), v.upper() + f" ({v})", font=FONT_BOLD, fill="#00f5d4", anchor="mt")
            curr_x += card_w + col_spacing

        curr_y = margin + header_h + 20
        for cat_name, char_list in rows:
            draw.text((margin, curr_y + card_h // 2), cat_name, font=FONT_BOLD, fill="#fca311", anchor="lm")
            curr_x = margin + cat_label_w
            for ch in char_list:
                c_img = draw_cell_safe(ch, scale=scale)
                img.paste(c_img, (curr_x, curr_y), c_img)
                curr_x += card_w + col_spacing
            curr_y += card_h + row_spacing
            
        out_path = os.path.join(OUT_DIR, out_filename)
        img.save(out_path)
        print(f"Saved: {out_path}")

    create_master_sheet("Harry Potter GBC — Greek Polytonic Vowels Master Chart", cleaned_rows, "vowels_master_overview.png", scale=9)
    
    # 2. Individual Vowel Family Strips
    create_gallery_strip("Alpha (α) Polytonic Family", ['α', 'ά', 'ὰ', 'ᾶ', 'ἀ', 'ἁ', 'ἄ', 'ἅ', 'ἆ', 'ἇ', 'ᾳ', 'ᾷ', 'ᾄ', 'ᾅ'], "alpha_family.png", scale=10)
    create_gallery_strip("Eta (η) & Omega (ω) Iota Subscript Families", ['η', 'ή', 'ὴ', 'ῆ', 'ἠ', 'ἡ', 'ἤ', 'ῃ', 'ῇ', 'ω', 'ώ', 'ὼ', 'ῶ', 'ὠ', 'ὡ', 'ὤ', 'ῳ', 'ῷ'], "eta_omega_family.png", scale=10)
    create_gallery_strip("Iota (ι) & Upsilon (υ) Diaeresis Families", ['ι', 'ί', 'ὶ', 'ῖ', 'ἰ', 'ἱ', 'ἴ', 'ϊ', 'ΐ', 'υ', 'ύ', 'ὺ', 'ῦ', 'ὐ', 'ὑ', 'ὔ', 'ϋ', 'ΰ'], "iota_upsilon_family.png", scale=10)
    create_gallery_strip("Uppercase Greek Vowels (with preceding marks)", ['Α', 'Ε', 'Η', 'Ι', 'Ο', 'Υ', 'Ω'], "uppercase_vowels.png", scale=11)
