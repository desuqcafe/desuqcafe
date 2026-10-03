"""Builds the profile README's SVGs: banner, section headers, tech stack,
the cc-mascot hero card and the featured-work cards.

Every SVG is self-contained (fonts subset and embedded, art embedded) because
GitHub shows them as <img>, which loads nothing from outside the file."""
import base64, io, math, os, random, re
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
FRAMES = os.environ.get("YUNSEUL_FRAMES", r"C:\Users\desuu\Desktop\InhyeongClaudeMod\mascot\frames\yunseul")
os.makedirs(OUT, exist_ok=True)

# palette: a moonlit night, antique gold linework, three gemstone accents
NIGHT0, NIGHT1, NIGHT2 = "#0c0713", "#160d22", "#24153a"
SILVER, MIST, DIM = "#ece6f4", "#b3a6c6", "#7d6f92"
GOLD, GOLD_DIM = "#d9b872", "#8f7646"
CRIMSON, AMETHYST, MOON = "#e0435f", "#a77be0", "#6fd6cb"

FONTS = {
    "Cinzel": ("cinzel500.ttf", 500, "normal"),
    "CinzelB": ("cinzel700.ttf", 700, "normal"),
    "Deco": ("deco700.ttf", 700, "normal"),
    "Corm": ("corm500.ttf", 500, "normal"),
    "CormB": ("corm600.ttf", 600, "normal"),
    "CormI": ("corm500i.ttf", 500, "italic"),
}
_tt = {k: TTFont(os.path.join(HERE, "fonts", v[0])) for k, v in FONTS.items()}


def width(text, font, size, spacing=0.0):
    f = _tt[font]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text)
    return w / upm * size + spacing * max(len(text) - 1, 0)


