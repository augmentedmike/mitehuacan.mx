#!/usr/bin/env python3
"""Print sheet of "MAPA DE RUTAS" stickers with real, unique tracking QRs.

Each sticker carries the shared artwork with its OWN QR encoding
https://mitehuacan.mx/qr/<id> — a unique id per sticker so every physical
placement is tracked, all landing on the app home map. Tiled on a 13×19"
sheet with a 1 cm margin (the print-shop "margen de seguridad") to the edge
and gutters between stickers to cut through.

  python3 src/scripts/22_sticker_sheet.py [--start N] [--width-cm 9] [--sheets 1]

Outputs to resources/stickers/: a print-ready PDF, a preview PNG, and a CSV of
the ids/URLs on the sheet.
"""
import argparse
import csv
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = Path("/Users/michaeloneal/Downloads/mapa-de-rutas.png")
OUT = ROOT / "resources" / "stickers"
BASE_URL = "https://mitehuacan.mx/qr/"

DPI = 300
SHEET_W_IN, SHEET_H_IN = 13, 19
MARGIN_CM = 1.0
GUTTER_CM = 0.5
# the rounded border's INNER white area (measured from the artwork). The QR is
# placed centered inside this with a clear margin so it never touches the border.
QR_INNER = (514, 510, 892, 890)        # x0,y0,x1,y1 in source-image px, center (703,700)
QR_FILL = 0.70                         # QR side as a fraction of the inner box (rest = white margin)


def cm(v):
    return int(round(v / 2.54 * DPI))


def make_qr(url):
    q = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=10, border=2)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color="black", back_color="white").convert("RGB")


def build_sticker(art, sticker_id):
    """Composite a unique QR into a copy of the artwork."""
    im = art.copy()
    x0, y0, x1, y1 = QR_INNER
    # erase the placeholder QR inside the border (keeps the rounded border intact)
    Image.Image.paste(im, (255, 255, 255), (x0, y0, x1, y1))
    box_w, box_h = x1 - x0, y1 - y0
    side = int(min(box_w, box_h) * QR_FILL)
    qr = make_qr(BASE_URL + sticker_id).resize((side, side), Image.NEAREST)
    # centered in the inner box → equal white margin on all four sides
    px = x0 + (box_w - side) // 2
    py = y0 + (box_h - side) // 2
    im.paste(qr, (px, py))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--width-cm", type=float, default=9.0)
    ap.add_argument("--sheets", type=int, default=1)
    args = ap.parse_args()

    if not ART.exists():
        raise SystemExit(f"artwork not found: {ART}")
    OUT.mkdir(parents=True, exist_ok=True)
    art = Image.open(ART).convert("RGB")
    aspect = art.size[0] / art.size[1]

    sheet_w, sheet_h = cm(SHEET_W_IN * 2.54), cm(SHEET_H_IN * 2.54)
    margin, gutter = cm(MARGIN_CM), cm(GUTTER_CM)
    sw = cm(args.width_cm)
    sh = int(round(sw / aspect))
    usable_w, usable_h = sheet_w - 2 * margin, sheet_h - 2 * margin
    cols = (usable_w + gutter) // (sw + gutter)
    rows = (usable_h + gutter) // (sh + gutter)
    per_sheet = cols * rows
    block_w = cols * sw + (cols - 1) * gutter
    block_h = rows * sh + (rows - 1) * gutter
    ox = (sheet_w - block_w) // 2
    oy = (sheet_h - block_h) // 2

    print(f"sheet 13x19in @ {DPI}dpi = {sheet_w}x{sheet_h}px; sticker {args.width_cm}x{args.width_cm/aspect:.1f}cm; "
          f"grid {cols}x{rows} = {per_sheet}/sheet; 1cm margin, {GUTTER_CM}cm gutters")

    n = args.start
    for s in range(args.sheets):
        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
        rows_csv = []
        one = build_sticker(art, "TEH-0000").resize((sw, sh), Image.LANCZOS)  # size ref
        for r in range(rows):
            for c in range(cols):
                sid = f"TEH-{n:04d}"
                st = build_sticker(art, sid).resize((sw, sh), Image.LANCZOS)
                x = ox + c * (sw + gutter)
                y = oy + r * (sh + gutter)
                sheet.paste(st, (x, y))
                rows_csv.append((sid, BASE_URL + sid))
                n += 1
        idx = args.start // per_sheet + s + 1 if per_sheet else s + 1
        stem = f"mapa-de-rutas-sheet-{s+1:02d}"
        pdf = OUT / f"{stem}.pdf"
        sheet.save(pdf, "PDF", resolution=DPI)
        preview = OUT / f"{stem}-preview.png"
        sheet.resize((sheet_w // 4, sheet_h // 4), Image.LANCZOS).save(preview)
        with open(OUT / f"{stem}-ids.csv", "w", newline="") as f:
            csv.writer(f).writerows([("id", "url"), *rows_csv])
        print(f"  {stem}: {per_sheet} stickers ({rows_csv[0][0]}–{rows_csv[-1][0]}) -> {pdf.name}, {preview.name}, ids.csv")


if __name__ == "__main__":
    main()
