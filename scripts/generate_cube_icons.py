"""
scripts/generate_cube_icons.py — Generate high-resolution 3D isometric TripLine cube icons
(SVG, PNG 32x32, 180x180, 512x512, and ICO format) matching the brand spec.
"""

from pathlib import Path
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent

SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="64 46 272 272" width="64" height="64" role="img" aria-label="TripLine">
  <title>TripLine</title>
  <defs>
    <filter id="tl-glow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <linearGradient id="tl-shade" gradientUnits="userSpaceOnUse" x1="200" y1="90" x2="200" y2="310">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.16"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.25"/>
    </linearGradient>
  </defs>

  <!-- Left Face -->
  <path d="M104.74 145L200 200V310L104.74 255Z" fill="#6B6E7A" stroke="#FFFFFF" stroke-width="3.5" stroke-linejoin="round"/>

  <!-- Right Face -->
  <path d="M200 200L295.26 145V255L200 310Z" fill="#AEB1BA" stroke="#FFFFFF" stroke-width="3.5" stroke-linejoin="round"/>

  <!-- Top Face -->
  <path d="M200 90L295.26 145L200 200L104.74 145Z" fill="#0F1228" stroke="#FFFFFF" stroke-width="3.5" stroke-linejoin="round"/>

  <!-- Shading overlay -->
  <path d="M200 90L295.26 145V255L200 310L104.74 255V145Z" fill="url(#tl-shade)" pointer-events="none"/>

  <!-- Apex tripwire stub / antenna -->
  <path d="M200 90V62" stroke="#0F1228" stroke-width="3.5" stroke-linecap="round" fill="none"/>

  <!-- Live tripwire tip glow -->
  <circle cx="200" cy="62" r="5" fill="#5B4BFF" filter="url(#tl-glow)"/>

  <!-- Center inspection node -->
  <circle cx="200" cy="200" r="6.5" fill="#FFFFFF" stroke="#0F1228" stroke-width="3"/>
