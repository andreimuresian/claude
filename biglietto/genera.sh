#!/bin/sh
# Rigenera il PDF di stampa (96x56 mm con 3 mm di abbondanza, 2 pagine: fronte e retro).
cd "$(dirname "$0")"
CHROME=${CHROME:-/opt/pw-browsers/chromium}
"$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=biglietto_stampa.pdf --virtual-time-budget=2000 "file://$PWD/biglietto.html"
