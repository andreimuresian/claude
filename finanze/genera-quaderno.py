# -*- coding: utf-8 -*-
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import date, timedelta

OUT = "/home/user/claude/finanze/quaderno-5000.xlsx"

ARIAL   = "Arial"
BLUE    = Font(name=ARIAL, size=11, color="0000FF")           # celle da compilare
BLACK   = Font(name=ARIAL, size=11)
GREY    = Font(name=ARIAL, size=11, color="7C8A91")
ITAL    = Font(name=ARIAL, size=11, color="0000FF", italic=True)
GREENIT = Font(name=ARIAL, size=11, color="0000FF", italic=True)   # righe "previsto"
H1      = Font(name=ARIAL, size=15, bold=True, color="141C22")
H2      = Font(name=ARIAL, size=11, bold=True, color="FFFFFF")
LBL     = Font(name=ARIAL, size=11, bold=True)
LBLBOLD = Font(name=ARIAL, size=11, bold=True)
NOTE    = Font(name=ARIAL, size=10, color="4A565E", italic=True)
HEADFIL = PatternFill("solid", fgColor="0E6E5E")
YELLOW  = PatternFill("solid", fgColor="FFFF00")
SUNK    = PatternFill("solid", fgColor="EFEEE9")
THIN    = Border(bottom=Side(style="thin", color="D3D0C7"))

EUR  = '#,##0" €";(#,##0)" €";"–"'
EUR2 = '#,##0.00" €";(#,##0.00)" €";"–"'
DATA = "dd/mm/yyyy"
DATABREVE = "dd/mm"

NR   = 203   # ultima riga dati in Settimane (4..203)
SR   = 103   # ultima riga dati in Spese   (4..103)
ER   = 103   # ultima riga dati in Entrate (4..103)
MR   = 300   # ultima riga dati in Movimenti (15..300)

PIANO = [
    (date(2026, 9, 1), 0), (date(2026, 9, 20), 470), (date(2026, 10, 31), 1020),
]
P0, P1 = 12, 12 + len(PIANO) - 1          # righe della curva sul foglio Piano
PA = "Piano!$A${}:$A${}".format(P0, P1)
PB = "Piano!$B${}:$B${}".format(P0, P1)
N  = len(PIANO)

wb = Workbook()

# ============================================================ SETTIMANE
ws = wb.active
ws.title = "Settimane"

ws["A1"] = "Il quaderno dei 5.000 — registro settimanale"
ws["A1"].font = H1
ws["A2"] = ("Ogni domenica scrivi solo le colonne in blu: i saldi letti dalle app (banca, contanti "
            "contati a mente, buoni pasto residui) e le entrate della settimana. Tutto il resto si "
            "calcola da solo. Budget previsto: scrivi prima quanto pensi di spendere, così a fine "
            "settimana vedi lo scarto reale. La prima riga in corsivo è un esempio: cancellala.")
ws["A2"].font = NOTE
ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
ws.merge_cells("A2:K2")
ws.row_dimensions[2].height = 42

heads = [
    ("Domenica", 12), ("Conto corrente (€)", 17), ("Conto risparmio (€)", 18),
    ("Contanti (€)", 13), ("Buoni pasto (€)", 15),
    ("Entrate (€)", 12), ("Nota", 30),
    ("Patrimonio (€)", 15), ("Speso in settimana (€)", 20),
    ("Budget previsto (€)", 18), ("Scarto vs budget (€)", 18),
]
for i, (h, w) in enumerate(heads, start=1):
    c = ws.cell(row=3, column=i, value=h)
    c.font, c.fill = H2, HEADFIL
    c.alignment = Alignment(wrap_text=True, vertical="bottom")
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[3].height = 30
ws.freeze_panes = "A4"

# riga 4: esempio da cancellare — righe 5..: settimane reali (dal 20/09/2026)
ESEMPIO = (date(2026, 8, 30), 2190, 0, 0, 0, 2190, "ESEMPIO — stipendio di agosto (cancella questa riga)")
REALI = [
    (date(2026, 9, 20), 74, 470, 350, 81, 0, "Rinnovo caldaia (140 € — vedi foglio Spese)"),
    (date(2026, 9, 27), 120, 470, 350, 36, 300, "Soldi Tati (250) + Zio Laurea (50)"),
    (date(2026, 10, 5), 445, 1020, 300, 0, 2197, "Arrivato stipendio (pagato affitto, assicurazione auto, iscrizione lotta)"),
    (date(2026, 10, 12), 40, 1020, 300, 198, 198, "Arrivati buoni pasto: 198 € messi in Entrate (nel tuo foglio mancavano, lo speso risultava 207 invece di 405)"),
    (date(2026, 11, 2), 2081, 1020, 150, 0, 2230.5, "PROVVISORIO (dati del 31/10): stipendio 2.230 € del 29/10 + cashback 0,50. Contanti: 100 € spesi perché la carta era a zero + 50 € per un lavoro."),
]

