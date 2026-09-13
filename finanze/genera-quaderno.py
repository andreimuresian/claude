# -*- coding: utf-8 -*-
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import date

OUT = "/home/user/claude/finanze/quaderno-5000.xlsx"

ARIAL   = "Arial"
BLUE    = Font(name=ARIAL, size=11, color="0000FF")           # celle da compilare
BLACK   = Font(name=ARIAL, size=11)
GREY    = Font(name=ARIAL, size=11, color="7C8A91")
ITAL    = Font(name=ARIAL, size=11, color="0000FF", italic=True)
H1      = Font(name=ARIAL, size=15, bold=True, color="141C22")
H2      = Font(name=ARIAL, size=11, bold=True, color="FFFFFF")
LBL     = Font(name=ARIAL, size=11, bold=True)
NOTE    = Font(name=ARIAL, size=10, color="4A565E", italic=True)
HEADFIL = PatternFill("solid", fgColor="0E6E5E")
YELLOW  = PatternFill("solid", fgColor="FFFF00")
SUNK    = PatternFill("solid", fgColor="EFEEE9")
THIN    = Border(bottom=Side(style="thin", color="D3D0C7"))

EUR  = '#,##0" €";(#,##0)" €";"–"'
EUR2 = '#,##0.00" €";(#,##0.00)" €";"–"'
DATA = "dd/mm/yyyy"

NR   = 203   # ultima riga dati in Settimane (4..203)
SR   = 103   # ultima riga dati in Spese   (4..103)

PIANO = [
    (date(2026, 9, 1), 0), (date(2026, 9, 30), 446), (date(2026, 10, 31), 1442),
    (date(2026, 11, 30), 2188), (date(2026, 12, 31), 4094), (date(2027, 1, 31), 4355),
    (date(2027, 2, 28), 4616), (date(2027, 3, 31), 4877), (date(2027, 4, 30), 5138),
]
P0, P1 = 10, 10 + len(PIANO) - 1          # righe della curva sul foglio Piano
PA = "Piano!$A${}:$A${}".format(P0, P1)
PB = "Piano!$B${}:$B${}".format(P0, P1)
N  = len(PIANO)

wb = Workbook()

# ============================================================ SETTIMANE
ws = wb.active
ws.title = "Settimane"

ws["A1"] = "Il quaderno dei 5.000 — registro settimanale"
ws["A1"].font = H1
ws["A2"] = ("Ogni domenica scrivi solo le colonne in blu: i due saldi letti dall'app della banca, "
            "le entrate della settimana e le uscite grosse (affitto, bollette, spese annuali). "
            "Tutto il resto si calcola da solo. Le tre righe in corsivo sono un esempio: cancellale.")
ws["A2"].font = NOTE
ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
ws.merge_cells("A2:K2")
ws.row_dimensions[2].height = 42

heads = [
    ("Domenica", 12), ("Conto corrente (€)", 17), ("Conto risparmio (€)", 18),
    ("Entrate (€)", 12), ("Uscite grosse (€)", 16), ("Nota", 26),
    ("Patrimonio (€)", 15), ("Speso in settimana (€)", 20),
    ("Scarto vs budget (€)", 18), ("Piano a quella data (€)", 19), ("Fondo vs piano (€)", 17),
]
for i, (h, w) in enumerate(heads, start=1):
    c = ws.cell(row=3, column=i, value=h)
    c.font, c.fill = H2, HEADFIL
    c.alignment = Alignment(wrap_text=True, vertical="bottom")
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[3].height = 30
ws.freeze_panes = "A4"

ESEMPI = [
    (date(2026, 8, 30), 2190, 0,   2190, 0,    "ESEMPIO — stipendio di agosto"),
    (date(2026, 9, 6),  624,  446, 0,    1000, "ESEMPIO — affitto"),
    (date(2026, 9, 13), 479,  446, 0,    0,    "ESEMPIO — cancella queste tre righe"),
]

