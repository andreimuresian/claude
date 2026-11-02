# Genera fase4-interviste.xlsx: lista contatti, copione e griglia di decisione per le interviste della Fase 4.
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fase4-interviste.xlsx")
F = "Arial"
H1 = Font(name=F, size=14, bold=True); H2 = Font(name=F, size=10, bold=True, color="FFFFFF")
B = Font(name=F, size=10, bold=True); N = Font(name=F, size=10); BL = Font(name=F, size=10, color="0000FF")
NOTE = Font(name=F, size=10, italic=True, color="555555")
HF = PatternFill("solid", fgColor="1F3864"); W = Alignment(wrap_text=True, vertical="top")
T = Side(style="thin", color="BBBBBB"); TH = Border(left=T, right=T, top=T, bottom=T)

def head(ws, row, titles, widths):
    for c, (t, w) in enumerate(zip(titles, widths), start=1):
        x = ws.cell(row=row, column=c, value=t); x.font, x.fill = H2, HF
        x.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(c)].width = w

wb = Workbook()

# ---------------- Contatti
ws = wb.active; ws.title = "Contatti"
ws["A1"] = "Fase 4 — contatti entro 20 km da San Donato Milanese (verificati su aggregatori di dati camerali)"; ws["A1"].font = H1
ws["A2"] = ("Verifica del 02/11/2026 su ufficiocamerale.it, aziende.it, reportaziende.it, registroaziende.it, atoka.io e informazione-aziende.it. "
            "Sono aggregatori commerciali, non il Registro Imprese: le cifre variano da una fonte all'altra, quindi sono ordini di grandezza. "
            "A: aziende ATTIVE con circa 10 o più addetti. B: piccole attive (2-7 addetti): le chiami per capire il lavoro, di solito risponde il titolare. C: scartate (liquidazione o cessate). D: NON verificate. "
            "Con 6 + 6 contatti verificati la lista è ancora corta: serve cercare altre aziende.")
