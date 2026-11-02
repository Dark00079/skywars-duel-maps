"""Compose previews/overview.png (all maps in one grid) for the README."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main(cols=4, cw=420, ch=300, label_h=34):
    meta = json.load(open(os.path.join(ROOT, "maps.json")))
    rows = (len(meta) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cw, rows * (ch + label_h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(FONT, 20)
    except OSError:
        font = ImageFont.load_default()
    for k, m in enumerate(meta):
        im = Image.open(os.path.join(ROOT, "previews", m["file"] + ".png")).convert("RGBA")
        im.thumbnail((cw - 20, ch - 10), Image.LANCZOS)
        x0 = (k % cols) * cw
        y0 = (k // cols) * (ch + label_h)
        sheet.alpha_composite(im, (x0 + (cw - im.size[0]) // 2, y0 + (ch - im.size[1]) // 2))
        text = "%02d  %s" % (m["id"], m["name"])
        w = d.textlength(text, font=font)
        d.text((x0 + (cw - w) / 2, y0 + ch + 2), text, font=font, fill=(128, 138, 148, 255))
    out = os.path.join(ROOT, "previews", "overview.png")
    # 256-colour palette keeps the README image small
    sheet.quantize(colors=256, method=Image.Quantize.FASTOCTREE).save(out, optimize=True)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
