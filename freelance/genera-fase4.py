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
ws["A1"] = "Fase 4 — contatti entro 20 km da San Donato Milanese (elenco da verificare)"; ws["A1"].font = H1
ws["A2"] = ("Obiettivo: 15 conversazioni da 20-25 minuti, per telefono o videochiamata (in pausa pranzo o dopo le 18). Qui ci sono 28 candidate: se rispondono 1 su 2, bastano per le 15. "
            "Fonte: elenchi per comune e categoria di reteimprese.it (nome, indirizzo, categoria). L'elenco NON dice quanti addetti hanno né se hanno il problema: "
            "molti sono piccolissimi o sono solo rivenditori. Prima di chiamare, apri la scheda e cerca il sito aziendale; scarta chi ha meno di circa 8-10 persone o fa riparazioni auto. "
            "Ordina per ordine di interesse: carpenterie e officine con più linee di lavoro, poi costruttori di macchine e impianti, poi grossisti.")
ws["A2"].font, ws["A2"].alignment = NOTE, W; ws.merge_cells("A2:L2"); ws.row_dimensions[2].height = 64
cols = ["#", "Segmento", "Azienda", "Comune", "Perché è nella lista (dall'elenco, non verificato)", "Scheda", "Verificato? (addetti, sito)",
        "Chi contattare (ruolo)", "Data contatto", "Esito", "Data intervista", "Note"]
