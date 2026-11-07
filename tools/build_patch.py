#!/usr/bin/env python3
"""Harry Potter and the Sorcerer's Stone (GBC) - Greek patch builder.
Usage: build_patch.py base.gbc script.tsv out.gbc [out.ips] [full|reduced|strict] [us|uk]
Replaces one English text slot (us = banks 0x20-0x25, the menu default; uk = banks 0x26-0x2B) with the Greek script
(untranslated rows become Greek-letter transliteration), assigns symbol codes, and rewrites the font glyphs and width tables.
Writes <out.gbc>.symbols.json and <out.gbc>.report.txt next to the output ROM. See docs/translation_guide.md."""
import sys,heapq,unicodedata,collections,json
sys.path.insert(0,__import__('os').path.dirname(__file__))
from glyphs import compose, UP, LO
SLOT_BANK=0x26; N_STR=3063
# (glyph data base, width table) for the three in-game fonts. Glyph for code c = base + 8*c, row 0 first.
FONTS=[(0x2a5cab,0x682b),(0x2a60c3,0x692b),(0x2a64e3,0x68ab)]
BOX_W=93   # text-box wrap width in pixels: lines up to 93 px are known to fit, 101 px overflows (see docs/translation_guide.md)
END=0x7f
def decode_stream(rom,start,tree):
    b=0;c=1;i=start;out=[]
    while True:
        bit=1 if rom[i]&c else 0
        b=tree[(b*2+bit)&0xFF]; c=(c<<1)&0xFF
        if c==0: c=1;i+=1
        if b&0x80:
            ch=b&0x7f
            if ch==END:
                if out: out[-1]|=0x80
                return bytes(out)
            out.append(ch); b=0
def read_slot(rom,bank):
    B=bank*0x4000; cnt=rom[B+0x23e6]; tree=rom[B+0x23e7:B+0x23e7+2*cnt]+bytes(256-2*cnt)
    strs=[]
    for k in range(N_STR):
        o=rom[B+1+3*k]; p=rom[B+2+3*k]|rom[B+3+3*k]<<8
        strs.append(bytes(x&0x7f for x in decode_stream(rom,(bank+o)*0x4000+p,tree)))
    return strs
LAT2GR={'a':'α','b':'β','c':'κ','d':'δ','e':'ε','f':'φ','g':'γ','h':'η','i':'ι','j':'ι','k':'κ','l':'λ','m':'μ','n':'ν','o':'ο','p':'π','q':'κ','r':'ρ','s':'σ','t':'τ','u':'υ','v':'β','w':'ω','x':'ξ','y':'υ','z':'ζ'}
def translit(raw):
    out=[]
    for i,x in enumerate(raw):
        ch=chr(x)
        if x==0x0c: out.append('ε'); continue
        if ch.isalpha() and ch.isascii():
            g=LAT2GR[ch.lower()]
            if ch.isupper(): g=g.upper() if g!='ς' else 'Σ'
            out.append(g)
        elif x<0x20: out.append('ε')
        else: out.append(ch)
    s=''.join(out)
    # final sigma
    s2=[]
    for i,ch in enumerate(s):
        nxt=s[i+1] if i+1<len(s) else ' '
        if ch=='σ' and not (nxt.isalpha() and nxt in 'αβγδεζηθικλμνξοπρστυφχψως'): ch='ς'
        s2.append(ch)
    return ''.join(s2)
def huffman(freq):
    h=[(f,i,('L',s)) for i,(s,f) in enumerate(sorted(freq.items()))]; heapq.heapify(h); n=len(h)
    while len(h)>1:
        f1,_,a=heapq.heappop(h); f2,_,b=heapq.heappop(h); heapq.heappush(h,(f1+f2,n,('N',a,b))); n+=1
    return h[0][2]