for r in range(4, NR + 1):
    if r == 4:
        d, cc, rp, ct, bp, en, nt = ESEMPIO
        font = ITAL
    elif 5 <= r < 5 + len(REALI):
        d, cc, rp, ct, bp, en, nt = REALI[r - 5]
        font = BLACK
    else:
        d = cc = rp = ct = bp = en = nt = None
        font = BLUE

    if r < 5 + len(REALI):
        ws.cell(row=r, column=1, value=d).font = font
        for col, val in ((2, cc), (3, rp), (4, ct), (5, bp), (6, en)):
            ws.cell(row=r, column=col, value=val).font = font
        ws.cell(row=r, column=7, value=nt).font = font
    else:
        for col in range(1, 6):
            ws.cell(row=r, column=col).font = BLUE
        ws.cell(row=r, column=6, value=0).font = BLUE
        ws.cell(row=r, column=7).font = BLUE
        ws.cell(row=r, column=10).font = BLUE

    if r >= 4:
        ws.cell(row=r, column=10).font = BLUE  # budget previsto: sempre da compilare a mano

    ws.cell(row=r, column=1).number_format = DATA
    for col in (2, 3, 4, 5, 6, 10):
        ws.cell(row=r, column=col).number_format = EUR

    ws.cell(row=r, column=8, value='=IF(NOT(ISNUMBER($A{r})),"",$B{r}+$C{r}+$D{r}+$E{r})'.format(r=r))
    ws.cell(row=r, column=9, value=('=IF(OR(NOT(ISNUMBER($A{r})),NOT(ISNUMBER($A{p}))),"",'
                                     '$H{p}+$F{r}-$H{r})').format(r=r, p=r - 1))
    ws.cell(row=r, column=11, value='=IF(OR($I{r}="",$J{r}=""),"",$I{r}-$J{r})'.format(r=r))
    for col in (8, 9, 11):
        c = ws.cell(row=r, column=col)
        c.font, c.number_format, c.border = BLACK, EUR, THIN

# ============================================================ SPESE
sp = wb.create_sheet("Spese")
sp["A1"] = "Spese annuali — quello che esce dal buffer"
sp["A1"].font = H1
sp["A2"] = ("Il buffer si riempie da solo di 150 € al mese. Qui registri solo le uscite grosse: "
            "assicurazione, caldaia, bollo, gomme, revisione, tagliando. Le righe in corsivo blu "
            "sono previsioni (non ancora accadute): correggile o cancellale quando la spesa è reale.")
sp["A2"].font = NOTE
sp["A2"].alignment = Alignment(wrap_text=True, vertical="top")
sp.merge_cells("A2:C2")
sp.row_dimensions[2].height = 28

for i, (h, w) in enumerate([("Data", 12), ("Voce", 44), ("Importo (€)", 14)], start=1):
    c = sp.cell(row=3, column=i, value=h)
    c.font, c.fill = H2, HEADFIL
    sp.column_dimensions[get_column_letter(i)].width = w
sp.freeze_panes = "A4"

SPESE_RIGHE = [
    (date(2026, 9, 20), "Revisione caldaia + controllo fumi (100 € contanti + 40 € carta)", 140, BLACK),
    (date(2026, 10, 3), "Assicurazione auto — rinnovo Prima/Triglav, pagamento unico", 467.77, BLACK),
    (date(2026, 10, 5), "Lotta Club Seggiano — quota iscrizione + primo mese, MENSILE non semestrale (corretto): dal secondo mese 25 €/mese ricorrenti, va nel budget fisso non più qui. 2 allenamenti/settimana per ora.", 50, BLACK),
]
for i, (d, voce, imp, font) in enumerate(SPESE_RIGHE):
    r = 4 + i
    sp.cell(row=r, column=1, value=d).font = font
    sp.cell(row=r, column=2, value=voce).font = font
    sp.cell(row=r, column=3, value=imp).font = font

for r in range(4, SR + 1):
    sp.cell(row=r, column=1).number_format = DATA
    sp.cell(row=r, column=3).number_format = EUR
    if r > 4 + len(SPESE_RIGHE) - 1:
        for col in (1, 2, 3):
            sp.cell(row=r, column=col).font = BLUE

sp.cell(row=SR + 2, column=2, value="Totale speso dal buffer").font = LBL
tot = sp.cell(row=SR + 2, column=3, value="=SUM($C$4:$C${})".format(SR))
tot.font, tot.number_format = LBL, EUR

# ============================================================ ENTRATE
en_sh = wb.create_sheet("Entrate")
en_sh["A1"] = "Entrate — stipendi, contributi, rimborsi"
en_sh["A1"].font = H1
en_sh["A2"] = ("Registra qui ogni entrata importante, per sapere sempre da dove viene ogni euro. "
               "Le righe in corsivo blu sono previsioni (non ancora arrivate): correggile con "
               "l'importo vero appena arrivano, o cancellale se saltano.")
en_sh["A2"].font = NOTE
en_sh["A2"].alignment = Alignment(wrap_text=True, vertical="top")
en_sh.merge_cells("A2:C2")
en_sh.row_dimensions[2].height = 28

for i, (h, w) in enumerate([("Data", 12), ("Voce", 44), ("Importo (€)", 14)], start=1):
    c = en_sh.cell(row=3, column=i, value=h)
    c.font, c.fill = H2, HEADFIL
    en_sh.column_dimensions[get_column_letter(i)].width = w
en_sh.freeze_panes = "A4"

