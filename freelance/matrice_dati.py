# -*- coding: utf-8 -*-
# Dati dell'iterazione 1: matrice settore x funzione e candidate che ne escono.
# Tutte le celle sono IPOTESI di lavoro da filtrare (fasi 2 e 3), salvo dove la nota dice "V".

FUNZIONI = ["Preventivi e vendite", "Ordini e documenti", "Produzione e pianificazione", "Qualità e conformità",
            "Manutenzione e assistenza", "Logistica e magazzino", "Incassi e cassa", "Personale e turni",
            "Acquisti e fornitori", "Energia e costi"]

# etichetta, codici ATECO (divisioni a 2 cifre), celle della matrice (una per funzione; '' = non rilevante)
SETTORI = [
    ("Prodotti in metallo (25)", ["25"], [
        "Preventivo da disegno (DXF/STEP/PDF): peso, lavorazioni e tempi", "Ordini e conferme in formati diversi",
        "Pianificazione di macchine e commesse", "Certificati di collaudo e tracciabilità dei lotti",
        "Manutenzione programmata delle macchine utensili", "Spedizioni e imballi per conto terzi",
        "Incassi lenti da clienti industriali", "Turni e straordinari in produzione",
        "Acquisti di materia prima e prezzi dei metalli", "Costi energetici di forni e presse"]),
    ("Macchinari (28)", ["28"], [
        "Offerte tecniche configurabili", "Distinte base e ordini di ricambi", "Pianificazione di montaggio e collaudo",
        "Fascicolo tecnico e marcatura CE", "Assistenza post-vendita: manuali, ricambi, interventi",
        "Spedizioni internazionali e dogane", "Incassi a milestone di commessa", "Ufficio tecnico: carenza di progettisti",
        "Gestione dei fornitori di componenti", ""]),
    ("Riparazione e installazione macchine (33)", ["33"], [
        "Preventivi di intervento", "Rapporti di intervento e fatturazione", "Pianificazione dei tecnici sul campo",
        "Verifiche periodiche e certificati", "Contratti di manutenzione e scadenze", "Ricambi a magazzino",
        "Incassi da clienti industriali", "Disponibilità di tecnici", "Acquisto ricambi", ""]),
    ("Apparecchiature elettriche (27)", ["27"], [
        "Offerte per quadri e apparecchi su misura", "Distinte componenti e ordini", "Pianificazione di cablaggio e collaudo",
        "Test finali, marcatura CE e documentazione", "Assistenza e garanzia", "", "Incassi",
        "Carenza di tecnici e cablatori", "Componenti con tempi di consegna lunghi", ""]),
    ("Gomma e plastica (22)", ["22"], [
        "Preventivi per stampati e costo stampo", "Ordini programmati dai clienti", "Pianificazione di presse e stampi",
        "Tracciabilità lotti e conformità dei materiali", "Manutenzione di stampi e presse",
        "Magazzino materie e semilavorati", "Incassi", "Turni in produzione continua", "Prezzi dei polimeri",
        "Costi energetici delle presse"]),
    ("Chimica (20)", ["20"], [
        "Offerte tecniche e schede di prodotto", "Documenti di trasporto merci pericolose",
        "Pianificazione dei lotti di produzione", "Schede di sicurezza e CLP/REACH", "Manutenzione degli impianti",
        "Stoccaggio e tracciabilità dei lotti", "Incassi", "Turni continui", "Prezzi delle materie prime",
        "Costi energetici"]),
    ("Metallurgia (24)", ["24"], [
        "Offerte e listini per leghe", "Ordini e certificati di colata", "Pianificazione delle colate",
        "Certificati dei materiali e tracciabilità", "Manutenzione di forni e impianti",
        "Magazzino di rottami e prodotti", "Incassi", "Turni continui", "Acquisto di rottami e leghe",
        "Costi energetici elevati"]),
    ("Industrie alimentari (10)", ["10"], [
        "Offerte e listini per GDO e clienti professionali", "Ordini dei clienti e documenti di consegna",
        "Pianificazione della produzione e scadenze", "Rintracciabilità, HACCP e gestione dei richiami",
        "Manutenzione delle linee", "Magazzino a temperatura e scadenze", "Incassi (la GDO paga a lungo)",
        "Turni e stagionalità", "Acquisto di materie prime e prezzi", "Costi energetici del freddo"]),
    ("Tessile e abbigliamento (13, 14)", ["13", "14"], [
        "Campionari e offerte ai clienti", "Ordini e distinte di produzione",
        "Pianificazione della produzione con i terzisti", "Controllo qualità e tracciabilità dei fornitori", "",
        "Giacenze e resi", "Incassi", "Disponibilità di operai", "Approvvigionamento di tessuti", ""]),
    ("Mobili (31)", ["31"], [
        "Configuratore e preventivi su misura", "Ordini e distinte dei componenti", "Pianificazione di reparti e consegne",
        "Conformità dei materiali e marcatura", "Assistenza post-consegna", "Consegna e montaggio", "Incassi e acconti",
        "Turni in produzione", "Acquisto di pannelli e componenti", ""]),
    ("Commercio all'ingrosso (46)", ["46"], [
        "Preventivi con listini e codici articolo", "Ordini da PDF/email nel gestionale", "",
        "Documenti di origine e conformità dei prodotti", "", "Giacenze, riordino e picking", "Incassi e solleciti",
        "Turni di magazzino", "Confronto prezzi dei fornitori", "Costi di trasporto"]),
    ("Commercio al dettaglio (47)", ["47"], [
        "Promozioni e assistenza ai clienti", "Riordini e fatture dei fornitori", "", "", "", "Inventario e riordino",
        "Cassa e riconciliazioni", "Turni con regole di rotazione e coperture", "Acquisti e margini", "Costi energetici"]),
    ("Costruzioni specializzate (43)", ["43"], [
        "Computi e preventivi", "Ordini, bolle e documenti di cantiere", "Pianificazione delle squadre",
        "Sicurezza di cantiere e qualificazione dei subappaltatori", "Contratti di manutenzione degli impianti",
        "Materiali in cantiere", "SAL e incassi", "Disponibilità di operai", "Acquisti di materiali", ""]),
    ("Costruzione di edifici (41)", ["41"], [
        "Preventivi e capitolati", "Documenti di cantiere", "Avanzamento lavori e SAL", "Sicurezza e conformità", "",
        "Approvvigionamento in cantiere", "SAL e incassi", "Subappaltatori e squadre", "Acquisti e appalti", ""]),
    ("Trasporto terrestre (49)", ["49"], [
        "Preventivi per tratte e clienti", "DDT/CMR e fatturazione", "Pianificazione dei viaggi e dei mezzi",
        "Tempi di guida, tachigrafo e scadenze documentali", "Manutenzione e scadenze dei veicoli", "",
        "Incassi lenti e anticipi", "Carenza di autisti", "Carburante e pedaggi", "Costi del carburante"]),
    ("Logistica e magazzini (52)", ["52"], [
        "Offerte e tariffe", "Documenti di trasporto e dogane", "Pianificazione di banchine e carichi",
        "Tracciabilità e conformità dei lotti", "Manutenzione di carrelli e impianti", "Gestione del magazzino", "Incassi",
        "Turni con picchi di lavoro", "Subappalti di trasporto", "Costi energetici dei magazzini"]),
    ("Servizi per edifici (81)", ["81"], [
        "Preventivi e gare d'appalto", "Capitolati e rapporti di servizio", "Pianificazione delle squadre",
        "Controlli di qualità sui cantieri di pulizia", "Gestione delle attrezzature", "Prodotti e consumabili",
        "Incassi dai committenti", "Turni, presenze e assenze", "Acquisti di prodotti", ""]),
    ("Ristorazione (56)", ["56"], [
        "Prenotazioni e menu", "Ordini ai fornitori e fatture", "Pianificazione della cucina", "HACCP e autocontrollo", "",
        "Scorte e sprechi", "Cassa e riconciliazioni", "Turni e costo del lavoro", "Food cost e ordini", "Costi energetici"]),
    ("Alloggio (55)", ["55"], [
        "Prenotazioni dirette e prezzi dinamici", "Documenti degli ospiti", "", "", "", "",
        "Incassi e commissioni delle piattaforme", "Turni del personale", "Acquisti", "Costi energetici"]),
    ("Agenzie del lavoro (78)", ["78"], [
        "Ricerca e abbinamento dei candidati", "Documenti dei lavoratori", "", "Conformità e documentazione", "", "",
        "Fatturazione e incassi", "Gestione dei turni dei somministrati", "", ""]),
    ("Assistenza sociale e RSA (87, 88)", ["87", "88"], [
        "", "Documenti degli ospiti e fatture", "Pianificazione dell'assistenza", "Documentazione sanitaria e conformità",
        "", "Gestione di farmaci e materiali", "Incassi e rette", "Turni e assenze del personale", "Acquisti",
        "Costi energetici"]),
    ("Auto: commercio e riparazione (45)", ["45"], [
        "Preventivi di riparazione", "Ordini di ricambi", "Pianificazione dell'officina", "Conformità e garanzie",
        "Assistenza e richiami", "Magazzino ricambi", "Incassi", "Disponibilità di meccanici", "Acquisto di ricambi", ""]),
    ("Studi legali e contabili (69)", ["69"], [
        "Preventivi e parcelle", "Acquisizione dei documenti e delle fatture dei clienti", "",
        "Conformità antiriciclaggio e privacy", "", "", "Incassi delle parcelle", "", "", ""]),
]

