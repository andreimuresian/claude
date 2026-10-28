# -*- coding: utf-8 -*-
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

OUT = "/home/user/claude/freelance/studi-ingegneria.xlsx"

ARIAL   = "Arial"
BLUE    = Font(name=ARIAL, size=11, color="0000FF")           # celle da compilare
BLACK   = Font(name=ARIAL, size=11)
GREY    = Font(name=ARIAL, size=11, color="7C8A91")
H1      = Font(name=ARIAL, size=15, bold=True, color="141C22")
H2      = Font(name=ARIAL, size=11, bold=True, color="FFFFFF")
LBL     = Font(name=ARIAL, size=11, bold=True)
NOTE    = Font(name=ARIAL, size=10, color="4A565E", italic=True)
HEADFIL = PatternFill("solid", fgColor="0E6E5E")
THIN    = Border(bottom=Side(style="thin", color="D3D0C7"))
WRAP    = Alignment(wrap_text=True, vertical="top")

DATA_RICERCA = "28/10/2026"
NON_VERIF    = "Non verificato online"
NO_RISCONTRO = "Ricerca web del " + DATA_RICERCA + ": nessun riscontro"

# nome, tipo (stima dal nome), indirizzo, comune, sito, cosa fa, dati economici, fonte, priorità
STUDI = [
    ("Barci Engineering S.p.A.", "Società di ingegneria (S.p.A.)", "Via Tolstoj 86", "San Giuliano Milanese",
     "www.barciengineering.it",
     "Un elenco MePA (anno 2024) la dà con sede legale a Montalto Uffugo (CS), P.IVA 02444790782. "
     "Attività esatta e ruolo della sede di San Giuliano da verificare.",
     "Non trovati. Per le S.p.A. il bilancio si può chiedere al Registro Imprese (Telemaco, copia bilancio 2,50 €).",
     "Elenco MePA (parziale); nessun dato su fatturato e dipendenti", 1),
    ("Studiora", "Studio (da verificare)", "Via Emilia 24", "San Giuliano Milanese",
     "", NON_VERIF, "Non trovati", NO_RISCONTRO, 1),
    ("Ing. Lamanna Simone", "Professionista singolo (probabile)", "Via Molise 9", "San Giuliano Milanese",
     "", NON_VERIF, "Non pubblici (professionista)",
     "Ricerca non eseguita. Verifica sull'Albo dell'Ordine degli Ingegneri di Milano", 2),
    ("Studio Ingegneria Lomanno", "Studio (da verificare)", "Via Triulziana 38", "San Donato Milanese",
     "", NON_VERIF, "Non trovati", NO_RISCONTRO, 2),
    ("Monticone Ing. Marcello", "Professionista singolo (probabile)", "Via Adda 18", "San Donato Milanese",
     "", NON_VERIF, "Non pubblici (professionista)", NO_RISCONTRO, 2),
    ("Studio Parodi", "Studio (da verificare)", "Via Libertà (n. civico da trovare)", "San Donato Milanese",
     "", NON_VERIF, "Non trovati",
     NO_RISCONTRO + ". Numero civico non trovato: guardare su Google Maps o sulla scheda Pagine Gialle", 2),
    ("DEAL Progetti", "Società (da verificare)", "Via Mameli 2", "Milano",
     "", NON_VERIF, "Non trovati", NO_RISCONTRO, 3),
    ("Andrea Carlo Rota", "Professionista singolo (probabile)", "Via Astolfo 7", "Milano",
     "", NON_VERIF, "Non pubblici (professionista)", NO_RISCONTRO, 3),
]

COLS = [  # titolo, larghezza
    ("N", 5), ("Nome", 30), ("Tipo (stima dal nome)", 26), ("Indirizzo (come indicato)", 30),
    ("Comune", 22), ("Telefono", 16), ("Sito / contatto", 26), ("Cosa fa", 46),
    ("Dati economici", 38), ("Fonte / stato verifica", 38), ("Priorità suggerita (1-3)", 14),
    ("Contattato il", 14), ("Esito", 18), ("Note, consigli ricevuti, nomi suggeriti", 50),
]

ESITI = ["Da contattare", "Contattato", "Appuntamento fissato", "Incontrato", "Nessuna risposta", "Non interessato"]

wb = Workbook()

# ============================================================ STUDI
ws = wb.active
ws.title = "Studi"

