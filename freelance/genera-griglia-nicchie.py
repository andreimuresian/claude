# -*- coding: utf-8 -*-
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

OUT = "/home/user/claude/freelance/griglia-nicchie.xlsx"

ARIAL   = "Arial"
BLUE    = Font(name=ARIAL, size=11, color="0000FF")           # celle da compilare
BLACK   = Font(name=ARIAL, size=11)
GREY    = Font(name=ARIAL, size=11, color="7C8A91")
BOLD    = Font(name=ARIAL, size=11, bold=True)
H1      = Font(name=ARIAL, size=15, bold=True, color="141C22")
H2      = Font(name=ARIAL, size=11, bold=True, color="FFFFFF")
NOTE    = Font(name=ARIAL, size=10, color="4A565E", italic=True)
HEADFIL = PatternFill("solid", fgColor="0E6E5E")
WARNFIL = PatternFill("solid", fgColor="FFF2CC")
THIN    = Border(bottom=Side(style="thin", color="D3D0C7"))
WRAP    = Alignment(wrap_text=True, vertical="top")

# criterio, descrizione, peso, come si valuta (1 = peggio, 5 = meglio)
CRITERI = [
    ("Bisogno urgente / obbligo", "C'è una scadenza di legge o un costo evidente che spinge ad agire ora?",
     20, "1 = nice-to-have; 5 = obbligo di legge o costo alto e documentato"),
    ("Budget del cliente", "I clienti tipo hanno ricavi >1 M€ e capacità di spesa?",
     20, "1 = micro-imprese; 5 = PMI con >1 M€ di ricavi e abitudine a pagare software"),
    ("Ricavi ricorrenti", "Il cliente paga ogni anno o ogni mese?",
     10, "1 = una tantum; 5 = abbonamento naturale"),
    ("Scalabilità", "Quanto costa servire un cliente in più? Margine?",
     15, "1 = molto lavoro per cliente; 5 = costo marginale quasi zero"),
    ("Canale di vendita", "Sai dove trovare i clienti e come raggiungerli?",
     10, "1 = nessun canale chiaro; 5 = canale noto (associazioni, rivenditori, consulenti)"),
    ("Concorrenza (5 = poca)", "Quanti concorrenti e quanto forti?",
     10, "1 = mercato saturo; 5 = pochi o nessuno ben posizionato"),
    ("Vantaggio tuo", "Capisci il problema meglio di chi lo risolve oggi?",
     10, "1 = nessun vantaggio; 5 = lo conosci dall'interno"),
    ("Testabile a poco prezzo", "Puoi verificare la domanda con un prototipo e conversazioni, senza spendere?",
     5, "1 = serve capitale; 5 = test in 2 settimane a costo zero"),
]

TIPI_SEGNALE = ["Obbligo di legge", "Incentivi / fondi", "Annunci di lavoro", "Recensioni negative",
                "Acquisizioni di verticali", "Forum / community", "Altro"]
STATI = ["Da studiare", "In studio", "Da intervistare", "Intervistata", "Scartata", "Scelta"]

# segmenti B2B: nome, quota stimata (dall'altro chatbot), n. indicativo
SEGMENTI = [
    ("Manifattura avanzata e meccanica", "26–28%", "11.000–11.500"),
    ("Commercio all'ingrosso B2B", "20–22%", "8.500–9.000"),
    ("Servizi corporate, ICT e software", "12–14%", "5.000–5.800"),
    ("Costruzioni, impiantistica, real estate B2B", "10–12%", "4.200–4.800"),
    ("Chimica, polimeri, gomma-plastica", "7–8%", "3.000–3.300"),
    ("Logistica, spedizioni e trasporti B2B", "6–7%", "2.500–2.900"),
    ("Farmaceutica, biotech, dispositivi medici", "4–5%", "1.600–2.000"),
    ("Energia, ambiente, utilities B2B", "3–4%", "1.300–1.600"),
    ("Telecomunicazioni e reti", "1,5–2%", "600–800"),
]

# candidate iniziali: nicchia, cliente, tipo segnale, fonte, prezzo annuo stimato
CANDIDATE = [
    ("A. Strumenti per la filiera della fibra (report di collaudo, documentazione)",
     "Imprese di posa fibra e installatori", "Incentivi / fondi",
     "Piano Italia 1 Giga in ritardo (Domani, Segugio)", None),
    ("B. Preparazione alla NIS2 per PMI fornitrici di soggetti critici",
     "PMI in filiere critiche; consulenti e MSP come canale", "Obbligo di legge",
     "Scadenze ACN 2026 (Noze, Agenda Digitale)", None),
    ("C. Strumenti di pianificazione e monitoraggio per piccoli operatori FWA",
     "Piccoli provider wireless", "Altro",
     "FWA >2,7 M di linee (AGCOM via Segugio)", None),
]