# note sui segnali verificati che valgono per tutti i settori
SEGNALI = [
    "Incassi e cassa (V): Cribis, giugno 2026: solo il 42% delle imprese paga puntuale; Intrum 2024: ~81 giorni di incasso medi in Italia contro ~50 in Europa.",
    "Personale e turni (V): Excelsior Lombardia, aprile 2026: nel 46% dei casi le imprese prevedono difficoltà a trovare i profili; nelle aree tecniche e di progettazione il 64,8%.",
    "Ordini, documenti e produzione (da verificare): una fonte riporta che solo il 13% delle PMI ha un livello digitale avanzato; il dato va controllato sul rapporto originale.",
    "Qualità e conformità: dove la nota dice 'V' nelle candidate, l'obbligo è documentato (Regolamento Macchine, PPWR, NIS2); per il resto sono ipotesi.",
]

# candidate: id, settore (etichetta), indice funzione (0-9), idea di prodotto, permanenza 1-5, segnale V/I,
# concorrenza (mio giudizio, da verificare), già valutata (Sì/No), nota
CANDIDATE1 = [
    ("M01", "Prodotti in metallo (25)", 0, "Preventivo automatico da disegno per officine e carpenterie (peso, lavorazioni, tempi)", 5, "I", "Media", "No", ""),
    ("M02", "Prodotti in metallo (25)", 3, "Certificati di collaudo 3.1 e tracciabilità dei lotti per officine", 5, "I", "Media", "No", "Collegata alla vecchia idea dei report di collaudo."),
    ("M03", "Prodotti in metallo (25)", 2, "Pianificazione commesse e macchine per officine da 10-50 addetti", 5, "I", "Alta", "No", "ERP e MES già presenti."),
    ("M04", "Macchinari (28)", 4, "Assistenza post-vendita: manuali, ricambi e interventi per costruttori di macchine", 5, "I", "Media", "Sì", "Già valutata in Fase 2 e 3 (punteggio 3,96)."),
    ("M05", "Macchinari (28)", 0, "Offerte tecniche configurabili per costruttori di macchine", 5, "I", "Media", "No", ""),
    ("M06", "Macchinari (28)", 3, "Fascicolo tecnico e marcatura CE (Regolamento Macchine)", 3, "V", "Media", "Sì", "Già valutata (Certifico CEM4 presente)."),
    ("M07", "Macchinari (28)", 7, "Ufficio tecnico: automazione di distinte base e documentazione", 5, "V", "Media", "No", "Segnale: carenza di personale tecnico (Excelsior Lombardia, 64,8% di difficoltà)."),
    ("M08", "Riparazione e installazione macchine (33)", 4, "Contratti di manutenzione e scadenze per imprese di assistenza", 5, "I", "Media", "No", ""),
    ("M09", "Riparazione e installazione macchine (33)", 2, "Pianificazione dei tecnici sul campo per piccole imprese di assistenza", 5, "I", "Alta", "No", "Field service già coperto da molti strumenti."),
    ("M10", "Apparecchiature elettriche (27)", 3, "Test finali e documentazione di prodotto (CE, RED) per produttori di apparecchi", 3, "V", "Media", "No", "Normativa documentata; permanenza media."),
    ("M11", "Gomma e plastica (22)", 2, "Gestione stampi e pianificazione presse per stampatori", 5, "I", "Media", "No", ""),
    ("M12", "Gomma e plastica (22)", 3, "Tracciabilità lotti e conformità (PPWR, contatto alimentare) per plastica", 3, "V", "Media", "No", "PPWR dal 12/08/2026."),
    ("M13", "Chimica (20)", 3, "Schede di sicurezza e CLP/REACH per aziende chimiche", 4, "I", "Media", "No", "Da verificare sul mercato."),
    ("M14", "Metallurgia (24)", 9, "Monitoraggio e riduzione dei costi energetici per metallurgia", 5, "I", "Alta", "No", "Servizi energetici già diffusi."),
    ("M15", "Industrie alimentari (10)", 3, "Rintracciabilità, HACCP e gestione dei richiami per industrie alimentari", 5, "I", "Alta", "No", ""),
    ("M16", "Industrie alimentari (10)", 1, "Etichette e schede prodotto per alimentari (allergeni, più lingue)", 5, "I", "Media", "No", ""),
    ("M17", "Tessile e abbigliamento (13, 14)", 2, "Campionari e produzione con i terzisti per tessile e abbigliamento", 5, "I", "Media", "No", "Distretto di Como: da verificare con interviste."),
    ("M18", "Mobili (31)", 0, "Configuratore e preventivi per produttori di mobili su misura", 5, "I", "Media", "No", "Distretto della Brianza."),
    ("M19", "Commercio all'ingrosso (46)", 0, "Preventivatore con listini e codici per distributori tecnici", 5, "I", "Media", "Sì", "Già valutata (punteggio 3,29)."),
    ("M20", "Commercio all'ingrosso (46)", 6, "Incassi e solleciti automatici per grossisti", 5, "V", "Alta", "Sì", "Già valutata (punteggio 3,58)."),
    ("M21", "Commercio all'ingrosso (46)", 1, "Ordini da PDF/email nel gestionale per grossisti", 5, "I", "Media", "No", ""),
    ("M22", "Commercio all'ingrosso (46)", 8, "Confronto prezzi dei fornitori e riordino per grossisti", 5, "I", "Alta", "No", ""),
    ("M23", "Commercio al dettaglio (47)", 7, "Turni con regole di rotazione e coperture per negozi (tua esperienza)", 5, "I", "Alta", "No", "Software di turni molto presenti."),
    ("M24", "Costruzioni specializzate (43)", 3, "Sicurezza di cantiere e qualificazione dei subappaltatori", 4, "I", "Media", "No", "Verificare gli obblighi vigenti per i cantieri."),
    ("M25", "Costruzioni specializzate (43)", 0, "Computi e preventivi per impiantisti e imprese edili", 5, "I", "Alta", "No", ""),
    ("M26", "Costruzione di edifici (41)", 2, "Avanzamento lavori e SAL per imprese edili", 5, "I", "Alta", "No", ""),
    ("M27", "Trasporto terrestre (49)", 3, "Tempi di guida, tachigrafo e scadenze documentali per autotrasportatori", 5, "I", "Media", "No", "Autotrasporto in calo: -22% di imprese dal 2015."),
    ("M28", "Trasporto terrestre (49)", 1, "TMS leggero per piccoli autotrasportatori (DDT/CMR, fatturazione)", 4, "I", "Media", "Sì", "Già valutata in Fase 2."),
    ("M29", "Logistica e magazzini (52)", 7, "Turni per magazzini e conto terzi", 5, "I", "Media", "Sì", "Già valutata in Fase 2."),
    ("M30", "Logistica e magazzini (52)", 1, "Documenti e tracciamento per spedizionieri", 4, "I", "Media", "Sì", "Già valutata in Fase 2."),
    ("M31", "Servizi per edifici (81)", 7, "Turni, presenze e controllo per imprese di pulizia e servizi per edifici", 5, "I", "Media", "No", ""),
    ("M32", "Servizi per edifici (81)", 0, "Preventivi e capitolati per gare di pulizia", 4, "I", "Media", "No", ""),
    ("M33", "Ristorazione (56)", 7, "Turni e costo del lavoro per ristoranti", 5, "I", "Alta", "No", ""),
    ("M34", "Ristorazione (56)", 8, "Food cost e ordini ai fornitori per ristoranti", 5, "I", "Alta", "No", ""),
    ("M35", "Alloggio (55)", 0, "Prenotazioni dirette e prezzi dinamici per strutture ricettive", 5, "I", "Alta", "No", ""),
    ("M36", "Agenzie del lavoro (78)", 6, "Timesheet, cedolini e fatturazione per agenzie del lavoro", 5, "I", "Media", "No", ""),
    ("M37", "Assistenza sociale e RSA (87, 88)", 7, "Turni e documentazione del personale per RSA e cooperative sociali", 5, "I", "Media", "No", ""),
    ("M38", "Auto: commercio e riparazione (45)", 1, "Ordini di ricambi e preventivi per officine e carrozzerie", 5, "I", "Alta", "No", ""),
    ("M39", "Studi legali e contabili (69)", 1, "Acquisizione di documenti e fatture per studi contabili", 5, "I", "Alta", "No", ""),
    ("M40", "Trasversale", 7, "Ufficio tecnico e back-office: automazione di report, conversioni e verifiche", 5, "V", "Media", "No", "Segnale: carenza di personale tecnico in Lombardia; vale per molti settori."),
]