ws["A2"].font, ws["A2"].alignment = NOTE, W; ws.merge_cells("A2:K2"); ws.row_dimensions[2].height = 64
cols = ["#", "Segmento", "Azienda", "Comune", "Cosa fa (da dati camerali)", "Stato", "Addetti (stima)", "Fatturato 2024", "Esito", "Fonte", "Chi ha risposto / chi decide?"]
head(ws, 4, cols, [4, 24, 34, 18, 40, 14, 12, 14, 16, 44, 36])
U = "https://www.ufficiocamerale.it/"
A = "https://www.aziende.it/"
verificate = [
 ("Costruttore (valvole)", "Tassalini SpA (Fratelli Tassalini)", "Peschiera Borromeo", "Fabbricazione di rubinetti e valvole (ATECO 28.14): produce un prodotto, quindi ha un ufficio tecnico", "Attiva", "circa 51", "11,7 M€", "Da chiamare", U + "2399/tassalini-spa"),
 ("Grossista / trasformatore", "Cofermetal Srl", "San Donato Milanese", "Metalli non ferrosi (ATECO 24.45), sito cofermetal.com", "Attiva", "50-99 (circa 65)", "28,7 M€", "Da chiamare", U + "4531/cofermetal-srl"),
 ("Officina / carpenteria", "Soluzioni Tecnologiche Avanzate Srl (S.T.A.)", "Mediglia", "Meccanica generale dei metalli (ATECO 25.53)", "Attiva", "14-16", "7,6 M€", "Da chiamare", U + "4679/soluzioni-tecnologiche-avanzate-srl-in-breve-sta-srl"),
 ("Officina / carpenteria", "Tornital Industrial Srl", "Peschiera Borromeo", "Meccanica generale (ATECO 25.53 / 25.62)", "Attiva", "circa 16", "4,4 M€", "Da chiamare", U + "6683/tornital-industrial-srl"),
 ("Officina / carpenteria", "S.C. Officine Meccaniche Srl", "Mediglia", "Meccanica generale dei metalli", "Attiva", "circa 13", "1,8 M€ (in calo)", "Da chiamare", U + "2653/sc-officine-meccaniche-srl"),
 ("Officina / stampaggio", "Metaldisco Srl", "Segrate", "Fucinatura e formatura dei metalli (ATECO 25.4)", "Non esplicito", "circa 13", "1,8 M€", "Da chiamare (verificare stato)", U + "1622/metaldisco-srl"),
]
scartate = [
 ("Officina / carpenteria", "Carpenteria Ambrosiana Srl", "Opera", "In liquidazione (segnalato da te)", "In liquidazione", "-", "-", "Scartata", "https://www.ufficiocamerale.it/1824/carpenteria-ambrosiana-srl-in-liquidazione"),
 ("Officina / carpenteria", "Inferro Srl", "Segrate", "Fonti discordanti: una la dà cessata", "Dubbio", "6", "0,7 M€ (2025)", "Scartata", U + "5106/inferro-srl"),
 ("Officina / carpenteria", "Elast Srl", "San Giuliano Milanese", "Tranciatura, fatturato basso", "Attiva", "non indicato", "0,3-0,6 M€", "Piccola", "https://www.informazione-aziende.it/Azienda_ELAST-SRL"),
 ("Costruttore macchine", "Co.Re.Ma. Snc", "San Giuliano Milanese", "Meccanica generale, microimpresa", "n.d.", "4", "n.d.", "Piccola", "https://atoka.io/public/it/azienda/corema-snc-di-gesmundo-marianna-c/fd346796dce0"),
 ("Officina / carpenteria", "Ossitaglio Sas", "Opera", "Formatura metalli, 2 addetti", "n.d.", "2", "n.d.", "Piccola", U + "9024/ossitaglio-sas-di-alongi-calogero-e-c"),
 ("Officina", "S.T.M. Srl (Special Tools Manufacturing)", "Melegnano", "Utensili, piccola", "Attiva", "6", "0,8 M€ (2023)", "Piccola", U + "4948/stm-srl"),
 ("Costruttore macchine", "Oleodinamica Dell'Avo Srl", "Rozzano", "Macchine di impiego generale, microimpresa", "n.d.", "4", "0,5 M€", "Piccola", U + "8867/oleodinamica-dellavo-srl"),
 ("Costruttore macchine", "Attrezzature Galvaniche Snc", "San Giuliano Milanese", "Telai per galvanica, microimpresa", "Attiva", "4-7", "n.d.", "Piccola", "https://atoka.io/public/it/azienda/attrezzature-galvaniche-snc-di-rando-dante-c/90998b12899f"),
]
nonver = [
 ("Officina / carpenteria", "Med Srl Carpenteria Metallica", "Opera", "Non trovata nei database con quell'indirizzo"),
 ("Officina / carpenteria", "SCM Società Costruzioni Meccaniche Srl", "Opera", "Non trovata (esistono omonime in altre regioni)"),
 ("Officina / carpenteria", "B.S.A. Srl", "San Giuliano Milanese", "Non trovata a quell'indirizzo; una B.S.A. di Milano (cuscinetti, 45 addetti) potrebbe essere un'altra"),
 ("Grossista tecnico", "Fasaf", "Peschiera Borromeo", "Non trovata a Peschiera; una Fasaf di Como ha 3 addetti"),
 ("Grossista tecnico", "Rimex Srl", "San Giuliano Milanese", "Non trovata a San Giuliano"),
 ("Grossista tecnico", "Profilati e Metalli Srl", "Segrate", "Non trovata"),
 ("Officina / carpenteria", "A.R. Carpenteria di Taccardi & C. Sas", "Peschiera Borromeo", "Non controllata"),
 ("Officina / carpenteria", "Calzati Giuseppe costruzioni industriali meccaniche", "Mediglia", "Non controllata"),
 ("Officina / carpenteria", "V.P. Srl", "Pioltello", "Non controllata"),
 ("Officina / carpenteria", "Gi.fe. Srl", "Pioltello", "Non controllata"),
 ("Officina / carpenteria", "F.g.z. Carp. Mecc. di Granata Roberto & C. Snc", "Paullo", "Non controllata"),
 ("Costruttore macchine", "Ri.me.mu. di Cinquini Nevio & C. Sas", "San Donato Milanese", "Non controllata"),
 ("Costruttore macchine", "Comasmo Tek", "Segrate", "Non controllata"),
 ("Grossista tecnico", "Eure Inox", "Peschiera Borromeo", "Non controllata"),
]
r = 5
def riga(vals, bold=False):
    global r
    for c, v in enumerate(vals, start=1):
        x = ws.cell(row=r, column=c, value=v); x.font = N; x.alignment, x.border = W, TH
    ws.row_dimensions[r].height = 40
    r += 1
