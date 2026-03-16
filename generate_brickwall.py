"""Generate 512x512 seamless sci-fi textures: brickwall, stone, metal, door, floor."""
import random
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

SIZE = 64
OUT_DIR = "assets/textures"

# ── Shared sci-fi colour palette ──────────────────────────────────────────
# Dark blue-greys with cyan / teal accent glow
DARK_BASE    = (35, 38, 48)
MID_BASE     = (55, 60, 72)
LIGHT_BASE   = (78, 84, 98)
GLOW_CYAN    = (0, 210, 255)
GLOW_TEAL    = (0, 180, 200)
GLOW_DIM     = (0, 90, 120)
ACCENT_WARM  = (180, 100, 40)   # warning / rust accent


# ── Utility functions ─────────────────────────────────────────────────────

def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def lerp_color(c1, c2, t):
    return tuple(clamp(a + (b - a) * t) for a, b in zip(c1, c2))


def noise_color(base, spread=10):
    return tuple(clamp(c + random.randint(-spread, spread)) for c in base)


def put_wrapped(img, px, py, color):
    """Put a pixel, wrapping coords for seamlessness."""
    img.putpixel((px % SIZE, py % SIZE), color)


def draw_wrapped_rect(draw_obj, x, y, w, h, color):
    """Draw a filled rectangle with seamless wrapping."""
    for dy in [0, -SIZE, SIZE]:
        for dx in [0, -SIZE, SIZE]:
            rx, ry = x + dx, y + dy
            if rx + w < 0 or rx >= SIZE or ry + h < 0 or ry >= SIZE:
                continue
            draw_obj.rectangle([rx, ry, rx + w - 1, ry + h - 1], fill=color)


def draw_wrapped_line(draw_obj, x1, y1, x2, y2, color, width=1):
    """Draw a line with seamless wrapping."""
    for dy in [0, -SIZE, SIZE]:
        for dx in [0, -SIZE, SIZE]:
            draw_obj.line(
                [(x1 + dx, y1 + dy), (x2 + dx, y2 + dy)],
                fill=color, width=width,
            )