ENTRATE_RIGHE = [
    (date(2026, 9, 29), "Stipendio di settembre — accreditato, confermato", 2197, BLACK),
    (date(2026, 9, 22), "Bonifico da papà — contributo affitto, ultimo mese (arrivato; non ce ne saranno altri)", 250, BLACK),
    (date(2026, 9, 24), "Regalo laurea dallo zio (contanti)", 50, BLACK),
    (date(2026, 10, 9), "Ricarica buoni pasto EdenRed di ottobre", 198, BLACK),
    (date(2026, 10, 29), "Stipendio di ottobre — accreditato, confermato", 2230, BLACK),
    (date(2026, 11, 15), "Rimborso 730 — accredito su carta (atteso nov/dic, importo confermato dal 730-3)", 1481, GREENIT),
    (date(2026, 12, 1), "Tredicesima 2026 — 5/12 da assunzione 03/08/2026, netto stimato dal cedolino di agosto (previsto)", 800, GREENIT),
]
for i, (d, voce, imp, font) in enumerate(ENTRATE_RIGHE):
    r = 4 + i
    en_sh.cell(row=r, column=1, value=d).font = font
    en_sh.cell(row=r, column=2, value=voce).font = font
    en_sh.cell(row=r, column=3, value=imp).font = font

for r in range(4, ER + 1):
    en_sh.cell(row=r, column=1).number_format = DATA
    en_sh.cell(row=r, column=3).number_format = EUR
    if r > 4 + len(ENTRATE_RIGHE) - 1:
        for col in (1, 2, 3):
            en_sh.cell(row=r, column=col).font = BLUE

en_sh.cell(row=ER + 2, column=2, value="Totale entrate registrate").font = LBL
tot2 = en_sh.cell(row=ER + 2, column=3, value="=SUM($C$4:$C${})".format(ER))
tot2.font, tot2.number_format = LBL, EUR

# ============================================================ MOVIMENTI
# Tabella piatta, senza formule di riepilogo: le incollo io già raggruppate
# in chat come tabella pronta da incollare, i totali e le somme li fai tu
# come preferisci (SUM su un intervallo, filtro, come vuoi). Aggiungere una
# categoria nuova (es. "Benzina") è solo scrivere testo in una cella: niente
# formula da capire o da rompere.
mv = wb.create_sheet("Movimenti")
mv["A1"] = "Movimenti PostePay + buoni pasto — dati grezzi"
mv["A1"].font = H1
mv["A2"] = ("Nessuna formula qui dentro: è solo un elenco. Le somme e i confronti li fai tu, come "
            "vuoi. Importo è sempre positivo: la direzione (spesa o accredito) è nella colonna Tipo, "
            "così non ti tocca fare i conti con il segno meno. Per aggiungere una categoria nuova "
            "basta scriverla — non c'è nulla da rompere. Il raggruppamento per data e categoria te lo "
            "preparo io in chat ogni volta che incolli i movimenti nuovi: tu li copi qui sotto così "
            "come sono.")
mv["A2"].font = NOTE
mv["A2"].alignment = Alignment(wrap_text=True, vertical="top")
mv.merge_cells("A2:E2")
mv.row_dimensions[2].height = 50

hr = 4
DSTART = hr + 1
mv.cell(row=hr, column=1, value="Movimenti").font = LBL
MVHEAD = [("Data", 12), ("Descrizione", 58), ("Importo (€)", 13), ("Tipo", 13), ("Categoria", 16)]
for i, (h, w) in enumerate(MVHEAD, start=1):
    c = mv.cell(row=hr, column=i, value=h)
    c.font, c.fill = H2, HEADFIL
    mv.column_dimensions[get_column_letter(i)].width = w
mv.freeze_panes = "A{}".format(DSTART)