def build_tree(root):
    # BFS numbering of internal nodes; root=0
    nodes=[root]; idx={id(root):0}; q=[root]; i=0
    while i<len(q):
        nd=q[i]; i+=1
        for ch in nd[1:]:
            if ch[0]=='N': idx[id(ch)]=len(q); q.append(ch)
    tree=bytearray(2*len(q)); codes={}
    def walk(nd,path):
        for bit,ch in enumerate(nd[1:]):
            if ch[0]=='L': tree[2*idx[id(nd)]+bit]=0x80|ch[1]; codes[ch[1]]=path+[bit]
            else: tree[2*idx[id(nd)]+bit]=idx[id(ch)]; walk(ch,path+[bit])
    walk(root,[]); return bytes(tree),codes
def encode(codes,syms):
    bits=[]
    for s in syms: bits+=codes[s]
    bits+=codes[END]; out=bytearray()
    for i in range(0,len(bits),8):
        v=0
        for k,b in enumerate(bits[i:i+8]): v|=b<<k
        out.append(v)
    return bytes(out)
def reduce_marks(t):
    out=[]
    for ch in unicodedata.normalize('NFD',t):
        o=ord(ch)
        if o in (0x313,0x314,0x345): continue        # breathings, iota subscript dropped
        if o==0x300: ch='\u0301'                     # grave -> acute
        out.append(ch)
    return unicodedata.normalize('NFC',''.join(out))
PUNCT={'“':'"','”':'"','«':'"','»':'"','‘':"'",'—':'-','–':'-','…':'...','\u00a0':' ','\u0387':'·','\u037e':';','\u2019':'’'}
def normalize(t,stats=None):
    """Make a Greek string drawable with this font: NFC; punctuation folded to the game's glyphs; iota subscript dropped;
    capitals lose all marks; diaeresis dropped when an accent is also present."""
    out=[]
    for ch in unicodedata.normalize('NFC',t):
        ch=PUNCT.get(ch,ch)
        for c in (unicodedata.normalize('NFC',ch) if len(ch)==1 else ch):
            d=unicodedata.normalize('NFD',c); base,marks=d[0],[m for m in d[1:]]
            if base in UP or base in LO:
                keep=[]
                for m in marks:
                    o=ord(m)
                    if o==0x345: stat(stats,'iota subscript dropped'); continue
                    if base in UP: stat(stats,'mark on capital dropped'); continue
                    keep.append(m)
                if any(ord(m)==0x308 for m in keep) and any(ord(m) in (0x300,0x301,0x342) for m in keep):
                    keep=[m for m in keep if ord(m)!=0x308]; stat(stats,'diaeresis dropped (accent kept)')
                c=unicodedata.normalize('NFC',base+''.join(keep))
            out.append(c)
    return ''.join(out)
def stat(stats,k):
    if stats is not None: stats[k]=stats.get(k,0)+1
def adv(widths,s): return sum(widths(c)+1 for c in s)
def _variants(ch):
    """Simpler stand-ins for a marked lowercase form, best first: grave->acute, then drop the breathing,
    then drop the accent (keep the breathing), then the bare letter."""
    d=unicodedata.normalize('NFD',ch); base,marks=d[0],[ord(m) for m in d[1:]]
    acc=[m for m in marks if m in (0x300,0x301,0x342)]; br=[m for m in marks if m in (0x313,0x314)]
    out=[]
    def mk(ms): return unicodedata.normalize('NFC',base+''.join(chr(m) for m in ms))
    if 0x300 in acc: out.append(mk([0x301]+br))
    if br and acc: out.append(mk(acc))
    if br and acc: out.append(mk(br))
    out.append(base)
    seen=[];[seen.append(v) for v in out if v!=ch and v not in seen]
    return seen