wb = Workbook()

# ============================================================ CRITERI
wc = wb.active
wc.title = "Criteri"
wc["A1"] = "Criteri di valutazione delle nicchie"
wc["A1"].font = H1
wc["A2"] = ("I pesi (in blu) sono una proposta: cambiali e i punteggi della Lista lunga si ricalcolano. "
            "Ogni nicchia riceve da 1 a 5 su ogni criterio.")
wc["A2"].font = NOTE
wc["A2"].alignment = WRAP
wc.merge_cells("A2:D2")
wc.row_dimensions[2].height = 30

heads = ["Criterio", "Domanda", "Peso", "Come si valuta (1 = peggio, 5 = meglio)"]
widths = [30, 60, 8, 70]
for c, (t, w) in enumerate(zip(heads, widths), start=1):
    cell = wc.cell(row=4, column=c, value=t)
    cell.font, cell.fill = H2, HEADFIL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    wc.column_dimensions[get_column_letter(c)].width = w
for i, (nome, dom, peso, come) in enumerate(CRITERI, start=1):
    r = 4 + i
    for c, v in enumerate([nome, dom, peso, come], start=1):
        cell = wc.cell(row=r, column=c, value=v)
        cell.alignment = WRAP
        cell.border = THIN
        cell.font = BLUE if c == 3 else (BOLD if c == 1 else BLACK)
    wc.row_dimensions[r].height = 34
LASTC = 4 + len(CRITERI)
wc.cell(row=LASTC + 1, column=2, value="Somma dei pesi").font = BOLD
wc.cell(row=LASTC + 1, column=3, value="=SUM(C5:C{})".format(LASTC)).font = BOLD

# ============================================================ LISTA LUNGA
wl = wb.create_sheet("Lista lunga")
wl["A1"] = "Lista lunga delle nicchie"
wl["A1"].font = H1
wl["A2"] = ("Una riga per nicchia. In blu le celle da compilare: stima di aziende target e di prezzo (con fonte), "
            "punteggi 1-5. 'Clienti per 1 M€' e 'Punteggio' si calcolano da soli. Le candidate A-C sono ipotesi "
            "iniziali, non ancora valutate: dati di mercato non verificati.")
wl["A2"].font = NOTE
wl["A2"].alignment = WRAP
wl.merge_cells("A2:V2")
wl.row_dimensions[2].height = 34

BASE = ["N", "Nicchia", "Cliente tipo", "Tipo di segnale", "Fonte del segnale", "Aziende target (stima)",
        "Fonte della stima", "Prezzo annuo per cliente (€)", "Clienti per 1 M€ di ricavi", "Concorrenti noti"]
SC0 = len(BASE) + 1                      # prima colonna dei punteggi
HEAD = BASE + [c[0] for c in CRITERI] + ["Punteggio ponderato (1-5)", "Stato", "Note"]
wl_widths = [5, 44, 30, 20, 34, 14, 26, 14, 14, 26] + [11] * len(CRITERI) + [14, 16, 40]

WR = 4   # riga dei pesi
wl.cell(row=WR, column=SC0 - 1, value="Peso →").font = BOLD
for k in range(len(CRITERI)):
    cell = wl.cell(row=WR, column=SC0 + k, value="=Criteri!C{}".format(5 + k))
    cell.font = GREY
HR = 5
for c, (t, w) in enumerate(zip(HEAD, wl_widths), start=1):
    cell = wl.cell(row=HR, column=c, value=t)
    cell.font, cell.fill = H2, HEADFIL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    wl.column_dimensions[get_column_letter(c)].width = w
wl.row_dimensions[HR].height = 48