def piano_interp(r):
    """Valore del piano alla data in A{r}, interpolato fra i punti mensili."""
    m = "MATCH($A{r},{PA},1)".format(r=r, PA=PA)
    return (
        '=IF(NOT(ISNUMBER($A{r})),"",'
        'IF($A{r}<=INDEX({PA},1),0,'
        'IF($A{r}>=INDEX({PA},{N}),INDEX({PB},{N}),'
        'INDEX({PB},{m})+($A{r}-INDEX({PA},{m}))'
        '/(INDEX({PA},{m}+1)-INDEX({PA},{m}))'
        '*(INDEX({PB},{m}+1)-INDEX({PB},{m})))))'
    ).format(r=r, PA=PA, PB=PB, N=N, m=m)

for r in range(4, NR + 1):
    idx = r - 4
    if idx < len(ESEMPI):
        d, cc, rp, en, fi, nt = ESEMPI[idx]
        ws.cell(row=r, column=1, value=d).font = ITAL
        for col, val in ((2, cc), (3, rp), (4, en), (5, fi)):
            ws.cell(row=r, column=col, value=val).font = ITAL
        ws.cell(row=r, column=6, value=nt).font = ITAL
    else:
        for col in range(1, 6):
            ws.cell(row=r, column=col).font = BLUE
        ws.cell(row=r, column=6).font = BLUE
        ws.cell(row=r, column=4, value=0).font = BLUE
        ws.cell(row=r, column=5, value=0).font = BLUE

    ws.cell(row=r, column=1).number_format = DATA
    for col in (2, 3, 4, 5):
        ws.cell(row=r, column=col).number_format = EUR

    ws.cell(row=r, column=7,  value='=IF(NOT(ISNUMBER($A{r})),"",$B{r}+$C{r})'.format(r=r))
    ws.cell(row=r, column=8,  value=('=IF(OR(NOT(ISNUMBER($A{r})),NOT(ISNUMBER($A{p}))),"",'
                                     '$G{p}+$D{r}-$G{r}-$E{r})').format(r=r, p=r - 1))
    ws.cell(row=r, column=9,  value='=IF($H{r}="","",$H{r}-Piano!$B$4)'.format(r=r))
    ws.cell(row=r, column=10, value=piano_interp(r))
    ws.cell(row=r, column=11, value='=IF($J{r}="","",$C{r}-$J{r})'.format(r=r))
    for col in range(7, 12):
        c = ws.cell(row=r, column=col)
        c.font, c.number_format, c.border = BLACK, EUR, THIN

# ============================================================ SPESE
sp = wb.create_sheet("Spese")
sp["A1"] = "Spese annuali — quello che esce dal buffer"
sp["A1"].font = H1
sp["A2"] = ("Il buffer si riempie da solo di 150 € al mese. Qui registri solo le uscite: "
            "assicurazione, freni, bollo, gomme, revisione, tagliando.")
sp["A2"].font = NOTE
sp.merge_cells("A2:C2")

for i, (h, w) in enumerate([("Data", 12), ("Voce", 34), ("Importo (€)", 14)], start=1):
    c = sp.cell(row=3, column=i, value=h)
    c.font, c.fill = H2, HEADFIL
    sp.column_dimensions[get_column_letter(i)].width = w
sp.freeze_panes = "A4"

sp.cell(row=4, column=1, value=date(2026, 10, 15)).font = ITAL
sp.cell(row=4, column=2, value="ESEMPIO — assicurazione auto (cancella questa riga)").font = ITAL
sp.cell(row=4, column=3, value=550).font = ITAL
for r in range(4, SR + 1):
    sp.cell(row=r, column=1).number_format = DATA
    sp.cell(row=r, column=3).number_format = EUR
    if r > 4:
        for col in (1, 2, 3):
            sp.cell(row=r, column=col).font = BLUE

sp.cell(row=SR + 2, column=2, value="Totale speso dal buffer").font = LBL
tot = sp.cell(row=SR + 2, column=3, value="=SUM($C$4:$C${})".format(SR))
tot.font, tot.number_format = LBL, EUR