SPESA, ACCR = "Spesa", "Accredito"
MOVIMENTI = [
    (date(2026, 9, 7),  "PostePay — ricarica per attivazione nuova carta (saldo trasferito dalla vecchia)", 980.10, ACCR, "Trasferimento"),
    (date(2026, 9, 7),  "EdenRed — ricarica 21 buoni pasto", 189.00, ACCR, "Entrata"),
    (date(2026, 9, 10), "PostePay — POS 46084 San Donato (benzina)", 26.30, SPESA, "Benzina"),
    (date(2026, 9, 12), "PostePay — POS Market San Donato", 4.14, SPESA, "Cibo"),
    (date(2026, 9, 12), "PostePay — POS Ipercoop Peschiera Borromeo", 7.57, SPESA, "Cibo"),
    (date(2026, 9, 13), "PostePay — POS Scotti Andrea, Mediglia (Cascina de Lassi, Landriano — carne)", 46.00, SPESA, "Cibo"),
    (date(2026, 9, 13), "PostePay — commissioni PagoPA", 1.50, SPESA, "Bollette"),
    (date(2026, 9, 13), "PostePay — avviso PagoPA, Ente 06655971007", 137.49, SPESA, "Bollette"),
    (date(2026, 9, 14), "PostePay — commissioni PagoPA", 1.50, SPESA, "Bollette"),
    (date(2026, 9, 14), "PostePay — avviso PagoPA, Ente 06655971007", 84.76, SPESA, "Bollette"),
    (date(2026, 9, 14), "PostePay — POS Esselunga San Giuliano Milanese", 1.95, SPESA, "Cibo"),
    (date(2026, 9, 14), "EdenRed — Essselunga (buono pasto)", 9.00, SPESA, "Cibo"),
    (date(2026, 9, 14), "EdenRed — Essselunga (2 buoni pasto)", 18.00, SPESA, "Cibo"),
    (date(2026, 9, 15), "EdenRed — Meriggi (buono pasto)", 9.00, SPESA, "Cibo"),
    (date(2026, 9, 15), "PostePay — versamento sul Salvadanaio", 470.00, SPESA, "Trasferimento"),
    (date(2026, 9, 15), "PostePay — commissioni bonifico, estinzione conto BCC Caravaggio", 1.00, SPESA, "Trasferimento"),
    (date(2026, 9, 15), "PostePay — bonifico SEPA istantaneo, estinzione conto BCC Caravaggio", 25.00, SPESA, "Trasferimento"),
    (date(2026, 9, 16), "PostePay — POS PV1375, Milano (benzina)", 27.84, SPESA, "Benzina"),
    (date(2026, 9, 16), "PostePay — POS Esselunga Monza", 1.73, SPESA, "Cibo"),
    (date(2026, 9, 16), "EdenRed — Esselunga (buono pasto)", 9.00, SPESA, "Cibo"),
    (date(2026, 9, 17), "PostePay — bonifico SEPA, residuo estinzione conto BCC Caravaggio", 0.01, ACCR, "Trasferimento"),
    (date(2026, 9, 11), "PostePay — Anthropic, abbonamento Claude", 21.96, SPESA, "Abbonamenti"),
    (date(2026, 9, 19), "EdenRed — Tigros (3 buoni pasto)", 27.00, SPESA, "Cibo"),
    (date(2026, 9, 19), "EdenRed — Boss Carne (36 €, non era tracciato nel foglio Settimane)", 36.00, SPESA, "Cibo"),
    (date(2026, 9, 18), "PostePay — POS 3C SRL Milano, revisione caldaia (quota carta; altri 100 € in contanti)", 40.00, SPESA, "Revisione caldaia"),
    (date(2026, 9, 19), "PostePay — Vueling, volo Mila", 32.99, SPESA, "Volo Mila"),
    (date(2026, 9, 19), "PostePay — POS Tigros San Giuliano", 7.48, SPESA, "Cibo"),
    (date(2026, 9, 21), "PostePay — POS Market San Donato", 1.51, SPESA, "Cibo"),
    (date(2026, 9, 21), "EdenRed — Carrefour", 18.00, SPESA, "Cibo"),
    (date(2026, 9, 22), "PostePay — bonifico da Muresian Horia (contributo affitto, ultimo)", 250.00, ACCR, "Entrata"),
    (date(2026, 9, 22), "PostePay — POS Market San Giuliano", 7.65, SPESA, "Cibo"),
    (date(2026, 9, 22), "EdenRed — Carrefour", 9.00, SPESA, "Cibo"),
    (date(2026, 9, 24), "PostePay — POS ATM Milano, biglietto", 4.40, SPESA, "Trasporti"),
    (date(2026, 9, 25), "PostePay — POS Armagni Panetteria, Milano", 12.00, SPESA, "Altro"),
    (date(2026, 9, 25), "PostePay — POS ATM Milano, biglietto", 4.40, SPESA, "Trasporti"),
    (date(2026, 9, 26), "PostePay — POS Società Agricola Zuff, Melegnano (cascina)", 104.17, SPESA, "Cibo"),
    (date(2026, 9, 26), "PostePay — POS Market San Donato", 7.90, SPESA, "Cibo"),
    (date(2026, 9, 26), "EdenRed — Carrefour", 18.00, SPESA, "Cibo"),
    (date(2026, 9, 27), "PostePay — POS Market San Donato", 2.88, SPESA, "Cibo"),
    (date(2026, 9, 27), "PostePay — POS Trattoria Ticino, Bereguardo", 2.60, SPESA, "Altro"),
    (date(2026, 9, 27), "PostePay — POS distributore 7896, Casorate Primo (benzina)", 28.11, SPESA, "Benzina"),
    (date(2026, 9, 29), "PostePay — bonifico stipendio AFR, settembre", 2197.00, ACCR, "Stipendio"),
    (date(2026, 9, 29), "PostePay — commissioni bonifico affitto", 1.00, SPESA, "Affitto"),
    (date(2026, 9, 29), "PostePay — bonifico istantaneo affitto ottobre", 700.00, SPESA, "Affitto"),
    (date(2026, 9, 29), "PostePay — versamento sul Salvadanaio", 550.00, SPESA, "Trasferimento"),
    (date(2026, 9, 30), "PostePay — POS Market San Donato", 1.64, SPESA, "Cibo"),
    (date(2026, 9, 30), "EdenRed — Carrefour", 9.00, SPESA, "Cibo"),
    (date(2026, 10, 1), "PostePay — POS Famila San Giuliano", 7.71, SPESA, "Cibo"),
    (date(2026, 10, 1), "EdenRed — Famila", 9.00, SPESA, "Cibo"),
    (date(2026, 10, 1), "PostePay — POS Pittarosso, scarpe Mila", 99.90, SPESA, "Altro"),
    (date(2026, 10, 1), "PostePay — canone annuale carta", 13.00, SPESA, "Commissioni"),
    (date(2026, 10, 2), "PostePay — POS Esselunga San Donato", 26.52, SPESA, "Cibo"),
    (date(2026, 10, 2), "EdenRed — Esselunga (buoni finiti)", 18.00, SPESA, "Cibo"),
    (date(2026, 10, 3), "PostePay — Prima Assicurazioni, assicurazione auto", 467.77, SPESA, "Assicurazione auto"),
    (date(2026, 10, 4), "PostePay — POS ENI 12160, Peschiera Borromeo (benzina)", 33.59, SPESA, "Benzina"),
    (date(2026, 10, 4), "PostePay — POS Market San Donato", 3.54, SPESA, "Cibo"),
    (date(2026, 10, 4), "PostePay — POS Market San Donato", 29.07, SPESA, "Cibo"),
    (date(2026, 10, 4), "PostePay — POS Pasticceria Gino", 3.60, SPESA, "Cibo"),
    (date(2026, 10, 5), "PostePay — POS Farmacia Comunale Pioltello, antidolorifico", 13.90, SPESA, "Altro"),
    (date(2026, 10, 5), "PostePay — POS Tigros San Giuliano", 28.95, SPESA, "Cibo"),
    (date(2026, 10, 6), "PostePay — POS Pinoy Saver's Mart, mais per Mila", 6.89, SPESA, "Cibo"),
    (date(2026, 10, 6), "PostePay — TIM ricarica", 15.00, SPESA, "Tim"),
    (date(2026, 10, 8), "PostePay — POS Commercialunione, caffè per Amir", 1.20, SPESA, "Altro"),
    (date(2026, 10, 8), "PostePay — POS Barber, parrucchiere", 20.00, SPESA, "Altro"),
    (date(2026, 10, 8), "PostePay — POS Market San Donato", 16.37, SPESA, "Cibo"),
    (date(2026, 10, 9), "PostePay — Foorban", 4.30, SPESA, "Cibo"),
    (date(2026, 10, 9), "EdenRed — ricarica buoni pasto di ottobre", 198.00, ACCR, "Entrata"),
    (date(2026, 10, 10), "PostePay — POS Ipercoop Peschiera Borromeo", 29.31, SPESA, "Cibo"),
    (date(2026, 10, 10), "PostePay — POS Phone Lab Peschiera, auricolari nuovi", 19.00, SPESA, "Altro"),
    (date(2026, 10, 10), "PostePay — POS Market San Donato", 7.36, SPESA, "Cibo"),
    (date(2026, 10, 11), "PostePay — commissioni bonifico benzina", 1.00, SPESA, "Benzina"),
    (date(2026, 10, 11), "PostePay — bonifico istantaneo a Milagros Yakelin Borda Condorchoa (benzina)", 20.00, SPESA, "Benzina"),
    (date(2026, 10, 11), "PostePay — POS Esselunga Monza", 43.02, SPESA, "Cibo"),
    (date(2026, 10, 11), "PostePay — POS Sushiland San Giuliano, sushi con Sasha", 28.40, SPESA, "Altro"),
    (date(2026, 10, 11), "PostePay — POS S.B. Enterprise Milano, mais e altro per Mila", 26.80, SPESA, "Altro"),
    (date(2026, 10, 11), "PostePay — Anthropic, abbonamento Claude", 21.96, SPESA, "Abbonamenti"),
    (date(2026, 10, 12), "PostePay — POS Turkish, kebab io e Mila", 23.00, SPESA, "Altro"),
    (date(2026, 10, 13), "PostePay — cashback ScontiPoste su acquisto ENI del 04/10", 0.50, ACCR, "Rimborso"),
    (date(2026, 10, 16), "PostePay — POS La Sfinge, Pioltello", 8.50, SPESA, "Cibo (uscita)"),
    (date(2026, 10, 16), "PostePay — POS Market San Donato", 2.78, SPESA, "Cibo"),
    (date(2026, 10, 17), "PostePay — POS Market San Donato", 1.82, SPESA, "Cibo"),
    (date(2026, 10, 17), "PostePay — POS Le Delizie di Via Zucchi, Monza, focaccia", 3.50, SPESA, "Altro"),
    (date(2026, 10, 17), "PostePay — POS Monza Mobilità (non ricordo)", 2.80, SPESA, "Altro"),
    (date(2026, 10, 18), "PostePay — POS Market San Giuliano", 1.49, SPESA, "Cibo"),
    (date(2026, 10, 18), "PostePay — POS Tigros San Giuliano", 3.08, SPESA, "Cibo"),
    (date(2026, 10, 21), "PostePay — POS Market San Donato", 3.49, SPESA, "Cibo"),
    (date(2026, 10, 23), "PostePay — POS Market San Donato", 5.32, SPESA, "Cibo"),
    (date(2026, 10, 23), "PostePay — POS Market San Donato", 2.99, SPESA, "Cibo"),
    (date(2026, 10, 23), "PostePay — Foorban", 3.50, SPESA, "Cibo"),
    (date(2026, 10, 25), "PostePay — POS autolavaggio NYX Paullese, lavaggio auto", 5.00, SPESA, "Altro"),
    (date(2026, 10, 29), "PostePay — Foorban", 1.60, SPESA, "Cibo"),
    (date(2026, 10, 29), "PostePay — bonifico stipendio AFR, ottobre", 2230.00, ACCR, "Stipendio"),
]
MOVIMENTI.sort(key=lambda x: x[0])