# ---------------------------------------------------------------- Fase 2 e 3 delle 13 candidate
# id, chiave (inizio del testo dell'idea in CANDIDATE1), etichetta Fase 2, codici ATECO, prezzi annui (bassa, base, alta; IPOTESI),
# lettura, permanenza, tipo di segnale
FASE23 = [
    ("M40", "Ufficio tecnico e back-office", "Ufficio tecnico e back-office (automazione)", ["25", "28", "27", "22", "46"],
     (1200, 3000, 8000), "Motore comune ai documenti tecnici; la domanda nasce dalla carenza di tecnici.", 5, "Carenza di manodopera"),
    ("M01", "Preventivo automatico da disegno", "Preventivo da disegno (officine)", ["25"], (600, 1800, 4000),
     "Un'offerta italiana che prezzi da DXF/STEP non è stata trovata (Almacam Webquote è la più vicina). Da verificare con le officine.", 5, "Dolore operativo permanente"),
    ("M02", "Certificati di collaudo 3.1", "Certificati 3.1 e tracciabilità (officine)", ["25"], (600, 1500, 3000),
     "Nessun software specifico trovato; probabilmente coperto da ERP e MES.", 5, "Dolore operativo permanente"),
    ("M07", "Ufficio tecnico: automazione di distinte", "Distinte base da disegni 2D (macchine)", ["28"], (1500, 3500, 8000),
     "Nessun prodotto italiano trovato per l'estrazione da disegni 2D; la ricerca accademica indica oltre il 95% di rilevamento.", 5, "Carenza di manodopera"),
    ("M21", "Ordini da PDF/email", "Ordini da PDF/email (grossisti)", ["46"], (800, 2000, 5000),
     "Strumenti globali presenti (Parseur, Esker, OpusCapita); poco pensato per PMI italiane.", 5, "Dolore operativo permanente"),
    ("M03", "Pianificazione commesse e macchine", "Pianificazione commesse (officine)", ["25"], (1000, 2400, 5000),
     "Mercato di MES e job shop già popolato (TeamSystem, Epoptia da 1.200 €, Hexagon Workplan).", 5, "Dolore operativo permanente"),
    ("M05", "Offerte tecniche configurabili", "Offerte configurabili (macchine)", ["28"], (1500, 3500, 8000),
     "Esistono CPQ per prodotti complessi (Camos, Salesforce a 200 €/utente/mese); poco per PMI italiane.", 5, "Dolore operativo permanente"),
    ("M22", "Confronto prezzi dei fornitori", "Confronto prezzi fornitori (grossisti)", ["46"], (600, 1500, 4000),
     "Concorrenza non ancora cercata.", 5, "Dolore operativo permanente"),
    ("M23", "Turni con regole di rotazione", "Turni per negozi", ["47"], (300, 900, 2400),
     "Molto presidiato e a prezzi bassi (Skello, Factorial, Deputy).", 5, "Carenza di manodopera"),
    ("M31", "Turni, presenze e controllo", "Turni per pulizie e servizi", ["81"], (600, 1800, 4000),
     "Stessi strumenti dei negozi; il controllo dei cantieri potrebbe differenziare.", 5, "Carenza di manodopera"),
    ("M33", "Turni e costo del lavoro", "Turni per ristoranti", ["56"], (300, 900, 2400),
     "Molto presidiato e a prezzi bassi.", 5, "Carenza di manodopera"),
    ("M34", "Food cost e ordini", "Food cost per ristoranti", ["56"], (200, 600, 1500),
     "Strumenti da 25-30 € (Microrecipes, fogli di calcolo): bassa disponibilità a pagare.", 5, "Dolore operativo permanente"),
    ("M27", "Tempi di guida, tachigrafo", "Tachigrafo e tempi di guida", ["494"], (400, 1000, 2400),
     "Mercato servito (Geotab, Descartes SmartAnalysis a pagamento per file, app Qdriver): serve un prezzo molto basso.", 5, "Obbligo di legge"),
]