</svg>
"""


def render_cube_image(size: int = 512) -> Image.Image:
    # 4x supersampling for ultra smooth antialiasing
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def tx(x, y):
        # viewBox: 64 46 272 272
        cx = (x - 64.0) * canvas_size / 272.0
        cy = (y - 46.0) * canvas_size / 272.0
        return (cx, cy)

    # Key vertices
    top_apex = tx(200.0, 90.0)
    right_mid = tx(295.26, 145.0)
    center_node = tx(200.0, 200.0)
    left_mid = tx(104.74, 145.0)
    bottom_point = tx(200.0, 310.0)
    left_bot = tx(104.74, 255.0)
    right_bot = tx(295.26, 255.0)
    antenna_tip = tx(200.0, 62.0)

    stroke_w = int(3.5 * canvas_size / 272.0)
    white = (255, 255, 255, 255)

    # 1. Left Face (fill #6B6E7A, stroke #FFFFFF)
    draw.polygon([left_mid, center_node, bottom_point, left_bot], fill=(107, 110, 122, 255), outline=white, width=stroke_w)

    # 2. Right Face (fill #AEB1BA, stroke #FFFFFF)
    draw.polygon([center_node, right_mid, right_bot, bottom_point], fill=(174, 177, 186, 255), outline=white, width=stroke_w)

    # 3. Top Face (fill #0F1228, stroke #FFFFFF)
    draw.polygon([top_apex, right_mid, center_node, left_mid], fill=(15, 18, 40, 255), outline=white, width=stroke_w)

    # Redraw outer boundaries to guarantee crisp seams
    for p1, p2 in [
        (left_mid, center_node),
        (center_node, right_mid),
        (center_node, bottom_point),
        (top_apex, right_mid),
        (right_mid, right_bot),
        (right_bot, bottom_point),
        (bottom_point, left_bot),
        (left_bot, left_mid),
        (left_mid, top_apex),
    ]:
        draw.line([p1, p2], fill=white, width=stroke_w)

    # 4. Antenna rod from apex to tip
    rod_w = int(3.5 * canvas_size / 272.0)
    draw.line([top_apex, antenna_tip], fill=(15, 18, 40, 255), width=rod_w)

    # 5. Glowing violet dot at tip
    r_tip = 5.0 * canvas_size / 272.0
    # Glow halos
    draw.ellipse(
        [antenna_tip[0] - r_tip * 2.2, antenna_tip[1] - r_tip * 2.2, antenna_tip[0] + r_tip * 2.2, antenna_tip[1] + r_tip * 2.2],
        fill=(91, 75, 255, 60),
    )
    draw.ellipse(
        [antenna_tip[0] - r_tip * 1.5, antenna_tip[1] - r_tip * 1.5, antenna_tip[0] + r_tip * 1.5, antenna_tip[1] + r_tip * 1.5],
        fill=(91, 75, 255, 140),
    )
    # Core dot
    draw.ellipse(
        [antenna_tip[0] - r_tip, antenna_tip[1] - r_tip, antenna_tip[0] + r_tip, antenna_tip[1] + r_tip],
        fill=(91, 75, 255, 255),
    )

    # 6. Center node (circle with white fill and ink stroke)
    r_node = 6.5 * canvas_size / 272.0
    node_stroke = int(3.0 * canvas_size / 272.0)
    draw.ellipse(
        [center_node[0] - r_node, center_node[1] - r_node, center_node[0] + r_node, center_node[1] + r_node],
        fill=white,
        outline=(15, 18, 40, 255),
        width=node_stroke,
    )

    # Downsample using high-quality Lanczos filter
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main():
    print("Writing SVG assets...")
    # Write SVG to all target locations
    svg_destinations = [
        REPO_ROOT / "assets" / "brand" / "tripline-favicon.svg",
        REPO_ROOT / "tripline-frontend" / "public" / "tripline-favicon.svg",
        REPO_ROOT / "tripline-frontend" / "public" / "favicon.svg",
        REPO_ROOT / "tripline-frontend" / "public" / "icon.svg",
        REPO_ROOT / "tripline-frontend" / "app" / "icon.svg",
        REPO_ROOT / "dashboard" / "static" / "brand" / "tripline-favicon.svg",
    ]
    for dst in svg_destinations:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(SVG_CONTENT, encoding="utf-8")
        print(f"  -> {dst.relative_to(REPO_ROOT)}")

    # Also copy to frontend/out if it exists
    out_dir = REPO_ROOT / "tripline-frontend" / "out"
    if out_dir.exists():
        (out_dir / "tripline-favicon.svg").write_text(SVG_CONTENT, encoding="utf-8")
        (out_dir / "favicon.svg").write_text(SVG_CONTENT, encoding="utf-8")
        (out_dir / "icon.svg").write_text(SVG_CONTENT, encoding="utf-8")
        print("  -> Updated tripline-frontend/out SVGs")

    print("Generating PNG / ICO raster icons...")
    img_512 = render_cube_image(512)
    img_180 = render_cube_image(180)
    img_48 = render_cube_image(48)
    img_32 = render_cube_image(32)
    img_16 = render_cube_image(16)

    # 32x32 PNG
    png_32_dests = [
        REPO_ROOT / "assets" / "brand" / "tripline-favicon-32.png",
        REPO_ROOT / "tripline-frontend" / "public" / "tripline-favicon-32.png",
        REPO_ROOT / "tripline-frontend" / "public" / "favicon-32.png",
        REPO_ROOT / "tripline-frontend" / "public" / "icon-32.png",
        REPO_ROOT / "dashboard" / "static" / "brand" / "tripline-favicon-32.png",
    ]
    for dst in png_32_dests:
        dst.parent.mkdir(parents=True, exist_ok=True)
        img_32.save(dst, format="PNG")
        print(f"  -> {dst.relative_to(REPO_ROOT)}")

    # 180x180 Apple Touch PNG
    apple_dests = [
        REPO_ROOT / "assets" / "brand" / "tripline-apple-touch-180.png",
        REPO_ROOT / "tripline-frontend" / "public" / "tripline-apple-touch-180.png",
        REPO_ROOT / "tripline-frontend" / "public" / "apple-touch-icon.png",
        REPO_ROOT / "dashboard" / "static" / "brand" / "tripline-apple-touch-180.png",
    ]
    for dst in apple_dests:
        dst.parent.mkdir(parents=True, exist_ok=True)
        img_180.save(dst, format="PNG")
        print(f"  -> {dst.relative_to(REPO_ROOT)}")

    # ICO format (contains 16x16, 32x32, 48x48)
    ico_dests = [
        REPO_ROOT / "tripline-frontend" / "public" / "favicon.ico",
        REPO_ROOT / "tripline-frontend" / "app" / "favicon.ico",
    ]
    for dst in ico_dests:
        dst.parent.mkdir(parents=True, exist_ok=True)
        img_48.save(dst, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
        print(f"  -> {dst.relative_to(REPO_ROOT)}")

    if out_dir.exists():
        img_32.save(out_dir / "tripline-favicon-32.png", format="PNG")
        img_32.save(out_dir / "favicon-32.png", format="PNG")
        img_180.save(out_dir / "tripline-apple-touch-180.png", format="PNG")
        img_180.save(out_dir / "apple-touch-icon.png", format="PNG")
        img_48.save(out_dir / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
        print("  -> Updated tripline-frontend/out PNG and ICO icons")

    print("Icon generation complete.")


if __name__ == "__main__":
    main()
