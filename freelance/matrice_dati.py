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