def titolo(t):
    global r
    ws.cell(row=r, column=1, value=t).font = B
    r += 1
titolo("A. Verificate: attive, circa 10+ addetti — da chiamare")
for k, v in enumerate(verificate, start=1):
    riga([k, v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], None])
    ws.cell(row=r - 1, column=10).hyperlink = v[8]
r += 1; titolo("B. Piccole (circa 2-7 addetti), attive: da chiamare per imparare; spesso risponde il titolare")
for k, v in enumerate([x for x in scartate if x[7] == "Piccola"], start=1):
    riga([k, v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], None])
    ws.cell(row=r - 1, column=10).hyperlink = v[8]
r += 1; titolo("C. Scartate dopo la verifica (in liquidazione o cessate)")
for k, v in enumerate([x for x in scartate if x[7] == "Scartata"], start=1):
    riga([k, v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], None])
    ws.cell(row=r - 1, column=10).hyperlink = v[8]
r += 1; titolo("D. Non verificate — controlla su Google o ufficiocamerale.it prima di chiamare")
for k, v in enumerate(nonver, start=1):
    riga([k, v[0], v[1], v[2], v[3], "n.d.", "n.d.", "n.d.", "Da verificare", None, None])
r += 1
ws.cell(row=r, column=1, value="Come trovare altre aziende (il modo più rapido)").font = B
for k, t in enumerate([
    "Cerca il nome su Google con 'ufficiocamerale' oppure 'aziende.it': la scheda dice stato (attiva / in liquidazione), addetti e fatturato. Scarta chi è in liquidazione o ha meno di circa 8 addetti.",
    "Aggiungi comuni vicini oltre ai nove già usati (Lodi, Melzo, Cassina de' Pecchi, Vimodrone, Cologno Monzese, Assago, Buccinasco) e sempre le categorie 'carpenterie metalliche', 'costruzioni meccaniche', 'lavorazione lamiere', 'macchine per...'.",
    "Il sistema che ho usato per verificare non poteva leggere direttamente ufficiocamerale.it e registroaziende.it (bloccano i programmi): ho usato le informazioni indicizzate dalla ricerca. Qualche scheda può essere vecchia.",
    "Fonte per l'allargamento ideale: elenco soci delle associazioni di categoria (Assolombarda, UCIMU) e fiere del settore.",
], start=1):
    c = ws.cell(row=r + k, column=1, value=t); c.font, c.alignment = N, W
    ws.merge_cells(start_row=r + k, start_column=1, end_row=r + k, end_column=11); ws.row_dimensions[r + k].height = 32
ws.freeze_panes = "D5"

# ---------------- Copione
wc = wb.create_sheet("Copione")
wc["A1"] = "Copione dell'intervista (20-25 minuti)"; wc["A1"].font = H1
wc["A2"] = ("Regola unica: chiedi cosa è SUCCESSO l'ultima volta, non cosa farebbero. Non presentare l'idea di prodotto prima della domanda 12. "
            "Prendi appunti con numeri (ore, euro, persone, strumenti). Dopo ogni intervista compila la riga nel foglio Risposte entro un'ora.")