def wrap(text, font, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if width(t, font, size) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_css(svg_body):
    """@font-face rules for the families this SVG uses, each subset to its text."""
    rules = []
    for key, (file, weight, style) in FONTS.items():
        if f"f-{key} " not in svg_body and f'f-{key}"' not in svg_body:
            continue
        chars = set()
        for m in re.finditer(r'class="[^"]*f-%s\b[^"]*"[^>]*>(.*?)</text>' % key, svg_body, re.S):
            chars |= set(re.sub(r"<[^>]+>", "", m.group(1)))
        chars |= set("0123456789")
        opts = subset.Options()
        opts.layout_features = ["kern", "liga"]
        opts.name_IDs = []
        opts.notdef_outline = False
        sub = subset.Subsetter(opts)
        font = TTFont(os.path.join(HERE, "fonts", file), recalcTimestamp=False)  # same bytes on every build
        sub.populate(text="".join(chars).replace("&amp;", "&"))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = None
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(f"@font-face{{font-family:'{key}';font-weight:{weight};font-style:{style};"
                     f"src:url(data:font/ttf;base64,{b64}) format('truetype')}}")
        rules.append(f".f-{key}{{font-family:'{key}',Georgia,serif;font-weight:{weight};font-style:{style}}}")
    return "\n".join(rules)


BASE_CSS = """
.tw{animation:tw var(--d,4s) ease-in-out infinite;animation-delay:var(--dl,0s)}
@keyframes tw{0%,100%{opacity:.12}50%{opacity:var(--mo,.8)}}
.spin{animation:spin var(--d,60s) linear infinite}
.spinr{animation:spin var(--d,80s) linear infinite reverse}
@keyframes spin{to{transform:rotate(360deg)}}
.pulse{animation:pulse 4.5s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.55}50%{opacity:1}}
.rise{animation:rise var(--d,9s) ease-in infinite;animation-delay:var(--dl,0s);opacity:0}
@keyframes rise{0%{opacity:0;transform:translateY(0)}15%{opacity:var(--mo,.6)}100%{opacity:0;transform:translateY(-140px)}}
.fall{animation:fall var(--d,12s) linear infinite;animation-delay:var(--dl,0s);opacity:0}
@keyframes fall{0%{opacity:0;transform:translate(0,-20px) rotate(0)}10%{opacity:.85}90%{opacity:.7}100%{opacity:0;transform:translate(-60px,300px) rotate(300deg)}}
.flap{animation:flap .42s ease-in-out infinite alternate}
@keyframes flap{from{transform:scaleY(1)}to{transform:scaleY(.25)}}
.fly{animation:fly var(--d,26s) linear infinite;animation-delay:var(--dl,0s)}
@keyframes fly{0%{transform:translate(0,0)}50%{transform:translate(calc(var(--dx)/2),-14px)}100%{transform:translate(var(--dx),6px)}}
.shimmer{animation:shimmer 7s ease-in-out infinite}
@keyframes shimmer{0%,60%{transform:translateX(-900px)}100%{transform:translateX(900px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.rise,.fall{opacity:.5}}
"""


def svg(w, h, defs, body, extra_css=""):
    inner = defs + body
    css = font_css(inner) + BASE_CSS + extra_css
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n<defs><style>{css}</style>\n{defs}</defs>\n{body}\n</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{name}: {len(content.encode())/1024:.0f} KB")


GLOW = """<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="softglow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>"""


def stars(rng, w, h, n, ymax=None, rmax=1.2):
    out = []
    for _ in range(n):
        x, y = rng.uniform(4, w - 4), rng.uniform(4, ymax or h - 4)
        r = rng.uniform(0.4, rmax)
        out.append(f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{SILVER}" '
                   f'style="--d:{rng.uniform(2.5,6):.1f}s;--dl:{rng.uniform(0,5):.1f}s;--mo:{rng.uniform(.4,.95):.2f}"/>')
    # a few four-point glints
    for _ in range(max(2, n // 12)):
        x, y, s = rng.uniform(10, w - 10), rng.uniform(8, ymax or h - 8), rng.uniform(3, 5.5)
        out.append(f'<path class="tw" d="M{x:.1f} {y-s:.1f}Q{x:.1f} {y:.1f} {x+s:.1f} {y:.1f}Q{x:.1f} {y:.1f} {x:.1f} {y+s:.1f}'
                   f'Q{x:.1f} {y:.1f} {x-s:.1f} {y:.1f}Q{x:.1f} {y:.1f} {x:.1f} {y-s:.1f}Z" fill="{SILVER}" '
                   f'style="--d:{rng.uniform(3,6):.1f}s;--dl:{rng.uniform(0,4):.1f}s;--mo:.9"/>')
    return "\n".join(out)


def bat(x, y, s, dx, d, dl, color="#05030a", op=0.9):
    wing = "M0 0 C-3 -5 -9 -6 -14 -3 C-11 -2 -10 1 -12 3 C-9 1 -6 2 -5 4 C-3 2 -1 2 0 3 Z"
    return (f'<g transform="translate({x},{y}) scale({s})" opacity="{op}"><g class="fly" style="--dx:{dx}px;--d:{d}s;--dl:{dl}s">'
            f'<g class="flap"><path d="{wing}" fill="{color}"/><path d="{wing}" transform="scale(-1,1)" fill="{color}"/></g>'
            f'<ellipse cx="0" cy="1" rx="2" ry="3" fill="{color}"/>'
            f'<path d="M-1.6 -1.5 L-1.2 -4 L-0.4 -2 M1.6 -1.5 L1.2 -4 L0.4 -2" fill="{color}" stroke="{color}" stroke-width=".6"/></g></g>')


def petal(x, y, s, d, dl, color=CRIMSON):
    return (f'<g transform="translate({x},{y})"><g class="fall" style="--d:{d}s;--dl:{dl}s">'
            f'<path d="M0 0 C{3*s} {-2*s} {5*s} {2*s} 0 {6*s} C{-5*s} {2*s} {-3*s} {-2*s} 0 0Z" fill="{color}" opacity=".8"/></g></g>')


def circle_path(id_, r):
    return f'<path id="{id_}" d="M0 {-r} A{r} {r} 0 1 1 0 {r} A{r} {r} 0 1 1 0 {-r}"/>'


def sigil(id_, cx, cy, r, points, accent, emblem, runes, rng, speed=1.0):
    """A magic circle: rune band, ticks, an inscribed star, a glowing emblem."""
    ticks = []
    for i in range(72):
        a = i / 72 * math.tau
        r0 = r * (0.885 if i % 6 else 0.84)
        ticks.append(f"M{math.cos(a)*r0:.2f} {math.sin(a)*r0:.2f}L{math.cos(a)*r*0.93:.2f} {math.sin(a)*r*0.93:.2f}")
    k = 2 if points in (5, 7, 8) else 1
    if points == 8:
        k = 3
    star = []
    verts = []
    for i in range(points):
        a = -math.pi / 2 + i * math.tau / points
        verts.append((math.cos(a) * r * 0.74, math.sin(a) * r * 0.74))
    order = [(i * k) % points for i in range(points)]
    if points == 6:  # hexagram: two triangles
        star = [f"M{verts[0][0]:.2f} {verts[0][1]:.2f}L{verts[2][0]:.2f} {verts[2][1]:.2f}L{verts[4][0]:.2f} {verts[4][1]:.2f}Z",
                f"M{verts[1][0]:.2f} {verts[1][1]:.2f}L{verts[3][0]:.2f} {verts[3][1]:.2f}L{verts[5][0]:.2f} {verts[5][1]:.2f}Z"]
    else:
        star = ["M" + "L".join(f"{verts[i][0]:.2f} {verts[i][1]:.2f}" for i in order) + "Z"]
    nodes = "".join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r*0.035:.2f}" fill="{NIGHT0}" stroke="{GOLD}" stroke-width=".8"/>' for x, y in verts)
    band = " · ".join([runes] * 3) + " · "
    fs = r * 0.085
    return f"""<g transform="translate({cx},{cy})">
<circle r="{r*1.25:.1f}" fill="url(#halo-{id_})"/>
<defs>{circle_path('rp-' + id_, r * 0.955 - fs * 0.35)}</defs>
<circle r="{r:.1f}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="1"/>
<circle r="{r*0.8:.1f}" fill="none" stroke="{GOLD}" stroke-opacity=".35" stroke-width=".7"/>
<g class="spinr" style="--d:{140/speed:.0f}s"><text class="f-Cinzel" font-size="{fs:.2f}" fill="{GOLD}" fill-opacity=".7" letter-spacing="{fs*0.25:.2f}"><textPath href="#rp-{id_}" xlink:href="#rp-{id_}" textLength="{math.tau*(r*0.955-fs*0.35)*0.985:.1f}">{esc(band.upper())}</textPath></text></g>
<g class="spin" style="--d:{90/speed:.0f}s"><path d="{''.join(ticks)}" stroke="{GOLD}" stroke-opacity=".45" stroke-width=".8"/></g>
<g class="spinr" style="--d:{70/speed:.0f}s"><path d="{''.join(star)}" fill="none" stroke="{accent}" stroke-opacity=".75" stroke-width="1.1"/>{nodes}</g>
<circle r="{r*0.42:.1f}" fill="{NIGHT0}" fill-opacity=".85" stroke="{SILVER}" stroke-opacity=".35" stroke-width=".8"/>
<g class="pulse" filter="url(#glow)" fill="none" stroke="{SILVER}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" transform="scale({r*0.42/30:.3f})">{emblem}</g>
</g>"""


def halo(id_, accent, op=0.35):
    return (f'<radialGradient id="halo-{id_}"><stop offset="0" stop-color="{accent}" stop-opacity="{op}"/>'
            f'<stop offset=".55" stop-color="{accent}" stop-opacity="{op*0.25}"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>')


def frame(w, h, inset=7):
    """Gilded double frame with corner flourishes."""
    o = []
    o.append(f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="none" stroke="#3b2752" />')
    o.append(f'<rect x="{inset}" y="{inset}" width="{w-2*inset}" height="{h-2*inset}" rx="9" fill="none" stroke="{GOLD}" stroke-opacity=".38" stroke-width=".8"/>')
    for (x, y, sx, sy) in [(inset, inset, 1, 1), (w - inset, inset, -1, 1), (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)]:
        o.append(f'<g transform="translate({x},{y}) scale({sx},{sy})" fill="none" stroke="{GOLD}" stroke-width=".9" stroke-opacity=".8">'
                 f'<path d="M4 22 C4 10 10 4 22 4"/><path d="M9 30 C9 16 16 9 30 9" stroke-opacity=".4"/>'
                 f'<path d="M10 10 l4 0 l-4 4 z" fill="{GOLD}" stroke="none"/></g>')
    return "\n".join(o)


def card_bg(id_, w, h, accent):
    return (f'<linearGradient id="bg-{id_}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NIGHT2}"/>'
            f'<stop offset=".55" stop-color="{NIGHT1}"/><stop offset="1" stop-color="{NIGHT0}"/></linearGradient>'
            f'<clipPath id="clip-{id_}"><rect width="{w}" height="{h}" rx="14"/></clipPath>' + halo(id_, accent))


# ---------- emblems, drawn in a 60x60 box centred on 0,0 ----------
EMBLEMS = {
    # a little doll ghost: Inhyeong's world of dolls and ghosts
    "ghost": '<path d="M-14 18 V-4 C-14 -16 -7 -22 0 -22 C7 -22 14 -16 14 -4 V18 L9 13 L4.5 18 L0 13 L-4.5 18 L-9 13 Z"/>'
             '<circle cx="-5" cy="-6" r="1.6" fill="#ece6f4"/><circle cx="5" cy="-6" r="1.6" fill="#ece6f4"/>'
             '<path d="M-3 1 Q0 3.5 3 1"/><path d="M-12 -14 L-17 -20 L-10 -18 M12 -14 L17 -20 L10 -18"/>',
    # woven threads: Weft's cloth
    "weave": '<path d="M-20 -12 C-10 -20 -10 -4 0 -12 S10 -4 20 -12"/><path d="M-20 0 C-10 -8 -10 8 0 0 S10 8 20 0"/>'
             '<path d="M-20 12 C-10 4 -10 20 0 12 S10 20 20 12"/><path d="M-12 -20 V20 M0 -20 V20 M12 -20 V20" stroke-opacity=".55"/>',
    # a shuttle passing between two frames: Loom's live link
    "link": '<rect x="-21" y="-11" width="12" height="22" rx="2"/><rect x="9" y="-11" width="12" height="22" rx="2"/>'
            '<path d="M-6 -4 H6 M3 -7 L6 -4 L3 -1"/><path d="M6 4 H-6 M-3 1 L-6 4 L-3 7"/>',
    # stacked inspector panels: Component Navigator
    "panels": '<rect x="-17" y="-19" width="34" height="10" rx="2"/><rect x="-17" y="-5" width="34" height="10" rx="2"/>'
              '<rect x="-17" y="9" width="34" height="10" rx="2"/><path d="M-12 -14 H-2 M-12 0 H4 M-12 14 H0"/>'
              '<circle cx="11" cy="-14" r="1.4" fill="#ece6f4"/><circle cx="11" cy="0" r="1.4" fill="#ece6f4"/><circle cx="11" cy="14" r="1.4" fill="#ece6f4"/>',
    # a fish on a network: FishySteamworks
    "fish": '<path d="M-16 0 C-8 -12 8 -12 14 0 C8 12 -8 12 -16 0 Z"/><path d="M-16 0 L-22 -7 V7 Z"/>'
            '<circle cx="7" cy="-2" r="1.5" fill="#ece6f4"/><path d="M-2 -6 Q1 0 -2 6"/>'
            '<path d="M0 -20 V-14 M0 14 V20 M-8 -20 H8 M-8 20 H8" stroke-opacity=".6"/>',
    # two arrows chasing round a circle: Syncthing
    "sync": '<path d="M-17 -4 A18 18 0 0 1 13 -13"/><path d="M14 -21 L13 -13 L5 -14"/>'
            '<path d="M17 4 A18 18 0 0 1 -13 13"/><path d="M-14 21 L-13 13 L-5 14"/>'
            '<circle cx="0" cy="0" r="3" fill="#ece6f4"/>',
    # a shield: Data Guardian
    "shield": '<path d="M0 -21 L16 -14 V0 C16 10 8 17 0 21 C-8 17 -16 10 -16 0 V-14 Z"/><path d="M-7 0 L-2 6 L8 -6"/>',
}


def card(id_, w, h, title, status, open_source, desc, tags, emblem, accent, points, runes, seed):
    rng = random.Random(seed)
    sx, sy, sr = 100, h / 2 + 2, 72
    tx, tmax = 194, w - 194 - 24
    size = 24
    while width(title, "CinzelB", size, 0.6) > tmax and size > 15:
        size -= 0.5
    lines = wrap(desc, "Corm", 15.5, tmax)
    status_col = MOON if open_source else MIST
    body = [f'<g clip-path="url(#clip-{id_})">',
            f'<rect width="{w}" height="{h}" fill="url(#bg-{id_})"/>',
            stars(rng, w, h, 26),
            sigil(id_, sx, sy, sr, points, accent, EMBLEMS[emblem], runes, rng),
            '</g>', frame(w, h)]
    y = 54
    body.append(f'<g transform="translate({tx},{y-4})"><path d="M0 -3.5 L3.5 0 L0 3.5 L-3.5 0Z" fill="{status_col}"/></g>')
    ss = 9.5
    while width(status.upper(), "Cinzel", ss, 1.8) > tmax - 10:
        ss -= 0.25
    body.append(f'<text class="f-Cinzel" x="{tx+9}" y="{y}" font-size="{ss}" letter-spacing="1.8" fill="{status_col}">{esc(status.upper())}</text>')
    y += 30
    body.append(f'<text class="f-CinzelB" x="{tx}" y="{y}" font-size="{size}" letter-spacing=".6" fill="{SILVER}">{esc(title)}</text>')
    y += 10
    body.append(f'<path d="M{tx} {y} H{tx+46}" stroke="{accent}" stroke-width="1.2"/><circle cx="{tx+50}" cy="{y}" r="1.6" fill="{accent}"/>')
    y += 21
    for ln in lines:
        body.append(f'<text class="f-Corm" x="{tx}" y="{y}" font-size="15.5" fill="{MIST}">{esc(ln)}</text>')
        y += 19
    tagline, ts, tl = "  ·  ".join(t.upper() for t in tags), 9.0, 1.6
    while width(tagline, "Cinzel", ts, tl) > tmax:
        ts, tl = ts - 0.25, max(tl - 0.1, 0.8)
    body.append(f'<text class="f-Cinzel" x="{tx}" y="{h-26}" font-size="{ts}" letter-spacing="{tl:.2f}" fill="{GOLD}">{esc(tagline)}</text>')
    defs = GLOW + card_bg(id_, w, h, accent)
    return svg(w, h, defs, "\n".join(body))


# ---------- the cc-mascot hero card, with Yunseul's rigged idle loop ----------
def sprite_sheet(mood="idle", step=2, height=290):
    names = sorted((n for n in os.listdir(FRAMES) if re.fullmatch(rf"{mood}-\d+\.png", n)),
                   key=lambda n: int(re.findall(r"\d+", n)[0]))[::step]
    ims = [Image.open(os.path.join(FRAMES, n)).convert("RGBA") for n in names]
    box = None
    for im in ims:
        b = im.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    ims = [im.crop(box) for im in ims]
    fw = round(ims[0].width * height / ims[0].height)
    sheet = Image.new("RGBA", (fw * len(ims), height))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((fw, height), Image.LANCZOS), (i * fw, 0))
    buf = io.BytesIO()
    sheet.save(buf, "WEBP", quality=78, method=6, alpha_quality=70)
    return base64.b64encode(buf.getvalue()).decode(), fw, height, len(ims)


def hero():
    w, h = 840, 360
    rng = random.Random(7)
    sheet, fw, fh, n = sprite_sheet()
    ax, feet = 548, h - 34
    ay = feet - fh
    loop_s = n * 2 / 12  # the overlay plays idle at 12 fps; every 2nd frame kept
    css = (f".sheet{{animation:play {loop_s:.2f}s steps({n}) infinite}}"
           f"@keyframes play{{to{{transform:translateX(-{fw*n}px)}}}}")
    defs = GLOW + card_bg("hero", w, h, CRIMSON) + f"""
<radialGradient id="moonglow"><stop offset="0" stop-color="#d9d2ee" stop-opacity=".35"/><stop offset=".4" stop-color="#9d8cc8" stop-opacity=".12"/><stop offset="1" stop-color="#9d8cc8" stop-opacity="0"/></radialGradient>
<radialGradient id="moonface" cx=".4" cy=".4"><stop offset="0" stop-color="#fbf7ff"/><stop offset="1" stop-color="#c9bfe0"/></radialGradient>
<mask id="crescent"><rect x="-100" y="-100" width="200" height="200" fill="#fff"/><circle cx="20" cy="-12" r="52" fill="#000"/></mask>
<linearGradient id="titlegrad" x1="0" x2="1"><stop offset="0" stop-color="{SILVER}"/><stop offset=".55" stop-color="#f3c4d2"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
<linearGradient id="sheen" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="titleclip"><text class="f-Deco" x="48" y="122" font-size="50" letter-spacing="1">cc-mascot</text></clipPath>
<radialGradient id="floorglow"><stop offset="0" stop-color="{CRIMSON}" stop-opacity=".45"/><stop offset="1" stop-color="{CRIMSON}" stop-opacity="0"/></radialGradient>
<linearGradient id="mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NIGHT0}" stop-opacity="0"/><stop offset="1" stop-color="{NIGHT0}" stop-opacity=".9"/></linearGradient>"""
    # the floor circle, flattened into perspective under her boots
    floor_r = 128
    ring_ticks = "".join(f"M{math.cos(i/48*math.tau)*floor_r*0.86:.1f} {math.sin(i/48*math.tau)*floor_r*0.86:.1f}L{math.cos(i/48*math.tau)*floor_r:.1f} {math.sin(i/48*math.tau)*floor_r:.1f}" for i in range(48))
    hexa = []
    for off in (0, 1):
        pts = [(math.cos(-math.pi/2 + (2*i+off)*math.pi/3)*floor_r*0.8, math.sin(-math.pi/2 + (2*i+off)*math.pi/3)*floor_r*0.8) for i in range(3)]
        hexa.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    body = [f'<g clip-path="url(#clip-hero)">',
            f'<rect width="{w}" height="{h}" fill="url(#bg-hero)"/>',
            stars(rng, w, h, 70, ymax=h - 70, rmax=1.3),
            # moon
            f'<circle cx="770" cy="70" r="170" fill="url(#moonglow)"/>',
            f'<g transform="translate(784,66) scale(.72)"><circle r="46" fill="url(#moonface)" mask="url(#crescent)" opacity=".95"/></g>',
            # floor circle
            f'<ellipse cx="{ax+fw/2}" cy="{feet-4}" rx="165" ry="36" fill="url(#floorglow)"/>',
            f'<g transform="translate({ax+fw/2},{feet-4}) scale(1,.22)"><g class="spin" style="--d:40s">'
            f'<circle r="{floor_r}" fill="none" stroke="{CRIMSON}" stroke-opacity=".8" stroke-width="2.2"/>'
            f'<circle r="{floor_r*0.8}" fill="none" stroke="{GOLD}" stroke-opacity=".5" stroke-width="1.6"/>'
            f'<path d="{ring_ticks}" stroke="{GOLD}" stroke-opacity=".55" stroke-width="1.4"/>'
            f'<path d="{"".join(hexa)}" fill="none" stroke="{CRIMSON}" stroke-opacity=".7" stroke-width="1.8"/></g></g>',
            # Yunseul
            f'<svg x="{ax}" y="{ay}" width="{fw}" height="{fh}" viewBox="0 0 {fw} {fh}" overflow="hidden">'
            f'<image class="sheet" width="{fw*n}" height="{fh}" href="data:image/webp;base64,{sheet}" xlink:href="data:image/webp;base64,{sheet}"/></svg>',
            # ground mist over her boots' line
            f'<rect x="0" y="{h-46}" width="{w}" height="46" fill="url(#mist)"/>',
            ]
    for i in range(16):
        body.append(f'<circle class="rise" cx="{rng.uniform(470,800):.0f}" cy="{rng.uniform(h-40,h-10):.0f}" r="{rng.uniform(.8,2):.1f}" '
                    f'fill="{rng.choice([CRIMSON, "#f3c4d2", SILVER])}" style="--d:{rng.uniform(6,11):.1f}s;--dl:{rng.uniform(0,9):.1f}s;--mo:{rng.uniform(.4,.8):.2f}"/>')
    for i in range(7):
        body.append(petal(rng.uniform(420, 830), rng.uniform(-10, 40), rng.uniform(1.2, 1.9), rng.uniform(10, 16), rng.uniform(0, 14),
                          rng.choice([CRIMSON, "#b5203f", "#f08aa8"])))
    body += [bat(770, 40, 1.1, -260, 24, 0, "#1a0f24", .95), bat(820, 74, .8, -330, 30, 8, "#1a0f24", .8),
             bat(560, 30, .7, -200, 22, 13, "#1a0f24", .7)]
    body.append("</g>")
    body.append(frame(w, h, 8))
    # text column
    tx = 48
    body.append(f'<g transform="translate({tx+3},64)"><path d="M0 -3.5 L3.5 0 L0 3.5 L-3.5 0Z" fill="{MOON}"/></g>')
    body.append(f'<text class="f-Cinzel" x="{tx+13}" y="68" font-size="11" letter-spacing="2.4" fill="{MOON}">CLAUDE CODE PLUGIN  ·  OPEN SOURCE</text>')
    body.append(f'<text class="f-Deco" x="{tx}" y="122" font-size="50" letter-spacing="1" fill="url(#titlegrad)" filter="url(#glow)">cc-mascot</text>')
    body.append(f'<g clip-path="url(#titleclip)"><rect class="shimmer" x="0" y="70" width="140" height="70" fill="url(#sheen)" transform="skewX(-20)"/></g>')
    body.append(f'<path d="M{tx} 140 H{tx+70}" stroke="{CRIMSON}" stroke-width="1.4"/><circle cx="{tx+75}" cy="140" r="2" fill="{CRIMSON}"/>')
    desc = ("Anime desktop mascots that live beside your terminal and react as Claude thinks, runs tools, "
            "waits on you and finishes. Hatsune Miku, or Yunseul from my own RPG.")
    y = 168
    for ln in wrap(desc, "Corm", 18, 460):
        body.append(f'<text class="f-Corm" x="{tx}" y="{y}" font-size="18" fill="{MIST}">{esc(ln)}</text>')
        y += 23
    # her ten moods, as the overlay names them
    moods = ["idle", "thinking", "working", "waiting", "happy", "worried", "sleepy", "error", "held", "beam"]
    y += 14
    x = tx
    body.append(f'<text class="f-Cinzel" x="{tx}" y="{y}" font-size="9" letter-spacing="1.8" fill="{GOLD}">TEN MOODS</text>')
    y += 18
    for m in moods:
        mw = width(m, "CormI", 14) + 16
        if x + mw > tx + 470:
            x, y = tx, y + 24
        body.append(f'<rect x="{x}" y="{y-13}" width="{mw:.1f}" height="19" rx="9.5" fill="{NIGHT0}" fill-opacity=".6" stroke="{CRIMSON if m=="beam" else GOLD_DIM}" stroke-width=".8"/>')
        body.append(f'<text class="f-CormI" x="{x+mw/2:.1f}" y="{y+1}" font-size="14" text-anchor="middle" fill="{SILVER if m=="beam" else MIST}">{m}</text>')
        x += mw + 6
    body.append(f'<text class="f-Cinzel" x="{tx}" y="{h-30}" font-size="9.5" letter-spacing="1.7" fill="{GOLD}">PYTHON  ·  TYPESCRIPT  ·  WINDOWS</text>')
    body.append(f'<text class="f-CormI" x="{w-36}" y="{h-26}" font-size="13" text-anchor="end" fill="{DIM}">Yunseul · idle</text>')
    return svg(w, h, defs, "\n".join(body), css)


# ---------- banner ----------
def banner():
    w, h = 840, 250
    rng = random.Random(3)
    cx, cy, R = 420, 118, 112
    band = "UNITY · UNREAL ENGINE · BLENDER · C# · C++ · HLSL · PYTHON · THREE.JS · "
    ticks = "".join(f"M{math.cos(i/96*math.tau)*R*0.9:.1f} {math.sin(i/96*math.tau)*R*0.9:.1f}L{math.cos(i/96*math.tau)*R*(0.95 if i%4 else 0.98):.1f} {math.sin(i/96*math.tau)*R*(0.95 if i%4 else 0.98):.1f}" for i in range(96))
    hexa = []
    for off in (0, 1):
        pts = [(math.cos(-math.pi/2 + (2*i+off)*math.pi/3)*R*0.72, math.sin(-math.pi/2 + (2*i+off)*math.pi/3)*R*0.72) for i in range(3)]
        hexa.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    defs = GLOW + f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NIGHT0}"/><stop offset=".6" stop-color="{NIGHT2}"/><stop offset="1" stop-color="#2e1838"/></linearGradient>
<radialGradient id="core"><stop offset="0" stop-color="{AMETHYST}" stop-opacity=".32"/><stop offset=".6" stop-color="{CRIMSON}" stop-opacity=".08"/><stop offset="1" stop-color="{CRIMSON}" stop-opacity="0"/></radialGradient>
<linearGradient id="tg" x1="0" x2="1"><stop offset="0" stop-color="{SILVER}"/><stop offset=".5" stop-color="#f3c4d2"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
<linearGradient id="sheen" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="tclip"><text class="f-Deco" x="{cx}" y="{cy+16}" font-size="56" text-anchor="middle" letter-spacing="2">desuqcafe</text></clipPath>
<clipPath id="clip"><rect width="{w}" height="{h}" rx="16"/></clipPath>
{circle_path('band', R*0.81)}
<radialGradient id="moonface" cx=".4" cy=".4"><stop offset="0" stop-color="#fbf7ff"/><stop offset="1" stop-color="#c9bfe0"/></radialGradient>
<mask id="cres"><rect x="-60" y="-60" width="120" height="120" fill="#fff"/><circle cx="9" cy="-6" r="20" fill="#000"/></mask>"""
    spires = []
    # a gothic skyline: spires and a castle, in place of the old city blocks
    x = 0
    while x < w:
        bw = rng.choice([18, 22, 26, 34, 40])
        bh = rng.uniform(16, 44)
        top = h - bh
        if rng.random() < .45:
            spires.append(f"M{x} {h}V{top}L{x+bw/2:.1f} {top-rng.uniform(14,34):.1f}L{x+bw} {top}V{h}Z")
        else:
            spires.append(f"M{x} {h}V{top}h{bw/5:.1f}v-5h{bw/5:.1f}v5h{bw/5:.1f}v-5h{bw/5:.1f}v5h{bw/5:.1f}V{h}Z")
        x += bw + rng.choice([0, 0, 4, 8])
    windows = []
    for _ in range(18):
        windows.append(f'<rect class="tw" x="{rng.uniform(10,830):.0f}" y="{rng.uniform(h-30,h-8):.0f}" width="2.2" height="3.4" rx=".6" '
                       f'fill="{rng.choice([CRIMSON, GOLD, AMETHYST])}" style="--d:{rng.uniform(3,6):.1f}s;--dl:{rng.uniform(0,4):.1f}s;--mo:.7"/>')
    body = ['<g clip-path="url(#clip)">', f'<rect width="{w}" height="{h}" fill="url(#sky)"/>',
            stars(rng, w, h, 80, ymax=h - 40, rmax=1.3),
            f'<g transform="translate(96,52)"><circle r="44" fill="#cfc4ea" opacity=".08"/><circle r="17" fill="url(#moonface)" mask="url(#cres)"/></g>',
            f'<g transform="translate({cx},{cy})"><circle r="{R*1.6}" fill="url(#core)"/>'
            f'<circle r="{R}" fill="none" stroke="{GOLD}" stroke-opacity=".5" stroke-width="1"/>'
            f'<circle r="{R*0.9}" fill="none" stroke="{GOLD}" stroke-opacity=".28" stroke-width=".8"/>'
            f'<circle r="{R*0.74}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width=".8"/>'
            f'<g class="spin" style="--d:120s"><path d="{ticks}" stroke="{GOLD}" stroke-opacity=".4" stroke-width=".8"/></g>'
            f'<g class="spinr" style="--d:160s"><text class="f-Cinzel" font-size="8.4" letter-spacing="2.2" fill="{GOLD}" fill-opacity=".55">'
            f'<textPath href="#band" xlink:href="#band" textLength="{math.tau*R*0.81*0.99:.1f}">{esc(band+band[:0])}</textPath></text></g>'
            f'<g class="spin" style="--d:90s"><path d="{"".join(hexa)}" fill="none" stroke="{CRIMSON}" stroke-opacity=".35" stroke-width="1"/></g></g>',
            f'<path d="{"".join(spires)}" fill="#07040c"/>', "\n".join(windows)]
    for i in range(14):
        body.append(f'<circle class="rise" cx="{rng.uniform(30,810):.0f}" cy="{rng.uniform(h-30,h-5):.0f}" r="{rng.uniform(.8,2.2):.1f}" '
                    f'fill="{rng.choice([CRIMSON, AMETHYST, "#f3c4d2", MOON])}" style="--d:{rng.uniform(7,12):.1f}s;--dl:{rng.uniform(0,10):.1f}s;--mo:{rng.uniform(.3,.6):.2f}"/>')
    body += [bat(760, 60, 1, -640, 34, 2, "#05030a", .85), bat(810, 96, .7, -700, 40, 14, "#05030a", .7)]
    body.append(f'<text class="f-Deco" x="{cx}" y="{cy+16}" font-size="56" text-anchor="middle" letter-spacing="2" fill="url(#tg)" filter="url(#softglow)">desuqcafe</text>')
    body.append(f'<g clip-path="url(#tclip)"><rect class="shimmer" x="{cx-300}" y="{cy-40}" width="160" height="80" fill="url(#sheen)" transform="skewX(-20)"/></g>')
    body.append(f'<text class="f-CormI" x="{cx}" y="{cy+48}" font-size="17" text-anchor="middle" fill="{MIST}" letter-spacing=".4">realtime anime characters, and the tools that bring them to life</text>')
    body.append('</g>')
    body.append(f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="16" fill="none" stroke="#3b2752"/>')
    return svg(w, h, defs, "\n".join(body))


# ---------- section header (a divider that carries the heading) ----------
def header(title):
    w, h = 840, 56
    cx, cy = w / 2, 30
    tw = width(title.upper(), "Cinzel", 15, 4.2)
    gap = tw / 2 + 30
    defs = (f'<linearGradient id="l" x1="1" x2="0"><stop offset="0" stop-color="{GOLD}" stop-opacity=".9"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="r" x1="0" x2="1"><stop offset="0" stop-color="{GOLD}" stop-opacity=".9"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>')
    def wing(sx):
        x0 = cx + sx * gap
        return (f'<path d="M{x0} {cy} H{cx + sx*(gap+300)}" stroke="url(#{"r" if sx>0 else "l"})" stroke-width="1"/>'
                f'<path d="M{x0} {cy-4} H{cx + sx*(gap+120)}" stroke="url(#{"r" if sx>0 else "l"})" stroke-width=".6" stroke-opacity=".5"/>'
                f'<path d="M{x0-sx*12} {cy} l{sx*6} -4 l{sx*6} 4 l{-sx*6} 4z" fill="{CRIMSON}"/>')
    body = [wing(-1), wing(1),
            f'<text class="f-Cinzel" x="{cx}" y="{cy+5.5}" font-size="15" letter-spacing="4.2" text-anchor="middle" fill="{SILVER}">{esc(title.upper())}</text>']
    return svg(w, h, defs, "\n".join(body))


# ---------- tech stack ----------
def stack():
    rows = [("Engines & tools", GOLD, ["Unity", "Unreal Engine", "Blender", "three.js", "Tauri"]),
            ("Languages", CRIMSON, ["C#", "C++", "HLSL", "Python", "TypeScript"]),
            ("Focus", AMETHYST, ["Anime avatars", "Cloth & hair sim", "Multiplayer", "Editor tooling", "VR / AR"])]
    w, rowh = 840, 46
    h = 24 + rowh * len(rows)
    body = []
    y = 30
    for label, col, items in rows:
        body.append(f'<text class="f-Cinzel" x="150" y="{y+5}" font-size="10" letter-spacing="2.2" text-anchor="end" fill="{col}">{esc(label.upper())}</text>')
        x = 172
        for it in items:
            iw = width(it, "CormB", 16) + 34
            body.append(f'<g transform="translate({x},{y})">'
                        f'<rect x="0" y="-14" width="{iw:.1f}" height="28" rx="14" fill="{NIGHT1}" stroke="{col}" stroke-opacity=".55"/>'
                        f'<path d="M13 -3.2 L16.2 0 L13 3.2 L9.8 0Z" fill="{col}"/>'
                        f'<text class="f-CormB" x="{iw/2+6:.1f}" y="5" font-size="16" text-anchor="middle" fill="{SILVER}">{esc(it)}</text></g>')
            x += iw + 9
        y += rowh
    return svg(w, h, "", "\n".join(body))


CARDS = [
    dict(id_="inhyeong", title="Inhyeong", status="Private · in development", open_source=False,
         desc="My long-running world: a desktop anime companion headed for Steam, a multiplayer RPG of dolls and ghosts, and the tools behind both.",
         tags=["Unity", "C#", "FishNet", "Python"], emblem="ghost", accent=CRIMSON, points=5, runes="Inhyeong · dolls and ghosts", seed=11),
    dict(id_="weft", title="Weft", status="Private", open_source=False,
         desc="My own XPBD cloth and hair solver for stylized avatars, built for skirts, ribbons and long hair in real time.",
         tags=["Unity", "C#", "Shaders"], emblem="weave", accent=AMETHYST, points=7, runes="Weft · cloth and hair", seed=12),
    dict(id_="loom", title="Loom", status="Private · release candidate", open_source=False,
         desc="A live link from Blender to Unity and Unreal. Move a vertex, a light or an animation and the engine's viewport follows in milliseconds.",
         tags=["Blender", "Unity", "Unreal", "C++", "Python"], emblem="link", accent=MOON, points=6, runes="Loom · Blender to engine", seed=13),
    dict(id_="navigator", title="Component Navigator", status="Private · release candidate", open_source=False,
         desc="A full Inspector replacement for Unity that sorts and groups your components for you, so you stop scrolling and start building.",
         tags=["Unity", "C#", "UI Toolkit"], emblem="panels", accent=GOLD, points=8, runes="Component Navigator", seed=14),
    dict(id_="syncthing", title="desuqcafe Syncthing", status="Open source · fork", open_source=True,
         desc="Syncthing as a one-click Windows install: no admin prompt, a tray app, telemetry compiled out, and set up for big Blender files.",
         tags=["Go", "Windows", "Installer"], emblem="sync", accent=AMETHYST, points=7, runes="Syncthing · one click", seed=15),
    dict(id_="dataguardian", title="Data Guardian", status="Open source", open_source=True,
         desc="A Blender add-on that stops your data being silently purged, with fake-user protection on save and creation for 20+ data types.",
         tags=["Blender", "Python"], emblem="shield", accent=CRIMSON, points=5, runes="Data Guardian", seed=16),
]

if __name__ == "__main__":
    write("banner.svg", banner())
    for t in ["About Me", "Tech Stack", "Contributions", "Featured Work"]:
        write(f"header-{t.lower().replace(' ', '-')}.svg", header(t))
    write("stack.svg", stack())
    write("card-cc-mascot.svg", hero())
    for c in CARDS:
        write(f"card-{c['id_']}.svg", card(w=412, h=250, **c))