for i, (d, desc, imp, tipo, cat) in enumerate(MOVIMENTI):
    r = hr + 1 + i
    mv.cell(row=r, column=1, value=d).font = BLACK
    mv.cell(row=r, column=1).number_format = DATA
    mv.cell(row=r, column=2, value=desc).font = BLACK
    c3 = mv.cell(row=r, column=3, value=imp)
    c3.font, c3.number_format = BLACK, EUR2
    mv.cell(row=r, column=4, value=tipo).font = BLACK
    mv.cell(row=r, column=5, value=cat).font = BLACK

for r in range(hr + 1 + len(MOVIMENTI), MR + 1):
    mv.cell(row=r, column=1).font = BLUE
    mv.cell(row=r, column=1).number_format = DATA
    mv.cell(row=r, column=2).font = BLUE
    mv.cell(row=r, column=3).font = BLUE
    mv.cell(row=r, column=3).number_format = EUR2
    mv.cell(row=r, column=4).font = BLUE
    mv.cell(row=r, column=5).font = BLUE

rnote = hr + 2 + len(MOVIMENTI)
mv.cell(row=rnote, column=1, value="Note").font = LBL
note_txt = ("«Trasferimento» = spostamenti fra tuoi conti (salvadanaio, chiusura BCC Caravaggio): non sono spesa "
            "reale, tienile fuori dai conteggi. Dati PostePay fino al 29/10: mancano i movimenti del 30-31/10. "
            "Categorie corrette rispetto al tuo elenco: ENI 12160 → Benzina (era Cibo), canone carta → Commissioni "
            "(era Cibo). EdenRed: saldo a 0 dal 02/10, ricarica di 198 € il 09/10; le spese fatte con quei 198 € "
            "non sono ancora state incollate.")