wc["A2"].font, wc["A2"].alignment = NOTE, W; wc.merge_cells("A2:C2"); wc.row_dimensions[2].height = 40
head(wc, 4, ["#", "Blocco", "Domanda / testo", ], [4, 22, 110])
wc.column_dimensions["D"].width = 50
wc.cell(row=4, column=4, value="Perché la chiedo").font, wc.cell(row=4, column=4).fill = H2, HF
copione = [
    ("Messaggio di invito (LinkedIn, email o telefono)",
     "Buongiorno [Nome], sono Andrei, ingegnere (Politecnico di Milano). Sto studiando come le PMI meccaniche lombarde gestiscono preventivi, distinte e documentazione tecnica. "
     "Non vendo nulla: cerco 20 minuti per capire come lavorate voi, e ricambio con quello che sto imparando dagli altri. Le va una telefonata di 20 minuti questa settimana, quando preferisce?",
     "Chiarisce che non è una vendita e riduce l'imbarazzo che hai indicato."),
    ("Apertura", "Grazie del tempo. Sono qui per imparare, non per vendere. Posso prendere appunti? Mi racconta in breve cosa fate e quante persone siete?",
     "Dimensione e prodotto reale."),
    ("Ultima volta (preventivo)", "Mi racconti l'ultima richiesta di preventivo che avete ricevuto: com'è arrivata, chi l'ha gestita, quanto tempo ci è voluto dall'arrivo all'invio.",
     "Comportamento passato, non opinioni. Misura le ore."),
    ("Ultima volta (documenti)", "Quando è arrivato un nuovo ordine, come passano disegni e documenti dall'ufficio commerciale a quello tecnico e alla produzione? Cosa si digita a mano?",
     "Individua il lavoro manuale su disegni, distinte, ordini."),
    ("Volume", "Quanti preventivi o ordini fate in una settimana? Quanti preventivi si trasformano in ordine?", "Dimensione del problema."),
    ("Chi lo fa", "Chi se ne occupa? Cosa succede quando quella persona è assente o lascia l'azienda? Avete cercato qualcuno per questo ruolo negli ultimi due anni?",
     "Collega il problema alla carenza di tecnici (Excelsior)."),
    ("Strumenti", "Quali programmi usate (gestionale, CAD, Excel, email)? Cosa non fanno e cosa fate a mano per compensare?", "Concorrente reale = foglio Excel."),
    ("Costo", "Se un preventivo sbagliato o in ritardo vi fa perdere un cliente, è già successo? Quando? Quanto valeva?", "Dolore con un numero."),
    ("Tentativi", "Avete già provato a risolverlo (software, consulente, assunzione)? Cosa avete pagato e come è andata?",
     "Chi ha già speso cerca davvero; chi non ha mai provato probabilmente non pagherà."),
    ("Priorità", "Tra i problemi dell'ufficio tecnico e commerciale, questo dove si colloca? Qual è il primo?", "Evita di inseguire un problema marginale."),
    ("Decisione", "Se doveste scegliere un software come questo, chi decide e chi firma? Che budget avete usato per l'ultimo strumento acquistato?",
     "Budget e processo d'acquisto."),
    ("Idea (solo ora)", "Sto valutando uno strumento che legge disegni e richieste e prepara dati, distinte o bozze di preventivo. Dove vi sembra utile e dove no? Cosa lo renderebbe inutilizzabile?",
     "Reazione dopo aver raccolto i fatti; cerca le obiezioni."),
    ("Impegno", "Potrei vedere un esempio anonimizzato di una richiesta e del preventivo? Sarebbe disposto a provare una bozza per due settimane? A che prezzo la considererebbe seria?",
     "Il test vero è un impegno (documento, tempo, soldi), non un 'interessante'."),
    ("Chiusura", "Chi altro dovrei sentire? Posso ricontattarla tra un mese per dirle cosa ho imparato?", "Genera contatti e permette il follow-up."),
]
for i, (blk, q, why) in enumerate(copione, start=1):
    r = 4 + i
    for c, v in enumerate([i, blk, q, why], start=1):
        x = wc.cell(row=r, column=c, value=v); x.font = B if c == 2 else N; x.alignment, x.border = W, TH
    wc.row_dimensions[r].height = 58