# punteggi provvisori (mio giudizio) dopo la Fase 3: urgente, permanente, budget, ricorrenti, scalabilità, canale, concorrenza (5 = poca), vantaggio, testabile
PUNTEGGI2 = {
    "Ufficio tecnico: automazione di distinte": [4, 5, 4, 4, 3, 3, 4, 5, 3],
    "Ufficio tecnico e back-office": [4, 5, 4, 4, 4, 3, 2, 4, 4],
    "Preventivo automatico da disegno": [3, 5, 4, 4, 3, 3, 4, 4, 5],
    "Offerte tecniche configurabili": [3, 5, 4, 4, 3, 4, 3, 4, 3],
    "Certificati di collaudo 3.1": [3, 5, 3, 3, 4, 3, 3, 4, 4],
    "Ordini da PDF/email": [3, 5, 3, 4, 4, 3, 2, 3, 4],
    "Turni, presenze e controllo": [3, 5, 3, 5, 4, 3, 1, 2, 3],
    "Turni con regole di rotazione": [3, 5, 2, 5, 4, 3, 1, 3, 4],
    "Turni e costo del lavoro": [3, 5, 2, 5, 4, 3, 1, 3, 4],
    "Tempi di guida, tachigrafo": [4, 5, 2, 4, 3, 3, 2, 2, 3],
    "Food cost e ordini": [3, 5, 2, 4, 4, 3, 1, 1, 4],
    "Pianificazione commesse e macchine": [3, 5, 3, 4, 2, 3, 1, 2, 3],
}

