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
ws["A1"] = "Fase 4 — lista di 15 contatti da intervistare (Lombardia, 10-49 addetti)"; ws["A1"].font = H1
ws["A2"] = ("Obiettivo: 15 conversazioni da 20-25 minuti, non vendite. Mix: 6 costruttori di macchine (ATECO 28), 6 officine/carpenterie (ATECO 25), "
            "3 grossisti tecnici (ATECO 46). Le prime righe sono PISTE trovate in ricerca web: non ho verificato dimensione e attività di nessuna, "
            "quindi vanno controllate (sito, bilancio) prima di contattarle. Le altre righe si riempiono con le fonti indicate sotto.")
ws["A2"].font, ws["A2"].alignment = NOTE, W; ws.merge_cells("A2:L2"); ws.row_dimensions[2].height = 48
cols = ["#", "Segmento", "Azienda", "Comune / provincia", "Perché è una buona candidata", "Verificato? (dimensione, attività)",
        "Chi contattare (ruolo)", "Canale", "Data contatto", "Esito", "Data intervista", "Note"]
head(ws, 4, cols, [4, 22, 30, 20, 40, 20, 24, 14, 12, 14, 12, 40])
seed = [
    ("Costruttore di macchine", "Imcar SpA", "area Monza", "Si descrive come costruttore di macchine per lamiera e impianti di saldatura e curvatura da oltre 60 anni"),
    ("Costruttore di macchine", "Arienti Costruzioni Meccaniche", "Albiate (MB)", "Elencata come produttrice di macchine per la lavorazione della lamiera"),
    ("Costruttore di macchine", "Laserevo", "Rovato (BS)", "Compare tra le aziende ATECO 28.49.09 di Brescia; l'attività va verificata"),
    ("Costruttore di macchine", "Co.ma.fer. Macchine", "Collebeato (BS)", "Compare tra le aziende ATECO 28.49.09 di Brescia; l'attività va verificata"),
    ("Costruttore di macchine", "Mcdue Automazioni", "Flero (BS)", "Compare tra le aziende ATECO 28.49.09 di Brescia; l'attività va verificata"),
    ("Costruttore di macchine", "Tonolini", "Nuvolera (BS)", "Compare tra le aziende ATECO 28.49.09 di Brescia; l'attività va verificata"),
]
quota = [("Officina / carpenteria", 6), ("Grossista tecnico", 3)]
r = 5
for i, (seg, az, com, perche) in enumerate(seed, start=1):
    for c, v in enumerate([i, seg, az, com, perche, "No"], start=1):
        x = ws.cell(row=r, column=c, value=v); x.font = BL if c == 6 else N; x.alignment, x.border = W, TH
    ws.cell(row=r, column=7, value="Responsabile ufficio tecnico / titolare").font = N
    r += 1
n = len(seed)
for seg, k in quota:
    for _ in range(k):
        n += 1
        for c, v in enumerate([n, seg] + [None] * 10, start=1):
            x = ws.cell(row=r, column=c, value=v); x.font = N; x.alignment, x.border = W, TH
        r += 1
for rr in range(5, r): ws.row_dimensions[rr].height = 34
r += 1
ws.cell(row=r, column=1, value="Dove trovare le altre aziende").font = B
for k, t in enumerate([
    "Elenchi soci di associazioni di categoria: UCIMU-Sistemi per produrre e Federmacchine (costruttori), Confindustria Lecco e Sondrio, Bergamo, Brescia, Monza e Brianza (officine e carpenterie).",
    "Camere di commercio / Registro Imprese per ATECO 28.xx, 25.xx, 46.6x, filtrando per provincia e per addetti (10-49). Gli elenchi gratuiti hanno limiti: usali per i nomi, poi controlla il sito.",
    "LinkedIn: cerca il ruolo (responsabile ufficio tecnico, responsabile commerciale, titolare) nell'azienda scelta e invia il messaggio del foglio Copione.",
    "Tieni fuori: aziende dove hai conoscenti stretti (preferisci estranei), grandi gruppi oltre 250 addetti, rivenditori senza produzione propria se la candidata è di officina.",
    "Rispetta la privacy: contatta solo ruoli aziendali (B2B), dichiara chi sei e perché scrivi, e se ti dicono di non scrivere più, annotalo e fermati.",
], start=1):
    c = ws.cell(row=r + k, column=1, value=t); c.font, c.alignment = N, W
    ws.merge_cells(start_row=r + k, start_column=1, end_row=r + k, end_column=12); ws.row_dimensions[r + k].height = 30
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
    ("Messaggio di invito (LinkedIn / email)",
     "Buongiorno [Nome], sono Andrei, ingegnere (Politecnico di Milano). Sto studiando come le PMI meccaniche lombarde gestiscono preventivi, distinte e documentazione tecnica. "
     "Non vendo nulla: cerco 20 minuti per capire come lavorate voi, e ricambio con quello che sto imparando dagli altri. Le va una telefonata questa settimana?",
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
