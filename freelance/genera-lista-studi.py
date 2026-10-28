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
LINK    = Font(name=ARIAL, size=10, color="0563C1", underline="single")
HEADFIL = PatternFill("solid", fgColor="0E6E5E")
THIN    = Border(bottom=Side(style="thin", color="D3D0C7"))
WRAP    = Alignment(wrap_text=True, vertical="top")

PRIVATO = "Non pubblici (ditta individuale / professionista)"

# nome, tipo, indirizzo, comune, telefono, sito, cosa fa, dati economici, priorità, note di verifica
STUDI = [
    ("Studio di ingegneria Monticone Ing. Marcello", "Professionista singolo",
     "Via Adda 18", "San Donato Milanese", "02 36736620 (da elenchi; altri numeri discordanti)", "monticone.eu",
     "Progettazione e direzione lavori di impianti elettrici ed elettronici (rilevazione incendi, cablaggio strutturato), "
     "sicurezza sul lavoro e valutazione dei rischi.",
     PRIVATO, 1,
     "Il più vicino al tuo profilo (impianti elettrici/elettronici) e a casa tua. Verifica sul sito."),
    ("Barci Engineering S.p.A.", "Società di ingegneria",
     "Via Tolstoj 86", "San Giuliano Milanese", "", "barci.it",
     "Progettazione di impianti elettrici e meccanici, condotte (pipeline), telecontrollo, infrastrutture civili, "
     "collaudi e perizie, protezioni elettriche, efficienza energetica. Qualifiche con Eni ed Enel Rete Gas.",
     "Fatturato 2025 circa 18,1 M€, utile circa 2,9 M€ (ReportAziende); altra fonte: 14,4 M€ nel 2024. "
     "Dipendenti stimati 100–249 (altre fonti fino a 500). P.IVA 02444790782.", 2,
     "Sede legale a Montalto Uffugo (CS); un elenco la dà con sede a San Giuliano. Grande e strutturata: più "
     "difficile da avvicinare, ma strategica (settore energia). Contatto via LinkedIn o centralino."),
    ("DEAL Progetti S.r.l.", "Società di ingegneria (microimpresa)",
     "Via Mameli 2", "Milano", "02 783664 (da elenchi)", "",
     "Progettazione edile, di impianti e urbana; coordinamento della sicurezza e direzione lavori (ATECO 71.12.10). "
     "Pagine Bianche la associa all'Ing. Antonio De Marco.",
     "Fatturato 2024 circa 213.302 € con utile di 4.078 €; 1 dipendente. Le fonti divergono (2021: 144.543 €). "
     "Costituita il 30/05/2019. P.IVA 10835040964.", 2,
     "Società piccola; chiedi consigli all'ingegnere titolare."),
    ("Studiora - Studio Ingegneria", "Studio di ingegneria",
     "Via Emilia 24", "San Donato Milanese (negli elenchi; tu avevi indicato San Giuliano)", "393 0000868 (da elenco)", "",
     "Non chiaro: gli elenchi lo classificano solo come studio di ingegneria. Compare anche nell'elenco di Opera.",
     "Non trovati", 2,
     "Verifica l'indirizzo e la specialità con una telefonata."),
    ("Studio di ingegneria Lommano (indicato come 'Lomanno')", "Ditta individuale",
     "Via Triulziana 38", "San Donato Milanese", "02 7000 2422 (da elenchi)", "",
     "Ingegneria civile: prevenzione incendi, ingegneria della sicurezza antincendio, audit HSE. Titolare: Massimo Lommano, "
     "libero professionista (tecnico antincendio). Attivo dal 2000. Cerca personale per la prevenzione incendi (LinkedIn).",
     PRIVATO, 3, "Specialità lontana da elettronica/RF, ma utile come conoscenza del territorio."),
    ("Studio Tecnico Parodi (Ing. Furio Parodi)", "Professionista singolo",
     "Via/Viale della Libertà 68 (le fonti divergono sul nome della via)", "San Donato Milanese", "339 6439555 (da elenchi)",
     "studio-parodi.it",
     "Progettazione e direzione lavori per ristrutturazioni (CILA, SCIA, permessi), pratiche per i bonus fiscali, "
     "prevenzione incendi, catasto, certificazioni energetiche, perizie. Attivo dal 2010.",
     PRIVATO, 3, "Specialità edilizia residenziale: meno rilevante per te."),
    ("Studio Lamanna Simone", "Probabile geometra (le fonti discordano: 'Ing.' o 'Geometra')",
     "Via Molise 9 (coworking), Sesto Ulteriano", "San Giuliano Milanese", "", "geomlamannasimone.it",
     "Libero professionista: pratiche comunali, certificazioni energetiche, pratiche catastali. Sede legale in un "
     "coworking di Via Molise 9.",
     PRIVATO, 3, "Il sito è intestato a 'Geometra Lamanna Simone': verifica il titolo sull'albo prima di contattarlo come ingegnere."),
    ("Andrea Carlo Rota", "Da verificare",
     "Via Astolfo 7", "Milano", "", "",
     "Non trovato: nessun riscontro per questo nome. 'Carlo Rota' (CRC Engineering, zona Como) e Studio Rota Srl "
     "(Bergamo) sono persone/società diverse.",
     "Non trovati", 3, "Controlla sull'Albo dell'Ordine degli Ingegneri di Milano o su Pagine Gialle."),
]