# finalista (etichetta Fase 2), concorrente / segnale, tipo, cosa offre, prezzo trovato, fonte
COMP2 = [
    ("Preventivo da disegno (officine)", "Almacam (Alma Italia, Torino)", "Software CAD/CAM per lamiera",
     "Assembly2cam riconosce le parti di un assieme CAD per preventivi e produzione; Webquote è un servizio di preventivazione online",
     "Non trovato", "https://it.almacam.com/wp-content/uploads/2025/05/IT-2025-Almacam-Pass-brochure-web-2.pdf"),
    ("Preventivo da disegno (officine)", "RAS (piegatrici), Sophia (247tailorsteel), app Autodesk Inventor", "Programmazione ed esportazione",
     "Importano STEP/DXF per programmare macchine o esportare i pezzi; non fanno il preventivo", "Non applicabile",
     "https://www.ras-online.de/en/products/software/updowncenter-2-software/"),
    ("Certificati 3.1 e tracciabilità (officine)", "Nessun software specifico trovato", "Lacuna o incertezza",
     "Il certificato 3.1 va collegato a colata, lotti e pezzi lavorati; non ho trovato prodotti dedicati", "Non applicabile",
     "https://blog.projectmaterials.com/quick-answers/epc/en-10204-certificate-types/"),
    ("Distinte base da disegni 2D (macchine)", "Ricerca accademica (Univ. di Tampere)", "Ricerca",
     "Estrazione di distinte da disegni con AI, oltre il 95% di rilevamento; non è un prodotto", "Non applicabile",
     "https://trepo.tuni.fi/handle/10024/232922"),
    ("Distinte base da disegni 2D (macchine)", "Funzioni BOM di ERP e PLM (es. ECI)", "ERP/PLM",
     "Generazione di distinte dentro i sistemi di progettazione; l'estrazione da disegni 2D è poco coperta", "Non trovato",
     "https://ecisolutions.com/blog/manufacturing/the-importance-of-ai-and-innovation-for-erps-unleashing-the-power-of-ai-bom-builder"),
    ("Ordini da PDF/email (grossisti)", "Parseur", "Email parser con IA e OCR", "Estrae dati da email e PDF, anche scansionati",
     "Non trovato", "https://parseur.com/it/estrazione-dati/automazione-elaborazione-ordini-ecommerce"),
    ("Ordini da PDF/email (grossisti)", "Esker, OpusCapita, Fellowmind", "Piattaforme B2B", "Acquisizione ordini da email e PDF verso l'ERP",
     "Non trovato", "https://www.esker.com/it/risorse/ebook/om-ordini-multicanale-b2b/"),
    ("Pianificazione commesse (officine)", "TeamSystem MES, Epoptia MES, Hexagon Workplan, Fusion Operations", "MES e job shop",
     "Pianificazione, tracciabilità e commesse per officine", "Epoptia: da 1.200 € (Capterra)",
     "https://www.capterra.it/directory/30855/job-shop/software"),
    ("Offerte configurabili (macchine)", "Camos CPQ; Salesforce Revenue Cloud", "CPQ",
     "Configurazione di prodotti complessi e preventivi", "Salesforce: 200 €/utente/mese", "https://www.capterra.it/directory/30904/cpq/software"),
    ("Turni per negozi, pulizie e ristoranti", "Skello", "Software di turni", "Turni, presenze e gestione del personale",
     "Circa 5-6 €/dipendente/mese oppure 49-79 €/sede/mese (fonti discordanti)",
     "https://www.skello.io/it/blog/software-rilevazione-presenze-migliori-strumenti-prezzi"),
    ("Turni per negozi, pulizie e ristoranti", "Factorial, Deputy, Planday", "Software di turni", "Turni e presenze",
     "Factorial da 5 €/dipendente/mese; Deputy da 6,50 $ (Capterra)", "https://www.capterra.it/software/147589/deputy"),
    ("Tachigrafo e tempi di guida", "Geotab, Descartes SmartAnalysis, Qdriver", "Telematica e analisi",
     "Scarico remoto e analisi dei tempi di guida e riposo", "SmartAnalysis: pagamento per file; prezzi italiani non trovati",
     "https://smartcompliance.descartes.com/solutions/what-is-tachograph-analysis-software/"),
    ("Food cost per ristoranti", "Microrecipes, RatioChef, KitchenNmbrs", "Food cost",
     "Ricette, costi e import delle fatture dei fornitori", "Microrecipes da 30 €; foglio di calcolo 24,90 €",
     "https://www.capterra.it/software/204894/microrecipes"),
]