def fit_forms(texts,pool_size,extra_fixed=()):
    """Merge the rarest marked lowercase forms into simpler existing ones until the symbol count fits the code pool.
    Returns (new texts, {form: (replacement, occurrences)})."""
    cnt=collections.Counter(ch for t in texts for ch in t if not (ord(ch)<0x80 and not ch.isalpha()) and ch!='’')
    subs={}
    def marked(ch): return len(unicodedata.normalize('NFD',ch))>1 and ch in cnt and unicodedata.normalize('NFD',ch)[0] in LO
    while len(cnt)>pool_size:
        cand=[c for c in cnt if marked(c)]
        if not cand: break
        rare=min(cand,key=lambda c:(cnt[c],c))
        vs=_variants(rare)
        rep=next((v for v in vs if v in cnt),vs[-1])
        subs[rare]=(rep,cnt[rare]); cnt[rep]+=cnt[rare]; del cnt[rare]
    if subs:
        # chains (a->b, b->c) resolve to the final form
        def final(c):
            while c in subs: c=subs[c][0]
            return c
        texts=[''.join(final(ch) for ch in t) for t in texts]
    return texts,subs
def load_tsv(path):
    tr={}
    for line in open(path,encoding='utf-8'):
        p=line.rstrip('\n').split('\t')
        if len(p)>=3 and p[0].isdigit() and p[2].strip(): tr[int(p[0])]=unicodedata.normalize('NFC',p[2].rstrip('\r\n'))   # leading/trailing spaces are kept (UI alignment)
    return tr
def make_ips(a,b):
    recs=[];i=0;n=len(a)
    while i<n:
        if a[i]!=b[i]:
            j=i
            while j<n and (a[j]!=b[j] or (j+8<n and any(a[k]!=b[k] for k in range(j,j+8)))) and j-i<0xFFFF: j+=1
            if i==0x454F46: i-=1
            recs.append((i,b[i:j])); i=j
        else: i+=1
    out=bytearray(b'PATCH')
    for off,data in recs:
        out+=off.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
    out+=b'EOF'; return bytes(out)
