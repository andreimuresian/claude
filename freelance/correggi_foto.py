#!/usr/bin/env python3
"""Corregge colore e luminosità delle foto, mantenendo la risoluzione ORIGINALE.

Uso (Windows, dal terminale nella cartella con le foto):
    pip install pillow numpy
    python correggi_foto.py cartella_foto cartella_output

Come funziona: prende un riquadro di PARETE (in alto a sinistra, sotto l'appendino non serve)
come riferimento di bianco, neutralizza la dominante di colore (parete rosata) e schiarisce un po'.
Salva i JPEG a qualità 95 alla stessa risoluzione dell'originale.
Parametri da cambiare in alto se serve.
"""
import sys
import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

ALPHA = 0.75          # 0 = nessuna correzione del colore, 1 = correzione completa
TARGET_WALL = 238.0   # luminosità voluta della parete (0-255)
CONTRAST = 1.08
WALL_BOX = (0.02, 0.03, 0.15, 0.12)   # (x0, y0, x1, y1) in frazione dell'immagine: angolo alto a sinistra
QUALITY = 95


def correggi(percorso_in, percorso_out):
    im = Image.open(percorso_in).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape
    x0, y0, x1, y1 = WALL_BOX
    parete = a[int(h * y0):int(h * y1), int(w * x0):int(w * x1)].reshape(-1, 3)
    rif = np.median(parete, axis=0)
    g = rif.mean() / rif
    g = 1 + (g - 1) * ALPHA
    k = TARGET_WALL / (rif * g).mean()
    b = np.clip(a * g * k, 0, 255) / 255.0
    b = np.clip((b - 0.5) * CONTRAST + 0.5, 0, 1)
    out = Image.fromarray((b * 255).astype(np.uint8))
    out = ImageEnhance.Color(out).enhance(1.03)
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))
    out.save(percorso_out, quality=QUALITY, subsampling=0)
    print(os.path.basename(percorso_in), im.size, "->", os.path.getsize(percorso_out) // 1024, "KB")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    cartella_in, cartella_out = sys.argv[1], sys.argv[2]
    os.makedirs(cartella_out, exist_ok=True)
    for nome in sorted(os.listdir(cartella_in)):
        if nome.lower().endswith((".jpg", ".jpeg")):
            correggi(os.path.join(cartella_in, nome),
                     os.path.join(cartella_out, os.path.splitext(nome)[0] + "_corretta.jpg"))


if __name__ == "__main__":
    main()