SINTESI2 = [
    "Fase 3 sulle 13 candidate: dove ho trovato un vuoto e dove no. Un'offerta italiana che prezzi un pezzo direttamente da un disegno DXF/STEP non è emersa (Almacam Webquote è la più vicina); "
    "non ho trovato prodotti italiani che estraggano distinte base da disegni 2D; per i certificati 3.1 non ho trovato software dedicato. Sono i tre punti dove la concorrenza sembra più debole.",
    "Presidiati e a prezzi bassi: turni (circa 5-6 €/dipendente/mese), food cost (25-30 €), tachigrafo (servizi a pagamento per file), MES per officine, estrazione di ordini da PDF (strumenti globali).",
    "Un vuoto di ricerca non è un vuoto di mercato: va verificato con le interviste. Le 'prime' candidate dopo la Fase 3 sono le distinte da disegni 2D, il motore comune per l'ufficio tecnico, il preventivo da disegno e le offerte configurabili.",
]

# ---------------------------------------------------------------- Perù (domanda del 01/11/2026)
PERU = [
    ("Costituire un'impresa", "Guide del 2026: 15-30 giorni lavorativi e 500-1.500 soles. La Camera di Commercio di Lima (dati Doing Business) stima circa 26 giorni e 8 procedure contro 4 giorni e 6 procedure in Cile. Da dicembre 2024 la riserva del nome è solo online (SID-SUNARP); 225.666 imprese registrate così a ottobre 2025.",
     "https://laley.pe/como-crear-tu-empresa-en-peru/", "Non ho trovato il punteggio B-READY del Perù; le cifre variano molto tra le fonti."),
    ("Informalità", "Circa il 70% degli occupati è informale (INEI, 2025); l'88,6% dei lavoratori informali è in imprese da 1 a 10 persone; circa 5,5 milioni di attività informali (ENAHO 2023); secondo paese più informale del Sud America.",
     "https://infomercado.pe/informalidad-laboral-en-peru-llega-al-70-segun-el-inei/", "Significa anche concorrenza informale sui prezzi."),
    ("Crescita e inflazione", "Crescita 2025: 3,4%. FMI: 2,8% nel 2026, inflazione 2,5%. Banca Mondiale: 2,7% nel 2026.",
     "https://elperuano.pe/noticia/293519-fmi-eleva-a-28-su-prevision-de-crecimiento-de-peru-en-el-2026-con-una-inflacion-de-25", "Macro stabile."),
    ("Reddito per abitante", "PIL nominale pro capite previsto per il 2027: circa 11.800 dollari (Cile: circa 20.400).",
     "https://www.peru-retail.com/economia-peruana-podria-superar-a-la-chilena-en-2027-despues-de-38-anos-segun-el-fmi/",
     "Potere d'acquisto molto inferiore a quello lombardo (per l'Italia non ho cercato il dato)."),
    ("Stabilità politica", "Nono presidente in 15 anni; S&P avverte di un possibile declassamento nei prossimi due anni; il rischio paese percepito è alto, ma l'investimento privato è cresciuto.",
     "https://www.larepublica.co/globoeconomia/los-retos-economicos-que-tendra-el-noveno-presidente-de-peru-en-15-anos-4409383", "Esito delle elezioni 2026 non verificato."),
    ("Digitalizzazione delle PMI", "Nel 2023 solo il 24,7% delle PMI teneva registri contabili e il 3,3% usava sistemi di gestione completi. Esistono fornitori locali di ERP (Defontana, Kame, Ramo).",
     "https://portalerp.com/latam/noticia/del-excel-al-erp-el-paso-que-puede-marcar-la-diferencia-en-las-pymes-peruanas", "Grande bisogno non servito, ma anche bassa propensione a pagare."),
    ("Miniere (ingegneria)", "Portafoglio di 66 progetti per oltre 64 miliardi di dollari, circa il 70% di rame; 44 progetti (44,9 miliardi) senza data di avvio; esecuzione prevista 2026-2029: 10,7 miliardi.",
     "https://energiminas.com/2026/06/09/cartera-de-proyectos-de-inversion-minera-2026-contempla-66-proyectos-por-un-valor-superior-a-us-64075-millones/",
     "Domanda di ingegneria concreta ma legata a grandi committenti e al calendario."),
]
PERU_LETTURA = [
    "La sua tesi ha una parte vera: la digitalizzazione delle PMI è molto indietro, quindi c'è un bisogno non servito, e la concorrenza di prodotti software strutturati è probabilmente meno aggressiva.",
    "La tua obiezione regge su altri punti: facilità di aprire un'impresa non è facilità di crescere; il potere d'acquisto è molto più basso; l'informalità alimenta la concorrenza sui prezzi; l'instabilità politica pesa sul rischio; da qui non conosci il mercato né hai una rete.",
    "Proposta: non usare il Perù come mercato di partenza, ma come ipotesi di espansione da testare a basso costo con la tua ragazza (5 interviste a titolari di PMI peruviane sugli stessi problemi).",
]