ws["A1"] = "Studi di ingegneria in zona — lista di contatto"
ws["A1"].font = H1
ws["A2"] = ("Obiettivo: parlare con colleghi della zona per capire quali aziende hanno problemi tecnici o "
            "documentali e se possono servire collaboratori esterni. Le colonne in blu vanno compilate "
            "a mano. 'Tipo' è una stima dal solo nome: va confermata. Una ricerca web non ha confermato "
            "l'esistenza degli studi tranne parzialmente per Barci Engineering. Il fatturato degli studi "
            "individuali non è pubblico.")
ws["A2"].font = NOTE
ws["A2"].alignment = WRAP
ws.merge_cells("A2:N2")
ws.row_dimensions[2].height = 46

HR = 4
for c, (t, w) in enumerate(COLS, start=1):
    cell = ws.cell(row=HR, column=c, value=t)
    cell.font, cell.fill = H2, HEADFIL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.column_dimensions[get_column_letter(c)].width = w
ws.row_dimensions[HR].height = 32

for i, (nome, tipo, ind, comune, sito, cosa, eco, fonte, prio) in enumerate(STUDI, start=1):
    r = HR + i
    vals = [i, nome, tipo, ind, comune, "", sito, cosa, eco, fonte, prio, "", "Da contattare", ""]
    for c, v in enumerate(vals, start=1):
        cell = ws.cell(row=r, column=c, value=v if v != "" else None)
        cell.alignment = WRAP
        cell.border = THIN
        cell.font = BLUE if c in (6, 7, 11, 12, 13, 14) else BLACK
    ws.cell(row=r, column=1).font = GREY
    ws.cell(row=r, column=12).number_format = "dd/mm/yyyy"
    ws.row_dimensions[r].height = 78

LAST = HR + 40   # spazio per aggiungere altri studi
dv = DataValidation(type="list", formula1='"' + ",".join(ESITI) + '"', allow_blank=True)
ws.add_data_validation(dv)
dv.add("M{}:M{}".format(HR + 1, LAST))
for r in range(HR + len(STUDI) + 1, LAST + 1):
    for c in range(1, len(COLS) + 1):
        cell = ws.cell(row=r, column=c)
        cell.border = THIN
        cell.alignment = WRAP
        cell.font = BLUE if c > 1 else GREY
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.freeze_panes = ws.cell(row=HR + 1, column=3)
ws.auto_filter.ref = "A{}:{}{}".format(HR, get_column_letter(len(COLS)), LAST)

# ============================================================ DOMANDE
wd = wb.create_sheet("Domande")
wd.column_dimensions["A"].width = 6
wd.column_dimensions["B"].width = 110
wd["A1"] = "Cosa chiedere (15 minuti, da collega)"
wd["A1"].font = H1

wd["A3"] = "Messaggio o telefonata"
wd["A3"].font = LBL
wd["B4"] = ("«Buongiorno, sono un ingegnere delle telecomunicazioni della zona e sto avviando un'attività "
            "mia di automazione e analisi dati. Vorrei farle tre domande da collega, 15 minuti, quando "
            "le è comodo.»")
wd["B4"].font, wd["B4"].alignment = BLACK, WRAP
wd.row_dimensions[4].height = 48

wd["A6"] = "Domande"
wd["A6"].font = LBL
DOMANDE = [
    "Che tipo di clienti (PMI, industrie) avete in zona?",
    "Quali attività ripetitive o documenti vi fanno perdere più tempo?",
    "Vi capita di avere bisogno di collaboratori esterni per calcoli, CAD o automazioni?",
    "Come avete cominciato? Cosa vi sarebbe servito sapere all'inizio?",
    "Conoscete aziende della zona con problemi tecnici o di gestione che potrei ascoltare?",
]
for i, d in enumerate(DOMANDE, start=1):
    wd.cell(row=6 + i, column=1, value=i).font = GREY
    c = wd.cell(row=6 + i, column=2, value=d)
    c.font, c.alignment = BLACK, WRAP

wd["A13"] = "Come verificare uno studio prima di contattarlo"
wd["A13"].font = LBL
VERIFICA = [
    "Professionisti: Albo dell'Ordine degli Ingegneri della Provincia di Milano (ricerca pubblica per nome).",
    "Società: Registro Imprese, 'Trova impresa' su registroimprese.it (attività, ATECO, stato).",
    "Bilancio di una S.r.l./S.p.A.: Telemaco, copia del bilancio 2,50 €; visura ordinaria società di capitali 5,00 €.",
    "Sito web dello studio, Google Maps (foto, recensioni) e scheda Pagine Gialle.",
]
for i, d in enumerate(VERIFICA, start=1):
    wd.cell(row=13 + i, column=1, value=i).font = GREY
    c = wd.cell(row=13 + i, column=2, value=d)
    c.font, c.alignment = BLACK, WRAP

wb.save(OUT)
print("salvato:", OUT)