mv.cell(row=rnote, column=2, value=note_txt).font = NOTE
mv.cell(row=rnote, column=2).alignment = Alignment(wrap_text=True, vertical="top")
mv.merge_cells(start_row=rnote, start_column=2, end_row=rnote, end_column=5)
mv.row_dimensions[rnote].height = 78

# ============================================================ PIANO
pl = wb.create_sheet("Piano")
pl["A1"] = "Parametri e curva del piano"
pl["A1"].font = H1
pl["A2"] = "Le celle gialle sono i parametri: cambiali se cambia il piano."
pl["A2"].font = NOTE
pl.column_dimensions["A"].width = 34
pl.column_dimensions["B"].width = 16
pl.column_dimensions["C"].width = 60

par = [
    ("Obiettivo del fondo (€)", 5000, EUR, "Fondo di emergenza: circa 3 mesi di spese essenziali."),
    ("Accantonamento buffer al mese (€)", 150, EUR, "Assicurazione, bollo, freni, gomme, revisione."),
    ("Inizio accantonamento buffer", date(2026, 9, 1), DATA, "Primo mese in cui hai messo via i 150 €."),
]
for i, (lab, val, fmt, nota) in enumerate(par):
    r = 3 + i
    pl.cell(row=r, column=1, value=lab).font = LBL
    c = pl.cell(row=r, column=2, value=val)
    c.font, c.number_format, c.fill = BLUE, fmt, YELLOW
    pl.cell(row=r, column=3, value=nota).font = NOTE

pl.cell(row=7, column=1, value="Impegni noti, pagati dal conto corrente (non dal fondo)").font = LBL
impegni = [
    "Assicurazione auto: 467,77 € pagati il 03/10 (confermato, vedi foglio Spese).",
    "Lotta Club Seggiano: 50 € a ottobre (iscrizione + primo mese), poi 25 €/mese ricorrenti — è "
    "mensile, non semestrale (corretto). Da novembre è un costo fisso ricorrente, non più una spesa "
    "una tantum del buffer.",
    "Rimborso 730: 1.481 € netti attesi nov/dic (vedi foglio Entrate). Non ancora nella curva sotto: "
    "la aggiungo quando arriva davvero.",
]
for i, t in enumerate(impegni):
    pl.cell(row=8 + i, column=3, value="• " + t).font = NOTE

pl.cell(row=12, column=1, value="Curva del piano — solo punti confermati o decisi").font = LBL
pl.cell(row=P0 - 1, column=1, value="Data").font = LBL
pl.cell(row=P0 - 1, column=2, value="Fondo (€)").font = LBL
pl.cell(row=P0 - 1, column=3, value="Da dove viene").font = LBL
origini = [
    "Punto di partenza.",
    "Saldo reale letto dal foglio Settimane il 20/09.",
    "470 + 550 € versati a ottobre (deciso il 20/09). Assicurazione e lotta escono dal conto corrente, "
    "non dal fondo: non riducono questo numero.",
]
for i, (d, v) in enumerate(PIANO):
    r = P0 + i
    a = pl.cell(row=r, column=1, value=d); a.font, a.number_format = BLACK, DATA
    b = pl.cell(row=r, column=2, value=v); b.font, b.number_format = BLACK, EUR
    if origini[i]:
        pl.cell(row=r, column=3, value=origini[i]).font = NOTE