FONTI = {
    "Studio di ingegneria Monticone Ing. Marcello": [
        "https://aziende.virgilio.it/ingegneria/san-donato-milanese-mi/studio-ingegneria-monticone-ing-marcello",
        "https://www.misterimprese.it/lombardia/milano/san-donato-milanese/ingegneri-studi/2576926.html"],
    "Barci Engineering S.p.A.": [
        "https://barci.it/", "https://barci.it/qualifiche/",
        "https://www.reportaziende.it/barci_engineering_spa_cs_02444790782",
        "https://www.aziende.it/barci-engineering-societa-a-responsabilita"],
    "DEAL Progetti S.r.l.": [
        "https://atoka.io/public/it/azienda/deal-progetti-srl/0eb9c851cbc5",
        "https://www.fatturatoitalia.it/deal-progetti-srl-10835040964",
        "https://www.paginebianche.it/scheda/milano/de-marco-ing-antonio-deal-progetti.362945"],
    "Studiora - Studio Ingegneria": [
        "https://www.reteimprese.it/ingegneri/san-donato-milanese", "https://www.reteimprese.it/ingegneri/opera"],
    "Studio di ingegneria Lommano": [
        "https://trova-aperto.it/san-donato-milanese/studio-di-ingegneria-lommano-2187902",
        "https://it.linkedin.com/company/studio-di-ingegneria-lommano",
        "https://firmania.it/san-donato-milanese/studio-di-ingegneria-lommano-4110959"],
    "Studio Tecnico Parodi": [
        "https://www.studio-parodi.it/", "https://www.studio-parodi.it/certificazione-energetica-ape-milano/"],
    "Studio Lamanna Simone": [
        "http://www.geomlamannasimone.it/contatti", "https://www.facebook.com/inglamanna/"],
    "Andrea Carlo Rota": [],
}

COLS = [  # titolo, larghezza
    ("N", 5), ("Nome", 32), ("Tipo", 24), ("Indirizzo", 30), ("Comune", 24), ("Telefono (da elenchi)", 24),
    ("Sito", 20), ("Cosa fa", 52), ("Dati economici", 44), ("Priorità suggerita (1-3)", 14),
    ("Note di verifica", 40), ("Contattato il", 14), ("Esito", 18), ("Note, consigli ricevuti, nomi suggeriti", 50),
]

ESITI = ["Da contattare", "Contattato", "Appuntamento fissato", "Incontrato", "Nessuna risposta", "Non interessato"]

wb = Workbook()

# ============================================================ STUDI
ws = wb.active
ws.title = "Studi"

ws["A1"] = "Studi di ingegneria in zona — lista di contatto"
ws["A1"].font = H1
ws["A2"] = ("Obiettivo: parlare con colleghi della zona per capire quali aziende hanno problemi tecnici o "
            "documentali e se servono collaboratori esterni. Le colonne in blu vanno compilate a mano. "
            "Dati raccolti da elenchi pubblici (28/10/2026): possono essere vecchi o discordanti, quindi "
            "vanno confermati con una telefonata. Priorità = affinità con il tuo profilo (elettrico/elettronico, "
            "industria), non qualità dello studio. Il fatturato degli studi individuali non è pubblico.")
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

for i, (nome, tipo, ind, comune, tel, sito, cosa, eco, prio, note) in enumerate(STUDI, start=1):
    r = HR + i
    vals = [i, nome, tipo, ind, comune, tel, sito, cosa, eco, prio, note, None, "Da contattare", None]
    for c, v in enumerate(vals, start=1):
        cell = ws.cell(row=r, column=c, value=v if v != "" else None)
        cell.alignment = WRAP
        cell.border = THIN
        cell.font = BLUE if c in (12, 13, 14) else BLACK
    ws.cell(row=r, column=1).font = GREY
    ws.cell(row=r, column=12).number_format = "dd/mm/yyyy"
    ws.row_dimensions[r].height = 92

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

# ============================================================ FONTI
wf = wb.create_sheet("Fonti")
wf.column_dimensions["A"].width = 48
wf.column_dimensions["B"].width = 110
wf["A1"] = "Fonti consultate (28/10/2026)"
wf["A1"].font = H1
r = 3
for nome, urls in FONTI.items():
    wf.cell(row=r, column=1, value=nome).font = LBL
    if not urls:
        wf.cell(row=r, column=2, value="Nessuna fonte pertinente trovata").font = GREY
        r += 1
    for u in urls:
        c = wf.cell(row=r, column=2, value=u)
        c.hyperlink = u
        c.font = LINK
        r += 1
    r += 1

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