def _tileable_blur(img, radius):
    """Apply GaussianBlur that tiles seamlessly.

    Tiles the image 2×2, blurs (kernel sees no hard edge), crops back.
    Supports both RGB and RGBA images."""
    w, h = img.size
    big = Image.new(img.mode, (w * 2, h * 2))
    for dy in (0, h):
        for dx in (0, w):
            big.paste(img, (dx, dy))
    big = big.filter(ImageFilter.GaussianBlur(radius=radius))
    return big.crop((w // 2, h // 2, w // 2 + w, h // 2 + h))


def _make_tileable_noise(blur=1.2):
    """Generate a tileable grayscale noise layer.

    Works by generating a 2×2 tiled noise field, blurring it (so the
    blur kernel doesn't see a hard edge), then cropping back to SIZE.
    The result tiles perfectly because opposite edges came from the same
    source pixels."""
    # Generate one tile of raw noise
    tile = Image.new("L", (SIZE, SIZE))
    for py in range(SIZE):
        for px in range(SIZE):
            tile.putpixel((px, py), random.randint(0, 255))
    # Paste into 2×2 grid
    big = Image.new("L", (SIZE * 2, SIZE * 2))
    for dy in (0, SIZE):
        for dx in (0, SIZE):
            big.paste(tile, (dx, dy))
    # Blur the big version (kernel crosses seams safely)
    big = big.filter(ImageFilter.GaussianBlur(radius=blur))
    # Crop back to one tile
    return big.crop((SIZE // 2, SIZE // 2, SIZE // 2 + SIZE, SIZE // 2 + SIZE))


def add_noise_overlay(img, strength=0.30, blur=1.2):
    """Multiply-blend a tileable noise layer for surface grit."""
    noise = _make_tileable_noise(blur)
    noise_rgb = noise.convert("RGB")
    noise_rgb = ImageEnhance.Contrast(noise_rgb).enhance(0.08)
    noise_rgb = ImageEnhance.Brightness(noise_rgb).enhance(1.8)
    blended = ImageChops.multiply(img, noise_rgb)
    return Image.blend(img, blended, strength)


def add_stains(img, count=80, seed_offset=0):
    """Dark smudge stains with wrapping."""
    rng = random.Random(42 + seed_offset)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(count):
        sx, sy = rng.randint(0, SIZE - 1), rng.randint(0, SIZE - 1)
        sr = rng.randint(4, 18)
        alpha = rng.randint(12, 45)
        shade = rng.randint(0, 30)
        for dx in [0, -SIZE, SIZE]:
            for dy in [0, -SIZE, SIZE]:
                d.ellipse(
                    [sx + dx - sr, sy + dy - sr, sx + dx + sr, sy + dy + sr],
                    fill=(shade, shade, shade, alpha),
                )
    layer = _tileable_blur(layer, 5)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def finalize(img, noise_strength=0.30, blur_final=0.4, stains=80, seed=0):
    """Apply shared finishing passes (all tileable)."""
    img = add_stains(img, count=stains, seed_offset=seed)
    img = add_noise_overlay(img, strength=noise_strength)
    # Blur via the 2×2-crop trick so edges stay seamless
    if blur_final > 0:
        big = Image.new("RGB", (SIZE * 2, SIZE * 2))
        for dy in (0, SIZE):
            for dx in (0, SIZE):
                big.paste(img, (dx, dy))
        big = big.filter(ImageFilter.GaussianBlur(radius=blur_final))
        img = big.crop((SIZE // 2, SIZE // 2, SIZE // 2 + SIZE, SIZE // 2 + SIZE))
    return img


# ══════════════════════════════════════════════════════════════════════════
#  1.  BRICKWALL  – sci-fi panelled wall with glowing mortar lines
# ══════════════════════════════════════════════════════════════════════════

def generate_brickwall():
    random.seed(100)
    img = Image.new("RGB", (SIZE, SIZE), DARK_BASE)
    draw = ImageDraw.Draw(img)

    # Grid dims MUST divide SIZE evenly for perfect tiling.
    # COL_W // 2 must also divide SIZE (stagger offset).
    MORTAR = 4
    ROWS = 16                        # number of brick rows
    COLS = 8                         # number of brick columns
    ROW_H = SIZE // ROWS             # 32  – divides 512 evenly
    COL_W = SIZE // COLS             # 64  – divides 512 evenly
    BRICK_H = ROW_H - MORTAR         # 28
    BRICK_W = COL_W - MORTAR         # 60
    assert SIZE % ROWS == 0, f"ROWS={ROWS} must divide SIZE={SIZE}"
    assert SIZE % COLS == 0, f"COLS={COLS} must divide SIZE={SIZE}"
    assert SIZE % (COL_W // 2) == 0, "stagger offset must divide SIZE"

    # Mortar = dark base (already filled)
    # Draw glow lines in mortar gaps
    glow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    palettes = [
        (50, 55, 68), (58, 62, 75), (45, 50, 65),
        (62, 68, 82), (40, 45, 58), (55, 58, 70),
        (48, 52, 66), (60, 65, 78), (52, 56, 70),
    ]

    # Exact row/col counts – no +2 overflow needed because dims divide SIZE
    for row in range(ROWS):
        y = row * ROW_H
        offset = (COL_W // 2) if (row % 2 == 1) else 0
        for col in range(COLS + 1):          # +1 to cover stagger overhang
            x = col * COL_W + offset
            bx, by = x + MORTAR // 2, y + MORTAR // 2
            base = random.choice(palettes)
            base = noise_color(base, 8)

            # Draw brick body, wrapping via modulo
            for py in range(BRICK_H):
                for px in range(BRICK_W):
                    edge_x = min(px, BRICK_W - 1 - px)
                    edge_y = min(py, BRICK_H - 1 - py)
                    edge = min(edge_x, edge_y)
                    darken = max(0, 25 - edge * 8) if edge <= 3 else 0
                    scan = 6 if ((by + py) % 4 == 0) else 0
                    pixel = tuple(
                        clamp(c + random.randint(-5, 5) - darken - scan)
                        for c in base
                    )
                    img.putpixel(((bx + px) % SIZE, (by + py) % SIZE), pixel)

        # Horizontal mortar glow line at y
        for lx in range(SIZE):
            for t in range(MORTAR):
                glow_draw.point(
                    (lx, (y + t) % SIZE),
                    fill=(*GLOW_DIM, 35 + random.randint(0, 25)),
                )

    # Vertical mortar glow lines
    for row in range(ROWS):
        y = row * ROW_H
        offset = (COL_W // 2) if (row % 2 == 1) else 0
        for col in range(COLS + 1):
            x = col * COL_W + offset
            for t in range(MORTAR):
                for ly in range(ROW_H):
                    glow_draw.point(
                        ((x + t) % SIZE, (y + ly) % SIZE),
                        fill=(*GLOW_DIM, 30 + random.randint(0, 20)),
                    )

    glow_layer = _tileable_blur(glow_layer, 1.8)
    img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")

    # Occasional bright cyan accent dots on bricks (panel indicators)
    accent = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ad = ImageDraw.Draw(accent)
    for _ in range(30):
        ax, ay = random.randint(0, SIZE - 1), random.randint(0, SIZE - 1)
        r = random.randint(1, 3)
        a = random.randint(40, 100)
        for ddx in [0, -SIZE, SIZE]:
            for ddy in [0, -SIZE, SIZE]:
                ad.ellipse([ax+ddx-r, ay+ddy-r, ax+ddx+r, ay+ddy+r],
                           fill=(*GLOW_CYAN, a))
    accent = _tileable_blur(accent, 2)
    img = Image.alpha_composite(img.convert("RGBA"), accent).convert("RGB")

    img = finalize(img, seed=1)
    img.save(f"{OUT_DIR}/brickwall.png")
    print("  -> brickwall.png")


# ══════════════════════════════════════════════════════════════════════════
#  2.  STONE  – Voronoi cracked alien stone with glowing seam edges
# ══════════════════════════════════════════════════════════════════════════

def generate_stone():
    random.seed(200)
    img = Image.new("RGB", (SIZE, SIZE))

    NUM_CELLS = 80  # number of Voronoi seed points

    stone_pals = [
        (42, 44, 52), (48, 50, 58), (38, 40, 50),
        (52, 55, 62), (45, 47, 56), (50, 52, 60),
        (44, 46, 55), (55, 57, 64), (40, 42, 51),
    ]

    # Generate seed points (only within 0..SIZE-1)
    seeds = [(random.randint(0, SIZE - 1), random.randint(0, SIZE - 1))
             for _ in range(NUM_CELLS)]
    cell_colors = [noise_color(random.choice(stone_pals), 8) for _ in range(NUM_CELLS)]

    # Build wrapped seed list: duplicate each seed into a 3x3 tile grid
    # so the nearest-cell lookup wraps seamlessly at edges
    wrapped_seeds = []
    wrapped_colors = []
    for i, (sx, sy) in enumerate(seeds):
        for dx in (-SIZE, 0, SIZE):
            for dy in (-SIZE, 0, SIZE):
                wrapped_seeds.append((sx + dx, sy + dy))
                wrapped_colors.append(cell_colors[i])

    # Pre-compute as tuples for speed
    ws = wrapped_seeds
    wc = wrapped_colors
    n_wrapped = len(ws)

    # For each pixel find nearest and second-nearest cell (toroidal Voronoi)
    for py in range(SIZE):
        for px in range(SIZE):
            d1 = float("inf")   # nearest distance²
            d2 = float("inf")   # second nearest distance²
            best_idx = 0

            for i in range(n_wrapped):
                ddx = px - ws[i][0]
                ddy = py - ws[i][1]
                dist2 = ddx * ddx + ddy * ddy
                if dist2 < d1:
                    d2 = d1
                    d1 = dist2
                    best_idx = i
                elif dist2 < d2:
                    d2 = dist2

            base = wc[best_idx]

            # Edge factor: how close this pixel is to a cell boundary
            sqrt_d1 = math.sqrt(d1)
            sqrt_d2 = math.sqrt(d2)
            edge_gap = sqrt_d2 - sqrt_d1

            # Darken near edges to carve out seam grooves
            darken = 0
            if edge_gap < 4.0:
                darken = int((4.0 - edge_gap) * 10)

            # Roughness noise
            pixel = tuple(
                clamp(c + random.randint(-8, 8) - darken)
                for c in base
            )
            img.putpixel((px, py), pixel)

    # Glowing Voronoi edges (seam glow)
    edge_glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for py in range(SIZE):
        for px in range(SIZE):
            d1 = float("inf")
            d2 = float("inf")
            for i in range(n_wrapped):
                ddx = px - ws[i][0]
                ddy = py - ws[i][1]
                dist2 = ddx * ddx + ddy * ddy
                if dist2 < d1:
                    d2 = d1
                    d1 = dist2
                elif dist2 < d2:
                    d2 = dist2
            edge_gap = math.sqrt(d2) - math.sqrt(d1)
            if edge_gap < 3.0:
                alpha = int((3.0 - edge_gap) / 3.0 * 60)
                edge_glow.putpixel((px, py), (*GLOW_DIM, clamp(alpha, 0, 60)))

    edge_glow = _tileable_blur(edge_glow, 2.0)
    img = Image.alpha_composite(img.convert("RGBA"), edge_glow).convert("RGB")

    # Faint carved rune lines scattered over the stones
    rune_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rune_layer)
    for _ in range(25):
        rx = random.randint(0, SIZE - 1)
        ry = random.randint(0, SIZE - 1)
        segments = random.randint(3, 8)
        angle = random.uniform(0, 2 * math.pi)
        pts = [(rx, ry)]
        for _ in range(segments):
            angle += random.choice([-math.pi/2, math.pi/2, 0, math.pi/4, -math.pi/4])
            length = random.randint(6, 20)
            nx = pts[-1][0] + math.cos(angle) * length
            ny = pts[-1][1] + math.sin(angle) * length
            pts.append((nx, ny))
        alpha = random.randint(25, 65)
        for i in range(len(pts) - 1):
            draw_wrapped_line(rd, int(pts[i][0]), int(pts[i][1]),
                              int(pts[i+1][0]), int(pts[i+1][1]),
                              (*GLOW_TEAL, alpha), width=1)

    rune_layer = _tileable_blur(rune_layer, 1.5)
    img = Image.alpha_composite(img.convert("RGBA"), rune_layer).convert("RGB")

    img = finalize(img, noise_strength=0.25, stains=60, seed=2)
    img.save(f"{OUT_DIR}/stone.png")
    print("  -> stone.png")


# ══════════════════════════════════════════════════════════════════════════
#  3.  METAL  – brushed / riveted metal panels with seam glow
# ══════════════════════════════════════════════════════════════════════════

def generate_metal():
    random.seed(300)
    img = Image.new("RGB", (SIZE, SIZE))

    # Grid dims MUST divide SIZE evenly for perfect tiling.
    SEAM = 4
    GRID = 4                           # 4×4 panels
    CELL = SIZE // GRID                # 128 – divides 512 evenly
    PANEL_W = CELL - SEAM              # 124
    PANEL_H = CELL - SEAM              # 124
    ROW_H = CELL
    COL_W = CELL
    assert SIZE % GRID == 0, f"GRID={GRID} must divide SIZE={SIZE}"

    metal_pals = [
        (60, 62, 70), (65, 67, 76), (55, 58, 66),
        (70, 72, 80), (58, 60, 68),
    ]

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SIZE - 1, SIZE - 1], fill=(30, 32, 38))

    for row in range(GRID):
        y = row * ROW_H
        for col in range(GRID):
            x = col * COL_W
            bx, by = x + SEAM // 2, y + SEAM // 2
            base = random.choice(metal_pals)
            base = noise_color(base, 5)

            for py in range(PANEL_H):
                for px in range(PANEL_W):
                    edge_x = min(px, PANEL_W - 1 - px)
                    edge_y = min(py, PANEL_H - 1 - py)
                    edge = min(edge_x, edge_y)
                    darken = max(0, 15 - edge * 5) if edge <= 3 else 0
                    streak = random.randint(-3, 3) if (random.random() < 0.3) else 0
                    pixel = tuple(
                        clamp(c + random.randint(-4, 4) - darken + streak)
                        for c in base
                    )
                    img.putpixel(((bx + px) % SIZE, (by + py) % SIZE), pixel)

    # Rivets at panel corners
    rivet_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rv = ImageDraw.Draw(rivet_layer)
    RIVET_R = 4
    RIVET_INSET = 10
    for row in range(GRID):
        y = row * ROW_H + SEAM // 2
        for col in range(GRID):
            x = col * COL_W + SEAM // 2
            corners = [
                (x + RIVET_INSET, y + RIVET_INSET),
                (x + PANEL_W - RIVET_INSET, y + RIVET_INSET),
                (x + RIVET_INSET, y + PANEL_H - RIVET_INSET),
                (x + PANEL_W - RIVET_INSET, y + PANEL_H - RIVET_INSET),
            ]
            for cx, cy in corners:
                rcx, rcy = cx % SIZE, cy % SIZE
                rv.ellipse([rcx-RIVET_R, rcy-RIVET_R, rcx+RIVET_R, rcy+RIVET_R],
                           fill=(35, 37, 44, 200))
                rv.ellipse([rcx-RIVET_R+1, rcy-RIVET_R+1, rcx+RIVET_R-1, rcy+RIVET_R-1],
                           fill=(85, 90, 100, 220))
                rv.ellipse([rcx-1, rcy-2, rcx+1, rcy], fill=(120, 125, 135, 180))

    img = Image.alpha_composite(img.convert("RGBA"), rivet_layer).convert("RGB")

    # Seam glow — draw at grid-aligned positions (always tile-safe)
    seam_glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seam_glow)
    for row in range(GRID):
        y = row * ROW_H
        for lx in range(SIZE):
            for t in range(SEAM):
                sd.point((lx, (y + t) % SIZE), fill=(*GLOW_DIM, 25 + random.randint(0, 20)))
    for col in range(GRID):
        x = col * COL_W
        for ly in range(SIZE):
            for t in range(SEAM):
                sd.point(((x + t) % SIZE, ly), fill=(*GLOW_DIM, 25 + random.randint(0, 20)))
    seam_glow = _tileable_blur(seam_glow, 2)
    img = Image.alpha_composite(img.convert("RGBA"), seam_glow).convert("RGB")

    # Scratches
    scratch = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    scr = ImageDraw.Draw(scratch)
    for _ in range(40):
        sx = random.randint(0, SIZE - 1)
        sy = random.randint(0, SIZE - 1)
        length = random.randint(20, 80)
        angle = random.uniform(-0.3, 0.3)  # mostly horizontal
        pts = [(sx, sy)]
        for _ in range(length):
            angle += random.uniform(-0.05, 0.05)
            pts.append((pts[-1][0] + math.cos(angle) * 2,
                        pts[-1][1] + math.sin(angle) * 2))
        a = random.randint(20, 55)
        bright = random.randint(90, 130)
        for i in range(len(pts) - 1):
            draw_wrapped_line(scr, int(pts[i][0]), int(pts[i][1]),
                              int(pts[i+1][0]), int(pts[i+1][1]),
                              (bright, bright, bright + 10, a), width=1)
    scratch = _tileable_blur(scratch, 0.5)
    img = Image.alpha_composite(img.convert("RGBA"), scratch).convert("RGB")

    img = finalize(img, noise_strength=0.20, stains=40, seed=3)
    img.save(f"{OUT_DIR}/metal.png")
    print("  -> metal.png")


# ══════════════════════════════════════════════════════════════════════════
#  4.  DOOR  – heavy sci-fi blast door with central split & warning stripe
# ══════════════════════════════════════════════════════════════════════════

def generate_door():
    random.seed(400)
    img = Image.new("RGB", (SIZE, SIZE))

    # Fill door body - dark steel
    door_base = (50, 52, 62)
    for py in range(SIZE):
        for px in range(SIZE):
            pixel = noise_color(door_base, 5)
            # Horizontal brushed streaks
            if random.random() < 0.25:
                pixel = tuple(clamp(c + random.randint(-3, 3)) for c in pixel)
            img.putpixel((px, py), pixel)

    draw = ImageDraw.Draw(img)

    # Door frame border (darker inset)
    FRAME = 16
    frame_col = (30, 32, 40)
    # Top & bottom frame
    draw.rectangle([0, 0, SIZE - 1, FRAME - 1], fill=frame_col)
    draw.rectangle([0, SIZE - FRAME, SIZE - 1, SIZE - 1], fill=frame_col)
    # Left & right frame
    draw.rectangle([0, 0, FRAME - 1, SIZE - 1], fill=frame_col)
    draw.rectangle([SIZE - FRAME, 0, SIZE - 1, SIZE - 1], fill=frame_col)

    # Inner frame edge glow
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(4):
        a = 60 - i * 15
        c = (*GLOW_CYAN, max(a, 5))
        # Inner top
        gd.line([(FRAME + i, FRAME + i), (SIZE - FRAME - i, FRAME + i)], fill=c, width=1)
        # Inner bottom
        gd.line([(FRAME + i, SIZE - FRAME - i - 1), (SIZE - FRAME - i, SIZE - FRAME - i - 1)], fill=c, width=1)
        # Inner left
        gd.line([(FRAME + i, FRAME + i), (FRAME + i, SIZE - FRAME - i)], fill=c, width=1)
        # Inner right
        gd.line([(SIZE - FRAME - i - 1, FRAME + i), (SIZE - FRAME - i - 1, SIZE - FRAME - i)], fill=c, width=1)

    glow = glow.filter(ImageFilter.GaussianBlur(radius=2))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    # Central vertical split line with glow
    split_x = SIZE // 2
    split_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(split_layer)
    # Dark gap
    sd.rectangle([split_x - 2, FRAME, split_x + 1, SIZE - FRAME], fill=(15, 16, 20, 255))
    # Glow around split
    for i in range(6):
        a = 50 - i * 8
        sd.line([(split_x - 3 - i, FRAME), (split_x - 3 - i, SIZE - FRAME)],
                fill=(*GLOW_CYAN, max(a, 3)), width=1)
        sd.line([(split_x + 2 + i, FRAME), (split_x + 2 + i, SIZE - FRAME)],
                fill=(*GLOW_CYAN, max(a, 3)), width=1)
    split_layer = split_layer.filter(ImageFilter.GaussianBlur(radius=1.5))
    img = Image.alpha_composite(img.convert("RGBA"), split_layer).convert("RGB")

    # Warning chevron stripes (diagonal) near top and bottom
    chevron = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chevron)
    STRIPE_W = 12
    BAND_H = 28
    # Top band
    band_y_top = FRAME + 8
    # Bottom band
    band_y_bot = SIZE - FRAME - 8 - BAND_H

    for band_y in [band_y_top, band_y_bot]:
        for sx in range(-SIZE, SIZE * 2, STRIPE_W * 2):
            pts = [
                (sx, band_y),
                (sx + STRIPE_W, band_y),
                (sx + STRIPE_W + BAND_H // 2, band_y + BAND_H),
                (sx + BAND_H // 2, band_y + BAND_H),
            ]
            cd.polygon(pts, fill=(*ACCENT_WARM, 120))

    chevron = chevron.filter(ImageFilter.GaussianBlur(radius=0.5))
    img = Image.alpha_composite(img.convert("RGBA"), chevron).convert("RGB")

    # Horizontal panel lines across each door half
    panel_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel_layer)
    for panel_y in range(FRAME + BAND_H + 20, SIZE - FRAME - BAND_H - 20, 48):
        pd.line([(FRAME + 4, panel_y), (split_x - 8, panel_y)],
                fill=(25, 28, 35, 150), width=2)
        pd.line([(split_x + 8, panel_y), (SIZE - FRAME - 4, panel_y)],
                fill=(25, 28, 35, 150), width=2)
        # Subtle glow under panel lines
        pd.line([(FRAME + 4, panel_y + 2), (split_x - 8, panel_y + 2)],
                fill=(*GLOW_DIM, 25), width=1)
        pd.line([(split_x + 8, panel_y + 2), (SIZE - FRAME - 4, panel_y + 2)],
                fill=(*GLOW_DIM, 25), width=1)
    panel_layer = panel_layer.filter(ImageFilter.GaussianBlur(radius=0.8))
    img = Image.alpha_composite(img.convert("RGBA"), panel_layer).convert("RGB")

    # Small indicator lights on each door half
    indicator = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ind = ImageDraw.Draw(indicator)
    # Left half indicators
    for iy in range(FRAME + BAND_H + 40, SIZE - FRAME - BAND_H - 20, 64):
        ix = FRAME + 28
        ind.ellipse([ix-3, iy-3, ix+3, iy+3], fill=(*GLOW_CYAN, 140))
        ind.ellipse([ix-1, iy-1, ix+1, iy+1], fill=(200, 255, 255, 200))
    # Right half indicators
    for iy in range(FRAME + BAND_H + 40, SIZE - FRAME - BAND_H - 20, 64):
        ix = SIZE - FRAME - 28
        ind.ellipse([ix-3, iy-3, ix+3, iy+3], fill=(*GLOW_CYAN, 140))
        ind.ellipse([ix-1, iy-1, ix+1, iy+1], fill=(200, 255, 255, 200))
    indicator = indicator.filter(ImageFilter.GaussianBlur(radius=1.5))
    img = Image.alpha_composite(img.convert("RGBA"), indicator).convert("RGB")

    # Lock mechanism in center
    lock = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lock)
    lock_y = SIZE // 2
    lock_x = SIZE // 2
    # Hexagonal-ish lock plate
    hex_r = 18
    hex_pts = []
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3
        hex_pts.append((lock_x + math.cos(a) * hex_r, lock_y + math.sin(a) * hex_r))
    ld.polygon(hex_pts, fill=(35, 38, 48, 220))
    # Inner glow ring
    for r in range(hex_r - 2, hex_r - 6, -1):
        a = 40 + (hex_r - 2 - r) * 15
        inner_pts = []
        for i in range(6):
            ang = math.pi / 6 + i * math.pi / 3
            inner_pts.append((lock_x + math.cos(ang) * r, lock_y + math.sin(ang) * r))
        ld.polygon(inner_pts, outline=(*GLOW_CYAN, min(a, 120)))
    # Center dot
    ld.ellipse([lock_x-3, lock_y-3, lock_x+3, lock_y+3], fill=(*GLOW_CYAN, 180))
    lock = lock.filter(ImageFilter.GaussianBlur(radius=1))
    img = Image.alpha_composite(img.convert("RGBA"), lock).convert("RGB")

    # Final passes (lighter stains for door)
    img = add_stains(img, count=30, seed_offset=4)
    img = add_noise_overlay(img, strength=0.18)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))

    img.save(f"{OUT_DIR}/door.png")
    print("  -> door.png")


# ══════════════════════════════════════════════════════════════════════════
#  5.  FLOOR  – dirt ground with scattered grass patches
# ══════════════════════════════════════════════════════════════════════════

def generate_floor():
    random.seed(500)
    img = Image.new("RGB", (SIZE, SIZE))

    # ── Base dirt fill with per-pixel noise ────────────────────────────
    DIRT_BASE = (58, 45, 32)      # warm brown
    DIRT_PALS = [
        (62, 48, 34), (55, 42, 30), (68, 52, 36),
        (50, 40, 28), (65, 50, 35), (58, 44, 31),
        (60, 46, 33), (53, 41, 29),
    ]

    for py in range(SIZE):
        for px in range(SIZE):
            base = random.choice(DIRT_PALS)
            pixel = tuple(clamp(c + random.randint(-8, 8)) for c in base)
            img.putpixel((px, py), pixel)

    # ── Large-scale colour variation (Voronoi blobs) ──────────────────
    # Creates natural-looking patches of lighter/darker dirt
    NUM_DIRT_CELLS = 40
    dirt_seeds = [(random.randint(0, SIZE - 1), random.randint(0, SIZE - 1))
                  for _ in range(NUM_DIRT_CELLS)]
    dirt_shifts = [random.randint(-12, 12) for _ in range(NUM_DIRT_CELLS)]

    # Wrap seeds for seamless Voronoi
    ws = []
    wc = []
    for i, (sx, sy) in enumerate(dirt_seeds):
        for dx in (-SIZE, 0, SIZE):
            for dy in (-SIZE, 0, SIZE):
                ws.append((sx + dx, sy + dy))
                wc.append(dirt_shifts[i])

    variation = Image.new("L", (SIZE, SIZE))
    for py in range(SIZE):
        for px in range(SIZE):
            best_d = float("inf")
            best_i = 0
            for i in range(len(ws)):
                ddx = px - ws[i][0]
                ddy = py - ws[i][1]
                d = ddx * ddx + ddy * ddy
                if d < best_d:
                    best_d = d
                    best_i = i
            variation.putpixel((px, py), clamp(128 + wc[best_i], 0, 255))

    variation = _tileable_blur(variation, 8)
    # Apply variation as brightness shift
    for py in range(SIZE):
        for px in range(SIZE):
            shift = variation.getpixel((px, py)) - 128
            r, g, b = img.getpixel((px, py))
            img.putpixel((px, py), (clamp(r + shift), clamp(g + shift), clamp(b + shift)))

    # ── Grass patches (Voronoi-selected cells get grass) ──────────────
    NUM_GRASS = 30
    grass_seeds = [(random.randint(0, SIZE - 1), random.randint(0, SIZE - 1))
                   for _ in range(NUM_GRASS)]
    # Each grass patch: is_grass bool, colour
    GRASS_PALS = [
        (45, 72, 32), (40, 68, 28), (50, 78, 35),
        (38, 65, 26), (48, 75, 33), (42, 70, 30),
        (55, 80, 38), (35, 62, 24),
    ]
    grass_colors = [random.choice(GRASS_PALS) for _ in range(NUM_GRASS)]
    grass_active = [random.random() < 0.5 for _ in range(NUM_GRASS)]  # ~half are grass

    # Wrapped grass seeds
    gws = []
    gwc = []
    gwa = []
    for i, (sx, sy) in enumerate(grass_seeds):
        for dx in (-SIZE, 0, SIZE):
            for dy in (-SIZE, 0, SIZE):
                gws.append((sx + dx, sy + dy))
                gwc.append(grass_colors[i])
                gwa.append(grass_active[i])

    # Paint grass cells with feathered edges
    grass_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for py in range(SIZE):
        for px in range(SIZE):
            d1 = float("inf")
            d2 = float("inf")
            best_i = 0
            for i in range(len(gws)):
                ddx = px - gws[i][0]
                ddy = py - gws[i][1]
                d = ddx * ddx + ddy * ddy
                if d < d1:
                    d2 = d1
                    d1 = d
                    best_i = i
                elif d < d2:
                    d2 = d

            if not gwa[best_i]:
                continue

            # Feather: fade near cell boundary
            edge_gap = math.sqrt(d2) - math.sqrt(d1)
            if edge_gap < 6.0:
                alpha = int((edge_gap / 6.0) * 180)
            else:
                alpha = 180

            gc = gwc[best_i]
            # Per-pixel noise on grass
            pixel = tuple(clamp(c + random.randint(-10, 10)) for c in gc)
            grass_layer.putpixel((px, py), (*pixel, alpha))

    grass_layer = _tileable_blur(grass_layer, 1.5)
    img = Image.alpha_composite(img.convert("RGBA"), grass_layer).convert("RGB")

    # ── Grass blade strokes ───────────────────────────────────────────
    blades = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blades)
    for _ in range(600):
        bx = random.randint(0, SIZE - 1)
        by = random.randint(0, SIZE - 1)
        # Only draw blades in grass zones (check grass_layer alpha)
        if grass_layer.getpixel((bx, by))[3] < 60:
            continue
        blade_len = random.randint(4, 12)
        angle = random.uniform(-0.5, 0.5) + math.pi * 1.5  # mostly upward
        ex = bx + math.cos(angle) * blade_len
        ey = by + math.sin(angle) * blade_len
        blade_col = random.choice(GRASS_PALS)
        bright = random.randint(-10, 20)
        col = tuple(clamp(c + bright) for c in blade_col)
        a = random.randint(80, 160)
        draw_wrapped_line(bd, bx, by, int(ex), int(ey), (*col, a), width=1)

    blades = _tileable_blur(blades, 0.5)
    img = Image.alpha_composite(img.convert("RGBA"), blades).convert("RGB")

    # ── Small pebbles / debris ────────────────────────────────────────
    pebbles = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pebbles)
    for _ in range(80):
        px_ = random.randint(0, SIZE - 1)
        py_ = random.randint(0, SIZE - 1)
        r = random.randint(1, 3)
        shade = random.randint(35, 60)
        a = random.randint(80, 150)
        for ddx in [0, -SIZE, SIZE]:
            for ddy in [0, -SIZE, SIZE]:
                pd.ellipse([px_ + ddx - r, py_ + ddy - r,
                            px_ + ddx + r, py_ + ddy + r],
                           fill=(shade, shade - 5, shade - 10, a))
    img = Image.alpha_composite(img.convert("RGBA"), pebbles).convert("RGB")

    img = finalize(img, noise_strength=0.22, stains=50, seed=5)
    img.save(f"{OUT_DIR}/floor.png")
    print("  -> floor.png")


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating sci-fi textures (512x512)...")
    generate_brickwall()
    generate_stone()
    generate_metal()
    generate_door()
    generate_floor()
    print("Done! All textures saved to assets/textures/")