pl.cell(row=P1 + 2, column=1, value="Da novembre in poi").font = LBL
pl.cell(row=P1 + 2, column=3,
        value="Non ancora stimato. Noto: i 250 € di tuo padre sono finiti (l'ultimo è del 22/09), lo "
              "stipendio di ottobre è 2.230 €. Manca ancora il rimborso 730 (data) e il costo reale di "
              "bollette e auto a novembre. Appena hai il dato reale di novembre aggiungo il punto qui "
              "invece di indovinarlo adesso.").font = NOTE
pl.cell(row=P1 + 2, column=3).alignment = Alignment(wrap_text=True, vertical="top")
pl.row_dimensions[P1 + 2].height = 50

pl.cell(row=P1 + 4, column=1, value="Fonte dei numeri").font = LBL
pl.cell(row=P1 + 4, column=3,
        value="Piano concordato il 13/09/2026. Curva rifatta il 20/09/2026 con i costi reali di caldaia e "
              "assicurazione. La lotta è mensile (50 € il primo mese, poi 25 €/mese): costo fisso, non "
              "una tantum del buffer.").font = NOTE
pl.cell(row=P1 + 4, column=3).alignment = Alignment(wrap_text=True, vertical="top")
pl.row_dimensions[P1 + 4].height = 40

# ============================================================ CRUSCOTTO
cr = wb.create_sheet("Cruscotto", 0)
cr["A1"] = "Come stai andando"
cr["A1"].font = H1
cr["A2"] = "Tutto qui dentro si calcola dai fogli Settimane, Spese e Piano. Non c'è niente da scrivere."
cr["A2"].font = NOTE
cr.column_dimensions["A"].width = 34
cr.column_dimensions["B"].width = 17
cr.column_dimensions["C"].width = 58

SA = "Settimane!$A$4:$A${}".format(NR)
def col(letter):
    return "Settimane!${L}$4:${L}${n}".format(L=letter, n=NR)

def ultima(letter):
    return "INDEX({c},MATCH(MAX({a}),{a},0))".format(c=col(letter), a=SA)

ETICHETTE = [
    "n_settimane", "ultima", "fondo", "obiettivo", "mancano",
    "cc", "contanti", "buoni_pasto", "buf_acc", "buf_speso", "buf_disp", "cassa",
    "piano", "scarto_piano", "speso_ult", "media4", "scarto_budget_ult",
]
R = {k: 4 + i for i, k in enumerate(ETICHETTE)}
def B(k):
    return "$B${}".format(R[k])

def piano_interp(cellref):
    m = "MATCH({d},{PA},1)".format(d=cellref, PA=PA)
    return (
        '=IF(NOT(ISNUMBER({d})),0,'
        'IF({d}<=INDEX({PA},1),0,'
        'IF({d}>=INDEX({PA},{N}),INDEX({PB},{N}),'
        'INDEX({PB},{m})+({d}-INDEX({PA},{m}))'
        '/(INDEX({PA},{m}+1)-INDEX({PA},{m}))'
        '*(INDEX({PB},{m}+1)-INDEX({PB},{m})))))'
    ).format(d=cellref, PA=PA, PB=PB, N=N, m=m)

