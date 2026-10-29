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

# lista lunga: nicchia, cliente tipo, tipo di segnale, fonte del segnale, note (stato di verifica, date)
V  = "Segnale verificato in ricerca (stampa di settore)."
IP = "Solo ipotesi nostra: domanda non verificata."
DV = "Segnale da verificare: non cercato."
CANDIDATE = [
    # ---- obblighi di legge con scadenza
    ("NIS2: preparazione alla conformità per PMI fornitrici di soggetti critici",
     "PMI in filiere critiche; consulenti e MSP come canale", "Obbligo di legge", "Noze; Agenda Digitale",
     V + " Notifica incidenti operativa dal 15/01/2026; misure di base con scadenze da ottobre 2026 per chi ha ricevuto la comunicazione ad aprile 2025. Mercato affollato di consulenti. Numero di imprese coinvolte non trovato."),
    ("NIS2 per MSP e consulenti: piattaforma multi-cliente per gestire la conformità di più aziende",
     "MSP, studi di consulenza IT", "Obbligo di legge", "Noze; Agenda Digitale",
     V + " Variante della precedente: vendi al canale, non alla PMI finale. Da confrontare con piattaforme esistenti."),
    ("Cyber Resilience Act: gestione segnalazione vulnerabilità e fascicolo tecnico per produttori",
     "Produttori di prodotti con elementi digitali (elettronica, IoT, macchine con software)", "Obbligo di legge",
     "Agenda Digitale; IPSOA",
     V + " Obbligo di segnalazione dall'11/09/2026 (preallarme in 24 ore); piena applicazione 11/12/2027; sanzioni fino a 15 M€ (stampa). Vantaggio tuo: medio-alto."),
    ("Direttiva RED (cybersicurezza): assistente alla conformità EN 18031 per produttori di apparecchi radio/IoT",
     "Produttori e importatori di apparecchi radio e dispositivi connessi", "Obbligo di legge", "TÜV SÜD; Yarix",
     V + " Applicabile dal 01/08/2025. Stato di armonizzazione degli standard discordante tra le fonti. Vantaggio tuo: alto (RF)."),
    ("Regolamento Macchine 2023/1230: generatore di fascicolo tecnico e dichiarazione UE",
     "Costruttori di macchine (Lombardia è un polo)", "Obbligo di legge", "Certifico; UCIMU",
     V + " Applicazione dal 20/01/2027; UCIMU chiede una proroga condizionata. Dettagli sulla documentazione tecnica non verificati."),
    ("AI Act: inventario dei sistemi di IA e conformità agli obblighi di trasparenza (art. 50)",
     "PMI che usano o forniscono sistemi di IA", "Obbligo di legge", "Agenda Digitale; Noze",
     V + " Trasparenza dal 02/08/2026; alto rischio rinviato a dicembre 2027 / agosto 2028 (accordo provvisorio del 07/05/2026, da verificare in Gazzetta UE). Domanda specifica debole."),
    ("Trasparenza retributiva: annunci e report sul divario di genere",
     "Aziende con 100+ dipendenti, uffici HR", "Obbligo di legge", "QuiFinanza; PartitaIVA.it",
     V + " Stato del decreto di recepimento discordante tra le fonti (D.Lgs. 96/2026?). Report annuale dal 07/06/2027 per 250+ dipendenti. Il target è piccolo: poche aziende con 100+ dipendenti."),
    ("PPWR imballaggi: gestione dati e dichiarazioni di conformità",
     "Produttori e utilizzatori di imballaggi (Lombardia ha molti)", "Obbligo di legge", "Assolombarda",
     V + " Applicabile dal 12/08/2026; date di etichettatura discordanti (2026, 2027, 2028). Assolombarda ha attivato un desk dedicato."),
    ("Passaporto digitale di prodotto: raccolta dati per batterie e tessile",
     "Produttori di batterie e tessile", "Obbligo di legge", "Bluestone PIM; PMI.it",
     V + " Batterie dal 18/02/2027; tessile non ancora definito. Dominato da grandi fornitori e dagli atti delegati."),
    ("Accessibilità digitale (EAA): audit e correzione per e-commerce",
     "E-commerce italiani", "Obbligo di legge", "Agenda Digitale; Iubenda",
     V + " Obbligo dal 28/06/2025; piattaforma di segnalazione AgID dal 11/03/2026; sanzioni da verificare (nessun procedimento pubblico trovato a giugno 2026). Molti fornitori."),
    # ---- incentivi / fondi
    ("Iperammortamento 2026: pratica per perizia asseverata, certificazione e comunicazioni al GSE",
     "Studi di ingegneria che firmano perizie; imprese manifatturiere", "Incentivi / fondi",
     "Agenda Digitale; Pasquale Pillitteri",
     V + " Piattaforma GSE dal 12/06/2026; comunicazione di completamento entro 15/11/2028. La perizia è di un ingegnere iscritto all'albo: collegato agli studi che stai contattando. Regole (soglie, SaaS) discordanti tra le fonti."),
    ("Fibra ottica: report di collaudo e documentazione per imprese di posa",
     "Imprese di posa fibra e installatori", "Incentivi / fondi", "Domani",
     V + " Piano Italia 1 Giga in ritardo: 250–700 mila civici potrebbero uscire dal Piano. Committenti con portali propri; strumenti degli OTDR con report già inclusi."),
    ("Comunità energetiche: piattaforma di gestione per CER, condomini e comuni",
     "Promotori di CER, amministratori di condominio, comuni", "Incentivi / fondi", "InfoBuild Energia",
     V + " Obiettivo di 15.000 CER a giugno 2026 probabilmente mancato; regole ancora instabili."),
    ("Diagnosi energetica obbligatoria: strumento per redigere e gestire le diagnosi",
     "Studi di ingegneria, ESCO, grandi imprese ed energivori", "Incentivi / fondi", "da cercare",
     DV + " Obbligo ricorrente (ogni 4 anni per le imprese soggette). Da verificare sulle norme e sul mercato."),
    # ---- telecom / reti
    ("FWA: pianificazione e monitoraggio per piccoli operatori wireless",
     "Piccoli provider FWA/WISP", "Altro", "Segugio (dati AGCOM)",
     V + " Oltre 2,7 milioni di linee FWA, +13% in un anno; frequenze 26 GHz in assegnazione. Nessun dato recente sul numero di piccoli provider."),
    ("Audit e ottimizzazione dei costi telecom per PMI",
     "PMI con molte linee e contratti", "Altro", "da cercare",
     IP + " Vantaggio tuo alto; modello a risparmio condiviso. Da verificare quanto si risparmia davvero."),
    # ---- verticali acquisite dai grandi gruppi
    ("Pianificazione turni e presenze per magazzini, logistica e conto terzi",
     "Logistica, confezionamento conto terzi, magazzini", "Acquisizioni di verticali", "Aventis Advisors (Zucchetti)",
     "Zucchetti ha acquisito la maggioranza di AWMS (personale per fabbriche e logistica): segnale che il verticale vale. In zona: 6 imprese di conto terzi nell'elenco. Software di turni già presenti."),
    ("Gestione commesse e avanzamento lavori per piccole imprese edili e impiantisti",
     "Imprese edili, impiantisti", "Acquisizioni di verticali", "Aventis Advisors (TeamSystem)",
     "TeamSystem ha fatto 7 acquisizioni nel comparto industria/costruzioni/real estate: segnale di valore del verticale. Mercato presidiato da gruppi grandi."),
    ("Scadenzario obblighi di sicurezza sul lavoro (formazione, visite, DPI) per PMI",
     "PMI manifatturiere e di servizi", "Acquisizioni di verticali", "Aventis Advisors (TeamSystem: legal, compliance, sicurezza)",
     "5 acquisizioni TeamSystem in legal/compliance/sicurezza. Prodotti già esistenti; da mappare i concorrenti."),
    # ---- idee nostre, domanda da verificare
    ("Report di collaudo automatici da dati di misura per laboratori e officine",
     "Laboratori di prova, officine di precisione, assemblatori", "Altro", "idea precedente",
     IP + " Gli strumenti hanno già software di report. Vantaggio tuo: alto."),
    ("Scadenzario tarature degli strumenti di misura (ISO 9001)",
     "Officine, laboratori, PMI certificate", "Altro", "idea precedente", IP),
    ("Preventivatore con codici articolo per distributori tecnici",
     "Distributori di bulloneria, acciai, plastiche, macchine utensili", "Altro", "idea precedente",
     IP + " Probabile presenza di gestionali; da verificare."),
    ("Estrazione dati da ordini, DDT e preventivi in PDF per il back-office",
     "PMI con ufficio ordini", "Annunci di lavoro", "da cercare",
     DV + " Da cercare tra gli annunci per ruoli ripetitivi (ufficio ordini, data entry)."),
    ("Assistente a documentazione tecnica per l'assistenza post-vendita dei costruttori di macchine",
     "Costruttori di macchine", "Altro", "idea Gemini", IP),
    ("Automazione di relazioni, perizie e pratiche per studi tecnici",
     "Studi di ingegneria e professionisti", "Altro", "studi contattati",
     IP + " Gli studi (DEAL, Parodi, Lommano) fanno pratiche antincendio, certificazioni energetiche, perizie."),
    ("Gestione dei file di misura RF e ottici per R&D e produzione",
     "Laboratori R&D e produzione elettronica", "Altro", "tuo campo", IP + " Vantaggio tuo: alto."),
    ("Schede di sicurezza e conformità CLP/REACH per chimica e gomma-plastica",
     "Aziende chimiche e della gomma-plastica", "Altro", "segmenti B2B (non verificati)", DV),
    ("Documentazione elettronica di lotto (batch record) per piccole aziende farmaceutiche/CDMO",
     "Piccole aziende farmaceutiche e CDMO", "Altro", "segmenti B2B (non verificati)",
     DV + " Barriera regolatoria alta (GMP)."),
    ("Formazione e simulazioni di phishing per PMI (obblighi di formazione NIS2)",
     "PMI", "Obbligo di legge", "Noze; Agenda Digitale", V + " Mercato affollato e a basso prezzo."),
    ("Manutenzione predittiva a basso costo per macchine di PMI manifatturiere",
     "PMI manifatturiere", "Altro", "idea nostra", IP + " Concorrenza forte (grandi fornitori)."),
    ("Gestione documentale per sicurezza prodotti (GPSR) di importatori e venditori online",
     "Importatori e e-commerce di prodotti per consumatori", "Obbligo di legge", "da cercare", DV),
]