def main(base,tsv,outrom,outips=None,mode='full',slot='us'):
    global SLOT_BANK
    SLOT_BANK={'uk':0x26,'us':0x20}[slot.lower()]   # which language slot gets replaced (US = the menu's default)
    rom=bytearray(open(base,'rb').read()); orig=bytes(rom)
    uk=read_slot(rom,SLOT_BANK); tr=load_tsv(tsv)
    stats={}
    if mode=='reduced': tr={k:reduce_marks(v) for k,v in tr.items()}
    tr={k:normalize(v,stats) for k,v in tr.items()}
    texts=[]
    for k in range(N_STR): texts.append(tr[k] if k in tr else translit(uk[k]))
    reserved={0,END}
    for s_ in uk:
        for x in s_:
            if not (chr(x).isascii() and chr(x).isalpha()) and x!=0x0c and x>=0x20: reserved.add(x)
    reserved|={0x40,0x3c}  # '@' variable escape; '<' draws extra dots in this engine
    need=collections.OrderedDict(); ascii_ok=lambda ch: ord(ch)<0x80 and not ch.isalpha()
    for t in texts:
        for ch in t:
            if ch=='’': continue
            if not ascii_ok(ch): need[ch]=need.get(ch,0)+1
    bad=[ch for ch in need if not (unicodedata.normalize('NFD',ch)[0] in UP or unicodedata.normalize('NFD',ch)[0] in LO or ch=='·')]
    if bad: raise SystemExit('Characters with no glyph (replace them in the translation): '+' '.join(f'{c!r}(U+{ord(c):04X})' for c in bad))
    # code pool, safest first: Latin letter codes (ordinary letters in the English text), then 0x01-0x1f, then the rest
    free=[c for c in range(1,0x7f) if c not in reserved]
    pool=[c for c in free if chr(c).isalpha()]+[c for c in free if c<0x20]+[c for c in free if c>=0x20 and not chr(c).isalpha()]
    reduced_subs={}
    if len(need)>len(pool) and mode!='strict':
        texts,reduced_subs=fit_forms(texts,len(pool))
        need=collections.OrderedDict()
        for t in texts:
            for ch in t:
                if ch=='’': continue
                if not ascii_ok(ch): need[ch]=need.get(ch,0)+1
    forms=sorted(need,key=lambda ch:(-need[ch],ch))
    if len(forms)>len(pool):
        raise SystemExit(f'Too many distinct symbols: need {len(forms)}, pool {len(pool)}. Rarest forms: '+' '.join(forms[len(pool):])+'  (use mode "reduced", or rewrite those words)')
    cmap={ch:pool[i] for i,ch in enumerate(forms)}
    def to_syms(t):
        return [0x27 if ch=='’' else cmap.get(ch,ord(ch)) for ch in t]
    streams_syms=[to_syms(t) for t in texts]
    freq=collections.Counter()
    for s_ in streams_syms: freq.update(s_); freq[END]+=1
    tree,codes=build_tree(huffman(freq)); N=len(tree)//2
    assert N<=127 and len(tree)<=254,'tree too big'
    B=SLOT_BANK*0x4000
    rom[B+0x23e6]=N; rom[B+0x23e7:B+0x23e7+len(tree)]=tree
    ptr=0x23e7+len(tree); off=0; used=0; overflow=0
    for k,s_ in enumerate(streams_syms):
        data=encode(codes,s_)
        if ptr+len(data)>0x4000:
            if off<5: off+=1; ptr=1
            elif off==5:
                assert all(b==0xff for b in orig[0xff*0x4000:0x100*0x4000]),'bank 0xFF is not free'
                off=0xff-SLOT_BANK; ptr=1
            else: raise SystemExit('script does not fit even with the overflow bank')
        if off>5: overflow+=len(data)
        a=(SLOT_BANK+off)*0x4000+ptr; rom[a:a+len(data)]=data
        rom[B+1+3*k]=off; rom[B+2+3*k]=ptr&0xff; rom[B+3+3*k]=ptr>>8
        ptr+=len(data); used+=len(data)
    # fonts: glyph bitmaps AND width tables (the engine spaces text with the width table; width = pixels used)
    width_of={}
    for ch,code in cmap.items():
        g,w=compose(ch); width_of[ch]=w
        for gb,wt in FONTS:
            rom[gb+code*8:gb+code*8+8]=g; rom[wt+code]=w
    open(outrom,'wb').write(rom)
    if outips: open(outips,'wb').write(make_ips(orig,bytes(rom)))
    json.dump({ch:code for ch,code in cmap.items()},open(outrom+'.symbols.json','w'),ensure_ascii=False,indent=0)
    # report: wrapping estimate with the real widths (space = original table value)
    wt=orig[FONTS[0][1]:FONTS[0][1]+128]; sp=wt[0x20]+1
    def pw(word): return sum((width_of[c] if c in width_of else (wt[0x27] if c=='’' else wt[ord(c)]))+1 for c in word)
    longest=[];lines_n=[]
    for k,t in enumerate(texts):
        cur=0;nl=1
        for w_ in t.split(' '):
            ww=pw(w_)
            if ww>BOX_W: longest.append((k,w_,ww))
            if cur and cur+sp+ww>BOX_W: nl+=1;cur=ww
            else: cur=cur+sp+ww if cur else ww
        lines_n.append(nl)
    rep=[f'strings {N_STR} translated {len(tr)} | symbols {len(cmap)} of {len(pool)} free codes | tree nodes {N} | script bytes {used} | final bank offset {off} ptr {ptr:#x}',
         f'bytes in the overflow bank (0xFF): {overflow}',
         f'normalisation: {stats if stats else "nothing needed"}',
     (f'symbol limit: {len(reduced_subs)} rare forms merged into simpler ones ({sum(n for r,n in reduced_subs.values())} occurrences): '+', '.join(f'{a}->{b} x{n}' for a,(b,n) in sorted(reduced_subs.items(),key=lambda kv:-kv[1][1]))) if reduced_subs else 'symbol limit: no merging needed',
         f'estimated lines at {BOX_W}px: longest string {max(lines_n)} lines (long strings page with the arrow, so this is informational)',
         f'words wider than the box ({len(longest)}): '+', '.join(f'#{k} {w!r}={x}px' for k,w,x in longest[:20])]
    print('\n'.join(rep)); open(outrom+'.report.txt','w').write('\n'.join(rep)+'\n')
    return cmap,texts
if __name__=='__main__': main(*sys.argv[1:])