head(ws, 4, cols, [4, 22, 34, 18, 44, 30, 18, 24, 12, 14, 12, 36])
R = "https://www.reteimprese.it/"
seed = [
 # officine e carpenterie
 ("Officina / carpenteria", "Carpenteria Ambrosiana Srl", "Opera", "Carpenteria, zona industriale di Opera", ""),
 ("Officina / carpenteria", "Med Srl Carpenteria Metallica", "Opera", "Carpenteria metallica", R + "carpenterie-metalliche/opera/azienda/109710"),
 ("Officina / carpenteria", "SCM Società Costruzioni Meccaniche Srl", "Opera", "Costruzioni meccaniche", R + "costruzioni-meccaniche/opera/azienda/69633"),
 ("Officina / carpenteria", "Ossitaglio Sas", "Opera", "Lavorazione lamiere (taglio)", R + "lamiere-lavorazione/opera/azienda/387731"),
 ("Officina / carpenteria", "Fratelli Tassalini Officina Meccanica SpA", "Peschiera Borromeo", "Officina meccanica con forma SpA: probabilmente strutturata", R + "officine-meccaniche/peschiera-borromeo/azienda/291815"),
 ("Officina / carpenteria", "Tornital Industrial Srl", "Peschiera Borromeo", "Officina meccanica", R + "officine-meccaniche/peschiera-borromeo/azienda/2103712"),
 ("Officina / carpenteria", "A.R. Carpenteria di Taccardi & C. Sas", "Peschiera Borromeo", "Carpenteria in ferro", R + "carpenterie-ferro/peschiera-borromeo/azienda/1947853"),
 ("Officina / carpenteria", "S.C. Officine Meccaniche Srl", "Mediglia", "Officina meccanica di precisione", R + "officine-meccaniche-precisione/mediglia/azienda/86760"),
 ("Officina / carpenteria", "Calzati Giuseppe costruzioni industriali meccaniche", "Mediglia", "Costruzioni industriali meccaniche", R + "costruzioni-meccaniche/mediglia/azienda/1892669"),
 ("Officina / carpenteria", "B.S.A. Srl", "San Giuliano Milanese", "Officina meccanica di precisione", R + "officine-meccaniche-precisione/san-giuliano-milanese/azienda/1097058"),
 ("Officina / carpenteria", "Elast Srl", "San Giuliano Milanese", "Tranciatura metalli", R + "tranciatura-metalli/san-giuliano-milanese/azienda/1519595"),
 ("Officina / carpenteria", "Metaldisco Srl", "Segrate", "Lavorazione lamiere e macchine", R + "lamiere-lavorazione-macchine/segrate/azienda/1475874"),
 ("Officina / carpenteria", "Inferro Srl", "Segrate", "Carpenteria metallica", R + "carpenterie-metalliche/segrate/azienda/2748353"),
 ("Officina / carpenteria", "V.P. Srl", "Pioltello", "Costruzioni meccaniche", R + "costruzioni-meccaniche/pioltello/azienda/1833186"),
 ("Officina / carpenteria", "Gi.fe. Srl", "Pioltello", "Tranciatura metalli", R + "tranciatura-metalli/pioltello/azienda/1488796"),
 ("Officina / carpenteria", "F.g.z. Carp. Mecc. di Granata Roberto & C. Snc", "Paullo", "Carpenteria meccanica e lamiere", R + "lamiere-commercio/paullo/azienda/33210"),
 ("Officina / carpenteria", "STM Special Tools Manufacturing Srl", "Melegnano", "Attrezzature speciali (verificare cosa produce)", ""),
 # costruttori di macchine e impianti
 ("Costruttore macchine / impianti", "Co.Re.Ma.", "San Giuliano Milanese", "Macchine per lavorazione alluminio", R + "alluminio-macchine-lavorazione/san-giuliano-milanese/azienda/1592176"),
 ("Costruttore macchine / impianti", "Ri.me.mu. di Cinquini Nevio & C. Sas", "San Donato Milanese", "Produzione macchine utensili", R + "macchine-utensili-produzione/san-donato-milanese/azienda/2593272"),
 ("Costruttore macchine / impianti", "Attrezzature Galvaniche Snc di Rando Dante & C.", "San Giuliano Milanese", "Macchine e impianti per galvanotecnica", R + "galvanotecnica-macchine-impianti-forniture/san-giuliano-milanese/azienda/181371"),
 ("Costruttore macchine / impianti", "Soluzioni Tecnologiche Avanzate Srl", "Mediglia", "Cilindri pneumatici e oleodinamici", R + "cilindri-pneumatici-oleodinamici-idraulici/mediglia/azienda/1840768"),
 ("Costruttore macchine / impianti", "Comasmo Tek", "Segrate", "Compare tra le aziende meccaniche di Segrate (verificare cosa produce)", ""),
 ("Costruttore macchine / impianti", "Oleodinamica Dell'Avo Srl", "Rozzano", "Oleodinamica (componenti e impianti)", ""),
 # grossisti tecnici
 ("Grossista tecnico", "Fasaf", "Peschiera Borromeo", "Macchine utensili, attrezzature e accessori", R + "macchine-utensili-attrezzature-accessori/peschiera-borromeo/azienda/177346"),
 ("Grossista tecnico", "Rimex Srl", "San Giuliano Milanese", "Commercio di macchine utensili", R + "macchine-utensili-commercio/san-giuliano-milanese/azienda/1961615"),
 ("Grossista tecnico", "Eure Inox", "Peschiera Borromeo", "Commercio di acciai inossidabili", R + "acciai-inossidabili-commercio/peschiera-borromeo/azienda/139430"),
 ("Grossista tecnico", "Profilati e Metalli Srl", "Segrate", "Profilati in ferro e acciaio", R + "profilati-ferro-acciaio/segrate/azienda/220727"),
 ("Grossista tecnico", "Cofermetal Srl", "San Donato Milanese", "Metalli non ferrosi e leghe", R + "metalli-non-ferrosi-leghe/san-donato-milanese/azienda/1420301"),
]
r = 5
for i, (seg, az, com, perche, link) in enumerate(seed, start=1):
    for c, v in enumerate([i, seg, az, com, perche, link or "cerca sul sito reteimprese.it", "No"], start=1):
        x = ws.cell(row=r, column=c, value=v); x.font = BL if c == 7 else N; x.alignment, x.border = W, TH
    if link: ws.cell(row=r, column=6).hyperlink = link
    ws.cell(row=r, column=8, value="Responsabile ufficio tecnico / titolare").font = N
    for c in range(9, 13): ws.cell(row=r, column=c).border = TH
    ws.row_dimensions[r].height = 34
    r += 1
r += 1
ws.cell(row=r, column=1, value="Come usarla").font = B
for k, t in enumerate([
    "Le 28 righe sono 'da verificare': l'elenco dà nome, indirizzo e categoria. Ho scelto quelle con attività plausibile (carpenteria, officina, macchine, ricambi) e scartato riparazioni auto e piccole botteghe evidenti, ma la dimensione resta sconosciuta.",
    "Prima di chiamare: 5 minuti sul sito aziendale o su Google. Se trovi un ufficio tecnico, un catalogo o più macchine di produzione, sono segnali di azienda adatta.",
    "Non servono viaggi: telefono in pausa pranzo (12:30-14:00) o dopo le 17:30, oppure una videochiamata. Se vogliono vederti, scegli un orario serale o il sabato mattina.",
    "Entro 20 km da San Donato: Mediglia, Peschiera Borromeo, San Giuliano, Melegnano, Opera, Rozzano, Segrate, Pioltello, Paullo. Per ampliare, usa le stesse categorie su reteimprese.it per altri comuni.",
    "Privacy: contatta solo ruoli aziendali (B2B), dì chi sei e perché scrivi, e se ti dicono di non scrivere più, annotalo e fermati.",
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
