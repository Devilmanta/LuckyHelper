"""
LuckyHelper - Icon Generator
Creates the app icon as a .ico file using only Pillow (or falls back to PyQt6).
Run once to generate assets/icon.ico
"""

import os
import sys

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
ICO_PATH  = os.path.join(ASSETS_DIR, "icon.ico")
PNG_PATH  = os.path.join(ASSETS_DIR, "icon.png")

def generate_with_pyqt6():
    """Fallback: draw icon with PyQt6 if Pillow is unavailable."""
    if os.path.exists(PNG_PATH):
        print(f"[i] Custom icon.png already exists at {PNG_PATH}. Skipping PyQt6 drawing fallback.")
        return PNG_PATH

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QPainter, QColor, QPixmap, QRadialGradient, QPainterPath, QBrush, QPen
    from PyQt6.QtCore import Qt, QRectF, QPointF
    import math

    app = QApplication.instance() or QApplication(sys.argv)

    size = 256
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    grad = QRadialGradient(size / 2, size / 2, size / 2)
    grad.setColorAt(0.0, QColor("#1C2840"))
    grad.setColorAt(1.0, QColor("#0D1117"))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, size - 8, size - 8)

    # Draw 4 leaf clovers as rounded rectangles (rotated)
    leaf_color = QColor("#00D4FF")
    glow_color = QColor(0, 212, 255, 60)
    cx, cy = size / 2, size / 2
    leaf_w, leaf_h = 52, 72
    offsets = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # top, right, bottom, left
    angles  = [0, 90, 180, 270]

    for (ox, oy), angle in zip(offsets, angles):
        p.save()
        p.translate(cx + ox * 28, cy + oy * 28)
        p.rotate(angle)
        # Glow
        p.setBrush(QBrush(glow_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(-leaf_w // 2 - 4, -leaf_h // 2 - 4,
                          leaf_w + 8, leaf_h + 8, 30, 30)
        # Leaf
        p.setBrush(QBrush(leaf_color))
        p.drawRoundedRect(-leaf_w // 2, -leaf_h // 2, leaf_w, leaf_h, 26, 26)
        p.restore()

    # Stem
    pen = QPen(QColor("#00D4FF"), 8, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(int(cx), int(cy + 28), int(cx), int(cy + 72))

    # Tiny uptrend arrow
    p.setBrush(QBrush(QColor("#00C853")))
    p.setPen(Qt.PenStyle.NoPen)
    arrow = QPainterPath()
    ax, ay = cx - 18, cy + 78
    arrow.moveTo(ax,      ay + 20)
    arrow.lineTo(ax + 14, ay)
    arrow.lineTo(ax + 22, ay + 10)
    arrow.lineTo(ax + 36, ay - 8)
    arrow.lineTo(ax + 36, ay + 4)
    arrow.lineTo(ax + 26, ay + 4)
    arrow.lineTo(ax + 14, ay + 16)
    arrow.lineTo(ax + 6,  ay + 8)
    arrow.lineTo(ax,      ay + 20)
    # skip arrow — keep icon clean
    p.end()

    # Save PNG
    px.save(PNG_PATH, "PNG")

    # Convert to ICO sizes
    img_256 = px.toImage()

    from PyQt6.QtGui import QImageWriter
    sizes = [256, 128, 64, 48, 32, 16]
    # We'll just save the 256 PNG and let PyInstaller use it
    print(f"[✓] Icon PNG saved: {PNG_PATH}")
    return PNG_PATH


def main():
    if os.path.exists(PNG_PATH):
        try:
            from PIL import Image
            print(f"[i] Custom icon.png found at {PNG_PATH}. Generating icon.ico from it...")
            img = Image.open(PNG_PATH).convert("RGBA")
            icons = []
            for s in [256, 128, 64, 48, 32, 16]:
                resampling = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
                icons.append(img.resize((s, s), resampling))
            icons[0].save(ICO_PATH, format="ICO", sizes=[(s, s) for s in [256, 128, 64, 48, 32, 16]],
                          append_images=icons[1:])
            print(f"[OK] Icon ICO saved: {ICO_PATH}")
            return
        except Exception as e:
            print(f"[!] Failed to generate ICO from custom PNG: {e}")

    try:
        from PIL import Image, ImageDraw, ImageFilter
        print("[i] Using Pillow to generate icon...")

        size = 512
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        draw.ellipse([8, 8, size - 8, size - 8], fill="#0D1117")

        # Four leaves (rounded rects at 45° rotated positions)
        import math
        cx, cy = size // 2, size // 2
        leaf_size = 90
        gap = 24

        for angle_deg in [0, 90, 180, 270]:
            angle = math.radians(angle_deg)
            ox = int(math.sin(angle) * gap)
            oy = int(-math.cos(angle) * gap)
            lx = cx + ox - leaf_size // 2
            ly = cy + oy - leaf_size

            # Glow layer
            glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse([lx - 8, ly - 8, lx + leaf_size + 8, cy + oy + 8],
                       fill=(0, 212, 255, 50))
            glow = glow.filter(ImageFilter.GaussianBlur(10))
            img = Image.alpha_composite(img, glow)
            draw = ImageDraw.Draw(img)

            # Leaf
            draw.rounded_rectangle(
                [lx, ly, lx + leaf_size, cy + oy],
                radius=30, fill="#00D4FF"
            )

        # Stem
        draw.rounded_rectangle(
            [cx - 5, cy + 20, cx + 5, cy + 90],
            radius=4, fill="#00D4FF"
        )

        # Save
        img.save(PNG_PATH)
        print(f"[OK] Icon PNG saved: {PNG_PATH}")

        # Save as ICO with multiple sizes
        icons = []
        for s in [256, 128, 64, 48, 32, 16]:
            resampling = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
            icons.append(img.resize((s, s), resampling))
        icons[0].save(ICO_PATH, format="ICO", sizes=[(s, s) for s in [256, 128, 64, 48, 32, 16]],
                      append_images=icons[1:])
        print(f"[OK] Icon ICO saved: {ICO_PATH}")

    except ImportError:
        print("[!] Pillow not found, using PyQt6 fallback...")
        generate_with_pyqt6()


if __name__ == "__main__":
    main()