r = 4 + len(copione) + 2
wc.cell(row=r, column=1, value="Da evitare").font = B
for k, t in enumerate([
    "Chiedere 'lo comprereste?' o 'vi piacerebbe?': le risposte sono cortesie.",
    "Spiegare la soluzione prima di aver sentito i fatti.",
    "Accettare 'interessante' come risultato: chiudi sempre con un impegno concreto (documento, secondo incontro, prezzo).",
    "Registrare la chiamata senza consenso esplicito.",
], start=1):
    c = wc.cell(row=r + k, column=2, value=t); c.font, c.alignment = N, W
    wc.merge_cells(start_row=r + k, start_column=2, end_row=r + k, end_column=3)

# ---------------- Risposte
wr = wb.create_sheet("Risposte")
wr["A1"] = "Risposte e decisione (una riga per intervista)"; wr["A1"].font = H1
wr["A2"] = ("Compila dopo ogni conversazione. 'Ha il problema' = lo racconta con un episodio recente e un numero, senza che tu lo suggerisca. "
            "'Ha speso' = ha già pagato software, consulente o assunzione per risolverlo. 'Impegno' = ha concesso un documento, un secondo incontro o un prezzo.")
wr["A2"].font, wr["A2"].alignment = NOTE, W; wr.merge_cells("A2:K2"); wr.row_dimensions[2].height = 40
hr = ["# contatto", "Azienda", "Addetti", "Ore/settimana sul processo", "Preventivi o ordini/settimana", "Strumento attuale",
      "Ha il problema? (1 = sì)", "Ha speso per risolverlo? (1 = sì)", "Impegno concreto? (1 = sì)", "Prezzo accettabile (€/anno)", "Obiezione principale"]
head(wr, 4, hr, [10, 28, 9, 14, 14, 24, 12, 12, 12, 14, 50])
wr.row_dimensions[4].height = 48
for r in range(5, 20):
    wr.cell(row=r, column=1, value=r - 4).font = N
    for c in range(1, 12):
        wr.cell(row=r, column=c).border = TH
        if c > 1: wr.cell(row=r, column=c).font = BL
r = 21
lab = [("Interviste completate", '=COUNTA(B5:B19)'),
       ("Hanno il problema", '=SUM(G5:G19)'), ("Hanno già speso", '=SUM(H5:H19)'), ("Impegno concreto", '=SUM(I5:I19)'),
       ("Ore/settimana (mediana)", '=IFERROR(MEDIAN(D5:D19),"")'), ("Prezzo accettabile (mediana)", '=IFERROR(MEDIAN(J5:J19),"")'),
       ("Esito della regola", '=IF(B21<10,"Servono più interviste",IF(AND(B22>=B21*0.6,B23>=3,B24>=3),"Procedi a un pilota",IF(B22>=B21*0.4,"Cambia segmento o problema","Scarta la candidata")))')]
for k, (l, f) in enumerate(lab):
    wr.cell(row=r + k, column=1, value=l).font = B
    wr.merge_cells(start_row=r + k, start_column=1, end_row=r + k, end_column=1)
    wr.cell(row=r + k, column=2, value=f).font = B
wr.column_dimensions["A"].width = 26
r = r + len(lab) + 1
wr.cell(row=r, column=1, value="Regola di decisione (soglie mie, da rivedere)").font = B
for k, t in enumerate([
    "Almeno 10 interviste per ogni candidata prima di decidere.",
    "Procedi se almeno il 60% ha il problema, almeno 3 hanno già speso e almeno 3 concedono un impegno concreto.",
    "Se solo il 40-60% ha il problema: cambia segmento o riformula. Sotto il 40%: scarta.",
    "Se la ricorrenza dei ricavi o il prezzo accettabile non permette 1 M€ di ricavi con i clienti raggiungibili (vedi foglio Fase 2), la candidata non basta anche se il problema esiste.",
], start=1):
    c = wr.cell(row=r + k, column=1, value=t); c.font, c.alignment = N, W
    wr.merge_cells(start_row=r + k, start_column=1, end_row=r + k, end_column=11)
wb.save(OUT); print("salvato", OUT)