SA = get_column_letter(SC0)
SZ = get_column_letter(SC0 + len(CRITERI) - 1)
TOT = SC0 + len(CRITERI)
NROWS = 60
dv_tipo = DataValidation(type="list", formula1='"' + ",".join(TIPI_SEGNALE) + '"', allow_blank=True)
dv_stato = DataValidation(type="list", formula1='"' + ",".join(STATI) + '"', allow_blank=True)
dv_pt = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True)
wl.add_data_validation(dv_tipo)
wl.add_data_validation(dv_stato)
wl.add_data_validation(dv_pt)
for i in range(1, NROWS + 1):
    r = HR + i
    cand = CANDIDATE[i - 1] if i <= len(CANDIDATE) else None
    vals = {1: i}
    if cand:
        vals.update({2: cand[0], 3: cand[1], 4: cand[2], 5: cand[3]})
    for c in range(1, len(HEAD) + 1):
        cell = wl.cell(row=r, column=c, value=vals.get(c))
        cell.border = THIN
        cell.alignment = WRAP
        cell.font = GREY if c == 1 else BLUE
    wl.cell(row=r, column=9, value='=IF(H{0}>0,ROUND(1000000/H{0},0),"")'.format(r)).font = BLACK
    wl.cell(row=r, column=TOT,
            value='=IF(COUNT({a}{r}:{z}{r})=0,"",ROUND(SUMPRODUCT({a}{r}:{z}{r},{a}${w}:{z}${w})/SUM({a}${w}:{z}${w}),2))'
            .format(a=SA, z=SZ, r=r, w=WR)).font = BOLD
    wl.cell(row=r, column=TOT + 1, value="Da studiare" if cand else None).font = BLUE
    wl.cell(row=r, column=6).number_format = "#,##0"
    wl.cell(row=r, column=8).number_format = "#,##0"
    wl.cell(row=r, column=9).number_format = "#,##0"
    if cand:
        wl.row_dimensions[r].height = 46
dv_tipo.add("D{}:D{}".format(HR + 1, HR + NROWS))
dv_stato.add("{}{}:{}{}".format(get_column_letter(TOT + 1), HR + 1, get_column_letter(TOT + 1), HR + NROWS))
dv_pt.add("{}{}:{}{}".format(SA, HR + 1, SZ, HR + NROWS))
wl.freeze_panes = wl.cell(row=HR + 1, column=3)
wl.auto_filter.ref = "A{}:{}{}".format(HR, get_column_letter(len(HEAD)), HR + NROWS)

# ============================================================ SEGMENTI B2B
wsg = wb.create_sheet("Segmenti B2B")
wsg["A1"] = "Segmenti B2B lombardi con ricavi sopra 1 M€ — DATI NON VERIFICATI"
wsg["A1"].font = H1
wsg["A2"] = ("Stime fornite da un altro chatbot, senza fonte. Servono come ipotesi di lavoro per scegliere "
             "dove guardare. Da confermare con i dati Istat (unità locali per ATECO e classe di addetti) e della "
             "Camera di Commercio prima di usarle in qualsiasi decisione.")
wsg["A2"].font = NOTE
wsg["A2"].alignment = WRAP
wsg.merge_cells("A2:E2")
wsg.row_dimensions[2].height = 44
for c, (t, w) in enumerate(zip(["Segmento", "Quota stimata", "Aziende (stima)", "Verificato?", "Fonte verificata"],
                               [46, 16, 18, 14, 50]), start=1):
    cell = wsg.cell(row=4, column=c, value=t)
    cell.font, cell.fill = H2, HEADFIL
    wsg.column_dimensions[get_column_letter(c)].width = w
for i, (nome, quota, n) in enumerate(SEGMENTI, start=1):
    r = 4 + i
    for c, v in enumerate([nome, quota, n, "No", None], start=1):
        cell = wsg.cell(row=r, column=c, value=v)
        cell.border = THIN
        cell.font = BLUE if c in (4, 5) else BLACK
        if c in (2, 3, 4):
            cell.fill = WARNFIL

r0 = 4 + len(SEGMENTI) + 2
wsg.cell(row=r0, column=1, value="Altre cifre da verificare").font = BOLD
ALTRE = [
    "Quota di aziende lombarde con ricavi >1 M€ per forma giuridica: ditte individuali <0,5%, società di persone ~17%, società di capitali ~34% (fornite da te, senza fonte).",
    "B2B contro B2C: ~11-12% delle imprese B2B sopra 1 M€ contro ~2% delle B2C (altro chatbot, senza fonte). La direzione è plausibile, il rapporto 5-6x no.",
    "Ripartizione B2B/B2C per forma giuridica: individuali 65/35, persone 55/45, capitali 60/40 (tue stime).",
]
for i, t in enumerate(ALTRE, start=1):
    c = wsg.cell(row=r0 + i, column=1, value=t)
    c.font, c.alignment = BLACK, WRAP
    wsg.merge_cells(start_row=r0 + i, start_column=1, end_row=r0 + i, end_column=5)
    wsg.row_dimensions[r0 + i].height = 32

wb.save(OUT)
print("salvato:", OUT)