# ============================================================ PIANO
pl = wb.create_sheet("Piano")
pl["A1"] = "Parametri e curva del piano"
pl["A1"].font = H1
pl["A2"] = "Le celle gialle sono i parametri: cambiali se cambia il piano."
pl["A2"].font = NOTE
pl.column_dimensions["A"].width = 34
pl.column_dimensions["B"].width = 16
pl.column_dimensions["C"].width = 56

par = [
    ("Obiettivo del fondo (€)", 5000, EUR, "Fondo di emergenza: circa 3 mesi di spese essenziali."),
    ("Budget settimanale (€)", 130, EUR, "Spesa, benzina, vita, casa e utenze. Affitto escluso."),
    ("Accantonamento buffer al mese (€)", 150, EUR, "Assicurazione, bollo, freni, gomme, revisione."),
    ("Inizio accantonamento buffer", date(2026, 9, 1), DATA, "Primo mese in cui hai messo via i 150 €."),
]
for i, (lab, val, fmt, nota) in enumerate(par):
    r = 3 + i
    pl.cell(row=r, column=1, value=lab).font = LBL
    c = pl.cell(row=r, column=2, value=val)
    c.font, c.number_format, c.fill = BLUE, fmt, YELLOW
    pl.cell(row=r, column=3, value=nota).font = NOTE

pl.cell(row=8, column=1, value="Curva del piano — fondo cumulato atteso").font = LBL
pl.cell(row=9, column=1, value="Data").font = LBL
pl.cell(row=9, column=2, value="Fondo (€)").font = LBL
pl.cell(row=9, column=3, value="Da dove viene").font = LBL
origini = [
    "Punto di partenza.",
    "446 € versati a settembre.",
    "446 + 550 € dai tuoi (affitto a 700 e 250 € da tuo padre).",
    "446 + 300 € dai tuoi.",
    "446 + 300 € dai tuoi + ~1.160 € fra tredicesima e conguaglio.",
    "Netto sceso a ~2.005 €: al fondo restano ~261 €/mese.",
    "", "", "Traguardo raggiunto.",
]
for i, (d, v) in enumerate(PIANO):
    r = P0 + i
    a = pl.cell(row=r, column=1, value=d); a.font, a.number_format = BLACK, DATA
    b = pl.cell(row=r, column=2, value=v); b.font, b.number_format = BLACK, EUR
    if origini[i]:
        pl.cell(row=r, column=3, value=origini[i]).font = NOTE

pl.cell(row=P1 + 2, column=1, value="Fonte dei numeri").font = LBL
pl.cell(row=P1 + 2, column=3,
        value="Piano concordato il 13/09/2026, sezione «Quando arrivi davvero a 5.000».").font = NOTE

# ============================================================ CRUSCOTTO
cr = wb.create_sheet("Cruscotto", 0)
cr["A1"] = "Come stai andando"
cr["A1"].font = H1
cr["A2"] = "Tutto qui dentro si calcola dai fogli Settimane e Spese. Non c'è niente da scrivere."
cr["A2"].font = NOTE
cr.column_dimensions["A"].width = 34
cr.column_dimensions["B"].width = 17
cr.column_dimensions["C"].width = 58

SA = "Settimane!$A$4:$A${}".format(NR)
def col(letter):
    return "Settimane!${L}$4:${L}${n}".format(L=letter, n=NR)

def ultima(letter):
    return "INDEX({c},MATCH(MAX({a}),{a},0))".format(c=col(letter), a=SA)