FONTI_URL = {
    "NIS2": ["https://www.noze.it/insights/nis2-pmi-cyberagent/",
             "https://www.agendadigitale.eu/sicurezza/nis2-scadenze-2026-la-guida-per-le-piccole-imprese/"],
    "AI Act": ["https://www.agendadigitale.eu/industry-4-0/digital-omnibus-e-ai-act-cosa-puo-slittare-e-cosa-va-fatto-prima-di-agosto-2026/",
               "https://www.noze.it/insights/ai-act-digital-omnibus-2026/"],
    "Cyber Resilience Act": ["https://www.agendadigitale.eu/sicurezza/cyber-resilience-act-la-scadenza-chiave-arriva-l11-settembre-2026/",
                             "https://www.ipsoa.it/documents/quotidiano/2026/09/02/cyber-resilience-act-11-settembre-2026-scatta-obbligo-segnalare-vulnerabilita-incidenti-gravi"],
    "Direttiva RED": ["https://www.tuvsud.com/en-us/services/product-certification/red-cybersecurity-requirements",
                      "https://www.yarix.com/Advisory-and-Consulting-Services/RED-Compliance"],
    "Regolamento Macchine": ["https://certifico.com/macchine/regolamento-ue-2023-1230",
                             "https://www.ilsussidiario.net/news/regolamento-macchine-ue-rosa-ucimu-mancano-criteri-comuni-e-chiari-serve-una-proroga/2986256/amp/"],
    "Trasparenza retributiva": ["https://quifinanza.it/lavoro/trasparenza-salariale-7-giugno-2026/960990/",
                                "https://www.partitaiva.it/trasparenza-salariale/"],
    "PPWR": ["https://www.assolombarda.it/servizi/ambiente/informazioni/ppwr-dal-12-agosto-in-applicazione-il-nuovo-regolamento-ue-sugli-imballaggi"],
    "Passaporto digitale di prodotto": ["https://www.bluestonepim.com/blog/digital-product-passport-for-batteries",
                                        "https://www.pmi.it/tecnologia/prodotti-e-servizi-ict/492107/passaporto-digitale-prodotto.html"],
    "Accessibilità (EAA)": ["https://www.agendadigitale.eu/mercati-digitali/ecommerce/siti-ecommerce-accessibili-guida-in-5-step-per-evitare-sanzioni/",
                            "https://www.iubenda.com/it/help/178476-accessibilita-101/"],
    "Iperammortamento 2026": ["https://www.agendadigitale.eu/industry-4-0/iperammortamento-2026-la-guida-cose-e-come-fare-le-comunicazioni-al-gse/",
                              "https://pasqualepillitteri.it/perizia-iperammortamento"],
    "Acquisizioni TeamSystem / Zucchetti": ["https://aventis-advisors.com/teamsystem-acquisitions/"],
    "Piano Italia 1 Giga": ["https://www.editorialedomani.it/economia/banda-ultralarga-cantieri-obiettivi-pnrr-ritardi-regioni-oqbs3i02",
                            "https://tariffe.segugio.it/news-tariffe/italia-1-giga-nuovi-ritardi-per-la-banda-ultra-larga-cosa-sta-succedendo-00043657.aspx"],
    "FWA e frequenze 26 GHz": ["https://tariffe.segugio.it/news-tariffe/internet-senza-fibra-la-fwa-supera-2-7-milioni-di-linee-00047779.aspx",
                               "https://www.smartworld.it/news/frequenze-5g-26-ghz-gara-italia-agosto-2026.html"],
    "Comunità energetiche (CER)": ["https://www.infobuildenergia.it/approfondimenti/cer-comunita-energetiche-in-italia/"],
}

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
wl["A2"] = ("Una riga per nicchia (lista lunga, Fase 1). Il segnale è solo il punto di partenza: la colonna Note dice "
            "se è stato verificato in ricerca (stampa di settore, non fonti ufficiali) o se è solo un'ipotesi. In blu le celle da "
            "compilare nelle fasi 2-3: stima di aziende target e di prezzo (con fonte) e punteggi 1-5. "
            "'Clienti per 1 M€' e 'Punteggio' si calcolano da soli.")
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
NROWS = 70
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
        vals.update({2: cand[0], 3: cand[1], 4: cand[2], 5: cand[3], TOT + 2: cand[4]})
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
        wl.row_dimensions[r].height = 92
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

wf = wb.create_sheet("Fonti")
wf.column_dimensions["A"].width = 38
wf.column_dimensions["B"].width = 120
wf["A1"] = "Fonti dei segnali (consultate il 03/11/2026)"
wf["A1"].font = H1
wf["A2"] = "Quasi tutte sono stampa di settore e blog di consulenza, non testi ufficiali: le date vanno confermate sulla fonte primaria."
wf["A2"].font = NOTE
fr = 4
LINK = Font(name=ARIAL, size=10, color="0563C1", underline="single")
for nome, urls in FONTI_URL.items():
    wf.cell(row=fr, column=1, value=nome).font = BOLD
    for u in urls:
        c = wf.cell(row=fr, column=2, value=u)
        c.hyperlink = u
        c.font = LINK
        fr += 1
    fr += 1

wb.save(OUT)
print("salvato:", OUT)