righe = [
    ("n_settimane", "Settimane registrate", "=COUNT({})".format(SA), "0",
     "Quante domeniche hai chiuso."),
    ("ultima", "Ultima domenica chiusa", '=IF({n}=0,"",MAX({a}))'.format(n=B("n_settimane"), a=SA), DATA,
     "Se è più vecchia di una settimana, sei in ritardo."),
    ("fondo", "Fondo sul conto risparmio", '=IF({n}=0,0,{u})'.format(n=B("n_settimane"), u=ultima("C")), EUR,
     "L'ultimo saldo che hai registrato."),
    ("obiettivo", "Obiettivo", "=Piano!$B$3", EUR, "Il traguardo."),
    ("mancano", "Mancano al traguardo", "=MAX(0,{o}-{f})".format(o=B("obiettivo"), f=B("fondo")), EUR,
     "Quanto resta da mettere via."),
    ("cc", "Conto corrente", '=IF({n}=0,0,{u})'.format(n=B("n_settimane"), u=ultima("B")), EUR,
     "L'ultimo saldo del conto operativo."),
    ("contanti", "Contanti", '=IF({n}=0,0,{u})'.format(n=B("n_settimane"), u=ultima("D")), EUR,
     "L'ultimo contante dichiarato."),
    ("buoni_pasto", "Buoni pasto residui", '=IF({n}=0,0,{u})'.format(n=B("n_settimane"), u=ultima("E")), EUR,
     "L'ultimo saldo EdenRed dichiarato."),
    ("buf_acc", "Buffer accantonato",
     '=IF({d}="",0,Piano!$B$4*MAX(0,(YEAR({d})-YEAR(Piano!$B$5))*12+MONTH({d})-MONTH(Piano!$B$5)+1))'
     .format(d=B("ultima")), EUR,
     "150 € per ogni mese trascorso dall'inizio."),
    ("buf_speso", "Già speso dal buffer", "=Spese!$C${}".format(SR + 2), EUR,
     "Somma del foglio Spese, incluse le righe previsto."),
    ("buf_disp", "Buffer disponibile", "={a}-{s}".format(a=B("buf_acc"), s=B("buf_speso")), EUR,
     "Se va sotto zero lo sta finanziando il fondo: normale con assicurazione e lotta insieme."),
    ("cassa", "Cassa libera", "={c}-MAX(0,{b})".format(c=B("cc"), b=B("buf_disp")), EUR,
     "Sul conto corrente, tolto il buffer. È quello che puoi spendere davvero."),
    ("piano", "Il piano a quella data", piano_interp(B("ultima")), EUR,
     "Dove dovresti essere secondo la curva del foglio Piano."),
    ("scarto_piano", "Avanti (+) o indietro (−) sul piano", "={f}-{p}".format(f=B("fondo"), p=B("piano")), EUR,
     "Positivo: sei in anticipo. Negativo: recupera."),
    ("speso_ult", "Speso l'ultima settimana", '=IF({n}<2,"",{u})'.format(n=B("n_settimane"), u=ultima("I")), EUR,
     "Calcolato dai saldi, non dagli scontrini."),
    ("media4", "Media delle ultime 4 settimane",
     '=IFERROR(AVERAGEIFS({h},{a},">="&({d}-21),{a},"<="&{d}),"")'.format(h=col("I"), a=SA, d=B("ultima")), EUR,
     "Il numero da guardare: una settimana storta non vuol dire niente."),
    ("scarto_budget_ult", "Scarto vs budget, ultima settimana", '=IF({n}<1,"",{u})'.format(n=B("n_settimane"), u=ultima("K")), EUR,
     "Dal foglio Settimane: negativo è buono, hai speso meno del previsto."),
]
assert [x[0] for x in righe] == ETICHETTE, "ordine delle righe non allineato"

for i, (key, lab, formula, fmt, nota) in enumerate(righe):
    r = R[key]
    cr.cell(row=r, column=1, value=lab).font = LBL
    c = cr.cell(row=r, column=2, value=formula)
    c.font, c.number_format, c.border = BLACK, fmt, THIN
    if key in ("fondo", "scarto_piano", "buf_disp", "cassa", "media4"):
        c.font = Font(name=ARIAL, size=11, bold=True)
    cr.cell(row=r, column=3, value=nota).font = NOTE

r = 4 + len(righe) + 2
cr.cell(row=r, column=1, value="Come si usa").font = LBL
istr = [
    "Domenica sera apri l'app della banca, conta i contanti e leggi il saldo EdenRed.",
    "Vai sul foglio Settimane, prima riga vuota, e scrivi data e i quattro saldi (celle blu).",
    "Prima di chiudere la settimana, scrivi in «Budget previsto» quanto pensavi di spendere.",
    "Se in settimana è entrato qualcosa — stipendio, ripetizioni, i soldi dei tuoi — scrivilo in «Entrate» "
    "e, se vuoi tenerne memoria precisa, anche nel foglio Entrate.",
    "Ogni settimana (o mese) incolla i movimenti PostePay nel foglio Movimenti, aggiungendo a mano quelli EdenRed.",
    "Torna qui. Due minuti in tutto.",
]
for i, t in enumerate(istr):
    cr.cell(row=r + 1 + i, column=1, value="{}.".format(i + 1)).font = LBL
    cr.cell(row=r + 1 + i, column=3, value=t).font = Font(name=ARIAL, size=11)
    cr.cell(row=r + 1 + i, column=3).alignment = Alignment(wrap_text=True, vertical="top")

r2 = r + len(istr) + 2
cr.cell(row=r2, column=1, value="Perché funziona").font = LBL
cr.cell(row=r2, column=3, value=("Non misura le spese ma il patrimonio: patrimonio di domenica scorsa "
                                 "+ entrate − patrimonio di oggi = quanto è uscito, contanti e buoni "
                                 "pasto compresi. Per lo stesso motivo il bonifico al conto risparmio non "
                                 "risulta come spesa: sposta i soldi da una tasca all'altra.")).font = NOTE
cr.cell(row=r2, column=3).alignment = Alignment(wrap_text=True, vertical="top")
cr.row_dimensions[r2].height = 58

cr.cell(row=r2 + 2, column=1, value="Legenda").font = LBL
cr.cell(row=r2 + 2, column=3, value="Blu = celle che scrivi tu.  Nero = formule, non toccarle.  Corsivo blu "
                                    "= previsione non ancora confermata (fogli Spese/Entrate).  Giallo "
                                    "(foglio Piano) = parametri da rivedere se cambia il piano.").font = NOTE
cr.cell(row=r2 + 2, column=3).alignment = Alignment(wrap_text=True, vertical="top")

cr.sheet_view.showGridLines = False
pl.sheet_view.showGridLines = False

wb.save(OUT)
print("scritto", OUT)
