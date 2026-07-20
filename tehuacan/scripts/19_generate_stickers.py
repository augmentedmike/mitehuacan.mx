#!/usr/bin/env python3
"""Generate QR sticker batch: printable sheets + D1 seed CSV.

Usage:
  python3 tehuacan/scripts/19_generate_stickers.py --batch 2026-07-A --count 100 --outdir tehuacan/stickers

Output:
  tehuacan/stickers/<batch>/   # per-sticker PNGs (3×3 cm @ 300 DPI)
  tehuacan/stickers/<batch>/sheet_*.png  # A4 printable sheets (10 per page)
  tehuacan/stickers/<batch>/stickers.csv # D1 seed (import via wrangler d1 execute)

Optional route assignment:
  --route 15  # all stickers assigned to this route
  --top-10    # distribute across top 10 routes by prospect count
"""

import argparse
import csv
import io
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QR_BASE = os.environ.get("QR_BASE_URL", "https://mitehuacan.mx/qr/")


def get_top_routes(n=10):
    """Return highest-prospect-density routes from prospects/_summary.csv."""
    summary = ROOT / "prospects" / "_summary.csv"
    if not summary.exists():
        print("warning: prospects/_summary.csv not found — no route assignment", file=sys.stderr)
        return []
    rows = list(csv.DictReader(summary.open(encoding="utf-8-sig")))
    rows.sort(key=lambda r: -int(r["prioridad_1"]))
    return [r["ruta"] for r in rows[:n]]


def get_route_display(route_key):
    """Look up display_name from master_route_index.csv."""
    idx = ROOT / "data" / "master_route_index.csv"
    for r in csv.DictReader(idx.open()):
        if r["route_key"] == route_key:
            return r["display_name"]
    return route_key


def generate_qr(text):
    """Generate a QR code PIL Image."""
    import qrcode
    qr = qrcode.QRCode(border=2, box_size=10)
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def create_sticker_image(qr_img, sticker_id, route_name=""):
    """Build a sticker with QR + label text, 3×3 cm @ 300 DPI (~354×354 px)."""
    from PIL import Image, ImageDraw, ImageFont
    mm = 300 / 25.4
    W, H = int(30 * mm), int(30 * mm)
    margin = int(2.5 * mm)

    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)

    # QR code centered in the upper portion
    qr_size = int(22 * mm)
    if qr_size % 2:
        qr_size += 1
    qr_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qx = (W - qr_size) // 2
    qy = margin
    canvas.paste(qr_resized, (qx, qy))

    # Label below QR
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttf", int(3 * mm))
        small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttf", int(2.2 * mm))
    except (OSError, IOError):
        font = ImageFont.load_default()
        small = font

    label = sticker_id
    draw.text(((W - draw.textlength(label, font=font)) // 2, int(26 * mm)), label, fill="black", font=font)

    return canvas


def make_sheet(images, cols=5, rows=2):
    """Arrange sticker images into an A4 sheet (printable)."""
    from PIL import Image
    mm = 300 / 25.4
    SW, SH = int(210 * mm), int(297 * mm)
    sticker_w = int(30 * mm)
    sticker_h = int(30 * mm)
    gap_x = (SW - cols * sticker_w) // (cols + 1)
    gap_y = (SH - rows * sticker_h) // (rows + 1)

    sheet = Image.new("RGB", (SW, SH), "white")
    for i, img in enumerate(images):
        if i >= cols * rows:
            break
        col = i % cols
        row = i // cols
        x = gap_x + col * (sticker_w + gap_x)
        y = gap_y + row * (sticker_h + gap_y)
        sheet.paste(img, (x, y))
    return sheet


def main():
    ap = argparse.ArgumentParser(description="Generate QR sticker batch")
    ap.add_argument("--batch", required=True, help='batch id, e.g. "2026-07-A"')
    ap.add_argument("--count", type=int, default=50, help="number of stickers in this batch")
    ap.add_argument("--outdir", default=str(ROOT / "stickers"), help="output directory")
    ap.add_argument("--route", help="assign all stickers to this route id")
    ap.add_argument("--top-10", action="store_true", help="distribute across top 10 routes by prospect density")
    args = ap.parse_args()

    out = Path(args.outdir) / args.batch
    out.mkdir(parents=True, exist_ok=True)

    # Determine route assignments
    route_for = {}
    if args.route:
        for i in range(1, args.count + 1):
            route_for[i] = args.route
    elif args.top_10:
        top = get_top_routes(10)
        if not top:
            print("error: no top routes available", file=sys.stderr)
            sys.exit(1)
        for i in range(1, args.count + 1):
            route_for[i] = top[(i - 1) % len(top)]

    # Generate stickers
    stickers = []
    images = []
    for i in range(1, args.count + 1):
        sid = f"{args.batch}-{i:04d}"
        rid = route_for.get(i, "")
        url = f"{QR_BASE}{sid}"

        qr_img = generate_qr(url)
        route_display = get_route_display(rid) if rid else ""
        img = create_sticker_image(qr_img, sid, route_display)
        img.save(str(out / f"{sid}.png"))

        stickers.append({"id": sid, "batch": args.batch, "status": "printed",
                         "route_id": rid, "unit_desc": "", "notes": ""})
        images.append(img)

        if i % 10 == 0:
            print(f"  generated {i}/{args.count}")

    # CSV for D1 seeding
    csv_path = out / "stickers.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "batch", "status", "route_id", "unit_desc", "notes"])
        w.writeheader()
        w.writerows(stickers)
    print(f"  csv: {csv_path} ({len(stickers)} stickers)")

    # Printable sheets (10 per A4 page)
    sheets_dir = out / "sheets"
    sheets_dir.mkdir(exist_ok=True)
    for page, start in enumerate(range(0, len(images), 10), 1):
        sheet = make_sheet(images[start:start + 10])
        sheet.save(str(sheets_dir / f"sheet_{page}.png"))
        print(f"  sheet: sheets/sheet_{page}.png")

    # Summary
    print(f"\nBatch {args.batch}: {len(stickers)} stickers → {out}")
    print(f"To seed D1:")
    print(f"  wrangler d1 execute mitehuacan --command \\")
    print(f"    \"INSERT OR IGNORE INTO stickers (id, batch, status, route_id) VALUES\\")
    for s in stickers[:5]:
        print(f"      ('{s['id']}', '{s['batch']}', '{s['status']}', \"{s['route_id'] or ''}\"),")
    if len(stickers) > 5:
        print(f"      ... ({len(stickers) - 5} more)")
    print(f"\nPrint: open sheets/ directory — each sheet.png is A4 @ 300 DPI")
    print(f"Cut: 10 stickers per sheet, 30×30 mm each")


if __name__ == "__main__":
    main()
