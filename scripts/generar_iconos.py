"""Genera iconos PWA basicos con Pillow."""

import os
from PIL import Image, ImageDraw, ImageFont


def crear_icono(ruta: str, tamano: int):
    img = Image.new("RGB", (tamano, tamano), "#0b3666")  # Color azul ALSI
    draw = ImageDraw.Draw(img)

    # Fondo con gradiente simple (solo color solido)
    # Borde redondeado
    margin = int(tamano * 0.1)
    draw.rounded_rectangle(
        [margin, margin, tamano - margin, tamano - margin],
        radius=int(tamano * 0.15),
        fill="#1f5fa8",
    )

    # Texto "ALSI"
    try:
        # Intentar cargar una fuente del sistema
        font_size = int(tamano * 0.30)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    text = "ALSI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (tamano - text_w) // 2
    text_y = (tamano - text_h) // 2 - int(tamano * 0.05)
    draw.text((text_x, text_y), text, fill="white", font=font)

    # Icono de balanza pequeño debajo
    peso_y = text_y + text_h + int(tamano * 0.08)
    peso_size = int(tamano * 0.08)
    # Brazo central
    draw.line(
        [(tamano // 2, peso_y), (tamano // 2, peso_y + peso_size)],
        fill="white",
        width=max(2, tamano // 96),
    )
    # Platillos
    plato_w = int(tamano * 0.20)
    draw.line(
        [(tamano // 2 - plato_w, peso_y + peso_size // 2),
         (tamano // 2 + plato_w, peso_y + peso_size // 2)],
        fill="white",
        width=max(2, tamano // 96),
    )
    # Platos (lineas curvas)
    for offset in [-plato_w, plato_w]:
        draw.line(
            [(tamano // 2 + offset - int(plato_w * 0.3), peso_y + peso_size // 2 + int(tamano * 0.04)),
             (tamano // 2 + offset, peso_y + peso_size // 2),
             (tamano // 2 + offset + int(plato_w * 0.3), peso_y + peso_size // 2 + int(tamano * 0.04))],
            fill="white",
            width=max(2, tamano // 96),
        )

    img.save(ruta, "PNG", optimize=True)
    print(f"Creado: {ruta} ({tamano}x{tamano})")


def main():
    base = r"C:\alsi balance\static\img"
    os.makedirs(base, exist_ok=True)

    # Favicon
    crear_icono(os.path.join(base, "favicon.png"), 64)

    # PWA icons
    crear_icono(os.path.join(base, "icon-192.png"), 192)
    crear_icono(os.path.join(base, "icon-512.png"), 512)

    print("OK")


if __name__ == "__main__":
    main()