# Le righe sono indirizzate per nome: i riferimenti si costruiscono dopo,
# così spostare una riga non rompe le formule.
ETICHETTE = [
    "n_settimane", "ultima", "fondo", "obiettivo", "mancano", "piano", "scarto_piano",
    "cc", "buf_acc", "buf_speso", "buf_disp", "cassa", "speso_ult", "media4",
    "budget", "scarto_ritmo",
]
R = {k: 4 + i for i, k in enumerate(ETICHETTE)}
def B(k):
    return "$B${}".format(R[k])

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
    ("piano", "Il piano a quella data", '=IF({n}=0,0,{u})'.format(n=B("n_settimane"), u=ultima("J")), EUR,
     "Dove dovresti essere secondo il piano."),
    ("scarto_piano", "Avanti (+) o indietro (−)", "={f}-{p}".format(f=B("fondo"), p=B("piano")), EUR,
     "Positivo: sei in anticipo. Negativo: recupera."),
    ("cc", "Conto corrente", '=IF({n}=0,0,{u})'.format(n=B("n_settimane"), u=ultima("B")), EUR,
     "L'ultimo saldo del conto operativo."),
    ("buf_acc", "Buffer accantonato",
     '=IF({d}="",0,Piano!$B$5*MAX(0,(YEAR({d})-YEAR(Piano!$B$6))*12+MONTH({d})-MONTH(Piano!$B$6)+1))'
     .format(d=B("ultima")), EUR,
     "150 € per ogni mese trascorso dall'inizio."),
    ("buf_speso", "Già speso dal buffer", "=Spese!$C${}".format(SR + 2), EUR,
     "Somma del foglio Spese."),
    ("buf_disp", "Buffer disponibile", "={a}-{s}".format(a=B("buf_acc"), s=B("buf_speso")), EUR,
     "Se va sotto zero lo sta finanziando il fondo: normale il primo inverno."),
    ("cassa", "Cassa libera", "={c}-MAX(0,{b})".format(c=B("cc"), b=B("buf_disp")), EUR,
     "Sul conto corrente, tolto il buffer. È quello che puoi spendere davvero."),
    ("speso_ult", "Speso l'ultima settimana", '=IF({n}<2,"",{u})'.format(n=B("n_settimane"), u=ultima("H")), EUR,
     "Calcolato dai saldi, non dagli scontrini."),
    ("media4", "Media delle ultime 4 settimane",
     '=IFERROR(AVERAGEIFS({h},{a},">="&({d}-21),{a},"<="&{d}),"")'.format(h=col("H"), a=SA, d=B("ultima")), EUR,
     "Il numero da guardare: una settimana storta non vuol dire niente."),
    ("budget", "Budget settimanale", "=Piano!$B$4", EUR, "Il ritmo di piano."),
    ("scarto_ritmo", "Scarto sul ritmo",
     '=IF({s}="","",{s}-{b})'.format(s=B("speso_ult"), b=B("budget")), EUR,
     "Negativo è buono: stai spendendo meno del previsto."),
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
    "Domenica sera apri l'app della banca e leggi i due saldi.",
    "Vai sul foglio Settimane, prima riga vuota, e scrivi data e saldi (le celle blu).",
    "Se in settimana è entrato qualcosa — stipendio, ripetizioni, i soldi dei tuoi — scrivilo in «Entrate».",
    "Se hai pagato affitto, bollette o una spesa annuale, scrivilo in «Uscite grosse».",
    "Torna qui. Novanta secondi in tutto.",
]
for i, t in enumerate(istr):
    cr.cell(row=r + 1 + i, column=1, value="{}.".format(i + 1)).font = LBL
    cr.cell(row=r + 1 + i, column=3, value=t).font = BLACK
    cr.cell(row=r + 1 + i, column=3).font = Font(name=ARIAL, size=11)

r2 = r + len(istr) + 2
cr.cell(row=r2, column=1, value="Perché funziona").font = LBL
cr.cell(row=r2, column=3, value=("Non misura le spese ma il patrimonio: patrimonio di domenica scorsa "
                                 "+ entrate − patrimonio di oggi = quanto è uscito, contanti compresi. "
                                 "Per lo stesso motivo il bonifico al conto risparmio non risulta come "
                                 "spesa: sposta i soldi da una tasca all'altra.")).font = NOTE
cr.cell(row=r2, column=3).alignment = Alignment(wrap_text=True, vertical="top")
cr.row_dimensions[r2].height = 58

cr.cell(row=r2 + 2, column=1, value="Legenda").font = LBL
cr.cell(row=r2 + 2, column=3, value="Blu = celle che scrivi tu.  Nero = formule, non toccarle.  "
                                    "Giallo (foglio Piano) = parametri da rivedere se cambia il piano.").font = NOTE

cr.sheet_view.showGridLines = False
pl.sheet_view.showGridLines = False

wb.save(OUT)
print("scritto", OUT)
